import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List

class SettingsDialog:
    """
    A simple tkinter dialog for configuring hotkeys and profile names.
    """
    def __init__(self, current_save_hotkey: str, current_restore_hotkey: str, 
                 profile_names: List[str], ignored_windows: List[str],
                 on_save_callback: Callable[[str, str, List[str], List[str]], None]) -> None:
        """
        Initializes the SettingsDialog.
        
        Args:
            current_save_hotkey (str): The current save hotkey.
            current_restore_hotkey (str): The current restore hotkey.
            profile_names (List[str]): List of current profile names.
            ignored_windows (List[str]): List of ignored window title/process substrings.
            on_save_callback (Callable[[str, str, List[str], List[str]], None]): Callback triggered with new hotkeys, profile names, and ignored windows when saved.
        """
        self.current_save_hotkey = current_save_hotkey
        self.current_restore_hotkey = current_restore_hotkey
        self.profile_names = profile_names
        self.ignored_windows = ignored_windows
        self.on_save_callback = on_save_callback

    def show(self) -> None:
        """Displays the settings dialog."""
        root = tk.Tk()
        root.title("WinAnchor Settings")
        root.resizable(False, False)
        root.minsize(380, 500)

        # Ensure it appears on top of other windows
        root.attributes('-topmost', True)

        main_frame = ttk.Frame(root, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Frame 1: Hotkeys ---
        hotkey_frame = ttk.LabelFrame(main_frame, text="Hotkeys", padding="10 10 10 10")
        hotkey_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(hotkey_frame, text="Save Layout Hotkey:").pack(anchor=tk.W)
        save_entry = ttk.Entry(hotkey_frame, width=30)
        save_entry.insert(0, self.current_save_hotkey)
        save_entry.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(hotkey_frame, text="Restore Layout Hotkey:").pack(anchor=tk.W)
        restore_entry = ttk.Entry(hotkey_frame, width=30)
        restore_entry.insert(0, self.current_restore_hotkey)
        restore_entry.pack(fill=tk.X)

        # --- Frame 2: Profile Names ---
        profile_frame = ttk.LabelFrame(main_frame, text="Profile Names", padding="10 10 10 10")
        profile_frame.pack(fill=tk.X, padx=10, pady=5)

        profile_entries = []
        for i in range(4):
            row = ttk.Frame(profile_frame)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=f"Profile {i+1}:", width=10).pack(side=tk.LEFT)
            entry = ttk.Entry(row)
            name = self.profile_names[i] if i < len(self.profile_names) else f"Profile {i+1}"
            entry.insert(0, name)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            profile_entries.append(entry)

        # --- Frame 3: Ignored Windows ---
        ignore_frame = ttk.LabelFrame(main_frame, text="Ignored Windows (comma-separated)", padding="10 10 10 10")
        ignore_frame.pack(fill=tk.X, padx=10, pady=5)

        ignored_entry = ttk.Entry(ignore_frame, width=30)
        ignored_entry.insert(0, ", ".join(self.ignored_windows))
        ignored_entry.pack(fill=tk.X)

        # --- Frame 4: Buttons ---
        def save_clicked():
            new_save = save_entry.get().strip()
            new_restore = restore_entry.get().strip()
            new_names = [e.get().strip() or f"Profile {i+1}" for i, e in enumerate(profile_entries)]
            new_ignored = [s.strip() for s in ignored_entry.get().split(",") if s.strip()]

            if not new_save or not new_restore:
                messagebox.showerror("Error", "Hotkeys cannot be empty.", parent=root)
                return

            try:
                self.on_save_callback(new_save, new_restore, new_names, new_ignored)
                root.destroy()
            except ValueError as e:
                # Caught an error during hotkey registration
                messagebox.showerror("Invalid Hotkey", str(e), parent=root)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save settings: {e}", parent=root)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=15)

        ttk.Button(btn_frame, text="Save Settings", command=save_clicked).pack(side=tk.LEFT, expand=True, padx=(0, 5))
        ttk.Button(btn_frame, text="Cancel", command=root.destroy).pack(side=tk.LEFT, expand=True, padx=(5, 0))

        # Let Tkinter compute the natural size, then center on screen
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - (root.winfo_reqwidth() // 2)
        y = (root.winfo_screenheight() // 2) - (root.winfo_reqheight() // 2)
        root.geometry(f"+{x}+{y}")

        root.mainloop()

