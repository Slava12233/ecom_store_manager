"""
Research Agent - responsible for external research and competitor analysis.
Handles market research, competitor analysis, and trend research.
"""
from typing import Dict, Any
import re

class ResearchAgent:
    def __init__(self):
        """Initialize research agent for external data gathering."""
        self.market_data = {
            "אופנה": {
                "מתחרים": [
                    "ZARA - מחירים ממוצעים גבוהים ב-20%",
                    "H&M - מחירים דומים, איכות בינונית",
                    "CASTRO - מחירים גבוהים ב-15%, מיקוד בקהל מקומי"
                ],
                "טרנדים": [
                    "בגדים בני-קיימא",
                    "אופנה מקיימת",
                    "חומרים טבעיים"
                ],
                "המלצות": [
                    "להתמקד במחירים תחרותיים",
                    "להדגיש איכות חומרים",
                    "לשלב קולקציות אקולוגיות"
                ]
            }
        }

    def analyze_competitors(self, market_segment: str) -> str:
        """
        Analyze competitors in the given market segment.
        """
        if market_segment in self.market_data:
            competitors = self.market_data[market_segment]["מתחרים"]
            return "ניתוח מתחרים:\n" + "\n".join(f"• {comp}" for comp in competitors)
        return "אין מידע על מתחרים בתחום זה"

    def get_market_trends(self, market_segment: str) -> str:
        """
        Get current market trends.
        """
        if market_segment in self.market_data:
            trends = self.market_data[market_segment]["טרנדים"]
            return "טרנדים נוכחיים:\n" + "\n".join(f"• {trend}" for trend in trends)
        return "אין מידע על טרנדים בתחום זה"

    def get_recommendations(self, market_segment: str) -> str:
        """
        Get business recommendations.
        """
        if market_segment in self.market_data:
            recommendations = self.market_data[market_segment]["המלצות"]
            return "המלצות עסקיות:\n" + "\n".join(f"• {rec}" for rec in recommendations)
        return "אין המלצות זמינות לתחום זה"

    async def handle_message(self, user_message: str) -> str:
        """
        Handle user messages and route to appropriate research method.
        """
        message_lower = user_message.lower()
        
        if "מתחרים" in message_lower and "אופנה" in message_lower:
            return self.analyze_competitors("אופנה")
        
        elif "טרנדים" in message_lower or "מגמות" in message_lower:
            return self.get_market_trends("אופנה")
        
        elif "המלצות" in message_lower or "מה כדאי" in message_lower:
            return self.get_recommendations("אופנה")
        
        elif "מחקר" in message_lower or "שוק" in message_lower:
            return (
                "מידע על השוק:\n\n" +
                self.analyze_competitors("אופנה") + "\n\n" +
                self.get_market_trends("אופנה") + "\n\n" +
                self.get_recommendations("אופנה")
            )
        
        return "אני יכול לעזור במחקר שוק, ניתוח מתחרים וטרנדים. נסה לשאול על:\n" + \
               "• מתחרים בתחום\n" + \
               "• טרנדים נוכחיים\n" + \
               "• המלצות עסקיות"

    # Future methods to be implemented:
    # def get_price_comparison(self, product_name: str) -> dict: 