# WinAnchor

**WinAnchor** is a lightweight Windows background utility designed to automatically save and restore the positions, sizes, and states (minimized/maximized/normal) of all open windows across multi-monitor setups. It's especially useful for users whose window layouts break after waking from sleep mode or disconnecting/reconnecting monitors.

## Features

- **Save and Restore Window Layouts:** Accurately captures the precise coordinates and window states of all open, visible applications.
- **4-Slot Profile System:** Save and easily switch between up to 4 independent window layout profiles right from the system tray.
- **Dynamic Settings UI:** A modern settings dialog to configure custom global hotkeys, rename your layout profiles, and manage your ignored windows list.
- **User-Defined Window Blacklist (New in v1.3):** Configure a personal list of window titles or process names to ignore (e.g., `pnpmgr`, `overlay.exe`). Managed directly from the Settings dialog as a comma-separated list, persisted in config.
- **Per-Monitor DPI Awareness (New in v1.3):** Calls `SetProcessDpiAwareness(2)` at startup so Windows reports true physical pixel coordinates across all monitors — no more DPI-virtualized misplacements on mixed-scale setups.
- **DPI Boundary Bleed Fix (New in v1.3):** For normal-state windows, enforces saved physical coordinates via `MoveWindow` after `SetWindowPlacement` to prevent windows from bleeding onto the wrong monitor at DPI boundaries.
- **Multi-Signal Window Fingerprinting:** Matches saved windows to live windows across sessions using a weighted scoring system (process name, class name, geometry, fuzzy title matching) instead of fragile HWND handles.
- **System Event Automation:** Runs silently in the background and automatically restores your active window layout when it detects a display configuration change (e.g., waking from sleep, connecting a new monitor).
- **System Tray Interface:** Manage the application and select your active profile directly from the Windows taskbar.
- **Global Hotkeys:** Use keyboard shortcuts to quickly save or restore your active profile from anywhere in Windows.
- **Multi-Monitor Support:** Precisely places windows back to their original screens using the Windows API (`SetWindowPlacement` + `MoveWindow`).
- **Ghost Window Filtering:** Filters out invisible phantom windows (DWM-cloaked apps, tool windows, zero-geometry listeners) using physical `GetWindowRect` checks and a configurable title/process blacklist.

<img width="389" height="626" alt="scr 1 v1 3" src="https://github.com/user-attachments/assets/e237d45b-afcd-4216-9d72-12670451aac4" />

<img width="257" height="224" alt="scr2 v1 3" src="https://github.com/user-attachments/assets/8233e9e7-da4a-4c35-9ca8-4a82747e4e90" />


## Installation (from Source)

### Prerequisites

- Python 3.10 or higher
- Windows OS

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/WinAnchor.git
   cd WinAnchor
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   # Launch the System Tray application
   python run.py tray
   
   # Or launch the interactive CLI menu for testing
   python run.py interactive
   ```

## Compiling to a Standalone Executable (.exe)

You can build WinAnchor into a single-file Windows executable, so it can run on machines without Python installed.

1. Make sure all dependencies (including `pyinstaller`) are installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the included build script:
   ```cmd
   build.bat
   ```

3. The compiled standalone executable `WinAnchor.exe` will be generated in the `dist/` directory. You can move this `.exe` anywhere or add it to your Windows Startup folder (`shell:startup`) for automatic execution on boot.

## Usage

When WinAnchor is running in background mode (System Tray):
- **System Tray Icon:** Right-click the blue "W" icon in your taskbar to access the menu.
- **Active Profile:** Use the "Active Profile" submenu to switch between 4 configurable layout profiles.
- **Save Layout:** Select "Save Layout" or press your configured Save Hotkey (default: `Alt+Shift+S`) to save to the currently active profile.
- **Restore Layout:** Select "Restore Layout" or press your configured Restore Hotkey (default: `Alt+Shift+R`) to load the currently active profile.
- **Settings:** Click "Settings..." in the tray menu to rename your profiles, change your hotkeys, and edit the ignored windows blacklist.

*Note: WinAnchor automatically restores your active layout when your monitors wake from sleep or reconnect.*

## Architecture

- **`src/core/window_manager.py`**: Interacts with the `win32gui` Windows API to read and set window placements. Implements DPI awareness, multi-signal fingerprinting, and ghost window filtering.
- **`src/core/profile_manager.py`**: Serializes layout data into JSON and stores it in `%APPDATA%\WinAnchor\profiles\`.
- **`src/core/hotkey_manager.py`**: Listens for global keyboard shortcuts using the `keyboard` library.
- **`src/core/event_listener.py`**: Runs a hidden message pump to intercept `WM_DISPLAYCHANGE` events for automatic layout restoration.
- **`src/core/config_manager.py`**: Manages user preferences (hotkeys, profile names, ignored windows list) in `%APPDATA%\WinAnchor\config.json`.
- **`src/ui/tray_app.py`**: Renders the System Tray icon and context menu using `pystray`.
- **`src/ui/settings_dialog.py`**: Provides a lightweight `tkinter` GUI for configuring hotkeys, profile names, and the window blacklist.

## Changelog

### v1.3 — Multi-Monitor DPI & User Blacklist
- **Per-Monitor DPI Awareness:** `SetProcessDpiAwareness(2)` with fallback to `SetProcessDPIAware()`, ensuring true physical coordinates on mixed-scale multi-monitor setups.
- **DPI Boundary Bleed Fix:** Normal-state windows are repositioned via `MoveWindow` after `SetWindowPlacement` to prevent cross-monitor bleed at DPI boundaries.
- **User-Defined Window Blacklist:** Configurable list of ignored window titles/process names (substring matching), editable from the Settings dialog and persisted in `config.json`.
- **Improved Ghost Window Filter:** Replaced `GetWindowPlacement` zero-geometry check with physical `GetWindowRect` + strict blacklist to catch phantom windows like Logitech's PnpMgr.
- **Settings Dialog Overhaul:** Auto-sizing layout (no hardcoded geometry), new "Ignored Windows" field, added Cancel button.

### v1.2 — Robust Window Matching
- **Multi-Signal Fingerprinting:** Weighted scoring system (process 40 pts, class 20 pts, geometry 30 pts, fuzzy title 10 pts) replaces fragile HWND-based matching.
- **DWM Cloaking Filter:** Filters out windows cloaked by the Desktop Window Manager (virtual desktops, background UWP apps).
- **Z-Order Preservation:** Restores windows in reverse EnumWindows order so the topmost window stays on top.
- **Owner Window Check:** Skips owned windows (using `GW_OWNER`) unless they have `WS_EX_APPWINDOW`.

### v1.1 — Profiles & Settings
- **4-Slot Profile System:** Save/switch between 4 independent layout profiles from the system tray.
- **Dynamic Settings Dialog:** Configure hotkeys and rename profiles via a tkinter UI.
- **Configurable Hotkeys:** User-defined save/restore keyboard shortcuts persisted to config.

## License

This project is licensed under the MIT License.
