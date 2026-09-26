# RFID bridge for the QIDI multi-color box.
#
# Captures the raw 16-byte fm17550_read_card_return payload per box slot,
# correlated with the slot that was active when it arrived, without
# touching any QIDI-shipped file on disk (mcu.py, stepper_enable.py,
# box_rfid.so, box_stepper.so). Also reports the spool number encoded on
# the tag to Moonraker's built-in Spoolman "active spool" tracking, so
# Fluidd/Spoolman follow the box's spool changes automatically.
#
# How it works:
#   - stepper_enable's EnableTracking.register_state_callback() (public
#     Klipper API) tells us which "box_stepper slotN" is currently active,
#     tracked purely in memory (no /tmp files).
#   - CommandQueryWrapper.send() in klippy's own mcu.py is monkey-patched
#     at runtime (in-memory only, mcu.py on disk is never modified) to
#     intercept every "fm17550_read_card_return" response - the same
#     response QIDI's own box_rfid code consumes to populate
#     multi_color_controller. We only observe it; we never touch the
#     handler QIDI itself registered, so their own read logic is
#     unaffected.
#   - The last raw read of every slot is cached. Whenever a slot becomes
#     active, a read arrives for the active slot, or a print job starts,
#     the spool number cached for the *active* slot is POSTed to
#     Moonraker's
#     "/server/spoolman/spool_id" endpoint on a background thread (never
#     blocking the reactor). Moonraker owns the actual Spoolman
#     conversation and consumption tracking from there.
#   - A spool removed from a slot is detected two ways: primarily by
#     polling multi_color_controller's own "slots.states" (backed by a
#     real per-slot runout sensor - the same signal Fluidd's spool grid
#     reads, via save_variables, to show a slot as present/empty), which
#     reacts immediately; as a fallback (older firmware without that
#     object, or a slot the RFID reader hasn't revisited yet), several
#     consecutive failed fm17550 reads for a slot also clear it. Either
#     way the cached tag is dropped and "no spool" is reported for that
#     slot, same as a real empty read would.
#
# Confirmed byte layout (matches multi_color_controller.config exactly):
#   data[0] = filament_type_id, data[1] = color_id, data[2..] = 0 (QIDI
#   only ever writes/uses the first ~3 bytes). Bytes 3-15 are free for
#   custom use; RFID Wisp's own tag writer puts the Spoolman spool number
#   in bytes 14-15 (big-endian) - see FilamentSpool.to_tag_bytes().
#
# printer.cfg:
#   [rfid_bridge]
#   box_stepper_count: 4
#   moonraker_url: http://127.0.0.1:7125    # optional, shown default
#   moonraker_api_key:                      # optional, only needed if
#                                            # Moonraker requires auth for
#                                            # local requests
#
# Query via Moonraker: GET /printer/objects/query?rfid_bridge
# Or:  RFID_BRIDGE_STATUS

import hashlib
import json
import logging
import queue
import threading
import urllib.error
import urllib.request

import mcu as mcu_module

# Version of this file, independent of the app's version, so that copies
# moved back and forth between the repository and the printer can be told
# apart: the higher number is the newer one. The patch number is raised
# automatically when a commit changes this file (.githooks/pre-commit,
# enabled with `git config core.hooksPath .githooks`); raise major or minor
# by hand. The release workflow refuses a changed file with an unchanged
# version or a lower one than the last release
# (scripts/check_bridge_version.py).
RFID_BRIDGE_VERSION = "1.0.2"


def _own_checksum():
    # Short checksum of this file with normalized line endings, so a copy
    # that went through Windows (CRLF) still matches. Two copies with the
    # same version but different checksums mean one was edited without
    # raising the version.
    try:
        with open(__file__, "rb") as f:
            data = f.read().replace(b"\r\n", b"\n")
        return hashlib.sha256(data).hexdigest()[:8]
    except Exception:
        return "unknown"


RFID_BRIDGE_CHECKSUM = _own_checksum()

MOONRAKER_REQUEST_TIMEOUT = 5.0

# A slot is only declared empty after this many consecutive failed reads
# (status != 1), not on the first one - a single failed read can just be a
# transient misread of a tag that is still physically present (vibration,
# a slightly-off rotor position, ...). Chosen empirically; raise it if
# slots still get flagged empty spuriously, lower it if a truly removed
# spool takes too long to be noticed.
EMPTY_READ_THRESHOLD = 3


