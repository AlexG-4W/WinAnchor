import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(name: str = "WinAnchor", log_file: str = "winanchor.log", level: int = logging.DEBUG) -> logging.Logger:
    """
    Sets up a rotating file logger.
    
    Args:
        name (str): Name of the logger.
        log_file (str): Name of the log file. It will be saved in %APPDATA%\WinAnchor.
        level (int): Logging level.
        
    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Ensure log file goes to AppData to avoid permission errors when running as executable
        appdata = os.environ.get('APPDATA')
        if not appdata:
            appdata = os.path.expanduser('~')
            
        log_dir = os.path.join(appdata, 'WinAnchor')
        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception:
            pass
            
        abs_log_file = os.path.join(log_dir, log_file)
        
        import sys
        if hasattr(sys.stdout, 'reconfigure') and sys.stdout is not None:
            sys.stdout.reconfigure(encoding='utf-8')

        # Create a rotating file handler (max 5MB, keep 3 backups)
        file_handler = RotatingFileHandler(abs_log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Also log to console if stdout is available (not the case in pythonw / PyInstaller --windowed)
        if sys.stdout is not None:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
    return logger
