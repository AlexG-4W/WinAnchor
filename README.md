# WinAnchor

**WinAnchor** is a lightweight Windows background utility designed to automatically save and restore the positions, sizes, and states (minimized/maximized/normal) of all open windows across multi-monitor setups. It's especially useful for users whose window layouts break after waking from sleep mode or disconnecting/reconnecting monitors.

## Key Features

- **Precise Layout Restoration:** Uses the Windows API (`SetWindowPlacement`) to perfectly restore window coordinates and states (Minimized, Maximized, or Normal).
- **System Event Automation:** Automatically detects display configuration changes (monitor plug/unplug, wake from sleep) and restores your layout after a short safety delay.
- **Global Hotkeys:** Quick-save (`Alt+Shift+S`) and quick-restore (`Alt+Shift+R`) your layout from any application.




- **System Tray Interface:** A clean background daemon with a taskbar icon and context menu.





<img width="369" height="185" alt="scr1" src="https://github.com/user-attachments/assets/df28f0c4-5894-4fd5-843a-bf82e6d7c69a" />

- **Dynamic Configuration:** Easily change your hotkeys via the built-in "Settings" UI without touching code or config files.
  <img width="453" height="275" alt="scr2" src="https://github.com/user-attachments/assets/375dddd8-49ff-4f9d-b74a-01b8fe952185" />

- **Robust & Thread-Safe:** Optimized for multi-threaded performance with atomic file writes to prevent data corruption.

## Installation (from Source)

### Prerequisites
- Python 3.10 or higher
- Windows 10/11

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/WinAnchor.git
   cd WinAnchor
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python run.py tray
   ```

## Compiling to Executable (.exe)
To build a standalone, single-file executable that doesn't require Python:
1. Ensure `pyinstaller` is installed (`pip install pyinstaller`).
2. Run the build script:
   ```cmd
   build.bat
   ```
3. Your executable will be in the `dist/WinAnchor.exe` folder.

## Technical Architecture
- **`src/core/`**: Contains the Windows API logic, system event listeners, and state/config managers.
- **`src/ui/`**: Implementation of the System Tray interface (`pystray`) and Settings GUI (`tkinter`).
- **`src/utils/`**: Robust logging utility that writes to `%APPDATA%\WinAnchor\winanchor.log`.

## QA & Reliability
This version includes the **Stage 9 QA Patchset**, which introduced:
- Atomic JSON persistence (via `tempfile` + `os.replace`).
- Thread-safe UI/Hotkey callbacks using `threading.Lock`.
- Top-level window event interception for reliable `WM_DISPLAYCHANGE` detection.
- Guaranteed handle cleanup for Windows API calls.

## License
MIT License.
