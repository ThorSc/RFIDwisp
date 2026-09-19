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
#   - Whenever the decoded spool number for the active slot changes, or a
#     print job starts, the spool id is POSTed to Moonraker's
#     "/server/spoolman/spool_id" endpoint on a background thread (never
#     blocking the reactor). Moonraker owns the actual Spoolman
#     conversation and consumption tracking from there.
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

import json
import logging
import queue
import threading
import urllib.error
import urllib.request

import mcu as mcu_module

MOONRAKER_REQUEST_TIMEOUT = 5.0


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

        self._patch_mcu_send()
        self.printer.register_event_handler("klippy:connect", self._connect)

        gcode = self.printer.lookup_object('gcode')
        gcode.register_command(
            "RFID_BRIDGE_STATUS", self.cmd_RFID_BRIDGE_STATUS,
            desc=self.cmd_RFID_BRIDGE_STATUS_help)

    def _patch_mcu_send(self):
        cls = mcu_module.CommandQueryWrapper
        if getattr(cls, '_rfid_bridge_orig_send', None) is not None:
            return  # already patched (e.g. by a prior [rfid_bridge] load)
        orig_send = cls.send
        bridge = self

        def patched_send(wrapper_self, data=(), minclock=0, reqclock=0):
            resp = orig_send(wrapper_self, data, minclock, reqclock)
            try:
                if (wrapper_self._response == "fm17550_read_card_return"
                        and isinstance(resp, dict)
                        and resp.get("status") == 1):
                    bridge._handle_raw_read(resp.get("data"))
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
        logging.info("rfid_bridge: slot%d raw=%s", slot, raw.hex())
        self._maybe_report_spool(slot, raw, reason="slot_read")

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

    def _try_register_slots(self, eventtime):
        stepper_enable = self.printer.lookup_object('stepper_enable')
        for slot in list(self._pending_slots):
            name = "box_stepper slot%d" % slot
            try:
                enable = stepper_enable.lookup_enable(name)
            except Exception:
                continue
            enable.register_state_callback(self._make_callback(slot))
            self._pending_slots.discard(slot)
            self._registered_slots.add(slot)
            logging.info("rfid_bridge: registered '%s'", name)
        if not self._pending_slots:
            return self.printer.get_reactor().NEVER
        return eventtime + 2.0

    def _make_callback(self, slot):
        def callback(print_time, is_enable):
            if is_enable:
                self.current_slot = slot
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
        slot = self.current_slot
        if slot is None:
            return
        raw = self.last_raw.get(slot)
        if raw is None:
            return
        self._maybe_report_spool(slot, raw, reason="print_start", force=True)

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
        if not self.last_raw:
            gcmd.respond_info("RFID_BRIDGE_STATUS: no data captured yet")
        else:
            for slot in sorted(self.last_raw):
                gcmd.respond_info(
                    "slot%d: %s" % (slot, self.last_raw[slot].hex()))
        gcmd.respond_info(
            "last reported spool_id: %s (reason: %s)"
            % (self.last_reported_spool_id, self.last_report_reason))

    def get_status(self, eventtime):
        return {
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
            "last_reported_spool_id": self.last_reported_spool_id,
            "last_report_time": self.last_report_time,
            "last_report_reason": self.last_report_reason,
        }


def load_config(config):
    return RFIDBridge(config)
