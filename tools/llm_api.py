"""
LLM API Client - מודול לתקשורת עם מודלים של בינה מלאכותית
"""
import os
import json
import logging
from typing import Dict, Any, Optional
import requests
from pydantic import BaseModel, SecretStr

# הגדרת לוגר
logger = logging.getLogger(__name__)

class LLMResponse(BaseModel):
    """מודל לתשובה מובנית מה-LLM"""
    agent: str
    method: str
    params: Dict[str, Any]

class LLMClient:
    """לקוח לתקשורת עם שירותי LLM שונים"""
    
    def __init__(self, provider: str = "openai"):
        """
        אתחול הלקוח
        :param provider: ספק ה-LLM (openai, anthropic וכו')
        """
        self.provider = provider
        self.api_url = os.getenv(f"{provider.upper()}_API_URL")
        self.api_key = SecretStr(os.getenv(f"{provider.upper()}_API_KEY", ""))
        
        if not self.api_url or not self.api_key:
            raise ValueError(f"Missing API configuration for {provider}")
    
    def prepare_prompt(self, user_message: str) -> str:
        """
        הכנת ה-prompt למודל
        :param user_message: הודעת המשתמש
        :return: prompt מוכן לשליחה
        """
        return f"""
        נתח את הבקשה הבאה ובחר את הסוכן והפעולה המתאימים.
        החזר JSON בפורמט הבא:
        {{
            "agent": "info/action/research",
            "method": "שם_המתודה",
            "params": {{
                "param1": "value1",
                ...
            }}
        }}
        
        הודעת המשתמש: {user_message}
        
        החזר רק את ה-JSON ללא טקסט נוסף.
        """
    
    def query(self, prompt: str) -> LLMResponse:
        """
        שליחת שאילתה ל-LLM
        :param prompt: ה-prompt לשליחה
        :return: תשובה מובנית
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key.get_secret_value()}",
                "Content-Type": "application/json"
            }
            
            if self.provider == "openai":
                data = {
                    "model": "gpt-4",
                    "messages": [
                        {"role": "system", "content": "אתה עוזר לניהול חנות WooCommerce. תענה תמיד ב-JSON בפורמט המבוקש."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7
                }
            else:
                data = {
                    "prompt": prompt,
                    "max_tokens": 150,
                    "temperature": 0.7
                }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            
            # טיפול בתשובה מ-OpenAI
            if self.provider == "openai":
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                # ניקוי התשובה והמרה ל-JSON
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:-3]  # הסרת ה-```json ו-```
                result = json.loads(content)
            else:
                # טיפול בתשובות מספקים אחרים
                result = response.json()
            
            # אם התשובה היא מחרוזת JSON, נמיר אותה למילון
            if isinstance(result, str):
                result = json.loads(result)
            
            # יצירת אובייקט LLMResponse מהתשובה
            return LLMResponse(**result)
            
        except Exception as e:
            logger.error(f"Error querying LLM: {str(e)}")
            raise

def query_llm(prompt: str, provider: str = "openai") -> Dict[str, Any]:
    """
    פונקציית מעטפת נוחה לשימוש
    :param prompt: ה-prompt לשליחה
    :param provider: ספק ה-LLM
    :return: תשובה כמילון
    """
    client = LLMClient(provider)
    formatted_prompt = client.prepare_prompt(prompt)
    response = client.query(formatted_prompt)
    return response.dict() 