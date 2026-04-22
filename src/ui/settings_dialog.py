import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List

class SettingsDialog:
    """
    A simple tkinter dialog for configuring hotkeys and profile names.
    """
    def __init__(self, current_save_hotkey: str, current_restore_hotkey: str, 
                 profile_names: List[str], on_save_callback: Callable[[str, str, List[str]], None]) -> None:
        """
        Initializes the SettingsDialog.
        
        Args:
            current_save_hotkey (str): The current save hotkey.
            current_restore_hotkey (str): The current restore hotkey.
            profile_names (List[str]): List of current profile names.
            on_save_callback (Callable[[str, str, List[str]], None]): Callback triggered with new hotkeys and profile names when saved.
        """
        self.current_save_hotkey = current_save_hotkey
        self.current_restore_hotkey = current_restore_hotkey
        self.profile_names = profile_names
        self.on_save_callback = on_save_callback

    def show(self) -> None:
        """Displays the settings dialog."""
        root = tk.Tk()
        root.title("WinAnchor Settings")
        root.geometry("350x380")
        root.resizable(False, False)
        
        # Ensure it appears on top of other windows
        root.attributes('-topmost', True)
        
        main_frame = ttk.Frame(root, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Hotkeys Section
        hotkey_frame = ttk.LabelFrame(main_frame, text="Hotkeys", padding="10 10 10 10")
        hotkey_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(hotkey_frame, text="Save Layout Hotkey:").pack(anchor=tk.W)
        save_entry = ttk.Entry(hotkey_frame, width=30)
        save_entry.insert(0, self.current_save_hotkey)
        save_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(hotkey_frame, text="Restore Layout Hotkey:").pack(anchor=tk.W)
        restore_entry = ttk.Entry(hotkey_frame, width=30)
        restore_entry.insert(0, self.current_restore_hotkey)
        restore_entry.pack(fill=tk.X)
        
        # Profiles Section
        profile_frame = ttk.LabelFrame(main_frame, text="Profile Names", padding="10 10 10 10")
        profile_frame.pack(fill=tk.X, pady=(0, 20))
        
        profile_entries = []
        for i in range(4):
            frame = ttk.Frame(profile_frame)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=f"Profile {i+1}:", width=10).pack(side=tk.LEFT)
            entry = ttk.Entry(frame)
            name = self.profile_names[i] if i < len(self.profile_names) else f"Profile {i+1}"
            entry.insert(0, name)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            profile_entries.append(entry)
            
        def save_clicked():
            new_save = save_entry.get().strip()
            new_restore = restore_entry.get().strip()
            new_names = [e.get().strip() or f"Profile {i+1}" for i, e in enumerate(profile_entries)]
            
            if not new_save or not new_restore:
                messagebox.showerror("Error", "Hotkeys cannot be empty.", parent=root)
                return
                
            try:
                self.on_save_callback(new_save, new_restore, new_names)
                root.destroy()
            except ValueError as e:
                # Caught an error during hotkey registration
                messagebox.showerror("Invalid Hotkey", str(e), parent=root)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save settings: {e}", parent=root)

        # Save Button
        save_btn = ttk.Button(main_frame, text="Save Settings", command=save_clicked)
        save_btn.pack()
        
        # Center the window on the screen
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
        y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
        root.geometry(f"+{x}+{y}")
        
        root.mainloop()
