"""
LLM API Client - מודול לתקשורת עם מודלים של בינה מלאכותית

מודול זה מספק ממשק לתקשורת עם שירותי LLM שונים (OpenAI, Anthropic וכו')
ומאפשר ניתוח בקשות בשפה טבעית והמרתן לפקודות מובנות.
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
    agent: str  # סוג הסוכן: info/action/research
    method: str  # שם המתודה לביצוע
    params: Dict[str, Any]  # פרמטרים לביצוע הפעולה

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
        הכנת ה-prompt למודל עם דוגמאות ספציפיות לפעולות חנות
        :param user_message: הודעת המשתמש
        :return: prompt מוכן לשליחה
        """
        return f"""אתה עוזר לניהול חנות WooCommerce. נתח את בקשת המשתמש ובחר את הסוכן והפעולה המתאימים.

החזר JSON בפורמט הבא:
{{
    "agent": "info/action/research",
    "method": "שם_המתודה",
    "params": {{
        "param1": "value1",
        ...
    }}
}}

דוגמאות לפעולות נפוצות:

1. ניהול מוצרים:
בקשה: "הראה לי את כל המוצרים בחנות"
תשובה: {{"agent": "info", "method": "get_products", "params": {{"page": 1, "per_page": 10}}}}

בקשה: "צור מוצר חדש בשם חולצה כחולה במחיר 99.90"
תשובה: {{"agent": "action", "method": "create_product", "params": {{"name": "חולצה כחולה", "price": "99.90"}}}}

בקשה: "עדכן את המחיר של חולצה כחולה ל-89.90"
תשובה: {{"agent": "action", "method": "update_product_price", "params": {{"product_name": "חולצה כחולה", "price": "89.90"}}}}

2. ניהול משלוחים:
בקשה: "הוסף אזור משלוח חדש למרכז הארץ"
תשובה: {{"agent": "action", "method": "create_shipping_zone", "params": {{"name": "מרכז הארץ", "regions": ["תל אביב", "רמת גן", "גבעתיים"]}}}}

בקשה: "הוסף שליח עד הבית לאזור המרכז במחיר 25 שקל"
תשובה: {{"agent": "action", "method": "add_shipping_method", "params": {{"zone_id": 1, "method_type": "local_pickup", "title": "שליח עד הבית", "cost": 25}}}}

בקשה: "מה סטטוס המשלוח של הזמנה 123?"
תשובה: {{"agent": "info", "method": "get_shipping_tracking", "params": {{"order_id": 123}}}}

3. ניהול תשלומים:
בקשה: "הוסף אפשרות תשלום בביט"
תשובה: {{"agent": "action", "method": "add_payment_method", "params": {{"title": "ביט", "description": "תשלום באמצעות אפליקציית ביט", "enabled": true}}}}

בקשה: "בצע החזר כספי להזמנה 456 על סך 150 שקל"
תשובה: {{"agent": "action", "method": "refund_payment", "params": {{"order_id": 456, "amount": 150, "reason": "בקשת לקוח"}}}}

4. ניהול לקוחות:
בקשה: "הוסף 100 נקודות למועדון ללקוח דני כהן"
תשובה: {{"agent": "action", "method": "manage_customer_points", "params": {{"customer_id": 789, "action": "add", "points": 100, "reason": "מבצע חודשי"}}}}

בקשה: "הראה לי את ההיסטוריה של הלקוח משה לוי"
תשובה: {{"agent": "info", "method": "get_customer_orders", "params": {{"customer_id": 321, "page": 1, "per_page": 10}}}}

5. מחקר שוק:
בקשה: "בדוק מחירים של חולצות כחולות אצל המתחרים"
תשובה: {{"agent": "research", "method": "analyze_competitors", "params": {{"market_segment": "אופנה", "product_type": "חולצות", "color": "כחול"}}}}

בקשה: "מה הטרנדים החמים באופנה החודש?"
תשובה: {{"agent": "research", "method": "get_market_trends", "params": {{"market_segment": "אופנה", "period": "month"}}}}

הודעת המשתמש: {user_message}

החזר רק את ה-JSON ללא טקסט נוסף."""
    
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