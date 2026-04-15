import sys
import os
import argparse

from src.core.window_manager import WindowManager
from src.core.profile_manager import ProfileManager
from src.core.hotkey_manager import HotkeyManager
from src.ui.tray_app import TrayApp
from src.utils.logger import setup_logger

logger = setup_logger("Main")

def cmd_save(profile_name: str) -> None:
    wm = WindowManager()
    pm = ProfileManager()
    
    logger.info(f"Fetching current window states for profile '{profile_name}'...")
    states = wm.get_windows_state()
    logger.info(f"Found {len(states)} valid windows.")
    
    if pm.save_profile(states, profile_name):
        print(f"Successfully saved {len(states)} windows to profile '{profile_name}'.")
    else:
        print(f"Failed to save profile '{profile_name}'. Check logs for details.")

def cmd_restore(profile_name: str) -> None:
    wm = WindowManager()
    pm = ProfileManager()
    
    logger.info(f"Loading window states from profile '{profile_name}'...")
    states = pm.load_profile(profile_name)
    
    if not states:
        print(f"No valid state found in profile '{profile_name}' or it is empty.")
        return
        
    logger.info(f"Restoring {len(states)} windows...")
    wm.restore_windows_state(states)
    print(f"Successfully restored windows from profile '{profile_name}'.")

def cmd_listen(profile_name: str) -> None:
    from src.core.config_manager import ConfigManager
    wm = WindowManager()
    pm = ProfileManager()
    cm = ConfigManager()
    
    def on_save() -> None:
        logger.info(f"Fetching current window states for profile '{profile_name}'...")
        states = wm.get_windows_state()
        if pm.save_profile(states, profile_name):
            logger.info(f"Successfully saved {len(states)} windows to profile '{profile_name}'.")
        else:
            logger.error(f"Failed to save profile '{profile_name}'.")
            
    def on_restore() -> None:
        logger.info(f"Loading window states from profile '{profile_name}'...")
        states = pm.load_profile(profile_name)
        if states:
            wm.restore_windows_state(states)
            logger.info(f"Successfully restored {len(states)} windows from profile '{profile_name}'.")
        else:
            logger.warning(f"No valid state found in profile '{profile_name}' or it is empty.")
            
    save_hk = cm.get("save_hotkey", "alt+shift+s")
    restore_hk = cm.get("restore_hotkey", "alt+shift+r")
            
    hm = HotkeyManager(save_callback=on_save, restore_callback=on_restore, save_hotkey=save_hk, restore_hotkey=restore_hk)
    
    print(f"Starting WinAnchor background listener for profile '{profile_name}'...")
    print(f"  Save Hotkey:    {save_hk.upper()}")
    print(f"  Restore Hotkey: {restore_hk.upper()}")
    print("  Quit:           CTRL + SHIFT + Q")
    hm.start_listening()

def cmd_tray(profile_name: str) -> None:
    app = TrayApp(profile_name=profile_name)
    app.run()

def interactive_loop() -> None:
    print("WinAnchor Interactive Test Menu")
    print("===============================")
    while True:
        print("\nOptions:")
        print("  1. Capture and Save layout (default profile)")
        print("  2. Load and Restore layout (default profile)")
        print("  3. Start Background Listener (default profile)")
        print("  4. Start System Tray Interface (default profile)")
        print("  5. Exit")
        
        try:
            choice = input("\nSelect an option [1-5]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break
            
        if choice == '1':
            cmd_save("default")
        elif choice == '2':
            cmd_restore("default")
        elif choice == '3':
            cmd_listen("default")
        elif choice == '4':
            cmd_tray("default")
        elif choice == '5':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please enter 1, 2, 3, 4, or 5.")

def main() -> None:
    """
    Main entry point for testing the WindowManager, ProfileManager, HotkeyManager, and TrayApp functionality.
    """
    # If running as a compiled PyInstaller executable, run the tray app directly
    if getattr(sys, 'frozen', False):
        logger.info("Running in frozen mode (compiled executable). Starting System Tray Interface...")
        cmd_tray("default")
        return

    parser = argparse.ArgumentParser(description="WinAnchor - Window State Manager")
    parser.add_argument('command', nargs='?', choices=['save', 'restore', 'listen', 'tray', 'interactive'], 
                        default='interactive', help="Command to run (save, restore, listen, tray, interactive)")
    parser.add_argument('-p', '--profile', type=str, default='default', help="Profile name to use")
    
    args = parser.parse_args()
    
    if args.command == 'save':
        cmd_save(args.profile)
    elif args.command == 'restore':
        cmd_restore(args.profile)
    elif args.command == 'listen':
        cmd_listen(args.profile)
    elif args.command == 'tray':
        cmd_tray(args.profile)
    else:
        interactive_loop()

if __name__ == "__main__":
    main()
