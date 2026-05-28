import ctypes
import win32gui
import win32con
import win32api
import win32process
import pywintypes
from difflib import SequenceMatcher
from typing import List, Dict, Any, Optional, Tuple
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# --- Matching score weights ---
SCORE_PROCESS_NAME = 40
SCORE_CLASS_NAME = 20
SCORE_GEOMETRY = 30
SCORE_TITLE = 10
MIN_MATCH_SCORE = 60

# Tolerance in pixels for rcNormalPosition comparison (per edge)
GEOMETRY_TOLERANCE = 50


class WindowManager:
    """
    Manages reading and setting of window coordinates and states using the Windows API.
    Uses multi-signal fingerprinting for robust cross-session window identification.
    """

    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Save Phase
    # ------------------------------------------------------------------

    def get_windows_state(self) -> List[Dict[str, Any]]:
        """
        Iterates through all top-level windows and retrieves their states.
        Captures visible and minimized windows on the active virtual desktop.
        Filters out tool windows, cloaked (background/other-desktop) windows,
        and windows with no title.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing window states.
                                  Order follows EnumWindows z-order (top → bottom).
        """
        windows_state: List[Dict[str, Any]] = []

        def enum_windows_callback(hwnd: int, ctx: List[Dict[str, Any]]) -> None:
            # 1. Must have a title
            if not win32gui.GetWindowText(hwnd):
                return

            # 2. Must NOT be a tool window
            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            if ex_style & win32con.WS_EX_TOOLWINDOW:
                return

            # 3. Must be visible OR minimized (iconic)
            if not win32gui.IsWindowVisible(hwnd) and not win32gui.IsIconic(hwnd):
                return

            # 4. Must NOT be cloaked by DWM (virtual desktop / background UWP)
            DWMWA_CLOAKED = 14
            cloaked = ctypes.c_int(0)
            try:
                ctypes.windll.dwmapi.DwmGetWindowAttribute(
                    hwnd, DWMWA_CLOAKED, ctypes.byref(cloaked), ctypes.sizeof(cloaked)
                )
                if cloaked.value != 0:
                    return
            except Exception:
                pass

            try:
                title = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)

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
                    "class_name": class_name,
                    "process_name": process_name,
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height,
                    "showCmd": showCmd,
                    "rcNormalPosition": list(rcNormalPosition)  # Convert tuple to list for JSON
                }
                ctx.append(state)
                logger.debug(
                    f"Saved state for window: {title} (HWND: {hwnd}, "
                    f"class: {class_name}, proc: {process_name}) "
                    f"at {rcNormalPosition}, showCmd: {showCmd}"
                )
            except Exception as e:
                logger.warning(f"Failed to get state for HWND {hwnd}: {e}")

        try:
            win32gui.EnumWindows(enum_windows_callback, windows_state)
        except Exception as e:
            logger.error(f"Error enumerating windows: {e}")

        return windows_state

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

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

    def _enumerate_live_windows(self) -> List[Dict[str, Any]]:
        """
        Enumerates all currently-live windows with the same criteria used
        during the save phase.  Returns a list of lightweight fingerprint
        dicts (hwnd, title, class_name, process_name, rcNormalPosition).
        """
        live: List[Dict[str, Any]] = []

        def callback(hwnd: int, ctx: List[Dict[str, Any]]) -> None:
            # 1. Must have a title
            if not win32gui.GetWindowText(hwnd):
                return

            # 2. Must NOT be a tool window
            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            if ex_style & win32con.WS_EX_TOOLWINDOW:
                return

            # 3. Must be visible OR minimized (iconic)
            if not win32gui.IsWindowVisible(hwnd) and not win32gui.IsIconic(hwnd):
                return

            # 4. Must NOT be cloaked by DWM (virtual desktop / background UWP)
            DWMWA_CLOAKED = 14
            cloaked = ctypes.c_int(0)
            try:
                ctypes.windll.dwmapi.DwmGetWindowAttribute(
                    hwnd, DWMWA_CLOAKED, ctypes.byref(cloaked), ctypes.sizeof(cloaked)
                )
                if cloaked.value != 0:
                    return
            except Exception:
                pass

            try:
                title = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)

                try:
                    placement = win32gui.GetWindowPlacement(hwnd)
                    _, _, _, _, rcNormalPosition = placement
                except pywintypes.error:
                    rcNormalPosition = None

                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                process_name = self._get_process_name_from_pid(pid)

                ctx.append({
                    "hwnd": hwnd,
                    "title": title,
                    "class_name": class_name,
                    "process_name": process_name,
                    "rcNormalPosition": list(rcNormalPosition) if rcNormalPosition else None,
                })
            except Exception:
                pass

        try:
            win32gui.EnumWindows(callback, live)
        except Exception as e:
            logger.error(f"Error enumerating live windows: {e}")

        return live

    # ------------------------------------------------------------------
    # Matching helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _geometry_matches(saved_rect: List[int], live_rect: List[int],
                          tolerance: int = GEOMETRY_TOLERANCE) -> bool:
        """
        Returns True if every edge of the two rects is within *tolerance* px.
        Both rects are [left, top, right, bottom].
        """
        if len(saved_rect) != 4 or len(live_rect) != 4:
            return False
        return all(abs(s - l) <= tolerance for s, l in zip(saved_rect, live_rect))

    @staticmethod
    def _title_similarity(saved_title: str, live_title: str) -> float:
        """
        Returns a similarity ratio in [0.0, 1.0] between two window titles.
        Uses substring containment as a fast-path and falls back to
        SequenceMatcher for fuzzy comparison.
        """
        if not saved_title or not live_title:
            return 0.0
        # Normalise for comparison
        s = saved_title.lower()
        l = live_title.lower()
        # Exact match
        if s == l:
            return 1.0
        # Substring containment (handles title suffix changes)
        if s in l or l in s:
            return 0.85
        # Fuzzy ratio
        return SequenceMatcher(None, s, l).ratio()

    def _score_match(self, saved: Dict[str, Any], live: Dict[str, Any]) -> int:
        """
        Computes a match score between a *saved* window state and a *live*
        window candidate.  Higher is better.

        Scoring:
            +40  process_name matches (case-insensitive)
            +20  class_name matches
            +30  rcNormalPosition within tolerance
            +10  title similarity (scaled: 1.0 → +10, 0.5 → +5, …)
        """
        score = 0

        # --- process_name (40 pts) ---
        saved_proc = (saved.get("process_name") or "").lower()
        live_proc = (live.get("process_name") or "").lower()
        if saved_proc and live_proc and saved_proc == live_proc:
            score += SCORE_PROCESS_NAME

        # --- class_name (20 pts) ---
        saved_cls = saved.get("class_name") or ""
        live_cls = live.get("class_name") or ""
        if saved_cls and live_cls and saved_cls == live_cls:
            score += SCORE_CLASS_NAME

        # --- geometry (30 pts) ---
        saved_rect = saved.get("rcNormalPosition")
        live_rect = live.get("rcNormalPosition")
        if saved_rect and live_rect and self._geometry_matches(saved_rect, live_rect):
            score += SCORE_GEOMETRY

        # --- title (up to 10 pts, scaled by similarity) ---
        saved_title = saved.get("title") or ""
        live_title = live.get("title") or ""
        similarity = self._title_similarity(saved_title, live_title)
        score += int(SCORE_TITLE * similarity)

        return score

    # ------------------------------------------------------------------
    # Restore Phase
    # ------------------------------------------------------------------

    def restore_windows_state(self, states: List[Dict[str, Any]]) -> None:
        """
        Restores windows to their saved placement using multi-signal fuzzy
        matching instead of raw HWND lookup.

        Algorithm:
            1. Enumerate all currently-live windows.
            2. For each saved state, score every unclaimed live window.
            3. Greedily assign the best-scoring live window (≥ MIN_MATCH_SCORE).
            4. Apply SetWindowPlacement in reverse z-order (bottom-up) so
               the topmost saved window is restored last and stays on top.

        Args:
            states (List[Dict[str, Any]]): List of saved window state dicts.
        """
        if not states:
            logger.warning("No states to restore.")
            return

        # 1. Discover all currently-live windows
        live_windows = self._enumerate_live_windows()
        logger.info(f"Discovered {len(live_windows)} live windows for matching.")

        # 2. Build a score matrix and perform greedy 1:1 assignment
        #    claimed_hwnds tracks which live windows have already been matched.
        claimed_hwnds: set = set()

        # Each element: (saved_state, matched_live_hwnd)
        matched_pairs: List[Tuple[Dict[str, Any], int]] = []

        for saved in states:
            best_score = 0
            best_live = None

            for live in live_windows:
                if live["hwnd"] in claimed_hwnds:
                    continue

                score = self._score_match(saved, live)
                if score > best_score:
                    best_score = score
                    best_live = live

            if best_live is not None and best_score >= MIN_MATCH_SCORE:
                claimed_hwnds.add(best_live["hwnd"])
                matched_pairs.append((saved, best_live["hwnd"]))
                logger.debug(
                    f"Matched saved '{saved.get('title')}' → live HWND {best_live['hwnd']} "
                    f"('{best_live.get('title')}') with score {best_score}"
                )
            else:
                logger.warning(
                    f"No match found for saved window '{saved.get('title')}' "
                    f"(best score: {best_score}). Skipping."
                )

        logger.info(
            f"Matched {len(matched_pairs)} of {len(states)} saved windows."
        )

        # 3. Restore in reverse z-order.
        #    `states` arrive in EnumWindows order (top → bottom).
        #    We iterate bottom → top so that the topmost window is the last
        #    one to receive SetWindowPlacement and therefore stays on top.
        for saved, live_hwnd in reversed(matched_pairs):
            self._apply_placement(saved, live_hwnd)

    def _apply_placement(self, saved: Dict[str, Any], hwnd: int) -> None:
        """
        Applies a saved placement to a live window identified by *hwnd*.
        Falls back to legacy MoveWindow for profiles without placement data.
        """
        title = saved.get("title", "<unknown>")
        showCmd = saved.get("showCmd")
        rcNormalPosition = saved.get("rcNormalPosition")

        # Legacy fallback fields
        x = saved.get("x")
        y = saved.get("y")
        width = saved.get("width")
        height = saved.get("height")

        try:
            if not win32gui.IsWindow(hwnd):
                logger.warning(f"Matched HWND {hwnd} for '{title}' is no longer valid. Skipping.")
                return

            if showCmd is not None and rcNormalPosition is not None:
                try:
                    # Get current placement to preserve flags, ptMin, ptMax
                    current_placement = win32gui.GetWindowPlacement(hwnd)
                    flags, _, ptMin, ptMax, _ = current_placement

                    # Inject our saved configuration
                    new_placement = (flags, showCmd, ptMin, ptMax, tuple(rcNormalPosition))
                    win32gui.SetWindowPlacement(hwnd, new_placement)
                    logger.info(
                        f"Restored window placement: {title} (HWND: {hwnd}) "
                        f"to showCmd {showCmd}, rect {rcNormalPosition}"
                    )
                except pywintypes.error as e:
                    logger.error(
                        f"Access denied or error placing window {title} (HWND: {hwnd}): {e}"
                    )
            elif x is not None and y is not None and width is not None and height is not None:
                # Fallback logic for profiles saved prior to GetWindowPlacement support
                win32gui.MoveWindow(hwnd, x, y, width, height, True)
                logger.info(
                    f"Restored window (legacy MoveWindow): {title} (HWND: {hwnd}) "
                    f"to ({x}, {y}, {width}, {height})"
                )
            else:
                logger.warning(
                    f"Insufficient state data to restore window {title} (HWND: {hwnd})."
                )
        except Exception as e:
            logger.error(f"Failed to restore window {title} (HWND: {hwnd}): {e}")
