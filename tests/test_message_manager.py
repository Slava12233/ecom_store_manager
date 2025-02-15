import pytest
from src.utils.message_manager import MessageManager

def test_message_manager():
    """בדיקת טעינת הודעות ופונקציונליות בסיסית"""
    # יצירת מופע של מנהל ההודעות
    message_manager = MessageManager()
    
    # בדיקת טעינת הודעות עזרה
    help_message = message_manager.get_help_message()
    assert help_message is not None
    assert "ניהול הזמנות" in help_message
    assert "ניהול משלוחים" in help_message
    
    # בדיקת הודעות שגיאה
    error_message = message_manager.get_error_message("not_found", item="מוצר")
    assert "לא נמצא מוצר" in error_message
    
    # בדיקת הודעות סטטוס
    status_message = message_manager.get_status_message("success")
    assert "הפעולה הושלמה בהצלחה" in status_message

if __name__ == "__main__":
    pytest.main([__file__]) 