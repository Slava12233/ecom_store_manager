"""
Orchestrator - Main agent that routes messages to appropriate sub-agents.
Manages communication between different agents and coordinates responses.
"""
from agents.information_agent import InformationAgent
from agents.action_agent import ActionAgent
from agents.research_agent import ResearchAgent

class Orchestrator:
    def __init__(self):
        """Initialize orchestrator with all sub-agents."""
        self.info_agent = InformationAgent()
        self.action_agent = ActionAgent()
        self.research_agent = ResearchAgent()

    def handle_user_message(self, user_message: str) -> str:
        """
        Route the user message to appropriate agent based on content.
        Enhanced with better keyword matching and priority handling.
        """
        message_lower = user_message.lower()
        
        # Action requests - בדיקה ראשונה כי הן מכילות מילים שיכולות להתנגש עם בקשות מידע
        if any(word in message_lower for word in ["הוסף", "צור", "יוצר", "עדכן", "שנה", "מחק", "הסר"]):
            return self.action_agent.handle_message(user_message)
        
        # Information requests
        elif any(word in message_lower for word in ["תראה", "הצג", "כמה", "מוצרים", "דוח", "מכירות", "קופונים", "הנחות"]):
            return self.info_agent.handle_message(user_message)
        
        # Research requests
        elif any(word in message_lower for word in ["מתחרים", "מחקר", "שוק", "השוואה"]):
            return self.research_agent.handle_message(user_message)
        
        # Unknown intent
        else:
            return "סוכן ראשי (Orchestrator): לא ברור על מה תרצה לדבר. אני יכול לעזור עם:\n" + \
                   "1. מידע על מוצרים ומכירות\n" + \
                   "2. יצירה ועדכון של מוצרים וקופונים\n" + \
                   "3. מחקר שוק ומתחרים"

    # Future enhancements:
    # - Add conversation history tracking
    # - Implement intent classification with LangChain
    # - Add multi-agent collaboration for complex queries 