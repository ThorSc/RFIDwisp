# Changelog

All notable changes to RFID Wisp are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

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
