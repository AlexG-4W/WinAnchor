import pystray
from PIL import Image, ImageDraw
import threading
import keyboard
from typing import Callable, List
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
        self._settings_open = False

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

    def _get_active_profile_id(self) -> str:
        try:
            active_index = int(self.cm.get("active_profile_index", 0))
        except (TypeError, ValueError):
            active_index = 0
        profile_names = self.cm.get("profile_names", ["Profile 1", "Profile 2", "Profile 3", "Profile 4"])
        active_index = max(0, min(active_index, len(profile_names) - 1))
        return f"profile_{active_index + 1}"

    def _on_save(self, icon=None, item=None) -> None:
        with self._action_lock:
            profile_id = self._get_active_profile_id()
            logger.info(f"Tray: Fetching current window states for profile '{profile_id}'...")
            try:
                states = self.wm.get_windows_state()
                if self.pm.save_profile(states, profile_id):
                    logger.info(f"Tray: Successfully saved {len(states)} windows.")
                else:
                    logger.error("Tray: Failed to save profile.")
            except Exception as e:
                logger.error(f"Tray: Error during save: {e}")

    def _on_restore(self, icon=None, item=None) -> None:
        with self._action_lock:
            profile_id = self._get_active_profile_id()
            logger.info(f"Tray: Loading window states from profile '{profile_id}'...")
            try:
                states = self.pm.load_profile(profile_id)
                if states:
                    self.wm.restore_windows_state(states)
                    logger.info(f"Tray: Successfully restored {len(states)} windows.")
                else:
                    logger.warning("Tray: No valid state found in profile.")
            except Exception as e:
                logger.error(f"Tray: Error during restore: {e}")
            
    def _on_settings_saved(self, new_save_hk: str, new_restore_hk: str, new_names: List[str]) -> None:
        """Callback from settings dialog when saving new hotkeys and profile names."""
        try:
            self.hm.update_hotkeys(new_save_hk, new_restore_hk)
        except Exception as e:
            logger.error(f"Tray: Failed to update hotkeys: {e}")
            raise
            
        self.cm.save_config({
            "save_hotkey": new_save_hk, 
            "restore_hotkey": new_restore_hk,
            "profile_names": new_names
        })
        logger.info("Tray: Settings updated.")
        if self.icon:
            self.icon.update_menu()

    def _on_settings(self, icon=None, item=None) -> None:
        if self._settings_open:
            logger.info("Tray: Settings dialog is already open.")
            return

        self._settings_open = True
        logger.info("Tray: Opening settings dialog...")
        
        save_hk = self.cm.get("save_hotkey", "alt+shift+s")
        restore_hk = self.cm.get("restore_hotkey", "alt+shift+r")
        profile_names = self.cm.get("profile_names", ["Profile 1", "Profile 2", "Profile 3", "Profile 4"])
        
        def run_dialog():
            try:
                dialog = SettingsDialog(save_hk, restore_hk, profile_names, self._on_settings_saved)
                dialog.show()
            finally:
                self._settings_open = False

        threading.Thread(target=run_dialog, daemon=True).start()

    def _get_menu_items(self):
        profile_names = self.cm.get("profile_names", ["Profile 1", "Profile 2", "Profile 3", "Profile 4"])
        
        def set_profile(index):
            def handler(icon, item):
                self.cm.save_config({"active_profile_index": index})
                if self.icon:
                    self.icon.update_menu()
            return handler
            
        def is_profile_checked(index):
            def handler(item):
                return self.cm.get("active_profile_index", 0) == index
            return handler
            
        profile_items = []
        for i, name in enumerate(profile_names):
            profile_items.append(
                pystray.MenuItem(
                    name,
                    set_profile(i),
                    radio=True,
                    checked=is_profile_checked(i)
                )
            )
            
        yield pystray.MenuItem("Save Layout", self._on_save)
        yield pystray.MenuItem("Restore Layout", self._on_restore)
        yield pystray.Menu.SEPARATOR
        yield pystray.MenuItem("Active Profile", pystray.Menu(*profile_items))
        yield pystray.Menu.SEPARATOR
        yield pystray.MenuItem("Settings...", self._on_settings)
        yield pystray.MenuItem("Quit", self._on_quit)

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
        self.icon = pystray.Icon("WinAnchor", image, "WinAnchor", menu=pystray.Menu(self._get_menu_items))
        
        # Start HotkeyManager in a daemon thread so pystray's blocking run() works
        hk_thread = threading.Thread(target=self._run_hotkey_listener, daemon=True)
        hk_thread.start()

        # Start SystemEventListener in a daemon thread
        el_thread = threading.Thread(target=self._run_event_listener, daemon=True)
        el_thread.start()

        logger.info("Running tray icon... (Blocking)")
        self.icon.run()
        logger.info("TrayApp stopped.")
