import keyboard
from typing import Callable, Optional
import threading
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class HotkeyManager:
    """
    Manages global hotkeys for saving, restoring, and exiting the application.
    """
    
    def __init__(self, save_callback: Callable[[], None], restore_callback: Callable[[], None],
                 save_hotkey: str = "alt+shift+s", restore_hotkey: str = "alt+shift+r", exit_hotkey: str = "ctrl+shift+q") -> None:
        """
        Initializes the HotkeyManager.
        
        Args:
            save_callback (Callable[[], None]): Function to call when save hotkey is pressed.
            restore_callback (Callable[[], None]): Function to call when restore hotkey is pressed.
            save_hotkey (str): Initial save hotkey.
            restore_hotkey (str): Initial restore hotkey.
            exit_hotkey (str): Initial exit hotkey.
        """
        self.save_callback = save_callback
        self.restore_callback = restore_callback
        
        self.save_hotkey = save_hotkey
        self.restore_hotkey = restore_hotkey
        self.exit_hotkey = exit_hotkey
        
        self._is_listening = False
        self._lock = threading.Lock()
        
        self._save_hook = None
        self._restore_hook = None

    def _safe_save(self) -> None:
        logger.info("Save hotkey triggered.")
        try:
            self.save_callback()
        except Exception as e:
            logger.error(f"Error during save callback: {e}")

    def _safe_restore(self) -> None:
        logger.info("Restore hotkey triggered.")
        try:
            self.restore_callback()
        except Exception as e:
            logger.error(f"Error during restore callback: {e}")

    def update_hotkeys(self, new_save_hotkey: str, new_restore_hotkey: str) -> None:
        """
        Updates the hotkeys safely if the listener is running.
        
        Args:
            new_save_hotkey (str): New save hotkey.
            new_restore_hotkey (str): New restore hotkey.
        """
        with self._lock:
            # Test keys before committing to the unhook process
            try:
                # We can't really test without hooking, so we just try to hook them inside a try block
                # but unhooking first is required to not leave dangling hooks if the new ones fail.
                pass
            except Exception:
                pass
                
            if self._is_listening:
                try:
                    # Unhook current hotkeys
                    if self._save_hook:
                        keyboard.remove_hotkey(self._save_hook)
                        self._save_hook = None
                        logger.debug("Removed old save hotkey.")
                except Exception as e:
                    logger.debug(f"Could not remove old save hotkey: {e}")
                    
                try:
                    if self._restore_hook:
                        keyboard.remove_hotkey(self._restore_hook)
                        self._restore_hook = None
                        logger.debug("Removed old restore hotkey.")
                except Exception as e:
                    logger.debug(f"Could not remove old restore hotkey: {e}")

            # Update state
            self.save_hotkey = new_save_hotkey
            self.restore_hotkey = new_restore_hotkey
            
            if self._is_listening:
                # Re-register
                try:
                    self._save_hook = keyboard.add_hotkey(self.save_hotkey, self._safe_save)
                    logger.info(f"Registered new save hotkey: {self.save_hotkey}")
                except Exception as e:
                    logger.error(f"Failed to register new save hotkey '{self.save_hotkey}': {e}")
                    raise ValueError(f"Invalid save hotkey: {self.save_hotkey}")

                try:
                    self._restore_hook = keyboard.add_hotkey(self.restore_hotkey, self._safe_restore)
                    logger.info(f"Registered new restore hotkey: {self.restore_hotkey}")
                except Exception as e:
                    logger.error(f"Failed to register new restore hotkey '{self.restore_hotkey}': {e}")
                    # Try to rollback save hotkey to keep state consistent? Not strictly required, 
                    # but raising ValueError will let UI handle it
                    raise ValueError(f"Invalid restore hotkey: {self.restore_hotkey}")

    def start_listening(self) -> None:
        """
        Registers hotkeys and blocks the thread until the exit hotkey is pressed.
        """
        with self._lock:
            try:
                self._save_hook = keyboard.add_hotkey(self.save_hotkey, self._safe_save)
                logger.info(f"Registered save hotkey: {self.save_hotkey}")
                
                self._restore_hook = keyboard.add_hotkey(self.restore_hotkey, self._safe_restore)
                logger.info(f"Registered restore hotkey: {self.restore_hotkey}")
                
                self._is_listening = True
            except Exception as e:
                logger.error(f"Failed to set up hotkeys: {e}")
                return
                
        try:
            logger.info(f"WinAnchor is now listening. Press '{self.exit_hotkey}' to quit.")
            keyboard.wait(self.exit_hotkey)
            logger.info("Exit hotkey triggered. Shutting down WinAnchor listener.")
        except Exception as e:
            logger.error(f"Error in keyboard.wait: {e}")
        finally:
            with self._lock:
                self._is_listening = False
                try:
                    keyboard.unhook_all()
                    logger.info("Hotkeys unregistered.")
                except Exception as e:
                    logger.error(f"Error while unhooking hotkeys: {e}")