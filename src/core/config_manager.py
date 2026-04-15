import json
import os
import tempfile
from typing import Dict
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class ConfigManager:
    """
    Manages application configuration, such as hotkeys.
    """
    
    def __init__(self) -> None:
        """
        Initializes ConfigManager and ensures the configuration file exists.
        """
        appdata = os.environ.get('APPDATA')
        if not appdata:
            appdata = os.path.expanduser('~')
            
        self.config_dir = os.path.join(appdata, 'WinAnchor')
        self.config_path = os.path.join(self.config_dir, 'config.json')
        
        # Default configuration
        self.config = {
            "save_hotkey": "alt+shift+s",
            "restore_hotkey": "alt+shift+r",
            "exit_hotkey": "ctrl+shift+q"  # Keep exit hotkey standard or also configurable (optional)
        }
        
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            self._load_config()
        except Exception as e:
            logger.error(f"Failed to create config directory {self.config_dir}: {e}")

    def _load_config(self) -> None:
        """Reads configuration from disk, creating it if it doesn't exist."""
        if not os.path.exists(self.config_path):
            logger.info(f"Config file not found, creating default at: {self.config_path}")
            self.save_config(self.config)
            return
            
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                
            if isinstance(loaded_config, dict):
                # Update existing config with loaded values (preserves defaults for missing keys)
                self.config.update(loaded_config)
                logger.info(f"Successfully loaded configuration from {self.config_path}")
            else:
                logger.warning(f"Config file {self.config_path} contains invalid data format. Using defaults.")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON in config {self.config_path}: {e}. Using defaults.")
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}. Using defaults.")

    def save_config(self, new_config: Dict[str, str]) -> bool:
        """
        Saves the given configuration to disk.
        
        Args:
            new_config (Dict[str, str]): The dictionary containing configuration data.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        self.config.update(new_config)
        try:
            with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False, dir=self.config_dir) as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
                f.flush()
                os.fsync(f.fileno())
                temp_name = f.name
            os.replace(temp_name, self.config_path)
            logger.info(f"Successfully saved config to {self.config_path}")
            return True
        except Exception as e:
            if 'temp_name' in locals() and os.path.exists(temp_name):
                try:
                    os.remove(temp_name)
                except Exception:
                    pass
            logger.error(f"Failed to save config to {self.config_path}: {e}")
            return False

    def get(self, key: str, default: str = "") -> str:
        """Gets a configuration value."""
        return self.config.get(key, default)
