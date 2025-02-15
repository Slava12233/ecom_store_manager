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
            version="wc/v3",
            verify=False  # Disable SSL verification for InstaWP
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
                    return "לא נמצאו מוצרים בחנות"
                
                result = "המוצרים בחנות:\n\n"
                for product in products:
                    name = product.get("name", "")
                    price = product.get("price", "")
                    status = "במלאי" if product.get("in_stock", False) else "אזל מהמלאי"
                    result += f"- {name}: {price} ש\"ח ({status})\n"
                
                return result
            else:
                return f"שגיאה בקבלת מוצרים: {response.status_code}"
        except Exception as e:
            return f"שגיאה בקבלת מוצרים: {str(e)}"

    def get_orders(self, page: int = 1, per_page: int = 5) -> str:
        """
        Fetch recent orders from WooCommerce.
        
        Args:
            page: Page number to fetch
            per_page: Number of orders per page
        """
        try:
            response = self.wcapi.get("orders", params={"page": page, "per_page": per_page})
            if response.status_code == 200:
                orders = response.json()
                if not orders:
                    return "לא נמצאו הזמנות בחנות"
                
                result = "ההזמנות האחרונות:\n\n"
                for order in orders:
                    order_id = order.get("id", "")
                    total = order.get("total", "")
                    status = order.get("status", "")
                    date = order.get("date_created", "").split("T")[0]  # Get just the date part
                    result += f"- הזמנה #{order_id}: {total} ש\"ח ({status}) - {date}\n"
                
                return result
            else:
                return f"שגיאה בקבלת הזמנות: {response.status_code}"
        except Exception as e:
            return f"שגיאה בקבלת הזמנות: {str(e)}"

    def get_sales_report(self, period: str = "week") -> str:
        """
        Get sales report for a specific period.
        
        Args:
            period: The period to get report for ("week", "month", "year")
        """
        try:
            response = self.wcapi.get(f"reports/sales", params={"period": period})
            if response.status_code == 200:
                report = response.json()
                if not report:
                    return f"לא נמצאו נתוני מכירות ל{period}"
                
                total_sales = report[0].get("total_sales", 0)
                total_orders = report[0].get("total_orders", 0)
                average_sales = report[0].get("average_sales", 0)
                
                result = f"דוח מכירות ל{period}:\n\n"
                result += f"- סה\"כ מכירות: {total_sales} ש\"ח\n"
                result += f"- מספר הזמנות: {total_orders}\n"
                result += f"- ממוצע ליום: {average_sales} ש\"ח\n"
                
                return result
            else:
                return f"שגיאה בקבלת דוח מכירות: {response.status_code}"
        except Exception as e:
            return f"שגיאה בקבלת דוח מכירות: {str(e)}"

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