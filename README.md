# RFID Wisp

A cross-platform (Windows/Linux/Android) app for reading and writing the
MIFARE Classic 1K RFID tags used by QIDI's multi-color filament boxes (the
QIDI Boxes that are connected to QIDI Plus4 and QIDI Max4 printers).

This repository hosts only the built releases; there is no source code here.
The desktop versions are portable downloads - no installation is required.

See [CHANGELOG.md](CHANGELOG.md) for release notes.

## Downloads

Each release provides one archive per platform - grab yours from the
[Releases page](https://github.com/ThorSc/RFIDwisp/releases/latest):

| Platform | File | Notes |
|----------|------|-------|
| Windows (x64) | `RFIDwisp-windows-x64-setup.exe` | Installer: Start menu entry, optional desktop icon, clean uninstall. Installing a newer version upgrades the existing install. |
| Windows (x64) | `RFIDwisp-windows-x64.zip`  | Portable: unzip, then run `rfid_wisp.exe` from the extracted folder. |
| Linux (x64, Debian/Ubuntu) | `RFIDwisp-linux-x64.deb` | Installer: `sudo apt install ./RFIDwisp-linux-x64.deb` adds a menu entry (`rfid_wisp` on PATH); `sudo apt remove rfid-wisp` uninstalls. |
| Linux (x64)   | `RFIDwisp-linux-x64.tar.gz` | Portable, any distribution: `tar xzf RFIDwisp-linux-x64.tar.gz`, then run `./RFIDwisp-linux-x64/rfid_wisp`. |
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

To update, install a newer APK over the old one; settings are kept. This works
from version 0.3.1 on: the APKs up to 0.3.0 were each signed with a different
key, which Android refuses to update. If you have such a version, uninstall it
once before installing 0.3.1 (its settings are lost this one time).

The **RFID Tag** frame uses the phone's own NFC reader, so there is no Reader
tab in the settings. NFC must be switched on, and the phone's NFC chip has to
support MIFARE Classic (most phones with an NXP chip do, many with a Broadcom
chip do not - the free app "MIFARE Classic Tool" tells you). Press **Read Tag**
or **Write Tag**, then hold the tag to the back of the phone.

## Features

Runs on Windows, Linux and Android. Implemented so far:

- Splash screen with the logo while the app starts up.
- Main window with a menu bar (File, Help) and a status bar showing the
  current state and the app version.
- User interface in English, German and Ukrainian; follows the system
  language by default and can be switched in **File → Settings**, where each
  language is shown with its flag.
- RFID reader selection in the settings (Windows and Linux; Android uses its
  built-in NFC reader): lists the PC/SC readers that can
  read and write RFID tags. Each reader's real capability is tested instead of
  trusting its name, and non-RFID smart card devices (e.g. a YubiKey) are never
  opened. One reader can be marked as the default reader; at startup the app
  checks that it is reachable and usable and shows the result in the status
  bar.
- **QIDI Data** frame in the main window (from the Python version): choose a
  printer and one of its QIDI boxes and see what the box reports for each of
  its four slots - material, vendor, colour, and the Spoolman spool number and
  vendor stored on the RFID tag. The last chosen printer is remembered.
- **RFID Tag** frame in the main window, below QIDI Data (from the Python
  version; on Android with the phone's own NFC reader, which needs no
  choosing, and without the QR Code frame): reads the filament data of the MIFARE Classic 1K
  tag on the default reader and writes it. A tag can be written for a new
  spool (created in Spoolman on the fly, optionally from an existing Spoolman
  filament) or for an existing Spoolman spool, or - with Spoolman switched
  off - from material, vendor, colour and a spool number entered by hand. A
  write is read back to check it.
- **QR Code** frame beside the RFID Tag frame (a third of the width, as high as
  the RFID Tag frame): the QR code of the spool shown there - spool number,
  the QIDI box material, vendor and colour, and the Spoolman vendor and colour
  - with the app logo in its centre. **Export** saves it as a DIN A4 PDF (QR
  code 20 x 20 mm) where you choose in the system's save dialog; **Print**
  prints that page on the default printer, and is disabled if there is no
  printer.
- Export and import of all settings as a JSON file, in the settings dialog.
  An imported file only fills in the dialog and applies with **OK**.
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
- Optional, to print the QR code of a spool: a printer that is set up in the
  system (on Linux through CUPS). Saving the QR code as a PDF file needs
  nothing.
- **Windows** - 64-bit Windows 10 or 11. The Microsoft Visual C++
  Redistributable (x64) must be installed; it already is on most systems.
- **Android** - Android 7.0 (API 24) or newer, any ABI (arm64, arm, x86_64).
  Tags are read and written with the phone's own NFC reader, which has to
  support MIFARE Classic.
- **Linux** - 64-bit distribution with GTK 3 (`libgtk-3-0`). The
  executables are built on Ubuntu 24.04, so a distribution of similar
  age or newer is required.

## Usage

1. Start the app; the main window appears once the splash screen is done.
2. Open **File → Settings …**. The settings are grouped on tabs:
   - **General** - language (system default, English, German or Ukrainian) and whether
     to check for a new version at startup. **Export settings …** saves all
     settings (language, update check, reader, printers, Spoolman) to a JSON
     file you choose; **Import settings …** loads them from such a file, e.g.
     to move to another computer or phone or to keep a backup. An import only
     fills in the dialog: like every other change it applies when you press
     **OK** and is dropped by **Cancel**. Settings the file does not contain
     stay as they are.
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
     printer; the vendor name also needs a Spoolman address in the settings),
     and the **Weight**: the remaining weight of that spool in whole grams, read from
     Spoolman (empty without a Spoolman address or for a spool Spoolman does not
     know). **Read Box Data** reads it again.
   - The dot in front of a slot is red if the slot is empty, green if it holds
     filament and cyan if it is feeding the extruder. Only slot 0 is shown by
     default; **Show all slots** shows all four.
   While the app checks a printer, reads a box or reads or writes a tag, the
   mouse pointer turns into the busy pointer (spinning ring) over the whole
   window.
