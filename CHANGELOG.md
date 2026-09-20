# Changelog

All notable changes to RFID Wisp are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.4.0] - 2026-09-21

### Fixed

- Reading and writing an RFID tag with a PC/SC reader (Windows, Linux) is fast
  in a debugging session too. The PC/SC package starts a new isolate for every
  single call - nine of them for one read - and with the debugger of VS Code
  attached every isolate takes about 0.75 s, so **Read Tag** took 6 s and more
  (0.3 s without a debugger). All PC/SC calls now run in one background isolate
  that is started once and reused, so a read costs a few messages: 0.3 s from
  the click to the data on screen in the same debugging session. An error of a
  call is reported with the code of the smart card service, e.g. `PC/SC
  SCardConnect failed (0x80100009)`.
- **Read Tag** no longer waits for Spoolman. It used to ask Spoolman for the
  vendors, filaments and spools one after the other before showing anything, so
  a slow or unreachable server (5 s timeout per request) made reading a tag take
  9 s, 15 s or more, although the tag itself is read in a fraction of a second.
  Now the tag's data is shown at once, the three requests run at the same time
  and complete the spool fields when they are answered (also for the weights in
  the QIDI Data frame). Until Spoolman has said whether it knows the tag's
  spool, **Write Tag** stays disabled, so that no new spool is created by
  mistake. Fields that were cleared, or a spool that was picked, in the
  meantime are left alone.

### Added

- **Weight** field in each slot of the QIDI Data frame, behind the Vendor in
  Spoolman: the remaining weight of the spool on the slot's tag in whole grams, read
  from Spoolman (all spools with one request when the app starts and whenever
  **Read Box Data** is pressed). It stays empty without a Spoolman address, for
  a spool Spoolman does not know or if Spoolman cannot be reached. The window is
  wider by the new field (1060 instead of 960 logical pixels), so the frames
  keep their room; the RFID Tag and QR Code frames still share the width 2 : 1.
- **Ukrainian** (Українська) as a third language: all texts and messages of the
  app are translated. It can be chosen under **File → Settings**, and the app
  uses it if the system language is Ukrainian.
- The language dropdown of the settings shows a small flag before each
  language (Germany, United Kingdom, Ukraine; a globe for the system default).
  The flags are drawn by the app, since Windows shows emoji flags as letters.
- **Export settings …** and **Import settings …** on the General tab of the
  settings: all settings (language, update check, default reader, printers,
  Spoolman address and switch) go to a JSON file the user chooses and can be
  loaded from one, e.g. to keep a backup or to move to another device. The
  export writes what the dialog shows now (an invalid printer or address is
  reported like with OK). An import only fills in the dialog and applies with
  OK; settings missing in the file stay as they are, and a file that is no
  RFID Wisp settings file, or was written by a newer version, is refused. The
  device's own NFC reader (Android) is not part of a file. On Android the file
  is created through the system's document dialog.

### Changed

- Windows and Linux: the main window opens centred on the first (primary)
  monitor and exactly as high as its content, without empty space below the
  RFID Tag frame. It follows the content while the app runs: showing all slots
  in the QIDI Data frame makes the window taller (hiding them makes it lower
  again), so the RFID Tag frame stays fully visible. A maximised window is
  left alone, and the window never gets taller than the screen.
- The Spool dropdown of the RFID Tag frame shows the colour of each spool's
  filament as a swatch, like the Spoolman filament dropdown.
- The spool number in the QIDI Data frame is left-aligned like the other
  fields, no longer centred.

## [0.3.1] - 2026-09-20

### Fixed

- Android: the APK is now signed with one fixed key, so a newer version can be
  installed over the previous one and keeps the settings (printers, Spoolman).
  Until 0.3.0 every release was signed with a different, automatically created
  debug key, and Android refuses to update an app to a version signed with
  another key. Uninstall 0.3.0 (or older) once before installing 0.3.1; its
  settings are lost this one time.

## [0.3.0] - 2026-09-20

### Added

- Android: the **RFID Tag** frame reads and writes MIFARE Classic 1K tags with
  the phone's own NFC reader (Android's `MifareClassic`, no code of the GPL
  licensed "MIFARE Classic Tool" is used). The reader is always used, so there
  is no Reader tab; the frame asks to hold the tag to the back of the phone
  after **Read Tag** or **Write Tag** was pressed and waits 20 seconds for it.
  The status bar tells if NFC is switched off or the phone has no NFC. The QR
  Code frame is not shown on Android. Tested on a Samsung Galaxy S25 Ultra.

