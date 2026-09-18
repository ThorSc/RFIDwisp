# RFID Wisp

# Still in development - most features are not implemented yet

A cross-platform (Windows/Linux) desktop app for reading and writing the
MIFARE Classic 1K RFID tags used by QIDI's multi-color filament boxes.

This repository hosts only the built releases; there is no source code here.
The app is a portable download - no installation is required.

See [CHANGELOG.md](CHANGELOG.md) for release notes.

## Downloads

Each release provides one archive per platform - grab yours from the
[Releases page](https://github.com/ThorSc/RFIDwisp/releases/latest):

| Platform | File | Notes |
|----------|------|-------|
| Windows (x64) | `RFIDwisp-windows-x64.zip`  | Unzip, then run `rfid_wisp.exe` from the extracted folder. |
| Linux (x64)   | `RFIDwisp-linux-x64.tar.gz` | `tar xzf RFIDwisp-linux-x64.tar.gz`, then run `./RFIDwisp-linux-x64/rfid_wisp`. |

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

## Features

Implemented so far (the application shell):

- Splash screen with the logo while the app starts up.
- Main window with a menu bar (File, Help) and a status bar showing the
  current state and the app version.
- User interface in English and German; follows the system language by
  default and can be switched in **File → Settings**.
- **Help → About** dialog with version, copyright and license information.

## Requirements

- **Windows** - 64-bit Windows 10 or 11. The Microsoft Visual C++
  Redistributable (x64) must be installed; it already is on most systems.
- **Linux** - 64-bit distribution with GTK 3 (`libgtk-3-0`). The
  executables are built on Ubuntu 24.04, so a distribution of similar
  age or newer is required.

## Usage

1. Start the app; the main window appears once the splash screen is done.
2. Open **File → Settings …** to choose the language (system default,
   English or German). The change takes effect immediately after **OK**.
3. **File → Exit** closes the app (desktop only), **Help → About** shows
   version and license information.

## License

RFID Wisp is licensed under the [MIT License](LICENSE). The license texts of
the Flutter framework and the packages the app depends on are bundled with the
app and shown under **Help → About → View licenses**.
