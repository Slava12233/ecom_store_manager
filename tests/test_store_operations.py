import pytest
import os
import sys
from datetime import datetime
import asyncio
import time

# הוספת נתיב הפרויקט ל-PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.agents.action_agent import ActionAgent
from src.agents.information_agent import InformationAgent
from src.core.config import settings

class TestStoreOperations:
    @pytest.fixture(autouse=True)
    def setup(self):
        """הגדרת המשתנים הדרושים לבדיקות"""
        self.action_agent = ActionAgent()
        self.info_agent = InformationAgent()
        self.test_product_name = f"Test Product {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.test_category_name = f"Test Category {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # יצירת מוצר בדיקה
        product_data = {
            "name": self.test_product_name,
            "type": "simple",
            "regular_price": "100.00",
            "description": "מוצר בדיקה",
            "short_description": "תיאור קצר למוצר בדיקה",
            "categories": [],
            "images": []
        }
        response = self.action_agent.wcapi.post("products", product_data)
        assert response.status_code == 201, "נכשל ביצירת מוצר בדיקה"
        self.test_product_id = response.json()["id"]

    def test_product_basic_operations(self):
        """בדיקת פעולות בסיסיות על מוצרים"""
        # יצירת מוצר חדש
        product_data = {
            "name": self.test_product_name,
            "type": "simple",
            "regular_price": "100.00",
            "description": "מוצר בדיקה",
            "short_description": "תיאור קצר למוצר בדיקה",
            "categories": [],
            "images": [],
            "manage_stock": True,
            "stock_quantity": 10,
            "stock_status": "instock"
        }
        result = self.action_agent.create_product(product_data)
        assert "נוצר מוצר חדש" in result

        # המתנה קצרה לוודא שהמוצר נוצר במערכת
        time.sleep(2)

        # עדכון מחיר
        result = self.action_agent.update_product_price(self.test_product_name, "150")
        assert "מחיר" in result and "עודכן" in result
        
        # עדכון מלאי
        result = self.action_agent.update_product_stock(self.test_product_name, "אזל")
        assert "סטטוס המלאי" in result and "עודכן" in result
        
        # עדכון שם
        new_name = f"{self.test_product_name}_updated"
        result = self.action_agent.update_product_name(self.test_product_name, new_name)
        assert "שם המוצר עודכן" in result
        self.test_product_name = new_name  # עדכון השם לשימוש בבדיקות הבאות
        
        # עדכון תיאור
        result = self.action_agent.update_product_description(self.test_product_name, "תיאור חדש לבדיקה")
        assert "תיאור" in result and "עודכן" in result

    def test_category_operations(self):
        """בדיקת פעולות על קטגוריות"""
        # יצירת קטגוריה ראשית
        category_data = {
            "name": self.test_category_name,
            "description": "קטגוריית בדיקה"
        }
        result = self.action_agent.create_category(category_data)
        assert "נוצרה" in result
        
        # יצירת תת-קטגוריה
        sub_category_data = {
            "name": f"Sub {self.test_category_name}",
            "parent": self.test_category_name
        }
        result = self.action_agent.create_category(sub_category_data)
        assert "נוצרה" in result
        
        # שיוך מוצר לקטגוריה
        result = self.action_agent.update_product_category(self.test_product_name, self.test_category_name)
        assert "עודכן" in result or "עודכנה" in result

    def test_image_operations(self):
        """בדיקת פעולות על תמונות"""
        # יצירת תמונת בדיקה
        test_image_path = "tests/test_data/test_image.jpg"
        if not os.path.exists("tests/test_data"):
            os.makedirs("tests/test_data")

        # העלאת תמונה
        media_id = self.action_agent.upload_media(test_image_path)
        assert media_id is not None

        # שיוך תמונה למוצר
        result = self.action_agent.assign_image_to_product(self.test_product_id, media_id)
        assert "שויכה בהצלחה" in result

        # עדכון גלריית תמונות
        result = asyncio.run(self.action_agent.update_product_gallery(self.test_product_name, [test_image_path]))
        assert "עודכנה בהצלחה" in result

    def test_coupon_operations(self):
        """בדיקת פעולות על קופונים"""
        # יצירת קופון באחוזים
        percent_coupon_data = {
            "code": f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "discount_type": "percent",
            "amount": "20",
            "description": "קופון בדיקה",
            "minimum_amount": "0",
            "maximum_amount": "1000",
            "individual_use": True,
            "exclude_sale_items": False,
            "usage_limit": 100,
            "usage_limit_per_user": 1,
            "email_restrictions": [],
            "free_shipping": False,
            "exclude_sale_items": False
        }
        result = self.action_agent.create_coupon(percent_coupon_data)
        assert "נוצר בהצלחה" in result
        
        # יצירת קופון בסכום קבוע
        fixed_coupon_data = {
            "code": f"FIXED{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "discount_type": "fixed_cart",
            "amount": "50",
            "description": "קופון בדיקה",
            "minimum_amount": "0",
            "maximum_amount": "1000",
            "individual_use": True,
            "exclude_sale_items": False,
            "usage_limit": 100,
            "usage_limit_per_user": 1,
            "email_restrictions": [],
            "free_shipping": False,
            "exclude_sale_items": False
        }
        result = self.action_agent.create_coupon(fixed_coupon_data)
        assert "נוצר בהצלחה" in result
        
        # יצירת קופון מוגבל למוצרים
        product_coupon_data = {
            "code": f"PROD{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "discount_type": "percent",
            "amount": "30",
            "description": "קופון בדיקה למוצר ספציפי",
            "product_ids": [self.test_product_id],
            "minimum_amount": "0",
            "maximum_amount": "1000",
            "individual_use": True,
            "exclude_sale_items": False,
            "usage_limit": 100,
            "usage_limit_per_user": 1,
            "email_restrictions": [],
            "free_shipping": False,
            "exclude_sale_items": False
        }
        result = self.action_agent.create_coupon(product_coupon_data)
        assert "נוצר בהצלחה" in result

    def test_variable_product_operations(self):
        """בדיקת פעולות על מוצר משתנה"""
        # יצירת מוצר משתנה
        variable_product_data = {
            "name": f"Variable {self.test_product_name}",
            "type": "variable",
            "attributes": [
                {
                    "name": "צבע",
                    "options": ["אדום", "כחול", "ירוק"]
                },
                {
                    "name": "מידה",
                    "options": ["S", "M", "L"]
                }
            ]
        }
        result = self.action_agent.create_product(variable_product_data)
        assert "נוצר מוצר חדש" in result
        
        # הוספת וריאציות
        variations_data = [
            {
                "regular_price": "100",
                "attributes": [
                    {"name": "צבע", "option": "אדום"},
                    {"name": "מידה", "option": "M"}
                ]
            }
        ]
        result = self.action_agent.create_variations(f"Variable {self.test_product_name}", variations_data)
        assert "נוצרו בהצלחה" in result

    def test_inventory_operations(self):
        """בדיקת פעולות על מלאי"""
        # עדכון כמות מלאי
        result = self.action_agent.update_product_stock_quantity(self.test_product_name, 10)
        assert "כמות המלאי" in result and "עודכנה" in result
        
        # הגדרת התראת מלאי נמוך
        result = self.action_agent.set_low_stock_threshold(self.test_product_name, 3)
        assert "הוגדר בהצלחה" in result
        
        # בדיקת ניהול מלאי מתקדם
        stock_data = {
            "manage_stock": True,
            "stock_quantity": 15,
            "backorders_allowed": True,
            "low_stock_amount": 5
        }
        result = self.action_agent.update_product_stock_management(self.test_product_name, stock_data)
        assert "הגדרות המלאי" in result and "עודכנו בהצלחה" in result

    def test_product_attributes_operations(self):
        """בדיקת פעולות על תכונות מוצר"""
        # יצירת תכונה גלובלית
        attribute_data = {
            "name": f"Test Brand {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "slug": f"brand_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "type": "select",
            "order_by": "menu_order",
            "has_archives": True,
            "terms": [
                {"name": "מותג א"},
                {"name": "מותג ב"},
                {"name": "מותג ג"}
            ]
        }
        result = self.action_agent.create_global_attribute(attribute_data)
        assert "התכונה" in result and "נוצרה בהצלחה" in result

        # המתנה קצרה לוודא שהתכונה נוצרה במערכת
        time.sleep(2)

        # הוספת ערכים לתכונה
        terms = ["Nike", "Adidas", "Puma"]
        result = self.action_agent.add_attribute_terms(attribute_data["name"], terms)
        assert "נוספו בהצלחה" in result

        # שיוך תכונה למוצר
        result = self.action_agent.assign_attribute_to_product(self.test_product_name, attribute_data["name"], "Nike")
        assert "התכונה" in result and "שויכה בהצלחה" in result

    def test_cleanup(self):
        """ניקוי נתוני הבדיקה"""
        # מחיקת המוצר
        result = self.action_agent.delete_product(self.test_product_name)
        assert "נמחק בהצלחה" in result
        
        # מחיקת המוצר המשתנה
        result = self.action_agent.delete_product(f"Variable {self.test_product_name}")
        assert "נמחק בהצלחה" in result
        
        # מחיקת הקטגוריה
        result = self.action_agent.delete_category(self.test_category_name)
        assert "נמחקה בהצלחה" in result

    def test_order_operations(self):
        """בדיקת פעולות על הזמנות"""
        # יצירת הזמנה לבדיקה
        order_data = {
            "status": "pending",
            "payment_method": "ppec_paypal",  # PayPal Express Checkout
            "payment_method_title": "PayPal",
            "set_paid": True,  # מסמן את ההזמנה כשולמה
            "line_items": [
                {
                    "product_id": 1,
                    "quantity": 1,
                    "price": "100.00"
                }
            ],
            "shipping_lines": [
                {
                    "method_id": "flat_rate",
                    "method_title": "משלוח רגיל",
                    "total": "0.00"
                }
            ]
        }
        response = self.action_agent.wcapi.post("orders", order_data)
        assert response.status_code == 201, "נכשל ביצירת הזמנה לבדיקה"
        order_id = response.json()["id"]
        
        # עדכון סטטוס הזמנה לבעיבוד
        result = self.action_agent.update_order_status(order_id, "בעיבוד", "התחלנו לטפל בהזמנה")
        assert "עודכן" in result
        
        # הוספת הערה להזמנה
        result = self.action_agent.add_order_note(order_id, "הערה לבדיקה", False)
        assert "נוספה בהצלחה" in result
        
        # הוספת הערת לקוח
        result = self.action_agent.add_order_note(order_id, "הערה ללקוח", True)
        assert "נוספה בהצלחה" in result
        
        # עדכון סטטוס ההזמנה להושלם
        result = self.action_agent.update_order_status(order_id, "הושלם", "ההזמנה הושלמה")
        assert "עודכן" in result
        
        # ביצוע החזר
        result = self.action_agent.process_refund(order_id, 50.00, "החזר לבדיקה")
        assert "בוצע החזר" in result

    def test_order_message_parsing(self):
        """בדיקת פענוח הודעות משתמש לניהול הזמנות"""
        # עדכון סטטוס
        message = "עדכן סטטוס הזמנה 123 לבעיבוד הערה: התחלנו לטפל"
        info = self.action_agent._extract_order_status_update_info(message)
        assert info is not None
        assert info["order_id"] == 123
        assert info["status"] == "בעיבוד"
        assert "התחלנו לטפל" in info["note"]
        
        # הוספת הערה
        message = "הוסף הערה להזמנה 123: הערה לבדיקה"
        info = self.action_agent._extract_order_note_info(message)
        assert info is not None
        assert info["order_id"] == 123
        assert "הערה לבדיקה" in info["note"]
        
        # הוספת הערת לקוח
        message = "הוסף הערה ללקוח להזמנה 123: הערה לבדיקה"
        info = self.action_agent._extract_order_note_info(message)
        assert info is not None
        assert info["is_customer_note"] is True
        
        # ביצוע החזר
        message = "בצע החזר להזמנה 123 בסך 50 שקל סיבה: בדיקת החזר"
        info = self.action_agent._extract_refund_info(message)
        assert info is not None
        assert info["order_id"] == 123
        assert info["amount"] == 50.0
        assert "בדיקת החזר" in info["reason"]

    def test_advanced_order_operations(self):
        """בדיקת פעולות מתקדמות על הזמנות"""
        # יצירת הזמנה לבדיקה
        order_data = {
            "status": "pending",
            "payment_method": "ppec_paypal",
            "payment_method_title": "PayPal",
            "set_paid": False,  # לא לסמן כשולם כדי להשאיר במצב pending
            "line_items": [
                {
                    "product_id": self.test_product_id,
                    "quantity": 2,
                    "price": "100.00"
                }
            ],
            "shipping_lines": [
                {
                    "method_id": "flat_rate",
                    "method_title": "משלוח רגיל",
                    "total": "0.00"
                }
            ]
        }
        response = self.action_agent.wcapi.post("orders", order_data)
        assert response.status_code == 201, "נכשל ביצירת הזמנה לבדיקה"
        order_id = response.json()["id"]

        # וידוא שההזמנה במצב pending
        order_response = self.action_agent.wcapi.get(f"orders/{order_id}")
        assert order_response.json()["status"] == "pending", "ההזמנה לא במצב pending"

        # אישור הזמנה
        result = self.action_agent.approve_order(order_id, "אושר לאחר בדיקת מלאי")
        assert "אושרה בהצלחה" in result

        # עדכון פרטי משלוח
        result = self.action_agent.update_shipping_status(
            order_id,
            "ABC123456",
            "חברת שליחויות לבדיקה"
        )
        assert "עודכנו בהצלחה" in result

        # בדיקת החזרת מוצרים
        return_items = [
            {
                "product_id": self.test_product_id,
                "quantity": 1
            }
        ]
        result = self.action_agent.process_return(
            order_id,
            return_items,
            "מוצר פגום"
        )
        assert "בוצעה בהצלחה" in result

        # בדיקת דחיית הזמנה
        # יצירת הזמנה חדשה לבדיקת דחייה
        response = self.action_agent.wcapi.post("orders", order_data)
        reject_order_id = response.json()["id"]

        result = self.action_agent.reject_order(
            reject_order_id,
            "מוצרים לא במלאי"
        )
        assert "נדחתה בהצלחה" in result

        # בדיקת ביטול הזמנה
        # יצירת הזמנה חדשה לבדיקת ביטול
        response = self.action_agent.wcapi.post("orders", order_data)
        cancel_order_id = response.json()["id"]

        result = self.action_agent.cancel_order(
            cancel_order_id,
            "בקשת לקוח",
            True  # החזרה למלאי
        )
        assert "בוטלה בהצלחה" in result

    def test_shipping_management(self):
        """בדיקת פעולות ניהול משלוחים"""
        # יצירת אזור משלוח
        zone_data = {
            "name": "מרכז הארץ",
            "regions": ["תל אביב", "רמת גן", "גבעתיים"],
            "price": 25.90
        }
        result = self.action_agent.create_shipping_zone(zone_data)
        assert "נוצר" in result

        # עדכון אזור משלוח
        zone_id = 1  # נניח שזה המזהה שקיבלנו
        update_data = {
            "name": "מרכז מורחב",
            "regions": ["תל אביב", "רמת גן", "גבעתיים", "חולון"],
            "price": 29.90
        }
        result = self.action_agent.update_shipping_zone(zone_id, update_data)
        assert "עודכן" in result

    def tearDown(self):
        """ניקוי סביבת הבדיקה"""
        # מחיקת מוצר הבדיקה
        self.action_agent.wcapi.delete(f"products/{self.test_product_id}", params={"force": True}) 