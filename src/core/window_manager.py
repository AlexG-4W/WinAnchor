import win32gui
import win32con
import win32api
import win32process
import pywintypes
from typing import List, Dict, Any, Optional
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class WindowManager:
    """
    Manages reading and setting of window coordinates and states using the Windows API.
    """

    def __init__(self) -> None:
        pass

    def get_windows_state(self) -> List[Dict[str, Any]]:
        """
        Iterates through all visible windows and retrieves their states.
        
        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing window states.
        """
        windows_state: List[Dict[str, Any]] = []

        def enum_windows_callback(hwnd: int, ctx: List[Dict[str, Any]]) -> None:
            # Filter out invisible and nameless windows
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                # Filter out tool windows
                ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                if ex_style & win32con.WS_EX_TOOLWINDOW:
                    return

                try:
                    title = win32gui.GetWindowText(hwnd)
                    
                    try:
                        # Use GetWindowPlacement to capture correct states for Min/Maximized windows
                        placement = win32gui.GetWindowPlacement(hwnd)
                        flags, showCmd, ptMin, ptMax, rcNormalPosition = placement
                    except pywintypes.error as e:
                        logger.warning(f"Failed to get placement for HWND {hwnd}: {e}")
                        return
                    
                    # Also keep standard rects for backward compatibility/logging
                    rect = win32gui.GetWindowRect(hwnd)
                    x, y, right, bottom = rect
                    width = right - x
                    height = bottom - y
                    
                    # Get process name
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    process_name = self._get_process_name_from_pid(pid)

                    state = {
                        "hwnd": hwnd,
                        "title": title,
                        "process_name": process_name,
                        "x": x,
                        "y": y,
                        "width": width,
                        "height": height,
                        "showCmd": showCmd,
                        "rcNormalPosition": list(rcNormalPosition) # Convert tuple to list for JSON
                    }
                    ctx.append(state)
                    logger.debug(f"Saved state for window: {title} (HWND: {hwnd}) at {rcNormalPosition}, showCmd: {showCmd}")
                except Exception as e:
                    logger.warning(f"Failed to get state for HWND {hwnd}: {e}")

        try:
            win32gui.EnumWindows(enum_windows_callback, windows_state)
        except Exception as e:
            logger.error(f"Error enumerating windows: {e}")
            
        return windows_state

    def _get_process_name_from_pid(self, pid: int) -> Optional[str]:
        """
        Retrieves the process name given its Process ID.
        
        Args:
            pid (int): Process ID.
            
        Returns:
            Optional[str]: Process name or None if unavailable.
        """
        try:
            PROCESS_QUERY_INFORMATION = 0x0400
            PROCESS_VM_READ = 0x0010
            h_process = win32api.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
            if h_process:
                try:
                    process_name = win32process.GetModuleFileNameEx(h_process, 0)
                    return process_name.split('\\')[-1]
                finally:
                    win32api.CloseHandle(h_process)
        except Exception:
            pass
        return None

    def restore_windows_state(self, states: List[Dict[str, Any]]) -> None:
        """
        Restores windows to their saved placement (and coordinates) based on HWND.
        
        Args:
            states (List[Dict[str, Any]]): List of window state dictionaries to restore.
        """
        for state in states:
            hwnd = state.get("hwnd")
            title = state.get("title")
            showCmd = state.get("showCmd")
            rcNormalPosition = state.get("rcNormalPosition")
            
            # Read standard properties as fallback
            x = state.get("x")
            y = state.get("y")
            width = state.get("width")
            height = state.get("height")
            
            if hwnd is None:
                logger.warning(f"Invalid state data: {state}")
                continue
                
            try:
                if win32gui.IsWindow(hwnd):
                    current_title = win32gui.GetWindowText(hwnd)
                    if current_title == title:
                        if showCmd is not None and rcNormalPosition is not None:
                            try:
                                # Get current placement to preserve flags, ptMin, ptMax
                                current_placement = win32gui.GetWindowPlacement(hwnd)
                                flags, curr_showCmd, ptMin, ptMax, curr_rcNormal = current_placement
                                
                                # Inject our saved configuration
                                new_placement = (flags, showCmd, ptMin, ptMax, tuple(rcNormalPosition))
                                win32gui.SetWindowPlacement(hwnd, new_placement)
                                logger.info(f"Restored window placement: {title} (HWND: {hwnd}) to showCmd {showCmd}, rect {rcNormalPosition}")
                            except pywintypes.error as e:
                                logger.error(f"Access denied or error placing window {title} (HWND: {hwnd}): {e}")
                        elif x is not None and y is not None and width is not None and height is not None:
                            # Fallback logic for profiles saved prior to GetWindowPlacement support
                            win32gui.MoveWindow(hwnd, x, y, width, height, True)
                            logger.info(f"Restored window (legacy MoveWindow): {title} (HWND: {hwnd}) to ({x}, {y}, {width}, {height})")
                        else:
                            logger.warning(f"Insufficient state data to restore window {title} (HWND: {hwnd}).")
                    else:
                        logger.warning(f"Window title mismatch for HWND {hwnd}. Expected '{title}', got '{current_title}'. Skipping.")
                else:
                    logger.warning(f"Window with HWND {hwnd} ({title}) no longer exists. Skipping.")
            except Exception as e:
                logger.error(f"Failed to restore window {title} (HWND: {hwnd}): {e}")
