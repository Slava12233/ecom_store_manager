"""
Information Agent - responsible for retrieving data from WooCommerce API.
Handles queries about products, orders, reports etc.
"""
from typing import Optional, List, Dict, Any
from woocommerce import API
from core.config import settings

class InformationAgent:
    def __init__(self):
        """Initialize the information agent with WooCommerce API connection."""
        self.wcapi = API(
            url=str(settings.WC_STORE_URL),
            consumer_key=settings.WC_CONSUMER_KEY,
            consumer_secret=settings.WC_CONSUMER_SECRET.get_secret_value(),
            version="wc/v3"
        )

    def get_products(self, page: int = 1, per_page: int = 5) -> str:
        """
        Fetch products from WooCommerce and return a formatted string.
        
        Args:
            page: Page number to fetch
            per_page: Number of products per page
        """
        try:
            response = self.wcapi.get("products", params={"page": page, "per_page": per_page})
            if response.status_code == 200:
                products = response.json()
                if not products:
                    return "אין כרגע מוצרים בחנות."
                
                answer = ["מוצרים בחנות:"]
                for p in products:
                    name = p.get("name", "ללא שם")
                    price = p.get("price", "לא צוין")
                    stock_status = p.get("stock_status", "לא ידוע")
                    status_hebrew = {
                        "instock": "במלאי",
                        "outofstock": "אזל מהמלאי",
                        "onbackorder": "בהזמנה מראש"
                    }.get(stock_status, stock_status)
                    
                    answer.append(f"- {name}, מחיר: {price} ₪, סטטוס: {status_hebrew}")
                return "\n".join(answer)
            else:
                return f"שגיאה בשליפת מוצרים: {response.status_code}"
        except Exception as e:
            return f"שגיאה בשליפת מוצרים: {str(e)}"

    def get_sales_report(self, period: str = "week") -> str:
        """
        Fetch sales report from WooCommerce.
        
        Args:
            period: Report period ('week', 'month', 'year')
        """
        try:
            response = self.wcapi.get(f"reports/sales", params={"period": period})
            if response.status_code == 200:
                data = response.json()
                if not data or len(data) == 0:
                    return (
                        f"אין נתוני מכירות לתקופה: {period}\n"
                        "זה תקין אם החנות חדשה או שלא היו מכירות בתקופה זו.\n"
                        "המלצות:\n"
                        "• לבדוק את מחירי המוצרים מול המתחרים\n"
                        "• לשקול יצירת קופוני הנחה לקידום מכירות\n"
                        "• לוודא שהמוצרים מוצגים היטב עם תמונות ותיאורים"
                    )
                
                # WooCommerce מחזיר רשימה של דוחות, ניקח את הראשון
                report = data[0] if isinstance(data, list) else data
                
                period_hebrew = {
                    "week": "שבוע",
                    "month": "חודש",
                    "year": "שנה"
                }.get(period, period)
                
                total_sales = float(report.get("total_sales", "0"))
                total_orders = int(report.get("total_orders", "0"))
                total_items = int(report.get("total_items", "0"))
                avg_order_value = total_sales / total_orders if total_orders > 0 else 0
                items_per_order = total_items / total_orders if total_orders > 0 else 0

                return (
                    f"דוח מכירות ל{period_hebrew} האחרון:\n"
                    f"• סה״כ מכירות: {total_sales:.2f} ₪\n"
                    f"• מספר הזמנות: {total_orders}\n"
                    f"• מספר פריטים: {total_items}\n"
                    f"• ממוצע להזמנה: {avg_order_value:.2f} ₪\n"
                    f"• פריטים להזמנה: {items_per_order:.1f}\n"
                    "\nמדדי ביצוע:\n" +
                    ("✅ מצוין" if total_sales > 10000 else
                     "⚠️ בינוני" if total_sales > 1000 else
                     "❌ נמוך")
                )
            else:
                return f"שגיאה בשליפת דוח מכירות: {response.status_code}"
        except Exception as e:
            return f"שגיאה בשליפת דוח מכירות: {str(e)}"

    def get_coupons(self, page: int = 1, per_page: int = 10) -> str:
        """
        Fetch active coupons from WooCommerce.
        
        Args:
            page: Page number to fetch
            per_page: Number of coupons per page
        """
        try:
            response = self.wcapi.get("coupons", params={"page": page, "per_page": per_page})
            if response.status_code == 200:
                coupons = response.json()
                if not coupons:
                    return "אין קופונים פעילים כרגע."
                
                answer = ["קופונים פעילים:"]
                for c in coupons:
                    code = c.get("code", "ללא קוד")
                    discount_type = c.get("discount_type", "")
                    amount = c.get("amount", "0")
                    
                    type_hebrew = {
                        "fixed_cart": "הנחה קבועה לסל",
                        "percent": "אחוז הנחה",
                        "fixed_product": "הנחה קבועה למוצר"
                    }.get(discount_type, discount_type)
                    
                    if discount_type == "percent":
                        answer.append(f"- קוד: {code}, {amount}% הנחה")
                    else:
                        answer.append(f"- קוד: {code}, {amount} ₪ {type_hebrew}")
                
                return "\n".join(answer)
            else:
                return f"שגיאה בשליפת קופונים: {response.status_code}"
        except Exception as e:
            return f"שגיאה בשליפת קופונים: {str(e)}"

    def handle_message(self, user_message: str) -> str:
        """
        Handle user messages and route to appropriate method.
        Enhanced with more specific keyword matching.
        """
        message_lower = user_message.lower()
        
        # Products query
        if "מוצרים" in message_lower:
            return self.get_products(page=1, per_page=5)
        
        # Sales report query
        elif "דוח" in message_lower or "מכירות" in message_lower:
            period = "week"  # Default to weekly
            if "חודש" in message_lower:
                period = "month"
            elif "שנה" in message_lower:
                period = "year"
            return self.get_sales_report(period=period)
        
        # Coupons query
        elif "קופונים" in message_lower or "הנחות" in message_lower:
            return self.get_coupons()
        
        # Unknown query
        else:
            return "סוכן המידע: אני יכול לעזור עם:\n" + \
                   "1. הצגת מוצרים\n" + \
                   "2. דוחות מכירות (שבועי/חודשי/שנתי)\n" + \
                   "3. קופונים פעילים"

    # Future methods to be implemented:
    # def get_products(self) -> list:
    # def get_sales_report(self) -> dict:
    # def get_orders(self) -> list: 