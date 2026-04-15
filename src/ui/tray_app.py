import pystray
from PIL import Image, ImageDraw
import threading
import keyboard
from typing import Callable
from src.core.window_manager import WindowManager
from src.core.profile_manager import ProfileManager
from src.core.hotkey_manager import HotkeyManager
from src.core.event_listener import SystemEventListener
from src.core.config_manager import ConfigManager
from src.ui.settings_dialog import SettingsDialog
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class TrayApp:
    def __init__(self, profile_name: str = "default") -> None:
        self.profile_name = profile_name
        self.wm = WindowManager()
        self.pm = ProfileManager()
        self.cm = ConfigManager()
        self.icon = None
        self._action_lock = threading.Lock()
        
        save_hk = self.cm.get("save_hotkey", "alt+shift+s")
        restore_hk = self.cm.get("restore_hotkey", "alt+shift+r")
        
        self.hm = HotkeyManager(
            save_callback=self._on_save, 
            restore_callback=self._on_restore,
            save_hotkey=save_hk,
            restore_hotkey=restore_hk
        )
        self.el = SystemEventListener(restore_callback=self._on_restore)

    def _create_icon_image(self) -> Image.Image:
        """Generates a 64x64 icon programmatically."""
        # Create a 64x64 blue square
        image = Image.new('RGB', (64, 64), color=(0, 122, 204))
        draw = ImageDraw.Draw(image)
        
        # Draw a white "W"
        points = [
            (10, 16), (22, 48), (32, 30), (42, 48), (54, 16)
        ]
        draw.line(points, fill=(255, 255, 255), width=6, joint="curve")
        
        # Add a subtle anchor arc at the bottom
        draw.line([(32, 30), (32, 60)], fill=(255, 255, 255), width=4)
        draw.arc((16, 40, 48, 60), start=0, end=180, fill=(255, 255, 255), width=4)
        
        return image

    def _on_save(self, icon=None, item=None) -> None:
        with self._action_lock:
            logger.info(f"Tray: Fetching current window states for profile '{self.profile_name}'...")
            try:
                states = self.wm.get_windows_state()
                if self.pm.save_profile(states, self.profile_name):
                    logger.info(f"Tray: Successfully saved {len(states)} windows.")
                else:
                    logger.error("Tray: Failed to save profile.")
            except Exception as e:
                logger.error(f"Tray: Error during save: {e}")

    def _on_restore(self, icon=None, item=None) -> None:
        with self._action_lock:
            logger.info(f"Tray: Loading window states from profile '{self.profile_name}'...")
            try:
                states = self.pm.load_profile(self.profile_name)
                if states:
                    self.wm.restore_windows_state(states)
                    logger.info(f"Tray: Successfully restored {len(states)} windows.")
                else:
                    logger.warning("Tray: No valid state found in profile.")
            except Exception as e:
                logger.error(f"Tray: Error during restore: {e}")
            
    def _on_settings_saved(self, new_save_hk: str, new_restore_hk: str) -> None:
        """Callback from settings dialog when saving new hotkeys."""
        self.hm.update_hotkeys(new_save_hk, new_restore_hk)
        self.cm.save_config({"save_hotkey": new_save_hk, "restore_hotkey": new_restore_hk})
        logger.info("Tray: Settings updated.")

    def _on_settings(self, icon=None, item=None) -> None:
        logger.info("Tray: Opening settings dialog...")
        save_hk = self.cm.get("save_hotkey", "alt+shift+s")
        restore_hk = self.cm.get("restore_hotkey", "alt+shift+r")
        dialog = SettingsDialog(save_hk, restore_hk, self._on_settings_saved)
        # Start dialog in a new thread so we don't block the tray icon event loop
        # Tkinter requires to be run in the main thread typically, but pystray blocks main thread.
        # Starting Tk in a side thread usually works on Windows as long as the entire Tk lifecycle is within that thread.
        threading.Thread(target=dialog.show, daemon=True).start()

    def _on_quit(self, icon, item) -> None:
        logger.info("Tray: Quitting application...")
        # Unhook hotkeys first to avoid any dangling listeners
        try:
            keyboard.unhook_all()
            logger.info("Tray: Hotkeys unregistered.")
        except Exception as e:
            logger.error(f"Tray: Error unhooking hotkeys: {e}")
            
        # Stop the system event listener
        try:
            self.el.stop()
        except Exception as e:
            logger.error(f"Tray: Error stopping system event listener: {e}")
            
        if self.icon:
            self.icon.stop()

    def _run_hotkey_listener(self) -> None:
        """Runs the hotkey listener in a separate thread."""
        logger.info("Tray: Starting hotkey listener thread...")
        try:
            self.hm.start_listening()
        except Exception as e:
            logger.error(f"Tray: Hotkey listener encountered an error: {e}")
        finally:
            # If the listener exits (e.g. exit hotkey pressed), shut down the tray icon as well
            if self.icon:
                logger.info("Tray: Hotkey listener ended, stopping tray icon...")
                self.icon.stop()

    def _run_event_listener(self) -> None:
        """Runs the system event listener in a separate thread."""
        logger.info("Tray: Starting system event listener thread...")
        try:
            self.el.start()
        except Exception as e:
            logger.error(f"Tray: System event listener encountered an error: {e}")

    def run(self) -> None:
        """Starts the tray application, hotkey listener, and system event listener."""
        logger.info("Initializing TrayApp...")
        
        image = self._create_icon_image()
        menu = pystray.Menu(
            pystray.MenuItem("Save Layout (Default)", self._on_save),
            pystray.MenuItem("Restore Layout (Default)", self._on_restore),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Settings...", self._on_settings),
            pystray.MenuItem("Quit", self._on_quit)
        )
        self.icon = pystray.Icon("WinAnchor", image, "WinAnchor", menu)
        
        # Start HotkeyManager in a daemon thread so pystray's blocking run() works
        hk_thread = threading.Thread(target=self._run_hotkey_listener, daemon=True)
        hk_thread.start()

        # Start SystemEventListener in a daemon thread
        el_thread = threading.Thread(target=self._run_event_listener, daemon=True)
        el_thread.start()

        logger.info("Running tray icon... (Blocking)")
        self.icon.run()
        logger.info("TrayApp stopped.")
