"""
Orchestrator - Main agent that routes messages to appropriate sub-agents.
Manages communication between different agents and coordinates responses.
"""
import logging
from typing import Dict, Any, Optional
import json

from agents.information_agent import InformationAgent
from agents.action_agent import ActionAgent
from agents.research_agent import ResearchAgent
from utils.message_manager import MessageManager
from tools.llm_api import query_llm

# הגדרת לוגר
logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self):
        """Initialize orchestrator with all sub-agents."""
        self.info_agent = InformationAgent()
        self.action_agent = ActionAgent()
        self.research_agent = ResearchAgent()
        self.message_manager = MessageManager()
        
        # מיפוי בין שמות הסוכנים לאובייקטים שלהם
        self.agent_mapping = {
            "info": self.info_agent,
            "action": self.action_agent,
            "research": self.research_agent
        }

    async def handle_user_message(self, user_message: str) -> str:
        """
        נתב את הודעת המשתמש לסוכן המתאים.
        :param user_message: הודעת המשתמש
        :return: תשובת הסוכן
        """
        try:
            # שליחת ההודעה ל-LLM לניתוח
            prompt = f"""
            נתח את הודעת המשתמש ומצא את הסוכן והפעולה המתאימים:
            
            הודעה: {user_message}
            
            אפשרויות הסוכנים:
            1. info - מידע על מוצרים, הזמנות ולקוחות
            2. action - ביצוע פעולות כמו הוספת מוצר, עדכון מחיר
            3. research - ניתוח מגמות שוק ומתחרים
            
            החזר JSON בפורמט:
            {{
                "agent": "שם הסוכן",
                "method": "שם המתודה",
                "params": {{
                    "פרמטר": "ערך"
                }}
            }}
            """
            
            llm_response = query_llm(prompt, provider="openai")  # שימוש ב-OpenAI
            logger.debug(f"LLM Response: {llm_response}")
            
            # המרת התשובה ל-JSON
            try:
                if isinstance(llm_response, str):
                    response_data = json.loads(llm_response)
                else:
                    response_data = llm_response
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing LLM response: {str(e)}")
                return self.message_manager.get_error_message('invalid_format')
            
            # קבלת הסוכן והפרמטרים מהתשובה
            agent_name = response_data.get("agent")
            method = response_data.get("method")
            params = response_data.get("params", {})
            
            # בדיקה שקיבלנו את כל המידע הנדרש
            if not agent_name or not method:
                return self.message_manager.get_error_message('invalid_format')
            
            # קבלת הסוכן המתאים
            agent = self.agent_mapping.get(agent_name)
            if not agent:
                return self.message_manager.get_error_message('not_found', item=f"סוכן {agent_name}")
            
            # העברת הבקשה לסוכן
            response = await agent.handle_message(method, params)
            
            # אם התשובה ריקה, החזר הודעת שגיאה
            if not response:
                return self.message_manager.get_error_message('general_error')
                
            return response
            
        except Exception as e:
            logger.error(f"Error in Orchestrator: {str(e)}")
            return self.message_manager.get_error_message('general_error')

    async def update_product_image(self, product_name: str, image_path: str) -> str:
        """
        עדכון תמונת מוצר
        :param product_name: שם המוצר
        :param image_path: נתיב לקובץ התמונה
        :return: הודעת תשובה
        """
        try:
            response = await self.action_agent.handle_message(
                "update_product_image",
                {"product_name": product_name, "image_path": image_path}
            )
            
            if response and "success" in response.lower():
                return self.message_manager.get_status_message('success')
            else:
                return self.message_manager.get_error_message('general_error')
                
        except Exception as e:
            logger.error(f"Error updating product image: {str(e)}")
            return self.message_manager.get_error_message('general_error')

    # Future enhancements:
    # - Add conversation history tracking
    # - Implement intent classification with LangChain
    # - Add multi-agent collaboration for complex queries 