4. Below it (Windows and Linux) is the **RFID Tag** frame, which works with the
   tag on the default reader (see the **Reader** tab of the settings; without
   a default reader both buttons are disabled):
   - **Read Tag** reads the tag and shows what is on it. A blank tag gives a
     blank form, a tag that was not written by this app is reported as such.
     Once the tag is taken off the reader the fields are cleared again (the
     reader is asked once a second).
   - **Write Tag** writes the values in the frame to the tag. The values stay
     afterwards, also when the tag is taken off, so the next tag can be
     written right away. The tag is read
     back to check that it holds the data. The data goes to sector 1, where
     the QIDI box expects it.
   - The frame has these rows: the buttons; the **Spool**; the **Spoolman
     filament**; a **QIDI Data** group (**Material**, **Vendor**, **Color**),
     which is what is written for the QIDI box; and a **Spoolman Data** group
     (**Spool number**, **Spoolman vendor**, **Weight**).
   - With **Use Spoolman** on (and an address set), pick an existing **Spool**
     or keep **+ New spool …**. For a new spool pick a **Spoolman filament**
     to prefill material, vendor, colour and weight, or choose a **Spoolman
     vendor** and let the app find the matching filament. Writing a new spool
     creates it in Spoolman first and shows it as the selected spool from then
     on, so more copies of the same tag do not create more spools. For an
     existing spool the weight field shows its remaining weight (read-only).
   - Without Spoolman, only the **QIDI Data** group is shown: choose
     **Material**, **Vendor** and **Color** and enter the **Spool number**
     (0-999) yourself.
   - Beside it, a third of the width and as high as the RFID Tag frame, is the
     **QR Code** frame. As soon as the RFID Tag frame shows a spool (read from
     a tag, picked in Spoolman, written, or entered by hand with a spool
     number) it shows the QR code of that spool, with the app logo in its
     centre. The code says:

         Number: <spool number>
         QIDI Material: <material>
         QIDI Vendor: <vendor>
         QIDI Color: <colour, #RRGGBB>
         Spoolman Vendor: <vendor in Spoolman>
         Spoolman Color: <colour in Spoolman, #RRGGBB>

     The Spoolman lines stay empty without Spoolman. **Export** makes a
     DIN A4 PDF with the code (20 x 20 mm, top left; to its right, one below
     the other, in 14 pt: the spool number, the Spoolman material and the
     Spoolman vendor, all inside a light frame; a line too long for the page is cut short with `…`) and shows the system's
     save dialog to choose where to save it. **Print** prints the same page
     on the default printer; it is disabled while there is no printer (the
     app looks again when its window is activated).
5. At startup the app checks that the default reader is connected and
   usable, while the splash screen is shown. The status bar then shows
   `Reader: <name>`, or a red message if the reader is missing, is not an
   RFID reader, or has a tag on it that is not a readable MIFARE Classic 1K.
   A reader with no tag on it counts as usable, because RFID support can only
   be verified with a tag present.
6. At startup the app also checks in the background whether a newer release
   is available (unless switched off in the settings). If so, a link
   "New version … available" appears in the status bar; clicking it opens
   the download page. The check only asks GitHub for the latest release
   number; nothing else is sent.
7. **File → Exit** closes the app (desktop only), **Help → About** shows
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

3. Restart Klipper (`RESTART` or `FIRMWARE_RESTART`). When you replace an
   already installed `rfid_bridge.py` with a newer one, restart the Klipper
   *service* instead (for example with `sudo systemctl restart klipper`, or
   by rebooting the printer): `RESTART` keeps Klipper's process and does not
   reload a Python module that was already imported, so the old code would
   keep running.

It works by capturing the raw 16-byte `fm17550_read_card_return` response
QIDI's own firmware already reads for each box slot - the same data the
box uses internally - by monkey-patching `mcu.CommandQueryWrapper.send` in
memory for the lifetime of the Klipper process, and by tracking the active
slot (`slotN` in `stepper_enable`, `box_stepper slotN` on older firmware)
via the public `stepper_enable` callback API. The patch is purely
observational (it never changes QIDI's own request/response, and never
modifies a QIDI-shipped file on disk) and is gone as soon as the Klipper
service is restarted. A Klipper `RESTART`/`FIRMWARE_RESTART` does not remove
it: Klipper keeps its process and the modules it already imported, so the
bridge simply carries on with the reloaded configuration.

Query the captured data via `RFID_BRIDGE_STATUS` in the Klipper console, or
`GET /printer/objects/query?rfid_bridge` through Moonraker. Both also show the
version of `rfid_bridge.py`, which is the version of the RFID Wisp release it
was downloaded from.

### Automatic active-spool reporting to Moonraker/Spoolman

`rfid_bridge` decodes the Spoolman spool number from the tag data (bytes
14-15, big-endian, as written by RFID Wisp) and POSTs it to Moonraker's
built-in Spoolman integration (`/server/spoolman/spool_id`), so the active
spool shown in Fluidd/Spoolman follows the box automatically - no manual
selection needed. This requires the `[spoolman]` component to be configured
in `moonraker.conf`.

It caches the last RFID read of every slot and reports the spool number of
whichever slot is currently active: whenever a different slot becomes active
(e.g. on a tool change), whenever a read arrives for the active slot, and
again whenever a print job starts (detected by polling
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
