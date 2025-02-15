"""
Message Manager - מודול לניהול הודעות המערכת
"""
import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

class MessageManager:
    def __init__(self, language: str = "he"):
        """
        אתחול מנהל ההודעות
        
        Args:
            language: קוד השפה (ברירת מחדל: עברית)
        """
        self.language = language
        self.messages = self._load_messages()
        
    def _load_messages(self) -> Dict[str, Any]:
        """
        טעינת קובץ ההודעות
        
        Returns:
            Dict[str, Any]: מילון ההודעות
        """
        messages_path = Path(__file__).parent.parent / "resources" / "messages" / self.language / "messages.yaml"
        
        try:
            with open(messages_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"שגיאה בטעינת קובץ ההודעות: {str(e)}")
            return {}
            
    def get_help_message(self, category: Optional[str] = None) -> str:
        """
        קבלת הודעת עזרה
        
        Args:
            category: קטגוריה ספציפית (אופציונלי)
            
        Returns:
            str: הודעת העזרה המבוקשת
        """
        help_messages = self.messages.get('help_messages', {})
        
        if not category:
            # החזרת כל הודעת העזרה
            result = [help_messages.get('title', '')]
            
            for cat_key, cat_data in help_messages.items():
                if cat_key != 'title':
                    result.append(f"\n{cat_data.get('title', '')}:")
                    for cmd in cat_data.get('commands', []):
                        result.append(f"   • {cmd.get('command', '')}")
                        if 'format' in cmd:
                            result.append(f"     {cmd['format']}")
                        if 'description' in cmd:
                            result.append(f"     {cmd['description']}")
                            
            return "\n".join(result)
        
        # החזרת קטגוריה ספציפית
        category_data = help_messages.get(category)
        if not category_data:
            return f"קטגוריה '{category}' לא נמצאה"
            
        result = [f"{category_data.get('title', '')}:"]
        for cmd in category_data.get('commands', []):
            result.append(f"   • {cmd.get('command', '')}")
            if 'format' in cmd:
                result.append(f"     {cmd['format']}")
            if 'description' in cmd:
                result.append(f"     {cmd['description']}")
                
        return "\n".join(result)
        
    def get_error_message(self, error_key: str, **kwargs) -> str:
        """
        קבלת הודעת שגיאה
        
        Args:
            error_key: מפתח השגיאה
            **kwargs: פרמטרים להחלפה בהודעה
            
        Returns:
            str: הודעת השגיאה
        """
        error_messages = self.messages.get('error_messages', {})
        message = error_messages.get(error_key, error_messages.get('general_error', ''))
        return message.format(**kwargs)
        
    def get_status_message(self, status_key: str) -> str:
        """
        קבלת הודעת סטטוס
        
        Args:
            status_key: מפתח הסטטוס
            
        Returns:
            str: הודעת הסטטוס
        """
        status_messages = self.messages.get('status_messages', {})
        return status_messages.get(status_key, '') 