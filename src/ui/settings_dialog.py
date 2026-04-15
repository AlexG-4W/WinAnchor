import tkinter as tk
from tkinter import messagebox
from typing import Callable

class SettingsDialog:
    """
    A simple tkinter dialog for configuring hotkeys.
    """
    def __init__(self, current_save_hotkey: str, current_restore_hotkey: str, on_save_callback: Callable[[str, str], None]) -> None:
        """
        Initializes the SettingsDialog.
        
        Args:
            current_save_hotkey (str): The current save hotkey.
            current_restore_hotkey (str): The current restore hotkey.
            on_save_callback (Callable[[str, str], None]): Callback triggered with new hotkeys when saved.
        """
        self.current_save_hotkey = current_save_hotkey
        self.current_restore_hotkey = current_restore_hotkey
        self.on_save_callback = on_save_callback

    def show(self) -> None:
        """Displays the settings dialog."""
        root = tk.Tk()
        root.title("WinAnchor Settings")
        root.geometry("300x150")
        root.resizable(False, False)
        
        # Ensure it appears on top of other windows
        root.attributes('-topmost', True)
        
        # Save Hotkey
        tk.Label(root, text="Save Layout Hotkey:").pack(pady=(10, 0))
        save_entry = tk.Entry(root, width=30)
        save_entry.insert(0, self.current_save_hotkey)
        save_entry.pack(pady=5)
        
        # Restore Hotkey
        tk.Label(root, text="Restore Layout Hotkey:").pack(pady=(5, 0))
        restore_entry = tk.Entry(root, width=30)
        restore_entry.insert(0, self.current_restore_hotkey)
        restore_entry.pack(pady=5)
        
        def save_clicked():
            new_save = save_entry.get().strip()
            new_restore = restore_entry.get().strip()
            
            if not new_save or not new_restore:
                messagebox.showerror("Error", "Hotkeys cannot be empty.", parent=root)
                return
                
            try:
                self.on_save_callback(new_save, new_restore)
                root.destroy()
            except ValueError as e:
                # Caught an error during hotkey registration
                messagebox.showerror("Invalid Hotkey", str(e), parent=root)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save settings: {e}", parent=root)

        # Save Button
        save_btn = tk.Button(root, text="Save", command=save_clicked, width=10)
        save_btn.pack(pady=10)
        
        # Center the window on the screen
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
        y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
        root.geometry(f"+{x}+{y}")
        
        root.mainloop()
