import json
import os
import tempfile
from typing import List, Dict, Any
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class ProfileManager:
    """
    Manages saving and loading of window state profiles to/from disk.
    """
    
    def __init__(self) -> None:
        """
        Initializes the ProfileManager and ensures the standard profile directory exists.
        """
        appdata = os.environ.get('APPDATA')
        if not appdata:
            appdata = os.path.expanduser('~')
            
        self.profiles_dir = os.path.join(appdata, 'WinAnchor', 'profiles')
        
        try:
            os.makedirs(self.profiles_dir, exist_ok=True)
            logger.debug(f"Profile directory set to: {self.profiles_dir}")
        except Exception as e:
            logger.error(f"Failed to create profile directory {self.profiles_dir}: {e}")

    def save_profile(self, state: List[Dict[str, Any]], profile_name: str = "default") -> bool:
        """
        Serializes the window state list to a JSON file.
        
        Args:
            state (List[Dict[str, Any]]): The list of window states to save.
            profile_name (str): The name of the profile (without .json extension).
            
        Returns:
            bool: True if successful, False otherwise.
        """
        file_path = os.path.join(self.profiles_dir, f"{profile_name}.json")
        try:
            with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False, dir=self.profiles_dir) as f:
                json.dump(state, f, ensure_ascii=False, indent=4)
                f.flush()
                os.fsync(f.fileno())
                temp_name = f.name
            os.replace(temp_name, file_path)
            logger.info(f"Successfully saved profile '{profile_name}' to {file_path}")
            return True
        except Exception as e:
            if 'temp_name' in locals() and os.path.exists(temp_name):
                try:
                    os.remove(temp_name)
                except Exception:
                    pass
            logger.error(f"Failed to save profile '{profile_name}' to {file_path}: {e}")
            return False

    def load_profile(self, profile_name: str = "default") -> List[Dict[str, Any]]:
        """
        Reads a window state list from a JSON file.
        
        Args:
            profile_name (str): The name of the profile to load.
            
        Returns:
            List[Dict[str, Any]]: The loaded window states, or an empty list if failed/not found.
        """
        file_path = os.path.join(self.profiles_dir, f"{profile_name}.json")
        if not os.path.exists(file_path):
            logger.warning(f"Profile file not found: {file_path}")
            return []
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Basic validation to ensure the loaded JSON is a list
            if not isinstance(data, list):
                logger.warning(f"Profile file {file_path} contains invalid data format. Expected a list.")
                return []
                
            logger.info(f"Successfully loaded profile '{profile_name}' from {file_path} ({len(data)} windows)")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON in profile {file_path}: {e}")
        except Exception as e:
            logger.error(f"Failed to load profile from {file_path}: {e}")
            
        return []
