# WinAnchor

**WinAnchor** is a lightweight Windows background utility designed to automatically save and restore the positions, sizes, and states (minimized/maximized/normal) of all open windows across multi-monitor setups. It's especially useful for users whose window layouts break after waking from sleep mode or disconnecting/reconnecting monitors.

## Features

- **Save and Restore Window Layouts:** Accurately captures the precise coordinates and window states of all open, visible applications.
- **4-Slot Profile System (New in v1.1):** Save and easily switch between up to 4 independent window layout profiles right from the system tray.

<img width="475" height="231" alt="scr1" src="https://github.com/user-attachments/assets/84910cfa-656c-4e2c-a3f2-59c46f22e828" />


- **Dynamic Settings UI (New in v1.1):** A modern settings dialog to configure custom global hotkeys and uniquely rename your 4 layout profiles.


<img width="524" height="622" alt="scr2" src="https://github.com/user-attachments/assets/fa982de3-4239-48f6-a2ea-e2c9b82f5d55" />


- **System Event Automation:** Runs silently in the background and automatically restores your active window layout when it detects a display configuration change (e.g., waking from sleep, connecting a new monitor).
- **System Tray Interface:** Manage the application and select your active profile directly from the Windows taskbar.
- **Global Hotkeys:** Use keyboard shortcuts to quickly save or restore your active profile from anywhere in Windows.
- **Multi-Monitor Support:** Perfectly places windows back to their original screens and scales using the Windows API (`SetWindowPlacement`).

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
- **Settings:** Click "Settings..." in the tray menu to rename your profiles and change your hotkeys.

*Note: WinAnchor automatically restores your active layout when your monitors wake from sleep or reconnect.*

## Architecture

- **`src/core/window_manager.py`**: Interacts with the `win32gui` Windows API to read and set window placements.
- **`src/core/profile_manager.py`**: Serializes layout data into JSON and stores it in `%APPDATA%\WinAnchor\profiles\`.
- **`src/core/hotkey_manager.py`**: Listens for global keyboard shortcuts using the `keyboard` library.
- **`src/core/event_listener.py`**: Runs a hidden message pump to intercept `WM_DISPLAYCHANGE` events for automatic layout restoration.
- **`src/core/config_manager.py`**: Manages user preferences (like custom hotkeys) in `%APPDATA%\WinAnchor\config.json`.
- **`src/ui/tray_app.py`**: Renders the System Tray icon and context menu using `pystray`.
- **`src/ui/settings_dialog.py`**: Provides a lightweight `tkinter` GUI for settings configuration.

## License

This project is licensed under the MIT License.
