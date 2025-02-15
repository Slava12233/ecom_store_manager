"""
מערכת לוגים מרכזית לכל הפרויקט
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from core.config import settings

class CustomFormatter(logging.Formatter):
    """מעצב מותאם אישית ללוגים עם צבעים וזמן מדויק"""
    
    # צבעים להדגשת חשיבות ההודעה
    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    # פורמט מותאם לכל רמת חשיבות
    FORMATS = {
        logging.DEBUG: grey + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.INFO: blue + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.WARNING: yellow + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.ERROR: red + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.CRITICAL: bold_red + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

def ensure_log_directory(log_dir: str) -> bool:
    """
    וידוא שתיקיית הלוגים קיימת ונגישה
    
    Args:
        log_dir: נתיב לתיקיית הלוגים
    
    Returns:
        bool: האם התיקייה קיימת ונגישה
    """
    try:
        # קבלת הנתיב המלא
        abs_log_dir = os.path.abspath(log_dir)
        print(f"מנסה ליצור תיקיית לוגים ב: {abs_log_dir}")
        
        # יצירת התיקייה אם לא קיימת
        if not os.path.exists(abs_log_dir):
            print(f"תיקיית הלוגים לא קיימת, יוצר אותה ב: {abs_log_dir}")
            os.makedirs(abs_log_dir, exist_ok=True)
            print(f"תיקיית הלוגים נוצרה בהצלחה: {abs_log_dir}")
        else:
            print(f"תיקיית הלוגים כבר קיימת ב: {abs_log_dir}")
        
        # בדיקת הרשאות כתיבה
        test_file = os.path.join(abs_log_dir, 'test.log')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print(f"בדיקת הרשאות כתיבה עברה בהצלחה: {abs_log_dir}")
        except Exception as write_error:
            print(f"שגיאה בבדיקת הרשאות כתיבה: {str(write_error)}", file=sys.stderr)
            return False
        
        return True
    except Exception as e:
        print(f"שגיאה קריטית ביצירת תיקיית הלוגים: {str(e)}", file=sys.stderr)
        print(f"נתיב מלא שנוסה: {abs_log_dir}", file=sys.stderr)
        return False

def setup_logger(name: str = "ecom_store_manager") -> logging.Logger:
    """
    הגדרת הלוגר המרכזי של המערכת
    
    Args:
        name: שם הלוגר (ברירת מחדל: ecom_store_manager)
    
    Returns:
        logging.Logger: הלוגר המוגדר
    """
    # יצירת תיקיית לוגים
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
    if not ensure_log_directory(log_dir):
        print("לא ניתן ליצור תיקיית לוגים. משתמש בלוגים לקונסול בלבד.", file=sys.stderr)
        
        # הגדרת לוגר בסיסי לקונסול
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(CustomFormatter())
        logger.addHandler(console_handler)
        
        return logger
    
    # הגדרת הלוגר
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # מניעת כפילות handlers
    if logger.handlers:
        return logger
    
    try:
        # הגדרת handler לקונסול עם פורמט צבעוני
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(CustomFormatter())
        logger.addHandler(console_handler)
        
        # הגדרת handler לקובץ לוגים רגיל (INFO ומעלה)
        file_handler = RotatingFileHandler(
            filename=os.path.join(log_dir, 'app.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(file_handler)

        # הגדרת handler לקובץ שגיאות (ERROR ומעלה)
        error_handler = RotatingFileHandler(
            filename=os.path.join(log_dir, 'error.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
            'Stack trace (if available):\n%(exc_info)s\n'
        ))
        logger.addHandler(error_handler)
        
        print(f"הלוגר הוגדר בהצלחה. קבצי לוג יישמרו ב: {log_dir}")
        return logger
        
    except Exception as e:
        print(f"שגיאה בהגדרת handlers ללוגר: {str(e)}", file=sys.stderr)
        return logger

# יצירת מופע גלובלי של הלוגר
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