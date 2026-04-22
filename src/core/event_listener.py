import win32gui
import win32con
import win32api
import threading
import pywintypes
from typing import Callable, Optional
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class SystemEventListener:
    """
    Listens for system events like WM_DISPLAYCHANGE and triggers a callback after a delay.
    """
    def __init__(self, restore_callback: Callable[[], None], delay_seconds: float = 3.0) -> None:
        """
        Initializes the listener.
        
        Args:
            restore_callback (Callable[[], None]): Function to call when display changes.
            delay_seconds (float): How long to wait before triggering the callback.
        """
        self.restore_callback = restore_callback
        self.delay_seconds = delay_seconds
        self.hwnd: Optional[int] = None
        self._timer: Optional[threading.Timer] = None

    def _wndproc(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        """Window procedure to handle system messages."""
        if msg == win32con.WM_DISPLAYCHANGE:
            logger.info("WM_DISPLAYCHANGE detected. Monitor configuration changed.")
            self._schedule_restore()
            return 0
        elif msg == win32con.WM_DESTROY:
            logger.debug("SystemEventListener window destroyed.")
            win32gui.PostQuitMessage(0)
            return 0
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _schedule_restore(self) -> None:
        """Schedules the restore callback with a delay, resetting it if already scheduled."""
        if self._timer and self._timer.is_alive():
            logger.debug("Restore timer already running. Resetting timer.")
            self._timer.cancel()
            
        logger.info(f"Scheduling restore in {self.delay_seconds} seconds...")
        self._timer = threading.Timer(self.delay_seconds, self._execute_restore)
        self._timer.daemon = True
        self._timer.start()

    def _execute_restore(self) -> None:
        """Executes the restore callback in the timer thread."""
        logger.info("Executing delayed restore after display change...")
        try:
            self.restore_callback()
        except Exception as e:
            logger.error(f"Error during delayed restore: {e}")

    def start(self) -> None:
        """
        Registers the window class, creates the hidden window, and starts the message pump.
        This method blocks until PostQuitMessage is called.
        """
        logger.info("Starting SystemEventListener message pump...")
        wc = win32gui.WNDCLASS()
        wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = "WinAnchorEventListener"
        wc.lpfnWndProc = self._wndproc

        try:
            win32gui.RegisterClass(wc)
        except pywintypes.error as e:
            if e.winerror == 1410:  # ERROR_CLASS_ALREADY_EXISTS
                pass
            else:
                logger.error(f"Failed to register window class: {e}")
                raise

        # Create a message-only window
        try:
            self.hwnd = win32gui.CreateWindowEx(
                0,
                wc.lpszClassName,
                "WinAnchor Hidden Listener",
                0,
                0, 0, 0, 0,
                0, # Parent is 0 to make it a top-level window capable of receiving broadcasts
                0,
                wc.hInstance,
                None
            )
        except Exception as e:
            logger.error(f"Failed to create hidden window for SystemEventListener: {e}")
            return

        if not self.hwnd:
            logger.error("Failed to create hidden window for SystemEventListener (hwnd is 0).")
            return

        logger.debug(f"Created message-only window with HWND: {self.hwnd}")
        
        # Start the message pump (blocking)
        win32gui.PumpMessages()
        logger.info("SystemEventListener message pump exited.")

    def stop(self) -> None:
        """
        Destroys the hidden window, which stops the message pump.
        """
        logger.info("Stopping SystemEventListener...")
        if self._timer and self._timer.is_alive():
            self._timer.cancel()
            
        if self.hwnd:
            try:
                # Posting WM_CLOSE to the window will trigger WM_DESTROY and PostQuitMessage
                win32gui.PostMessage(self.hwnd, win32con.WM_CLOSE, 0, 0)
            except Exception as e:
                logger.error(f"Failed to post close message to listener window: {e}")