class RFIDBridge:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.slot_count = config.getint('box_stepper_count', 4)
        self.moonraker_url = config.get(
            'moonraker_url', 'http://127.0.0.1:7125').rstrip('/')
        self.moonraker_api_key = config.get('moonraker_api_key', None)

        self.current_slot = None       # int or None
        self.last_raw = {}             # slot(int) -> bytes(16)
        self.last_raw_time = {}        # slot(int) -> reactor monotonic time
        self._empty_read_count = {}    # slot(int) -> consecutive failed reads
        self._slot_occupied = {}       # slot(int) -> bool, last known sensor state
        self._pending_slots = set(range(self.slot_count))
        self._registered_slots = set()

        self.last_reported_spool_id = None  # int or None
        self.last_report_time = None
        self.last_report_reason = None
        self._print_state = None
        self._notify_queue = queue.Queue()
        self._notify_thread = threading.Thread(
            target=self._notify_worker, daemon=True)
        self._notify_thread.start()

        logging.info("rfid_bridge: version %s (checksum %s)",
                     RFID_BRIDGE_VERSION, RFID_BRIDGE_CHECKSUM)
        self._patch_mcu_send()
        self.printer.register_event_handler("klippy:connect", self._connect)

        gcode = self.printer.lookup_object('gcode')
        gcode.register_command(
            "RFID_BRIDGE_STATUS", self.cmd_RFID_BRIDGE_STATUS,
            desc=self.cmd_RFID_BRIDGE_STATUS_help)

    def _patch_mcu_send(self):
        cls = mcu_module.CommandQueryWrapper
        # A Klipper RESTART recreates all printer objects inside the same
        # process: imported modules and this patch survive it. Always
        # point the patch at the newest bridge instance, otherwise reads
        # would keep going to the stale instance of the first load.
        cls._rfid_bridge_instance = self
        if getattr(cls, '_rfid_bridge_orig_send', None) is not None:
            return  # already patched (e.g. by a prior [rfid_bridge] load)
        orig_send = cls.send

        def patched_send(wrapper_self, data=(), minclock=0, reqclock=0):
            resp = orig_send(wrapper_self, data, minclock, reqclock)
            try:
                if (wrapper_self._response == "fm17550_read_card_return"
                        and isinstance(resp, dict)):
                    if resp.get("status") == 1:
                        cls._rfid_bridge_instance._handle_raw_read(
                            resp.get("data"))
                    else:
                        cls._rfid_bridge_instance._handle_failed_read(
                            resp.get("status"))
            except Exception:
                logging.exception("rfid_bridge: error handling RFID response")
            return resp

        cls._rfid_bridge_orig_send = orig_send
        cls.send = patched_send

    def _handle_raw_read(self, data):
        if self.current_slot is None or data is None:
            return
        raw = bytes(data)
        slot = self.current_slot
        self.last_raw[slot] = raw
        self.last_raw_time[slot] = self.printer.get_reactor().monotonic()
        self._empty_read_count[slot] = 0
        logging.info("rfid_bridge: slot%d raw=%s", slot, raw.hex())
        self._maybe_report_spool(slot, raw, reason="slot_read")

    def _handle_failed_read(self, status):
        """A read for the active slot came back without a tag.

        QIDI's own reader polls every slot's tag continuously (that's how
        multi_color_controller stays live), so a *lone* failed read is
        normal - the rotor can be slightly off position for an instant.
        Only clear the cached tag once several reads in a row fail, which
        means the spool was actually removed (or a slot was always empty
        and is being read for the first time).
        """
        slot = self.current_slot
        if slot is None:
            return
        count = self._empty_read_count.get(slot, 0) + 1
        self._empty_read_count[slot] = count
        if count < EMPTY_READ_THRESHOLD:
            return
        if slot not in self.last_raw:
            return  # already empty, nothing to clear
        logging.info(
            "rfid_bridge: slot%d has no tag after %d consecutive failed "
            "reads (status=%s) - clearing cached spool_id %s",
            slot, count, status, self._decode_spool_id(self.last_raw[slot]))
        del self.last_raw[slot]
        self.last_raw_time.pop(slot, None)
        self._maybe_report_spool(slot, None, reason="slot_empty")

    def _connect(self):
        """Track which box_stepper slot is active (public callback API).

        The box hardware finishes its own init/handshake some time after
        Klipper starts, so "box_stepper slotN" objects may not exist yet
        at klippy:connect. Keep retrying until all slots are found (or
        forever, at a low rate - harmless if some slots never appear).
        """
        reactor = self.printer.get_reactor()
        reactor.register_timer(self._try_register_slots, reactor.NOW)
        reactor.register_timer(self._poll_print_state, reactor.NOW)
        reactor.register_timer(self._poll_slot_occupancy, reactor.NOW)

    def _try_register_slots(self, eventtime):
        stepper_enable = self.printer.lookup_object('stepper_enable')
        for slot in list(self._pending_slots):
            # Older QIDI firmware registers the stepper as "box_stepper
            # slotN", newer firmware (Max4 01.01.06.05) as plain "slotN".
            enable = name = None
            for candidate in ("box_stepper slot%d" % slot, "slot%d" % slot):
                try:
                    enable = stepper_enable.lookup_enable(candidate)
                except Exception:
                    continue
                name = candidate
                break
            if enable is None:
                continue
            enable.register_state_callback(self._make_callback(slot))
            self._pending_slots.discard(slot)
            self._registered_slots.add(slot)
            logging.info("rfid_bridge: registered '%s'", name)
        if not self._pending_slots:
            return self.printer.get_reactor().NEVER
        return eventtime + 2.0

    def _poll_slot_occupancy(self, eventtime):
        """Cross-check the cached tag against QIDI's own presence sensor.

        QIDI's box has a dedicated runout sensor per slot - that is what
        Fluidd's own spool grid actually reads (via
        multi_color_controller's "slots.states", mirrored into
        save_variables) to show a slot as present/empty, not the RFID tag.
        It reacts the instant a spool is pulled, so it is both faster and
        more reliable than inferring "empty" from repeated failed RFID
        reads (_handle_failed_read) - which stays in place as a fallback
        for firmware without this object, or slots the reader hasn't
        revisited yet.
        """
        try:
            mcc = self.printer.lookup_object('multi_color_controller')
            states = mcc.get_status(eventtime)['slots']['states']
        except Exception:
            return eventtime + 2.0
        for slot in range(self.slot_count):
            raw_state = states.get('slot%d' % slot)
            if raw_state is None:
                continue
            occupied = bool(raw_state)
            was_occupied = self._slot_occupied.get(slot)
            self._slot_occupied[slot] = occupied
            if was_occupied and not occupied:
                self._on_slot_emptied(slot)
        return eventtime + 2.0

    def _on_slot_emptied(self, slot):
        self._empty_read_count[slot] = 0
        if slot not in self.last_raw:
            return  # already empty (or never read) - nothing to clear
        logging.info(
            "rfid_bridge: slot%d emptied (multi_color_controller runout "
            "sensor) - clearing cached spool_id %s",
            slot, self._decode_spool_id(self.last_raw[slot]))
        del self.last_raw[slot]
        self.last_raw_time.pop(slot, None)
        if slot == self.current_slot:
            self._maybe_report_spool(slot, None, reason="slot_empty_sensor")

    def _make_callback(self, slot):
        def callback(print_time, is_enable):
            if not is_enable:
                return
            self.current_slot = slot
            try:
                # Every slot's tag was read (and cached in last_raw) at
                # startup; now that this slot is the active one, report
                # *its* spool instead of whichever slot was read last.
                self._report_active_slot(reason="slot_active")
            except Exception:
                logging.exception("rfid_bridge: error reporting active slot")
        return callback

    def _poll_print_state(self, eventtime):
        """Detect a print job starting.

        Klipper has no dedicated "print started" event, only the
        print_stats state string, so this polls it at a low rate and
        reacts on the transition into "printing".
        """
        try:
            print_stats = self.printer.lookup_object('print_stats')
            state = print_stats.get_status(eventtime).get('state')
        except Exception:
            state = None
        if state == 'printing' and self._print_state != 'printing':
            self._on_print_start()
        self._print_state = state
        return eventtime + 2.0

    def _on_print_start(self):
        self._report_active_slot(reason="print_start", force=True)

    def _report_active_slot(self, reason, force=False):
        """Report the spool cached for the currently active slot, if any."""
        slot = self.current_slot
        if slot is None:
            return
        raw = self.last_raw.get(slot)
        if raw is None:
            return
        self._maybe_report_spool(slot, raw, reason=reason, force=force)

    def _maybe_report_spool(self, slot, raw, reason, force=False):
        spool_id = self._decode_spool_id(raw)
        if not force and spool_id == self.last_reported_spool_id:
            return
        self.last_reported_spool_id = spool_id
        self.last_report_time = self.printer.get_reactor().monotonic()
        self.last_report_reason = reason
        self._notify_queue.put(spool_id)

    @staticmethod
    def _decode_spool_id(raw):
        """Spool number as written by FilamentSpool.to_tag_bytes(): the
        last two bytes of the block, big-endian. 0 means "no spool
        written" and is reported as None (clears the active spool)."""
        if raw is None or len(raw) < 16:
            return None
        spool_id = (raw[14] << 8) | raw[15]
        return spool_id or None

    def _notify_worker(self):
        while True:
            spool_id = self._notify_queue.get()
            try:
                self._post_active_spool(spool_id)
                logging.info(
                    "rfid_bridge: reported active spool_id=%s to Moonraker",
                    spool_id)
            except Exception:
                logging.exception(
                    "rfid_bridge: failed to report spool_id=%s to Moonraker",
                    spool_id)

    def _post_active_spool(self, spool_id):
        url = self.moonraker_url + "/server/spoolman/spool_id"
        # Moonraker's get_int() tries int(None) and raises HTTP 400 if
        # "spool_id" is present but null - omit the key entirely to clear
        # the active spool instead of sending {"spool_id": null}.
        body_obj = {} if spool_id is None else {"spool_id": spool_id}
        body = json.dumps(body_obj).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.moonraker_api_key:
            headers["X-Api-Key"] = self.moonraker_api_key
        req = urllib.request.Request(
            url, data=body, method="POST", headers=headers)
        with urllib.request.urlopen(
                req, timeout=MOONRAKER_REQUEST_TIMEOUT) as resp:
            resp.read()

    cmd_RFID_BRIDGE_STATUS_help = (
        "Show the last raw fm17550 RFID payload captured per box slot")

    def cmd_RFID_BRIDGE_STATUS(self, gcmd):
        gcmd.respond_info("rfid_bridge version %s (checksum %s)" % (
            RFID_BRIDGE_VERSION, RFID_BRIDGE_CHECKSUM))
        known_slots = self._registered_slots | set(self.last_raw)
        if not known_slots:
            gcmd.respond_info("RFID_BRIDGE_STATUS: no data captured yet")
        else:
            for slot in sorted(known_slots):
                raw = self.last_raw.get(slot)
                if raw is None:
                    gcmd.respond_info("slot%d: empty" % slot)
                else:
                    gcmd.respond_info(
                        "slot%d: %s (spool_id: %s)" % (
                            slot, raw.hex(), self._decode_spool_id(raw)))
        gcmd.respond_info(
            "last reported spool_id: %s (reason: %s)"
            % (self.last_reported_spool_id, self.last_report_reason))

    def get_status(self, eventtime):
        return {
            "version": RFID_BRIDGE_VERSION,
            "checksum": RFID_BRIDGE_CHECKSUM,
            "current_slot": self.current_slot,
            "registered_slots": sorted(self._registered_slots),
            "pending_slots": sorted(self._pending_slots),
            "last_raw": {
                "slot%d" % slot: data.hex()
                for slot, data in self.last_raw.items()
            },
            "last_raw_time": {
                "slot%d" % slot: t
                for slot, t in self.last_raw_time.items()
            },
            "spool_ids": {
                "slot%d" % slot: self._decode_spool_id(data)
                for slot, data in self.last_raw.items()
            },
            "last_reported_spool_id": self.last_reported_spool_id,
            "last_report_time": self.last_report_time,
            "last_report_reason": self.last_report_reason,
        }


def load_config(config):
    return RFIDBridge(config)
