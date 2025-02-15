"""
Information Agent - responsible for retrieving data from WooCommerce API.
Handles queries about products, orders, reports etc.
"""
from typing import Optional, List, Dict, Any
from woocommerce import API
from src.core.config import settings
import re

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

    def get_order_details(self, order_id: int) -> str:
        """
        קבלת פרטים מלאים על הזמנה ספציפית
        
        Args:
            order_id: מזהה ההזמנה
        """
        try:
            response = self.wcapi.get(f"orders/{order_id}")
            if response.status_code == 200:
                order = response.json()
                
                # תרגום סטטוס לעברית
                status_map = {
                    "pending": "בהמתנה",
                    "processing": "בעיבוד",
                    "completed": "הושלם",
                    "cancelled": "בוטל",
                    "refunded": "הוחזר",
                    "failed": "נכשל"
                }
                status = status_map.get(order.get("status", ""), order.get("status", ""))
                
                # בניית פרטי ההזמנה
                result = [f"פרטי הזמנה #{order_id}:"]
                result.append(f"סטטוס: {status}")
                result.append(f"תאריך: {order.get('date_created', '').split('T')[0]}")
                result.append(f"סה\"כ: {order.get('total', '')} ₪")
                
                # פרטי לקוח
                billing = order.get("billing", {})
                result.append("\nפרטי לקוח:")
                result.append(f"שם: {billing.get('first_name', '')} {billing.get('last_name', '')}")
                result.append(f"טלפון: {billing.get('phone', '')}")
                result.append(f"אימייל: {billing.get('email', '')}")
                
                # כתובת למשלוח
                shipping = order.get("shipping", {})
                if shipping:
                    result.append("\nכתובת למשלוח:")
                    address_parts = [
                        shipping.get("address_1", ""),
                        shipping.get("address_2", ""),
                        shipping.get("city", ""),
                        shipping.get("state", ""),
                        shipping.get("postcode", "")
                    ]
                    result.append(" ".join(filter(None, address_parts)))
                
                # פריטים בהזמנה
                result.append("\nפריטים בהזמנה:")
                for item in order.get("line_items", []):
                    result.append(f"- {item.get('name', '')}: {item.get('quantity', '')} יח' × {item.get('price', '')} ₪")
                
                # הערות
                if order.get("customer_note"):
                    result.append(f"\nהערת לקוח: {order['customer_note']}")
                
                return "\n".join(result)
            else:
                return f"שגיאה בקבלת פרטי הזמנה: {response.status_code}"
        except Exception as e:
            return f"שגיאה בקבלת פרטי הזמנה: {str(e)}"

    def get_recent_orders(self, status: str = None, limit: int = 5) -> str:
        """
        קבלת ההזמנות האחרונות עם אפשרות לסינון לפי סטטוס
        
        Args:
            status: סטטוס ההזמנות לסינון (אופציונלי)
            limit: מספר ההזמנות להצגה
        """
        try:
            # תרגום סטטוס לאנגלית
            status_map = {
                "בהמתנה": "pending",
                "בעיבוד": "processing",
                "הושלם": "completed",
                "בוטל": "cancelled",
                "הוחזר": "refunded",
                "נכשל": "failed"
            }
            
            params = {
                "per_page": limit,
                "orderby": "date",
                "order": "desc"
            }
            
            if status:
                eng_status = status_map.get(status, status)
                params["status"] = eng_status
            
            response = self.wcapi.get("orders", params=params)
            if response.status_code == 200:
                orders = response.json()
                if not orders:
                    return "לא נמצאו הזמנות" + (f" בסטטוס {status}" if status else "")
                
                result = ["ההזמנות האחרונות:"]
                for order in orders:
                    order_status = status_map.get(order.get("status", ""), order.get("status", ""))
                    date = order.get("date_created", "").split("T")[0]
                    total = order.get("total", "")
                    billing = order.get("billing", {})
                    customer_name = f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip()
                    
                    result.append(
                        f"- הזמנה #{order['id']}: {total} ₪"
                        f" | {order_status}"
                        f" | {date}"
                        + (f" | {customer_name}" if customer_name else "")
                    )
                
                return "\n".join(result)
            else:
                return f"שגיאה בקבלת הזמנות: {response.status_code}"
        except Exception as e:
            return f"שגיאה בקבלת הזמנות: {str(e)}"

    def format_customer_details(self, customer: Dict[str, Any]) -> str:
        """
        פורמט פרטי לקוח לתצוגה
        
        Args:
            customer: נתוני הלקוח מה-API
            
        Returns:
            str: מחרוזת מפורמטת עם פרטי הלקוח
        """
        result = [f"פרטי לקוח (מזהה: {customer.get('id', '')})"]
        
        # פרטים בסיסיים
        name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()
        if name:
            result.append(f"שם: {name}")
        
        if customer.get('email'):
            result.append(f"אימייל: {customer['email']}")
            
        if customer.get('phone'):
            result.append(f"טלפון: {customer['phone']}")
            
        # כתובת
        billing = customer.get('billing', {})
        if any(billing.values()):
            result.append("\nכתובת חיוב:")
            address_parts = [
                billing.get('address_1', ''),
                billing.get('address_2', ''),
                billing.get('city', ''),
                billing.get('state', ''),
                billing.get('postcode', '')
            ]
            result.append(" ".join(filter(None, address_parts)))
            
        # סטטיסטיקות
        result.append("\nסטטיסטיקות:")
        result.append(f"סה\"כ הזמנות: {customer.get('orders_count', 0)}")
        result.append(f"סה\"כ הוצאות: {customer.get('total_spent', '0')} ₪")
        
        # תאריכים
        if customer.get('date_created'):
            result.append(f"\nתאריך הצטרפות: {customer['date_created'].split('T')[0]}")
        if customer.get('date_modified'):
            result.append(f"עדכון אחרון: {customer['date_modified'].split('T')[0]}")
            
        return "\n".join(result)

    def format_customer_orders(self, orders: List[Dict[str, Any]]) -> str:
        """
        פורמט היסטוריית הזמנות לקוח לתצוגה
        
        Args:
            orders: רשימת הזמנות מה-API
            
        Returns:
            str: מחרוזת מפורמטת עם היסטוריית ההזמנות
        """
        if not orders:
            return "לא נמצאו הזמנות ללקוח זה"
            
        result = ["היסטוריית הזמנות:"]
        
        for order in orders:
            order_id = order.get('id', '')
            date = order.get('date_created', '').split('T')[0]
            status = order.get('status', '')
            total = order.get('total', '0')
            
            # תרגום סטטוס לעברית
            status_hebrew = {
                'pending': 'בהמתנה',
                'processing': 'בעיבוד',
                'completed': 'הושלם',
                'cancelled': 'בוטל',
                'refunded': 'הוחזר',
                'failed': 'נכשל'
            }.get(status, status)
            
            result.append(
                f"- הזמנה #{order_id} ({date}): "
                f"{total} ₪ | {status_hebrew}"
            )
            
            # הוספת פריטים בהזמנה
            items = order.get('line_items', [])
            if items:
                for item in items:
                    result.append(
                        f"  • {item.get('name', '')}: "
                        f"{item.get('quantity', '')} יח' × {item.get('price', '')} ₪"
                    )
                    
        return "\n".join(result)

    def get_shipping_zones(self) -> str:
        """
        קבלת רשימת אזורי משלוח
        
        Returns:
            str: מחרוזת מפורמטת עם רשימת אזורי המשלוח
        """
        try:
            response = self.wcapi.get("shipping/zones")
            if response.status_code == 200:
                zones = response.json()
                if not zones:
                    return "לא נמצאו אזורי משלוח מוגדרים"
                
                result = ["אזורי משלוח מוגדרים:"]
                for zone in zones:
                    zone_id = zone.get('id')
                    name = zone.get('name')
                    
                    # קבלת שיטות משלוח לאזור
                    methods_response = self.wcapi.get(f"shipping/zones/{zone_id}/methods")
                    if methods_response.status_code == 200:
                        methods = methods_response.json()
                        methods_str = ", ".join([m.get('title', '') for m in methods])
                    else:
                        methods_str = "לא נמצאו שיטות משלוח"
                    
                    result.append(f"- {name} (#{zone_id})")
                    result.append(f"  שיטות משלוח: {methods_str}")
                
                return "\n".join(result)
            else:
                return f"שגיאה בקבלת אזורי משלוח: {response.status_code}"
        except Exception as e:
            return f"שגיאה בקבלת אזורי משלוח: {str(e)}"

    def get_shipping_methods(self, zone_id: int) -> str:
        """
        קבלת רשימת שיטות משלוח לאזור ספציפי
        
        Args:
            zone_id: מזהה אזור המשלוח
            
        Returns:
            str: מחרוזת מפורמטת עם רשימת שיטות המשלוח
        """
        try:
            # קבלת פרטי האזור
            zone_response = self.wcapi.get(f"shipping/zones/{zone_id}")
            if zone_response.status_code != 200:
                return f"שגיאה בקבלת פרטי אזור משלוח: {zone_response.status_code}"
            
            zone = zone_response.json()
            zone_name = zone.get('name', '')
            
            # קבלת שיטות המשלוח
            response = self.wcapi.get(f"shipping/zones/{zone_id}/methods")
            if response.status_code == 200:
                methods = response.json()
                if not methods:
                    return f"לא נמצאו שיטות משלוח לאזור {zone_name}"
                
                result = [f"שיטות משלוח לאזור {zone_name} (#{zone_id}):"]
                for method in methods:
                    title = method.get('title', '')
                    method_id = method.get('method_id', '')
                    cost = method.get('settings', {}).get('cost', {}).get('value', '0')
                    
                    result.append(f"- {title}")
                    result.append(f"  סוג: {method_id}")
                    result.append(f"  מחיר: {cost} ₪")
                
                return "\n".join(result)
            else:
                return f"שגיאה בקבלת שיטות משלוח: {response.status_code}"
        except Exception as e:
            return f"שגיאה בקבלת שיטות משלוח: {str(e)}"

    def format_payment_methods(self, payment_methods: List[Dict[str, Any]]) -> str:
        """
        פורמט שיטות תשלום לתצוגה
        
        Args:
            payment_methods: רשימת שיטות תשלום מה-API
            
        Returns:
            str: מחרוזת מפורמטת עם שיטות התשלום
        """
        if not payment_methods:
            return "לא נמצאו שיטות תשלום מוגדרות"
            
        result = ["שיטות תשלום זמינות:"]
        
        for method in payment_methods:
            title = method.get('title', '')
            method_id = method.get('id', '')
            description = method.get('description', '')
            enabled = "פעיל" if method.get('enabled', False) else "לא פעיל"
            
            result.append(f"- {title} (#{method_id})")
            if description:
                result.append(f"  תיאור: {description}")
            result.append(f"  סטטוס: {enabled}")
            
            # הצגת הגדרות נוספות אם קיימות
            settings = method.get('settings', {})
            if settings:
                if 'title' in settings:
                    result.append(f"  כותרת להצגה: {settings['title']}")
                if 'instructions' in settings:
                    result.append(f"  הוראות: {settings['instructions']}")
                    
        return "\n".join(result)

    def format_transaction_history(self, transactions: List[Dict[str, Any]]) -> str:
        """
        פורמט היסטוריית עסקאות לתצוגה
        
        Args:
            transactions: רשימת עסקאות מה-API
            
        Returns:
            str: מחרוזת מפורמטת עם היסטוריית העסקאות
        """
        if not transactions:
            return "לא נמצאו עסקאות"
            
        result = ["היסטוריית עסקאות:"]
        
        for transaction in transactions:
            # פרטי העסקה הבסיסיים
            trans_id = transaction.get('id', '')
            date = transaction.get('date_created', '').split('T')[0]
            amount = transaction.get('amount', '0')
            status = transaction.get('status', '')
            
            # תרגום סטטוס לעברית
            status_hebrew = {
                'pending': 'בהמתנה',
                'completed': 'הושלם',
                'failed': 'נכשל',
                'refunded': 'הוחזר',
                'cancelled': 'בוטל'
            }.get(status, status)
            
            result.append(
                f"- עסקה #{trans_id} ({date})"
            )
            result.append(f"  סכום: {amount} ₪")
            result.append(f"  סטטוס: {status_hebrew}")
            
            # פרטי תשלום
            payment_method = transaction.get('payment_method_title', '')
            if payment_method:
                result.append(f"  שיטת תשלום: {payment_method}")
            
            # פרטים נוספים
            if transaction.get('note', ''):
                result.append(f"  הערה: {transaction['note']}")
                
        return "\n".join(result)

    async def handle_message(self, user_message: str) -> str:
        """
        טיפול בהודעות משתמש - שאלות מידע
        """
        try:
            if "מוצרים" in user_message:
                # קבלת רשימת המוצרים מ-WooCommerce
                response = self.wcapi.get("products")
                if response.status_code != 200:
                    return f"שגיאה בקבלת מוצרים: {response.status_code}"
                
                products = response.json()
                if not products:
                    return "אין מוצרים בחנות כרגע."
                
                # בניית רשימת המוצרים
                product_list = "המוצרים בחנות:\n\n"
                for product in products:
                    price = product.get('price', 'לא צוין מחיר')
                    stock = product.get('stock_quantity', 'לא צוין')
                    status = 'במלאי' if product.get('in_stock', False) else 'אזל מהמלאי'
                    
                    product_list += f"🛍️ {product['name']}\n"
                    product_list += f"   מחיר: ₪{price}\n"
                    product_list += f"   כמות במלאי: {stock}\n"
                    product_list += f"   סטטוס: {status}\n\n"
                
                return product_list

            elif "דוח" in user_message or "מכירות" in user_message:
                # TODO: implement sales report
                return "מגיע מסוכן המידע: (בקרוב אציג דוחות מכירות)"
            else:
                return "סוכן המידע: לא זיהיתי בקשה לתצוגת מידע."
                
        except Exception as e:
            return f"שגיאה בטיפול בבקשת המידע: {str(e)}"

    def get_stock_report(self) -> str:
        """
        קבלת דוח מלאי נוכחי
        
        Returns:
            str: דוח מלאי מפורט
        """
        try:
            response = self.wcapi.get("products", params={"per_page": 100})
            if response.status_code != 200:
                return f"שגיאה בקבלת נתוני מלאי: {response.status_code}"
            
            products = response.json()
            if not products:
                return "לא נמצאו מוצרים במערכת"
            
            result = ["דוח מלאי נוכחי:"]
            low_stock = []
            out_of_stock = []
            
            for product in products:
                name = product.get("name", "")
                stock_quantity = product.get("stock_quantity", 0)
                low_stock_amount = product.get("low_stock_amount", 0)
                
                # בדיקת מלאי נמוך
                if stock_quantity <= low_stock_amount:
                    low_stock.append(f"- {name}: {stock_quantity} יחידות (סף התראה: {low_stock_amount})")
                
                # בדיקת מלאי אזל
                if product.get("stock_status") == "outofstock":
                    out_of_stock.append(f"- {name}")
                
                result.append(f"- {name}: {stock_quantity} יחידות")
            
            if low_stock:
                result.append("\nמוצרים במלאי נמוך:")
                result.extend(low_stock)
            
            if out_of_stock:
                result.append("\nמוצרים שאזלו מהמלאי:")
                result.extend(out_of_stock)
            
            return "\n".join(result)
        except Exception as e:
            return f"שגיאה בהפקת דוח מלאי: {str(e)}"

    def get_stock_history(self, product_id: int) -> str:
        """
        קבלת היסטוריית שינויי מלאי למוצר
        
        Args:
            product_id: מזהה המוצר
            
        Returns:
            str: היסטוריית שינויי מלאי
        """
        try:
            # קבלת פרטי המוצר
            product_response = self.wcapi.get(f"products/{product_id}")
            if product_response.status_code != 200:
                return f"שגיאה בקבלת פרטי מוצר: {product_response.status_code}"
            
            product = product_response.json()
            
            # קבלת היסטוריית הערות מלאי
            notes_response = self.wcapi.get(f"products/{product_id}/notes")
            if notes_response.status_code != 200:
                return f"שגיאה בקבלת היסטוריית מלאי: {notes_response.status_code}"
            
            notes = notes_response.json()
            stock_notes = [note for note in notes if "stock" in note.get("note", "").lower()]
            
            result = [f"היסטוריית מלאי עבור {product.get('name', '')}:"]
            
            for note in stock_notes:
                date = note.get("date_created", "").split("T")[0]
                result.append(f"- {date}: {note.get('note', '')}")
            
            if len(result) == 1:
                result.append("לא נמצאה היסטוריית שינויי מלאי")
            
            return "\n".join(result)
        except Exception as e:
            return f"שגיאה בקבלת היסטוריית מלאי: {str(e)}"

    def get_category_tree(self) -> str:
        """
        הצגת עץ קטגוריות
        
        Returns:
            str: עץ קטגוריות מפורט
        """
        try:
            response = self.wcapi.get("products/categories", params={"per_page": 100})
            if response.status_code != 200:
                return f"שגיאה בקבלת קטגוריות: {response.status_code}"
            
            categories = response.json()
            if not categories:
                return "לא נמצאו קטגוריות"
            
            # מיון קטגוריות לפי מבנה עץ
            root_categories = [cat for cat in categories if cat.get("parent") == 0]
            
            def build_tree(category, level=0):
                indent = "  " * level
                result = [f"{indent}- {category.get('name', '')} ({category.get('count', 0)} מוצרים)"]
                children = [cat for cat in categories if cat.get("parent") == category.get("id")]
                for child in children:
                    result.extend(build_tree(child, level + 1))
                return result
            
            result = ["עץ קטגוריות:"]
            for category in root_categories:
                result.extend(build_tree(category))
            
            return "\n".join(result)
        except Exception as e:
            return f"שגיאה בהצגת עץ קטגוריות: {str(e)}"

    def get_products_by_category(self, category_id: int) -> str:
        """
        קבלת רשימת מוצרים בקטגוריה
        
        Args:
            category_id: מזהה הקטגוריה
            
        Returns:
            str: רשימת המוצרים בקטגוריה
        """
        try:
            # קבלת פרטי הקטגוריה
            category_response = self.wcapi.get(f"products/categories/{category_id}")
            if category_response.status_code != 200:
                return f"שגיאה בקבלת פרטי קטגוריה: {category_response.status_code}"
            
            category = category_response.json()
            
            # קבלת מוצרים בקטגוריה
            products_response = self.wcapi.get("products", params={"category": category_id, "per_page": 100})
            if products_response.status_code != 200:
                return f"שגיאה בקבלת מוצרים: {products_response.status_code}"
            
            products = products_response.json()
            
            result = [f"מוצרים בקטגוריה {category.get('name', '')}:"]
            
            if not products:
                result.append("לא נמצאו מוצרים בקטגוריה זו")
            else:
                for product in products:
                    name = product.get("name", "")
                    price = product.get("price", "")
                    stock_status = "במלאי" if product.get("in_stock", False) else "אזל מהמלאי"
                    result.append(f"- {name}: {price} ₪ ({stock_status})")
            
            return "\n".join(result)
        except Exception as e:
            return f"שגיאה בקבלת מוצרים מהקטגוריה: {str(e)}"

    def get_advanced_statistics(self) -> str:
        """
        קבלת סטטיסטיקות מתקדמות
        
        Returns:
            str: דוח סטטיסטיקות מפורט
        """
        try:
            result = ["סטטיסטיקות מתקדמות:"]
            
            # מוצרים פופולריים
            popular_products = self.get_popular_products()
            result.append("\nמוצרים פופולריים:")
            result.extend(popular_products)
            
            # זמני משלוח
            shipping_times = self.get_average_shipping_times()
            result.append("\nזמני משלוח ממוצעים:")
            result.extend(shipping_times)
            
            # אחוזי המרה
            conversion_rates = self.get_conversion_rates()
            result.append("\nאחוזי המרה:")
            result.extend(conversion_rates)
            
            return "\n".join(result)
        except Exception as e:
            return f"שגיאה בקבלת סטטיסטיקות: {str(e)}"

    def get_popular_products(self) -> list:
        """
        קבלת רשימת המוצרים הפופולריים
        
        Returns:
            list: רשימת מוצרים פופולריים
        """
        try:
            response = self.wcapi.get("reports/top_sellers", params={"period": "month"})
            if response.status_code != 200:
                return ["שגיאה בקבלת מוצרים פופולריים"]
            
            products = response.json()
            result = []
            
            for product in products:
                name = product.get("name", "")
                total_sales = product.get("total_sales", 0)
                quantity = product.get("quantity", 0)
                result.append(f"- {name}: {quantity} יחידות נמכרו, סה\"כ {total_sales} ₪")
            
            return result if result else ["אין נתונים על מוצרים פופולריים"]
        except Exception as e:
            return [f"שגיאה בקבלת מוצרים פופולריים: {str(e)}"]

    def get_average_shipping_times(self) -> list:
        """
        חישוב זמני משלוח ממוצעים
        
        Returns:
            list: זמני משלוח ממוצעים לפי שיטת משלוח
        """
        try:
            # קבלת הזמנות שהושלמו
            response = self.wcapi.get("orders", params={
                "status": "completed",
                "per_page": 100
            })
            if response.status_code != 200:
                return ["שגיאה בקבלת נתוני משלוחים"]
            
            orders = response.json()
            shipping_times = {}
            
            for order in orders:
                shipping_method = order.get("shipping_lines", [{}])[0].get("method_title", "")
                if not shipping_method:
                    continue
                
                # חישוב זמן משלוח
                date_created = order.get("date_created", "")
                date_completed = order.get("date_completed", "")
                if date_created and date_completed:
                    from datetime import datetime
                    created = datetime.fromisoformat(date_created.replace('Z', '+00:00'))
                    completed = datetime.fromisoformat(date_completed.replace('Z', '+00:00'))
                    days = (completed - created).days
                    
                    if shipping_method not in shipping_times:
                        shipping_times[shipping_method] = {"total": 0, "count": 0}
                    shipping_times[shipping_method]["total"] += days
                    shipping_times[shipping_method]["count"] += 1
            
            result = []
            for method, data in shipping_times.items():
                avg_days = data["total"] / data["count"] if data["count"] > 0 else 0
                result.append(f"- {method}: {avg_days:.1f} ימים בממוצע")
            
            return result if result else ["אין נתונים על זמני משלוח"]
        except Exception as e:
            return [f"שגיאה בחישוב זמני משלוח: {str(e)}"]

    def get_conversion_rates(self) -> list:
        """
        חישוב אחוזי המרה
        
        Returns:
            list: נתוני המרה
        """
        try:
            # קבלת סה"כ הזמנות
            orders_response = self.wcapi.get("reports/orders/totals")
            if orders_response.status_code != 200:
                return ["שגיאה בקבלת נתוני הזמנות"]
            
            orders_data = orders_response.json()
            total_orders = sum(int(status.get("count", 0)) for status in orders_data)
            completed_orders = sum(int(status.get("count", 0)) for status in orders_data if status.get("slug") == "completed")
            
            # חישוב אחוזי המרה
            conversion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
            
            result = [
                f"- סה\"כ הזמנות: {total_orders}",
                f"- הזמנות שהושלמו: {completed_orders}",
                f"- אחוז המרה: {conversion_rate:.1f}%"
            ]
            
            return result
        except Exception as e:
            return [f"שגיאה בחישוב אחוזי המרה: {str(e)}"]

    # Future methods to be implemented:
    # def get_products(self) -> list:
    # def get_sales_report(self) -> dict:
    # def get_orders(self) -> list: 