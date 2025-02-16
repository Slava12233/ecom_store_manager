"""
Orchestrator - Main agent that routes messages to appropriate sub-agents.
Manages communication between different agents and coordinates responses.
"""
import logging
from typing import Dict, Any, Optional, List
import json
from datetime import datetime

from agents.information_agent import InformationAgent
from agents.action_agent import ActionAgent
from agents.research_agent import ResearchAgent
from utils.message_manager import MessageManager
from tools.llm_api import LLMClient, query_llm

# הגדרת לוגר
logger = logging.getLogger(__name__)

class ConversationHistory:
    """ניהול היסטוריית שיחה"""
    def __init__(self, max_history: int = 10):
        self.history: List[Dict[str, Any]] = []
        self.max_history = max_history
    
    def add_interaction(self, user_message: str, system_response: str, agent: str, method: str):
        """הוספת אינטראקציה להיסטוריה"""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "system_response": system_response,
            "agent": agent,
            "method": method
        }
        self.history.append(interaction)
        if len(self.history) > self.max_history:
            self.history.pop(0)
    
    def get_recent_context(self, num_messages: int = 3) -> str:
        """קבלת הקשר אחרון מההיסטוריה"""
        recent = self.history[-num_messages:] if self.history else []
        context = []
        for interaction in recent:
            context.append(f"משתמש: {interaction['user_message']}")
            context.append(f"מערכת: {interaction['system_response']}")
        return "\n".join(context)

class Orchestrator:
    def __init__(self):
        """Initialize orchestrator with all sub-agents."""
        self.info_agent = InformationAgent()
        self.action_agent = ActionAgent()
        self.research_agent = ResearchAgent()
        self.message_manager = MessageManager()
        self.llm_client = LLMClient()
        self.conversation_history = ConversationHistory()
        
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
            # קבלת הקשר מההיסטוריה
            context = self.conversation_history.get_recent_context()
            
            # שליחת ההודעה ל-LLM לניתוח עם ההקשר
            prompt = f"""הקשר קודם:
{context}

הודעה נוכחית: {user_message}

שים לב:
1. אם ההודעה מתייחסת למשהו מההקשר הקודם, התחשב בזה
2. אם יש מספרים או שמות ספציפיים, השתמש בהם בדיוק כפי שהם
3. אם חסר מידע חיוני, ציין זאת בפרמטרים עם ערך null"""
            
            llm_response = query_llm(prompt, provider="openai")
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
            
            # בדיקת תקינות הפרמטרים
            agent_name = response_data.get("agent")
            method = response_data.get("method")
            params = response_data.get("params", {})
            
            # בדיקה אם חסרים פרמטרים חיוניים
            missing_params = self._check_required_params(agent_name, method, params)
            if missing_params:
                return f"חסר מידע: {', '.join(missing_params)}. אנא ספק את המידע החסר."
            
            # קבלת הסוכן המתאים
            agent = self.agent_mapping.get(agent_name)
            if not agent:
                error_msg = self.message_manager.get_error_message('not_found', item=f"סוכן {agent_name}")
                logger.error(f"Agent not found: {agent_name}")
                return error_msg
            
            # העברת הבקשה לסוכן
            try:
                response = await agent.handle_message(method, params)
                
                # שמירת האינטראקציה בהיסטוריה
                if response:
                    self.conversation_history.add_interaction(
                        user_message, response, agent_name, method
                    )
                    return response
                else:
                    error_msg = self.message_manager.get_error_message('general_error')
                    logger.error(f"Empty response from agent {agent_name}.{method}")
                    return error_msg
                    
            except Exception as agent_error:
                logger.error(f"Error in agent {agent_name}.{method}: {str(agent_error)}")
                return self.message_manager.get_error_message(
                    'agent_error',
                    agent=agent_name,
                    method=method,
                    error=str(agent_error)
                )
            
        except Exception as e:
            logger.error(f"Error in Orchestrator: {str(e)}", exc_info=True)
            return self.message_manager.get_error_message('general_error')

    def _check_required_params(self, agent: str, method: str, params: Dict[str, Any]) -> List[str]:
        """
        בדיקת פרמטרים חיוניים לפי סוג הסוכן והמתודה
        :return: רשימת פרמטרים חסרים
        """
        required_params = {
            "action": {
                "create_product": ["name", "price"],
                "update_product_price": ["product_name", "price"],
                "create_shipping_zone": ["name", "regions"],
                "add_shipping_method": ["zone_id", "method_type", "title", "cost"],
                "manage_customer_points": ["customer_id", "action", "points"],
                "refund_payment": ["order_id", "amount"]
            },
            "info": {
                "get_products": ["page", "per_page"],
                "get_shipping_tracking": ["order_id"],
                "get_customer_orders": ["customer_id"]
            },
            "research": {
                "analyze_competitors": ["market_segment", "product_type"],
                "get_market_trends": ["market_segment"]
            }
        }
        
        if agent not in required_params or method not in required_params[agent]:
            return []
            
        missing = []
        for param in required_params[agent][method]:
            if param not in params or params[param] is None:
                missing.append(param)
                
        return missing

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
                success_msg = self.message_manager.get_status_message('success')
                # שמירת האינטראקציה בהיסטוריה
                self.conversation_history.add_interaction(
                    f"עדכון תמונה למוצר {product_name}",
                    success_msg,
                    "action",
                    "update_product_image"
                )
                return success_msg
            else:
                error_msg = self.message_manager.get_error_message('general_error')
                logger.error(f"Error updating product image: {response}")
                return error_msg
                
        except Exception as e:
            logger.error(f"Error updating product image: {str(e)}", exc_info=True)
            return self.message_manager.get_error_message('general_error')

    # Future enhancements:
    # - Add conversation history tracking
    # - Implement intent classification with LangChain
    # - Add multi-agent collaboration for complex queries 