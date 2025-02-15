"""
Action Agent - responsible for write operations in WooCommerce.
Handles product creation, updates, coupon generation etc.
"""
import re
import random
from typing import Optional, Dict, Any
from woocommerce import API
from core.config import settings

class ActionAgent:
    def __init__(self):
        """Initialize action agent with WooCommerce API connection."""
        self.wcapi = API(
            url=str(settings.WC_STORE_URL),
            consumer_key=settings.WC_CONSUMER_KEY,
            consumer_secret=settings.WC_CONSUMER_SECRET.get_secret_value(),
            version="wc/v3"
        )

    def create_product(self, product_data: Dict[str, Any]) -> str:
        """
        Create a new product in WooCommerce.
        
        Args:
            product_data: Dictionary with product details
        """
        try:
            # בדיקה אם המוצר כבר קיים
            existing_products = self.wcapi.get("products", params={"search": product_data["name"]}).json()
            for product in existing_products:
                if (product["name"].lower() == product_data["name"].lower() and 
                    str(product["regular_price"]) == str(product_data["regular_price"])):
                    return f'מוצר דומה כבר קיים: {product["name"]} (מזהה: {product["id"]})'

            response = self.wcapi.post("products", product_data)
            if response.status_code in [200, 201]:
                product = response.json()
                return f'נוצר מוצר חדש: {product.get("name")} (מזהה: {product.get("id")})'
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                if 'message' in error_data:
                    return f"שגיאה ביצירת מוצר: {error_data['message']}"
                return f"שגיאה ביצירת מוצר: {response.status_code}"
        except Exception as e:
            return f"שגיאה ביצירת מוצר: {str(e)}"

    def update_product(self, product_id: int, update_data: Dict[str, Any]) -> str:
        """
        Update an existing product.
        
        Args:
            product_id: The ID of the product to update
            update_data: Dictionary with fields to update
        """
        try:
            response = self.wcapi.put(f"products/{product_id}", update_data)
            if response.status_code == 200:
                product = response.json()
                return f'המוצר {product.get("name")} עודכן בהצלחה'
            else:
                return f"שגיאה בעדכון מוצר: {response.status_code}"
        except Exception as e:
            return f"שגיאה בעדכון מוצר: {str(e)}"

    def create_coupon(self, coupon_data: Dict[str, Any]) -> str:
        """
        Create a new coupon in WooCommerce.
        
        Args:
            coupon_data: Dictionary with coupon details
        """
        try:
            response = self.wcapi.post("coupons", coupon_data)
            if response.status_code in [200, 201]:
                coupon = response.json()
                return f'נוצר קופון חדש: {coupon.get("code")}'
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                if response.status_code == 400:
                    if 'message' in error_data:
                        return f"שגיאה ביצירת קופון: {error_data['message']}"
                    elif 'code' in error_data:
                        error_codes = {
                            'woocommerce_rest_coupon_code_already_exists': 'קוד הקופון כבר קיים במערכת',
                            'woocommerce_rest_invalid_coupon_amount': 'סכום הקופון לא תקין',
                            'woocommerce_rest_invalid_coupon_type': 'סוג הקופון לא תקין'
                        }
                        return f"שגיאה ביצירת קופון: {error_codes.get(error_data['code'], 'שגיאה לא ידועה')}"
                return f"שגיאה ביצירת קופון: {response.status_code}"
        except Exception as e:
            return f"שגיאה ביצירת קופון: {str(e)}"

    def _extract_product_info(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Extract product information from user message using regex.
        Example: 'הוסף מוצר חדש בשם חולצה במחיר 70'
        """
        name_match = re.search(r'בשם\s+([^\d]+?)\s+במחיר', message)
        price_match = re.search(r'במחיר\s+(\d+)', message)
        
        if name_match and price_match:
            return {
                "name": name_match.group(1).strip(),
                "regular_price": price_match.group(1),
                "type": "simple",
                "stock_status": "instock"
            }
        return None

    def _extract_coupon_info(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Extract coupon information from user message using regex.
        Example: 'צור קופון של 20 אחוז'
        """
        percent_match = re.search(r'(\d+)\s*אחוז', message)
        amount_match = re.search(r'(\d+)\s*שקל', message)
        
        # יצירת מספר רנדומלי בין 1000 ל-9999 לקוד ייחודי
        unique_id = random.randint(1000, 9999)
        
        base_data = {
            "description": "קופון שנוצר אוטומטית",
            "minimum_amount": "0",  # ללא סכום מינימלי
            "usage_limit": 100,  # מגבלת שימוש
            "usage_limit_per_user": 1,  # הגבלת שימוש פר משתמש
            "individual_use": True,  # לא ניתן לשלב עם קופונים אחרים
        }
        
        if percent_match:
            return {
                **base_data,
                "code": f"SALE{percent_match.group(1)}_{unique_id}",
                "discount_type": "percent",
                "amount": percent_match.group(1)
            }
        elif amount_match:
            return {
                **base_data,
                "code": f"FIXED{amount_match.group(1)}_{unique_id}",
                "discount_type": "fixed_cart",
                "amount": amount_match.group(1)
            }
        return None

    def handle_message(self, user_message: str) -> str:
        """
        Handle user messages and route to appropriate method.
        Now with actual implementation and parameter extraction.
        """
        message_lower = user_message.lower()
        
        # Product creation
        if "הוסף מוצר" in message_lower:
            product_data = self._extract_product_info(user_message)
            if product_data:
                return self.create_product(product_data)
            else:
                return "לא הצלחתי להבין את פרטי המוצר. נא לציין שם ומחיר, לדוגמה: 'הוסף מוצר חדש בשם חולצה במחיר 70'"
        
        # Coupon creation
        elif "צור קופון" in message_lower or "קופון חדש" in message_lower:
            coupon_data = self._extract_coupon_info(user_message)
            if coupon_data:
                return self.create_coupon(coupon_data)
            else:
                return "לא הצלחתי להבין את פרטי הקופון. נא לציין סכום או אחוז, לדוגמה: 'צור קופון של 20 אחוז' או 'צור קופון של 50 שקל'"
        
        # Product update (price)
        elif "עדכן מחיר" in message_lower or "שנה מחיר" in message_lower:
            # TODO: Implement price update logic
            return "עדכון מחירים יתווסף בקרוב. נא לציין מזהה מוצר ומחיר חדש."
        
        # Unknown action
        else:
            return "סוכן הפעולות: אני יכול לעזור עם:\n" + \
                   "1. הוספת מוצר חדש (ציין שם ומחיר)\n" + \
                   "2. יצירת קופון (ציין אחוז או סכום)\n" + \
                   "3. עדכון מחיר מוצר (בקרוב)" 