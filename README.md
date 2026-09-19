# RFID Wisp

# Still in development - reading and writing tags is not implemented yet

A cross-platform (Windows/Linux/Android) app for reading and writing the
MIFARE Classic 1K RFID tags used by QIDI's multi-color filament boxes.

This repository hosts only the built releases; there is no source code here.
The desktop versions are portable downloads - no installation is required.

See [CHANGELOG.md](CHANGELOG.md) for release notes.

## Downloads

Each release provides one archive per platform - grab yours from the
[Releases page](https://github.com/ThorSc/RFIDwisp/releases/latest):

| Platform | File | Notes |
|----------|------|-------|
| Windows (x64) | `RFIDwisp-windows-x64.zip`  | Unzip, then run `rfid_wisp.exe` from the extracted folder. |
| Linux (x64)   | `RFIDwisp-linux-x64.tar.gz` | `tar xzf RFIDwisp-linux-x64.tar.gz`, then run `./RFIDwisp-linux-x64/rfid_wisp`. |
| Android       | `RFIDwisp-android.apk`      | Open it on the phone and allow the installation, see "Android: installing the APK" below. |
| Printer (Klipper) | `rfid_bridge.py` | Optional companion module for the printer, not for the PC - see "Klipper integration" below. |

### Windows: blocked by Smart App Control?

`rfid_wisp.exe` isn't code-signed yet, so Windows 11's Smart App Control (and
plain SmartScreen) may flag it on first run. Signing is planned, but until
then:

- If you see a SmartScreen prompt ("Windows protected your PC"), click
  **More info → Run anyway**.
- If Smart App Control blocks it outright (no "Run anyway" option shown),
  the only workaround right now is turning Smart App Control off entirely:
  **Windows Security → App & browser control → Smart App Control settings →
  Off**. Note that this is one-way - once turned off, it can only be turned
  back on via a clean Windows install/reset.

### Android: installing the APK

The APK is not distributed through Google Play, so Android asks for permission
to install it:

1. Download `RFIDwisp-android.apk` on the phone (or copy it there).
2. Open it. When Android says that installing apps from this source is not
   allowed, open **Settings** from the prompt and allow it for the app you
   used (browser or file manager).
3. Confirm the installation. Play Protect may ask for a check, since the app
   does not come from the Play Store.

To update, install a newer APK over the old one; settings are kept. RFID
readers are not supported on Android yet, so the Reader tab is missing in the
settings there.

## Features

Runs on Windows, Linux and Android. Implemented so far:

- Splash screen with the logo while the app starts up.
- Main window with a menu bar (File, Help) and a status bar showing the
  current state and the app version.
- User interface in English and German; follows the system language by
  default and can be switched in **File → Settings**.
- RFID reader selection in the settings (Windows and Linux): lists the PC/SC readers that can
  read and write RFID tags. Each reader's real capability is tested instead of
  trusting its name, and non-RFID smart card devices (e.g. a YubiKey) are never
  opened. One reader can be marked as the default reader; at startup the app
  checks that it is reachable and usable and shows the result in the status
  bar.
- **QIDI Data** frame in the main window (from the Python version): choose a
  printer and one of its QIDI boxes and see what the box reports for each of
  its four slots - material, vendor, colour, and the Spoolman spool number and
  vendor stored on the RFID tag. The last chosen printer is remembered.
- Printer management in the settings: any number of printers, each with a
  name and the address of its Moonraker service.
- Spoolman settings: the server address, and a switch to use Spoolman or not.
- Background check for a newer release at startup (can be switched off in
  the settings). If one is found, a download link appears in the status bar.
- Optional Klipper companion module (`rfid_bridge.py`) that reads the RFID
  data of the QIDI box on the printer and keeps the active spool in
  Moonraker/Spoolman in sync (see "Klipper integration").
- **Help → About** dialog with version, copyright and license information.

## Requirements

- A PC/SC-compatible RFID reader (tested with the ACS ACR122) for reading and
  writing tags:
  - **Windows** - PC/SC support (WinSCard) is built in; the reader's driver
    must be installed.
  - **Linux** - install and run `pcscd` (e.g. `sudo apt install pcscd` /
    `sudo systemctl enable --now pcscd`); this also installs `libpcsclite1`,
    which the app loads at runtime. Your reader's CCID/ACS driver is needed
    too if the generic CCID driver does not recognize it.
- **Windows** - 64-bit Windows 10 or 11. The Microsoft Visual C++
  Redistributable (x64) must be installed; it already is on most systems.
- **Android** - Android 7.0 (API 24) or newer, any ABI (arm64, arm, x86_64).
  RFID readers are not supported on Android yet.
- **Linux** - 64-bit distribution with GTK 3 (`libgtk-3-0`). The
  executables are built on Ubuntu 24.04, so a distribution of similar
  age or newer is required.

## Usage

1. Start the app; the main window appears once the splash screen is done.
2. Open **File → Settings …**. The settings are grouped on tabs:
   - **General** - language (system default, English or German) and whether
     to check for a new version at startup.
   - **Reader** (Windows and Linux only) - pick one of the RFID readers that were found (use the
     refresh button to search again after plugging one in). Tick **Use as
     default reader** to mark the selected reader as the default; only one
     reader can be the default.
   - **Printers** - manage your printers. Pick a saved printer in the list
     to edit its **Name** and **Moonraker address** (e.g.
     `http://192.168.1.50:7125`), use **+** to add a printer and the bin to
     delete the selected one. A missing `http://` is added automatically.
   - **Spoolman** - the **Spoolman address** (e.g.
     `http://192.168.1.100:7912`) and **Use Spoolman**. With the option off,
     Spoolman is not contacted at all, even if an address is saved.

   Nothing is saved until you press **OK**; **Cancel** discards all changes.
   If a printer or the Spoolman address is invalid, **OK** takes you to it and
   marks the error.
3. The main window shows the **QIDI Data** frame:
   - Pick the **Printer** (from the ones set up in the settings) and the
     **Box**. When the app starts or the printer changes, the printer is asked
     how many QIDI boxes it has and the first box is read. If the printer
     cannot be reached, the frame says so in red; the circular arrow next to it
     checks again.
   - **Read Box Data** reads the selected box again. Each box is read only
     when you ask for it, so after switching to another box press the button.
   - Each slot shows its **Material**, **Vendor** and **Color** as reported by
     the box, the Spoolman spool **Number** and the **Vendor in Spoolman**, both
     read from the RFID tag (they need the optional `rfid_bridge` module on the
     printer; the vendor name also needs a Spoolman address in the settings).
   - The dot in front of a slot is red if the slot is empty, green if it holds
     filament and cyan if it is feeding the extruder. Only slot 0 is shown by
     default; **Show all slots** shows all four.
4. At startup the app checks that the default reader is connected and
   usable, while the splash screen is shown. The status bar then shows
   `Reader: <name>`, or a red message if the reader is missing, is not an
   RFID reader, or has a tag on it that is not a readable MIFARE Classic 1K.
   A reader with no tag on it counts as usable, because RFID support can only
   be verified with a tag present.
5. At startup the app also checks in the background whether a newer release
   is available (unless switched off in the settings). If so, a link
   "New version … available" appears in the status bar; clicking it opens
   the download page. The check only asks GitHub for the latest release
   number; nothing else is sent.
6. **File → Exit** closes the app (desktop only), **Help → About** shows
   version and license information.

## Klipper integration (`rfid_bridge`)

To have your QIDI printer capture the raw RFID payload of each loaded spool
during printing (so it can be correlated with the tag data written by the app)
and automatically keep Fluidd/Spoolman's active spool in sync, install
`rfid_bridge.py` as a Klipper extra:

1. Download [`rfid_bridge.py`](https://github.com/ThorSc/RFIDwisp/releases/latest/download/rfid_bridge.py)
   (it is attached to every release, and also available in this repository)
   and copy it into Klipper's `klippy/extras/` directory on the printer.
2. Add to `printer.cfg`:

   ```ini
   [rfid_bridge]
   box_stepper_count: 4
   moonraker_url: http://127.0.0.1:7125    # optional, shown default
   moonraker_api_key:                      # optional, only needed if
                                            # Moonraker requires auth for
                                            # local requests
   ```

3. Restart Klipper (`RESTART` or `FIRMWARE_RESTART`).

It works by capturing the raw 16-byte `fm17550_read_card_return` response
QIDI's own firmware already reads for each box slot - the same data the
box uses internally - by monkey-patching `mcu.CommandQueryWrapper.send` in
memory for the lifetime of the Klipper process, and by tracking the active
`box_stepper slotN` via the public `stepper_enable` callback API. The
patch is purely observational (it never changes QIDI's own
request/response, and never modifies a QIDI-shipped file on disk) and is
automatically undone by any Klipper `RESTART`/`FIRMWARE_RESTART`.

Query the captured data via `RFID_BRIDGE_STATUS` in the Klipper console, or
`GET /printer/objects/query?rfid_bridge` through Moonraker.

### Automatic active-spool reporting to Moonraker/Spoolman

`rfid_bridge` decodes the Spoolman spool number from the tag data (bytes
14-15, big-endian, as written by RFID Wisp) and POSTs it to Moonraker's
built-in Spoolman integration (`/server/spoolman/spool_id`), so the active
spool shown in Fluidd/Spoolman follows the box automatically - no manual
selection needed. This requires the `[spoolman]` component to be configured
in `moonraker.conf`.

It reports whenever the decoded spool number for the currently active slot
changes, and again whenever a print job starts (detected by polling
`print_stats`, since Klipper has no dedicated print-start event). The HTTP
call runs on a background thread via a queue so a slow or unreachable
Moonraker never blocks the reactor; an unset/blank tag is reported as
`spool_id: null`, clearing the active spool. Verified against a live
Moonraker/Fluidd/Spoolman stack (Moonraker v0.8.0).

The print-start report only has data to send if `rfid_bridge` has already
captured a fresh RFID read for the active slot. Enable the QIDI BOX's own
**"Check upon startup"** option (Filament page -> settings gear, in Fluidd
or on the printer's touchscreen) so every loaded spool is re-read
automatically on each printer/Klipper restart (takes about 1-2 minutes) -
otherwise a spool whose tag was rewritten after the last box read can be
missing from `last_raw` and gets silently skipped instead of reported. The
same page has a manual **"Re read filament information"** button per slot
for forcing a fresh read without a full restart (only while that slot's
filament isn't fed through the box hub). Do not rely on a slicer-side
`SET_ACTIVE_SPOOL` G-code call as a substitute or a "just in case" fallback:
it runs later in the print than `rfid_bridge`'s own report and will silently
overwrite the RFID-derived spool with whatever fixed ID is hardcoded in the
filament profile.

## License

RFID Wisp is licensed under the [MIT License](LICENSE). The license texts of
the Flutter framework and the packages the app depends on are bundled with the
app and shown under **Help → About → View licenses**.
