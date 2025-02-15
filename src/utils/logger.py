"""
Logger module - מודול לניהול לוגים
"""
import os
import logging
import colorlog
from datetime import datetime

from src.core.config import settings

def setup_logger(name: str = None) -> logging.Logger:
    """
    הגדרת לוגר עם פורמט צבעוני
    
    Args:
        name: שם הלוגר (אופציונלי)
        
    Returns:
        logging.Logger: הלוגר המוגדר
    """
    if name is None:
        name = "app"
        
    logger = colorlog.getLogger(name)
    
    if logger.handlers:
        return logger
        
    # הגדרת רמת הלוג
    logger.setLevel(settings.LOG_LEVEL)
    
    # יצירת תיקיית לוגים אם לא קיימת
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    # הגדרת פורמט צבעוני
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    
    # הגדרת handler לקונסול
    console_handler = colorlog.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # הגדרת handler לקובץ
    file_handler = logging.FileHandler(f"logs/{name}.log", encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    logger.addHandler(file_handler)
    
    # הגדרת handler לקובץ שגיאות
    error_handler = logging.FileHandler(f"logs/error.log", encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    logger.addHandler(error_handler)
    
    return logger

# יצירת לוגר ברירת מחדל
logger = setup_logger()

def log_action(user_id: str, action: str, level: str = "INFO", **kwargs):
    """
    פונקציית עזר לתיעוד פעולות משתמשים
    
    Args:
        user_id: מזהה המשתמש
        action: סוג הפעולה
        level: רמת החשיבות (ברירת מחדל: INFO)
        **kwargs: פרמטרים נוספים לתיעוד
    """
    log_message = f"User {user_id} performed {action}"
    if kwargs:
        params_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        log_message += f" with params: {params_str}"
    
    getattr(logger, level.lower())(log_message) 