## [0.2.0] - 2026-09-20

### Added

- **RFID Tag** frame in the main window, below QIDI Data (Windows and Linux;
  from the Python version's read/write dialog): **Read Tag** shows the filament
  data of the MIFARE Classic 1K tag on the default reader, **Write Tag** writes
  the entered data to it. With Spoolman, a tag is written for a new spool
  (created in Spoolman, from a chosen filament or the vendor, material and
  colour) or for an existing one; without Spoolman, material, vendor, colour
  and spool number are entered by hand. The values stay after writing, for the
  next tag; the fields of a tag that was read are cleared when the tag is taken
  off the reader. The frame is arranged in rows (buttons, spool, Spoolman filament,
  a QIDI Data group with material, vendor and colour, a Spoolman Data group
  with spool number, Spoolman vendor and weight); the sector field is hidden.
  Unlike the Python version, a write is read back to check the tag
  holds the data, and a spool created in Spoolman stays selected if writing the
  tag fails, so a second attempt does not create another spool.
- **QR Code** frame beside the RFID Tag frame (a third of the width, as high
  as the RFID Tag frame): the QR code of the spool the RFID Tag frame shows -
  `Number`, `QIDI Material`, `QIDI Vendor`, `QIDI Color`,
  `Spoolman Vendor` and `Spoolman Color`, one per line - with the app logo in
  its centre. **Export** creates a DIN A4 PDF with the code (20 x 20 mm, top
  left; to its right, one below the other in 14 pt: the spool number, the
  Spoolman material and the Spoolman vendor, all inside a light frame; a line too long for the page is cut short with `…`) and shows the system's save dialog; **Print** prints that page on the
  default printer and is disabled if there is no printer.
- While the app is busy - checking a printer, reading a QIDI box, reading or
  writing a tag - the mouse pointer is the busy pointer (spinning ring) over
  the whole window, so it is visible that something is going on.
- `rfid_bridge.py` now shows its version (in `RFID_BRIDGE_STATUS`, in the
  `rfid_bridge` object status and in the Klipper log). It has no version of
  its own: the release pipeline stamps the copy it publishes with the app's
  release version (`scripts/stamp_bridge_version.py`); the file in the
  repository shows `dev`.

### Changed

- The text in the QIDI Data and RFID Tag frames uses the standard text styles
  of the Material theme and sets no font or size of its own, so it follows the
  platform's typography and the system's text size setting, and both frames
  look alike. The slots in QIDI Data are now rows of labelled read-only text
  fields (like the fields of the RFID Tag frame) instead of a table with a
  header row; the values can be selected and copied. Vendor and Color are
  narrower than Material and Vendor in Spoolman, and the Number field is
  narrower (80 px); on narrow screens the Vendor field is half as wide as the
  others.
- The app window starts 960 x 720 px instead of 1280 x 720 px (Windows and
  Linux).
- The short description of the app now says what it is for: the QIDI Boxes
  connected to QIDI Plus4 and QIDI Max4 printers (README, package description,
  Windows file properties).


### Fixed

- The QIDI Data indicator of the slot that feeds the extruder was the darker
  `Colors.cyan` since a change after release 0.1.0 instead of the light cyan
  (`#4FD8EC`) of that release.
- `rfid_bridge.py` reported the wrong spool to Moonraker/Spoolman when the
  printed slot was not the one read last: at startup every slot's tag is read
  and the last one read stayed the active spool, and at print start the
  last-enabled slot was used. The bridge now caches the tag of every slot and
  reports the spool of the slot that is actually active, whenever a slot
  becomes active (e.g. on a tool change) as well as at print start.
  `RFID_BRIDGE_STATUS` also lists the spool number of each slot.
- `rfid_bridge.py` captured nothing on QIDI Max4 firmware 01.01.06.05: the
  box steppers are registered in `stepper_enable` as `slotN` instead of
  `box_stepper slotN`, so no slot was ever found, no slot was ever active
  and every RFID read was discarded. Both names are accepted now.
- `rfid_bridge.py` stopped seeing RFID reads after a Klipper `RESTART`: the
  read hook survives the restart inside Klipper's process but kept pointing at
  the bridge instance of the first load. It now always uses the newest
  instance. The README also said `RESTART` removes the hook and reloads the
  module, which is wrong; after replacing `rfid_bridge.py` the Klipper service
  has to be restarted.

## [0.1.0] - 2026-09-19

The QIDI box data of a printer can be shown; reading and writing RFID tags
is not implemented yet.

### Added

- **QIDI Data** frame in the main window (from the Python version): choose a
  printer and one of its QIDI boxes and see the four slots of the box -
  material, vendor, colour, and the Spoolman spool number and vendor stored on
  the RFID tag. The printer is checked at startup and when it is changed; the
  first box is read automatically, other boxes with **Read Box Data**. Slots
  have a red / green / cyan indicator (empty / loaded / feeding), and only
  slot 0 is shown until **Show all slots** is used. On narrow (phone) screens
  the slots are listed one below the other.
- The chosen printer is remembered between app starts.
- Moonraker client (`lib/moonraker_api.dart`, ported from the Python
  version): reads the number of QIDI boxes and the four material slots of a
  box from a printer, including the Spoolman spool number and vendor that the
  optional `[rfid_bridge]` Klipper extra captured from the tag. Used by the
  QIDI Data frame.
- Spoolman client (`lib/spoolman_api.dart`, ported from the Python version):
  reads spools, filaments and vendors, finds a filament by vendor, material
  and colour, creates spools and reads the remaining weight of a spool. The
  QIDI Data frame uses it to look up vendor names; the rest is not used by the
  UI yet.
- Printer management in the settings dialog (from the Python version's
  settings panel): add, edit and delete printers, each with a name and the
  address of its Moonraker service. Addresses are checked and cleaned up (a
  missing `http://` is added, trailing slashes are removed).
- Spoolman settings in the settings dialog: server address and a
  "Use Spoolman" switch that is independent of the address.
- RFID reader selection in the settings dialog: a combobox lists the PC/SC
  readers that can read and write RFID tags, with a refresh button. A checkbox
  marks the selected reader as the default reader. Readers are tested by what
  they can actually do (ATR decoding, and for MIFARE Classic 1K tags
  authenticating with the default keys and reading block 0) rather than by
  name; non-RFID devices such as YubiKeys are never opened. A reader with no
  tag on it is listed, since it cannot be disproved.
- At startup, while the splash screen is shown, the default reader is checked
  for being reachable and usable (with a 10 s limit). The result is shown in
  the status bar.
- Background check for a newer release at startup. A link to the download
  page appears in the status bar when one is available. Can be switched off
  with a checkbox in the settings dialog (on by default).
- The settings (default reader, printers, Spoolman, update check) are stored
  between app starts.
- Android version: an APK (`RFIDwisp-android.apk`, Android 7.0 or newer) is
  built and published with every release, next to Windows and Linux. The
  settings dialog fits phone screens, and the Reader tab is hidden because
  Android has no PC/SC (RFID readers are not supported there yet). Release APKs
  are signed with an upload keystore from the repository secrets, see the
  README ("Android signing").
- Application icon: the new RFID Wisp icon is used for the Windows `.exe`,
  window and taskbar, as Linux window icon and as web favicon. The icons are
  generated from `logo/neu/icon-1024x1024.png` by `scripts/build_icons.py`.
- Klipper companion module `klipper/rfid_bridge.py` (copied from the RFID
  Wisp Python project). It is attached to every release as `rfid_bridge.py`
  and synced to the distribution repo.

### Changed

- The status bar now also reports what the QIDI Data frame did (box read,
  printer or Spoolman not reachable); long messages are shortened with "…".
- The settings dialog is organised on tabs (General, Reader, Printers,
  Spoolman). Changes are applied all at once with OK; Cancel discards them.

## [0.0.1] - 2026-09-19

First release. Only the application shell exists so far; the RFID
functionality is not implemented yet.

### Added

- Splash screen with the logo, shown while the app starts up.
- Main window with a menu bar (File, Help) and a status bar showing the
  current state and the app version, in a compact desktop look.
- English and German user interface, following the system language by
  default; selectable under File → Settings.
- Help → About dialog.
