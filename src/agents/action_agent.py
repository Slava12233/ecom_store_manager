"""
Action Agent - responsible for write operations in WooCommerce.
Handles product creation, updates, coupon generation etc.
"""
import re
import random
import os
import requests
import base64
import mimetypes
from typing import Optional, Dict, Any
from woocommerce import API
from core.config import settings
from utils.logger import logger
from PIL import Image

class ActionAgent:
    def __init__(self):
        """Initialize action agent with WooCommerce API connection."""
        self.wcapi = API(
            url=str(settings.WC_STORE_URL),
            consumer_key=settings.WC_CONSUMER_KEY,
            consumer_secret=settings.WC_CONSUMER_SECRET.get_secret_value(),
            version="wc/v3",
            verify=False  # Disable SSL verification for InstaWP
        )
        self.logger = logger

    def _get_auth_header(self) -> Dict[str, str]:
        """
        יצירת כותרת אימות עבור ה-API של WooCommerce
        
        Returns:
            Dict[str, str]: כותרת אימות
        """
        auth_str = f"{self.wcapi.consumer_key}:{self.wcapi.consumer_secret}"
        return {
            "Authorization": f"Basic {base64.b64encode(auth_str.encode()).decode()}"
        }

    def _get_wp_auth_header(self) -> Dict[str, str]:
        """
        יצירת כותרת אימות עבור ה-API של WordPress
        
        Returns:
            Dict[str, str]: כותרת אימות
        """
        wp_username = settings.WP_USERNAME.strip()
        wp_password = settings.WP_PASSWORD.get_secret_value().strip()
        
        # לוג מפורט לצורך דיבוג
        self.logger.debug(f"Creating WordPress auth header for user: {wp_username}")
        self.logger.debug(f"Password length: {len(wp_password)}")
        
        auth_str = f"{wp_username}:{wp_password}"
        auth_b64 = base64.b64encode(auth_str.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Accept": "application/json"
        }
        
        # לוג של הכותרות (ללא הסיסמה)
        safe_headers = headers.copy()
        safe_headers["Authorization"] = "Basic ***"
        self.logger.debug(f"Generated headers: {safe_headers}")
        
        return headers

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
            if response.status_code == 201:
                coupon = response.json()
                return f'הקופון {coupon.get("code")} נוצר בהצלחה'
            else:
                return f"שגיאה ביצירת קופון: {response.status_code}"
        except Exception as e:
            return f"שגיאה ביצירת קופון: {str(e)}"

    def upload_media(self, image_path: str) -> Dict[str, Any]:
        """
        העלאת מדיה ל-WordPress
        
        Args:
            image_path: נתיב לקובץ התמונה
        
        Returns:
            Dict[str, Any]: תשובה מה-API של WordPress
        """
        try:
            # פתיחת וקריאת קובץ התמונה
            with open(image_path, 'rb') as img:
                image_data = img.read()

            # קבלת שם הקובץ וסוג ה-MIME
            file_name = os.path.basename(image_path)
            mime_type = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'

            # הכנת נתוני הקובץ
            files = {
                'file': (file_name, image_data, mime_type)
            }

            # שליחת בקשה ל-API של WordPress
            media_url = f"{settings.WC_STORE_URL}/wp-json/wp/v2/media"
            headers = self._get_wp_auth_header()
            
            self.logger.info(f"שולח בקשת העלאת מדיה ל: {media_url}")
            self.logger.debug(f"סוג MIME: {mime_type}")
            
            response = requests.post(
                media_url,
                headers=headers,
                files=files,
                verify=False
            )

            self.logger.info(f"קוד תשובה: {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                self.logger.info(f"המדיה הועלתה בהצלחה. מזהה: {result.get('id')}")
                return {
                    'id': result.get('id'),
                    'source_url': result.get('source_url'),
                    'media_details': result.get('media_details', {})
                }
            else:
                error_msg = f"נכשלה העלאת המדיה. קוד: {response.status_code}"
                if response.content:
                    try:
                        error_data = response.json()
                        error_msg += f"\nהודעת שגיאה: {error_data.get('message', 'אין הודעה')}"
                    except:
                        error_msg += f"\nתוכן התשובה: {response.text}"
                raise Exception(error_msg)

        except Exception as e:
            self.logger.error(f"שגיאה בהעלאת מדיה: {str(e)}")
            raise

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
        Example: 'צור קופון של 20 אחוז קוד קופון ABC123'
        """
        percent_match = re.search(r'(\d+)\s*אחוז', message)
        amount_match = re.search(r'(\d+)\s*שקל', message)
        code_match = re.search(r'קוד קופון\s+([a-zA-Z0-9_-]+)', message)
        
        base_data = {
            "description": "קופון שנוצר אוטומטית",
            "minimum_amount": "0",  # ללא סכום מינימלי
            "usage_limit": 100,  # מגבלת שימוש
            "usage_limit_per_user": 1,  # הגבלת שימוש פר משתמש
            "individual_use": True,  # לא ניתן לשלב עם קופונים אחרים
        }
        
        # אם המשתמש הגדיר קוד קופון, נשתמש בו
        coupon_code = code_match.group(1) if code_match else None
        
        if percent_match:
            return {
                **base_data,
                "code": coupon_code or f"SALE{percent_match.group(1)}_{random.randint(1000, 9999)}",
                "discount_type": "percent",
                "amount": percent_match.group(1)
            }
        elif amount_match:
            return {
                **base_data,
                "code": coupon_code or f"FIXED{amount_match.group(1)}_{random.randint(1000, 9999)}",
                "discount_type": "fixed_cart",
                "amount": amount_match.group(1)
            }
        return None

    def update_product_price(self, product_name: str, new_price: str) -> str:
        """
        עדכון מחיר למוצר קיים לפי שם המוצר
        """
        try:
            # חיפוש המוצר לפי שם
            products = self.wcapi.get("products", params={"search": product_name}).json()
            if not products:
                return f"לא נמצא מוצר בשם '{product_name}'"
            
            # מציאת התאמה מדויקת
            product = None
            for p in products:
                if p["name"].lower() == product_name.lower():
                    product = p
                    break
            
            if not product:
                return f"לא נמצאה התאמה מדויקת למוצר '{product_name}'"
            
            # עדכון המחיר
            update_data = {
                "regular_price": str(new_price)
            }
            
            response = self.wcapi.put(f"products/{product['id']}", update_data)
            if response.status_code == 200:
                updated = response.json()
                return f"מחיר המוצר '{updated['name']}' עודכן ל-{updated['regular_price']} ₪"
            else:
                return f"שגיאה בעדכון מחיר: {response.status_code}"
                
        except Exception as e:
            return f"שגיאה בעדכון מחיר: {str(e)}"

    def update_product_stock(self, product_name: str, stock_status: str) -> str:
        """
        עדכון סטטוס מלאי למוצר
        """
        try:
            # חיפוש המוצר
            products = self.wcapi.get("products", params={"search": product_name}).json()
            if not products:
                return f"לא נמצא מוצר בשם '{product_name}'"
            
            # מציאת התאמה מדויקת
            product = None
            for p in products:
                if p["name"].lower() == product_name.lower():
                    product = p
                    break
            
            if not product:
                return f"לא נמצאה התאמה מדויקת למוצר '{product_name}'"
            
            # תרגום סטטוס לאנגלית
            status_map = {
                "במלאי": "instock",
                "אזל": "outofstock",
                "בהזמנה מראש": "onbackorder"
            }
            eng_status = status_map.get(stock_status, stock_status)
            
            # עדכון סטטוס
            update_data = {
                "stock_status": eng_status
            }
            
            response = self.wcapi.put(f"products/{product['id']}", update_data)
            if response.status_code == 200:
                updated = response.json()
                status_hebrew = {v: k for k, v in status_map.items()}.get(updated['stock_status'], updated['stock_status'])
                return f"סטטוס המלאי של המוצר '{updated['name']}' עודכן ל{status_hebrew}"
            else:
                return f"שגיאה בעדכון סטטוס מלאי: {response.status_code}"
                
        except Exception as e:
            return f"שגיאה בעדכון סטטוס מלאי: {str(e)}"

    def delete_product(self, product_name: str) -> str:
        """
        מחיקת מוצר מהחנות
        """
        try:
            # חיפוש המוצר
            products = self.wcapi.get("products", params={"search": product_name}).json()
            if not products:
                return f"לא נמצא מוצר בשם '{product_name}'"
            
            # מציאת התאמה מדויקת
            product = None
            for p in products:
                if p["name"].lower() == product_name.lower():
                    product = p
                    break
            
            if not product:
                return f"לא נמצאה התאמה מדויקת למוצר '{product_name}'"
            
            # מחיקת המוצר
            response = self.wcapi.delete(f"products/{product['id']}", params={"force": True})
            if response.status_code == 200:
                deleted = response.json()
                return f"המוצר '{deleted['name']}' נמחק בהצלחה"
            else:
                return f"שגיאה במחיקת המוצר: {response.status_code}"
                
        except Exception as e:
            return f"שגיאה במחיקת המוצר: {str(e)}"

    def _extract_price_update_info(self, message: str) -> Optional[Dict[str, Any]]:
        """
        חילוץ מידע לעדכון מחיר מהודעת המשתמש
        דוגמה: 'עדכן מחיר למוצר חולצה כתומה ל-199'
        """
        product_match = re.search(r'מוצר\s+([^,]+?)(?:\s+ל|,|\s+מחיר\s+חדש|\s+במחיר)', message)
        price_match = re.search(r'(?:ל-|מחיר\s+חדש\s+|במחיר\s+)(\d+)', message)
        
        if product_match and price_match:
            return {
                "product_name": product_match.group(1).strip(),
                "new_price": price_match.group(1)
            }
        return None

    def _extract_stock_update_info(self, message: str) -> Optional[Dict[str, Any]]:
        """
        חילוץ מידע לעדכון מלאי מהודעת המשתמש
        דוגמה: 'עדכן מלאי למוצר חולצה כתומה לאזל מהמלאי'
        """
        product_match = re.search(r'מוצר\s+([^,]+?)(?:\s+ל|,|\s+סטטוס)', message)
        status_match = re.search(r'(?:ל|סטטוס\s+)(במלאי|אזל|בהזמנה מראש)', message)
        
        if product_match and status_match:
            return {
                "product_name": product_match.group(1).strip(),
                "stock_status": status_match.group(1)
            }
        return None

    def update_product_name(self, old_name: str, new_name: str) -> str:
        """
        עדכון שם מוצר
        """
        try:
            # חיפוש המוצר לפי שם
            products = self.wcapi.get("products", params={"search": old_name}).json()
            if not products:
                return f"לא נמצא מוצר בשם '{old_name}'"
            
            # מציאת התאמה מדויקת
            product = None
            for p in products:
                if p["name"].lower() == old_name.lower():
                    product = p
                    break
            
            if not product:
                return f"לא נמצאה התאמה מדויקת למוצר '{old_name}'"
            
            # עדכון השם
            update_data = {
                "name": new_name
            }
            
            response = self.wcapi.put(f"products/{product['id']}", update_data)
            if response.status_code == 200:
                updated = response.json()
                return f"שם המוצר עודכן מ-'{old_name}' ל-'{updated['name']}'"
            else:
                return f"שגיאה בעדכון שם המוצר: {response.status_code}"
                
        except Exception as e:
            return f"שגיאה בעדכון שם המוצר: {str(e)}"

    def update_product_description(self, product_name: str, new_description: str) -> str:
        """
        עדכון תיאור מוצר
        """
        try:
            print(f"מנסה לעדכן תיאור למוצר '{product_name}'")
            print(f"התיאור החדש שהתקבל: {new_description}")
            
            # חיפוש המוצר
            products = self.wcapi.get("products", params={"search": product_name}).json()
            if not products:
                return f"לא נמצא מוצר בשם '{product_name}'"
            
            # מציאת התאמה מדויקת
            product = None
            for p in products:
                if p["name"].lower() == product_name.lower():
                    product = p
                    break
            
            if not product:
                return f"לא נמצאה התאמה מדויקת למוצר '{product_name}'"
            
            print(f"נמצא מוצר עם ID: {product['id']}")
            
            # עדכון התיאור
            update_data = {
                "description": new_description,
                "short_description": new_description  # מעדכן גם את התיאור הקצר
            }
            
            print(f"שולח בקשת עדכון עם הנתונים: {update_data}")
            
            response = self.wcapi.put(f"products/{product['id']}", update_data)
            print(f"קוד תשובה מה-API: {response.status_code}")
            
            if response.status_code == 200:
                updated_product = response.json()
                print(f"תיאור שנשמר בפועל: {updated_product.get('description', '')}")
                return f"תיאור המוצר '{product_name}' עודכן בהצלחה.\nהתיאור החדש: {updated_product.get('description', '')}"
            else:
                print(f"תוכן התשובה מה-API: {response.text}")
                return f"שגיאה בעדכון תיאור המוצר: {response.status_code}"
                
        except Exception as e:
            print(f"שגיאה בעדכון תיאור המוצר: {str(e)}")
            return f"שגיאה בעדכון תיאור המוצר: {str(e)}"

    def update_product_category(self, product_name: str, category_name: str) -> str:
        """
        עדכון קטגוריה למוצר
        """
        try:
            # חיפוש המוצר
            products = self.wcapi.get("products", params={"search": product_name}).json()
            if not products:
                return f"לא נמצא מוצר בשם '{product_name}'"
            
            # מציאת התאמה מדויקת
            product = None
            for p in products:
                if p["name"].lower() == product_name.lower():
                    product = p
                    break
            
            if not product:
                return f"לא נמצאה התאמה מדויקת למוצר '{product_name}'"
            
            # חיפוש או יצירת קטגוריה
            categories = self.wcapi.get("products/categories", params={"search": category_name}).json()
            category = None
            
            if categories:
                for cat in categories:
                    if cat["name"].lower() == category_name.lower():
                        category = cat
                        break
            
            if not category:
                # יצירת קטגוריה חדשה
                category_data = {
                    "name": category_name
                }
                category_response = self.wcapi.post("products/categories", category_data)
                if category_response.status_code not in [200, 201]:
                    return f"שגיאה ביצירת קטגוריה חדשה: {category_response.status_code}"
                category = category_response.json()
            
            # עדכון הקטגוריה למוצר
            update_data = {
                "categories": [{"id": category["id"]}]
            }
            
            response = self.wcapi.put(f"products/{product['id']}", update_data)
            if response.status_code == 200:
                return f"הקטגוריה של המוצר '{product_name}' עודכנה ל-'{category_name}'"
            else:
                return f"שגיאה בעדכון קטגוריית המוצר: {response.status_code}"
                
        except Exception as e:
            return f"שגיאה בעדכון קטגוריית המוצר: {str(e)}"

    def _extract_name_update_info(self, message: str) -> Optional[Dict[str, Any]]:
        """
        חילוץ מידע לעדכון שם מוצר מהודעת המשתמש
        דוגמה: 'שנה שם מוצר ים למכנסי ג'ינס כחולים למכנסי ג'ינס כחולים'
        """
        # מחפש את השם הישן בין "מוצר" ל"ל" האחרון לפני השם החדש
        parts = message.split(' ל')
        if len(parts) >= 2:
            # מוצא את החלק שמכיל "שנה שם מוצר" או "עדכן שם מוצר"
            command_part = parts[0]
            old_name_match = re.search(r'(?:שנה|עדכן)\s+שם\s+מוצר\s+(.*?)$', command_part)
            
            if old_name_match:
                old_name = old_name_match.group(1).strip()
                # השם החדש הוא החלק האחרון אחרי ה-"ל" האחרון
                new_name = parts[-1].strip()
                if new_name:
                    return {
                        "old_name": old_name,
                        "new_name": new_name
                    }
        return None

    def _extract_description_update_info(self, message: str) -> Optional[Dict[str, Any]]:
        """
        חילוץ מידע לעדכון תיאור מוצר מהודעת המשתמש
        דוגמה: 'עדכן תיאור למוצר חולצה כתומה: חולצת כותנה איכותית'
        """
        # מחפש את שם המוצר
        product_match = re.search(r'מוצר\s+([^:]+?)(?:\s*:|תיאור חדש|\s*$)', message)
        
        if not product_match:
            return None
            
        product_name = product_match.group(1).strip()
        
        # מחפש את התיאור החדש
        if ': ' in message:
            # אם יש נקודותיים, לוקח את כל מה שאחריהן
            new_description = message.split(': ', 1)[1].strip()
        elif 'תיאור חדש' in message:
            # אם יש "תיאור חדש", לוקח את כל מה שאחריו
            new_description = message.split('תיאור חדש', 1)[1].strip()
        else:
            return None
            
        if not new_description:
            return None
            
        return {
            "product_name": product_name,
            "new_description": new_description
        }

    def _extract_category_update_info(self, message: str) -> Optional[Dict[str, Any]]:
        """
        חילוץ מידע לעדכון קטגוריה מהודעת המשתמש
        דוגמה: 'הוסף את המוצר חולצה כתומה לקטגוריה ביגוד'
        """
        product_match = re.search(r'מוצר\s+([^,]+?)(?:\s+לקטגוריה|\s+קטגוריה)', message)
        category_match = re.search(r'(?:לקטגוריה|קטגוריה)\s+([^,]+?)(?:\s*$|,)', message)
        
        if product_match and category_match:
            return {
                "product_name": product_match.group(1).strip(),
                "category_name": category_match.group(1).strip()
            }
        return None

    async def _check_wp_permissions(self) -> bool:
        """
        בדיקת הרשאות משתמש WordPress - גישה פשוטה יותר
        
        Returns:
            bool: האם למשתמש יש הרשאות מתאימות
        """
        try:
            # בניית כתובת ה-API
            check_url = f"{settings.WC_STORE_URL}/wp-json/wp/v2/users/me"
            
            # קבלת כותרות אימות
            headers = self._get_wp_auth_header()
            
            self.logger.info("=== בדיקת הרשאות WordPress ===")
            self.logger.info(f"URL: {check_url}")
            self.logger.info(f"משתמש: {settings.WP_USERNAME}")
            
            # שליחת בקשה לבדיקת הרשאות
            response = requests.get(
                check_url,
                headers=headers,
                verify=False,
                timeout=10
            )
            
            self.logger.info(f"קוד תשובה: {response.status_code}")
            
            if response.status_code == 401:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                error_message = error_data.get('message', 'שגיאת אימות לא ידועה')
                self.logger.error(f"שגיאת אימות: {error_message}")
                self.logger.error("וודא שהמשתמש והסיסמה נכונים ושהסיסמה היא אכן Application Password")
                return False
                
            if response.status_code != 200:
                self.logger.error(f"שגיאה לא צפויה בבדיקת הרשאות. קוד: {response.status_code}")
                self.logger.error(f"תוכן התשובה: {response.text}")
                return False
            
            user_data = response.json()
            
            # בדיקה פשוטה - אם המשתמש הוא super_admin או יש לו גישה לכתובת זו, נאשר
            if user_data.get('is_super_admin', False):
                self.logger.info("המשתמש הוא מנהל על - מאשר הרשאות")
                return True
                
            # בדיקה אם יש למשתמש גישה לפעולות עריכה
            links = user_data.get('_links', {}).get('self', [{}])[0]
            allowed_methods = links.get('targetHints', {}).get('allow', [])
            
            if 'POST' in allowed_methods and 'PUT' in allowed_methods:
                self.logger.info("למשתמש יש הרשאות עריכה - מאשר")
                return True
            
            self.logger.error("למשתמש אין הרשאות מתאימות")
            return False
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"שגיאת רשת בבדיקת הרשאות: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"שגיאה כללית בבדיקת הרשאות: {str(e)}")
            self.logger.error("פרטי השגיאה:", exc_info=True)
            return False

    def optimize_image(self, image_path: str, max_size: tuple = (800, 800)) -> str:
        """
        אופטימיזציה של תמונה - הקטנת גודל ואיכות
        
        Args:
            image_path: נתיב לקובץ התמונה
            max_size: גודל מקסימלי (רוחב, גובה)
            
        Returns:
            str: נתיב לקובץ המותאם
        """
        try:
            # Open image
            img = Image.open(image_path)
            
            # Convert to RGB if needed
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Resize if larger than max_size while maintaining aspect ratio
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save optimized image
            optimized_path = f"{image_path}_optimized.jpg"
            img.save(optimized_path, format='JPEG', quality=85, optimize=True)
            return optimized_path
            
        except Exception as e:
            self.logger.error(f"Error optimizing image: {e}")
            return image_path

    async def upload_image(self, image_path: str) -> Optional[int]:
        """
        העלאת תמונה לשרת WordPress וקבלת המזהה שלה
        
        Args:
            image_path: נתיב לקובץ התמונה
            
        Returns:
            Optional[int]: מזהה התמונה אם ההעלאה הצליחה, None אם נכשלה
        """
        self.logger.info(f"מתחיל העלאת תמונה מ: {image_path}")
        
        try:
            # אופטימיזציה של התמונה
            optimized_path = self.optimize_image(image_path)
            self.logger.info(f"התמונה עברה אופטימיזציה: {optimized_path}")
            
            # הכנת כתובת ה-API להעלאת מדיה
            media_url = f"{settings.WC_STORE_URL}/wp-json/wp/v2/media"
            
            # קבלת פרטי הקובץ
            filename = os.path.basename(optimized_path)
            mime_type, _ = mimetypes.guess_type(optimized_path)
            
            if not mime_type:
                mime_type = 'image/jpeg'  # ברירת מחדל אם לא זוהה סוג הקובץ
            
            self.logger.info(f"פרטי הקובץ - שם: {filename}, סוג: {mime_type}")
            
            # פתיחת הקובץ והכנה להעלאה
            with open(optimized_path, 'rb') as img:
                files = {
                    'file': (filename, img, mime_type)
                }
                
                # קבלת כותרות אימות ל-WordPress
                headers = self._get_wp_auth_header()
                
                self.logger.info(f"שולח בקשת POST ל: {media_url}")
                self.logger.debug(f"כותרות: {headers}")
                
                # העלאת התמונה
                response = requests.post(
                    media_url,
                    headers=headers,
                    files=files,
                    verify=False,
                    timeout=30
                )
                
                self.logger.info(f"קוד תשובה מההעלאה: {response.status_code}")
                self.logger.debug(f"כותרות תשובה: {response.headers}")
                
                if response.status_code == 401:
                    error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                    error_message = error_data.get('message', 'שגיאת אימות לא ידועה')
                    self.logger.error(f"שגיאת אימות: {error_message}")
                    self.logger.error("וודא שהמשתמש והסיסמה נכונים ושהסיסמה היא אכן Application Password")
                    raise Exception(f"שגיאת אימות: {error_message}")
                
                if response.status_code != 201:
                    error_msg = f"נכשלה העלאת התמונה. קוד: {response.status_code}"
                    if response.content:
                        try:
                            error_data = response.json()
                            error_msg += f"\nהודעת שגיאה: {error_data.get('message', 'אין הודעה')}"
                            error_msg += f"\nקוד שגיאה: {error_data.get('code', 'אין קוד')}"
                        except:
                            error_msg += f"\nתוכן התשובה: {response.content}"
                    raise Exception(error_msg)
                
                # קבלת מזהה המדיה מהתשובה
                media_id = response.json().get('id')
                self.logger.info(f"התמונה הועלתה בהצלחה. מזהה מדיה: {media_id}")
                
                return media_id
                
        except Exception as e:
            self.logger.error(f"שגיאה בהעלאת תמונה: {str(e)}")
            return None
        finally:
            # ניקוי קובץ התמונה המותאם
            try:
                if 'optimized_path' in locals() and os.path.exists(optimized_path):
                    os.remove(optimized_path)
                    self.logger.info(f"נוקה קובץ התמונה המותאם: {optimized_path}")
            except Exception as e:
                self.logger.error(f"שגיאה בניקוי קובץ התמונה המותאם: {str(e)}")

    def _extract_image_update_info(self, message: str) -> Optional[Dict[str, Any]]:
        """
        חילוץ מידע לעדכון תמונת מוצר מהודעת המשתמש
        דוגמה: 'עדכן תמונה למוצר חולצה אדומה: /path/to/image.jpg'
        """
        # מחפש את שם המוצר
        product_match = re.search(r'מוצר\s+([^:]+?)(?:\s*:|תמונה חדשה|\s*$)', message)
        
        if not product_match:
            return None
            
        product_name = product_match.group(1).strip()
        
        # מחפש את נתיב התמונה
        if ': ' in message:
            # אם יש נקודותיים, לוקח את כל מה שאחריהן
            image_url = message.split(': ', 1)[1].strip()
        else:
            return None
            
        if not image_url:
            return None
            
        return {
            "product_name": product_name,
            "image_url": image_url
        }

    async def assign_image_to_product(self, media_id: int, product_name: str) -> str:
        """
        שיוך תמונה שהועלתה למוצר
        
        Args:
            media_id: מזהה התמונה שהועלתה
            product_name: שם המוצר לשיוך
            
        Returns:
            str: הודעת הצלחה או שגיאה
        """
        try:
            self.logger.info(f"מנסה לשייך תמונה {media_id} למוצר {product_name}")
            
            # חיפוש המוצר
            product_id = self._find_product_id_by_name(product_name)
            if not product_id:
                self.logger.error(f"לא נמצא מוצר בשם '{product_name}'")
                return f"לא נמצא מוצר בשם '{product_name}'"
            
            self.logger.info(f"נמצא מוצר עם מזהה {product_id}")
            
            # עדכון המוצר עם התמונה החדשה
            data = {
                'images': [{'id': media_id}]
            }
            
            self.logger.info(f"שולח בקשת עדכון לשיוך תמונה. נתונים: {data}")
            
            response = self.wcapi.put(f'products/{product_id}', data)
            self.logger.info(f"קוד תשובה: {response.status_code}")
            self.logger.debug(f"תוכן תשובה: {response.text}")
            
            if response.status_code == 200:
                updated_product = response.json()
                if not updated_product.get('images'):
                    self.logger.error("התמונה לא נשמרה למרות קוד תשובה 200")
                    return "שגיאה: התמונה לא נשמרה למרות שהפעולה הצליחה"
                    
                self.logger.info(f"התמונה שויכה בהצלחה. פרטי המוצר המעודכן: {updated_product}")
                return f"התמונה שויכה בהצלחה למוצר '{product_name}'"
            else:
                error_msg = f"שגיאה בשיוך התמונה למוצר: {response.status_code}"
                if response.content:
                    try:
                        error_data = response.json()
                        error_msg += f"\nהודעת שגיאה: {error_data.get('message', 'אין הודעה')}"
                    except:
                        error_msg += f"\nתוכן התשובה: {response.content}"
                self.logger.error(error_msg)
                return error_msg
                
        except Exception as e:
            error_msg = f"שגיאה בשיוך התמונה למוצר: {str(e)}"
            self.logger.error(error_msg)
            return error_msg

    async def update_product_image(self, product_name: str, image_path: str) -> str:
        """
        מעלה תמונה ומשייכת אותה למוצר בפעולה אחת
        
        Args:
            product_name: שם המוצר
            image_path: נתיב לקובץ התמונה
            
        Returns:
            str: הודעת הצלחה או שגיאה
        """
        try:
            self.logger.info(f"מתחיל תהליך עדכון תמונה למוצר '{product_name}' מהקובץ: {image_path}")
            
            # בדיקה אם הקובץ קיים
            if not os.path.exists(image_path):
                error_msg = f"קובץ התמונה לא קיים: {image_path}"
                self.logger.error(error_msg)
                return error_msg
            
            # בדיקה אם המוצר קיים
            product_id = self._find_product_id_by_name(product_name)
            if not product_id:
                error_msg = f"לא נמצא מוצר בשם '{product_name}'"
                self.logger.error(error_msg)
                return error_msg
            
            self.logger.info(f"נמצא מוצר עם מזהה {product_id}, מתחיל העלאת תמונה")

            # העלאת התמונה באמצעות הפונקציה upload_image
            media_id = await self.upload_image(image_path)
            
            if not media_id:
                error_msg = "נכשלה העלאת התמונה"
                self.logger.error(error_msg)
                return error_msg
            
            self.logger.info(f"התמונה הועלתה בהצלחה. מזהה: {media_id}")
            
            # עדכון המוצר עם התמונה החדשה
            update_data = {
                'images': [{'id': media_id}]
            }
            
            self.logger.info(f"מעדכן מוצר {product_id} עם תמונה {media_id}")
            
            update_response = self.wcapi.put(f"products/{product_id}", update_data)
            self.logger.info(f"תשובה מעדכון המוצר: {update_response.status_code}")
            
            if update_response.status_code == 200:
                updated_product = update_response.json()
                if not updated_product.get('images'):
                    error_msg = "התמונה לא נשמרה למרות קוד תשובה 200"
                    self.logger.error(error_msg)
                    return error_msg
                
                self.logger.info(f"התמונה שויכה בהצלחה למוצר. פרטי המוצר המעודכן: {updated_product}")
                return f"התמונה הועלתה ושויכה בהצלחה למוצר '{product_name}'"
            else:
                error_msg = f"שגיאה בשיוך התמונה למוצר. קוד: {update_response.status_code}"
                if update_response.content:
                    try:
                        error_data = update_response.json()
                        error_msg += f"\nהודעת שגיאה: {error_data.get('message', 'אין הודעה')}"
                    except:
                        error_msg += f"\nתוכן התשובה: {update_response.content}"
                self.logger.error(error_msg)
                return error_msg
            
        except Exception as e:
            error_msg = f"שגיאה בעדכון תמונת המוצר: {str(e)}"
            self.logger.error(error_msg)
            return error_msg

    async def handle_message(self, user_message: str) -> str:
        """
        טיפול בהודעות משתמש וניתוב לפונקציה המתאימה
        """
        message_lower = user_message.lower()
        
        # העלאת תמונה
        if "העלה תמונה" in message_lower:
            # מחפש נתיב או URL של תמונה בהודעה
            image_match = re.search(r'(?:העלה תמונה|תמונה חדשה):\s*(.+?)(?:\s*$)', user_message)
            if image_match:
                image_path = image_match.group(1).strip()
                media_id = await self.upload_image(image_path)
                if media_id:
                    return f"התמונה הועלתה בהצלחה! מזהה התמונה: {media_id}\nכעת תוכל לשייך אותה למוצר על ידי הפקודה: 'שייך תמונה {media_id} למוצר [שם המוצר]'"
                else:
                    return "נכשלה העלאת התמונה. אנא נסה שנית."
            else:
                return "לא הצלחתי להבין את נתיב התמונה. נא לציין את הנתיב או ה-URL, לדוגמה: 'העלה תמונה: /path/to/image.jpg'"
        
        # שיוך תמונה למוצר
        elif "שייך תמונה" in message_lower:
            # מחפש מזהה תמונה ושם מוצר בהודעה
            assign_match = re.search(r'שייך תמונה\s+(\d+)\s+למוצר\s+(.+?)(?:\s*$)', user_message)
            if assign_match:
                media_id = int(assign_match.group(1))
                product_name = assign_match.group(2).strip()
                return await self.assign_image_to_product(media_id, product_name)
            else:
                return "לא הצלחתי להבין את פרטי השיוך. נא להשתמש בפורמט: 'שייך תמונה [מזהה] למוצר [שם המוצר]'"
        
        # עדכון תמונה ראשית
        if "עדכן תמונה" in message_lower:
            update_data = self._extract_image_update_info(user_message)
            if update_data:
                return self.update_product_image(update_data["product_name"], update_data["image_url"])
            else:
                return "לא הצלחתי להבין את פרטי העדכון. נא לציין שם מוצר וכתובת תמונה, לדוגמה: 'עדכן תמונה למוצר חולצה אדומה: https://example.com/image.jpg'"
        
        # עדכון גלריית תמונות
        elif "עדכן גלריה" in message_lower:
            update_data = self._extract_gallery_update_info(user_message)
            if update_data:
                return self.update_product_gallery(update_data["product_name"], update_data["image_urls"])
            else:
                return "לא הצלחתי להבין את פרטי העדכון. נא לציין שם מוצר וכתובות תמונות מופרדות בפסיקים, לדוגמה: 'עדכן גלריה למוצר חולצה אדומה: https://example.com/image1.jpg, https://example.com/image2.jpg'"
        
        # עדכון שם מוצר
        if "שנה שם" in message_lower or "עדכן שם" in message_lower:
            update_data = self._extract_name_update_info(user_message)
            if update_data:
                return self.update_product_name(update_data["old_name"], update_data["new_name"])
            else:
                return "לא הצלחתי להבין את פרטי העדכון. נא לציין שם מוצר נוכחי ושם חדש, לדוגמה: 'שנה שם מוצר חולצה כתומה לחולצה אדומה'"
        
        # עדכון תיאור מוצר
        elif "עדכן תיאור" in message_lower or "שנה תיאור" in message_lower:
            update_data = self._extract_description_update_info(user_message)
            if update_data:
                return self.update_product_description(update_data["product_name"], update_data["new_description"])
            else:
                return "לא הצלחתי להבין את פרטי העדכון. נא לציין שם מוצר ותיאור חדש, לדוגמה: 'עדכן תיאור למוצר חולצה כתומה: חולצת כותנה איכותית'"
        
        # עדכון קטגוריה
        elif "קטגוריה" in message_lower:
            update_data = self._extract_category_update_info(user_message)
            if update_data:
                return self.update_product_category(update_data["product_name"], update_data["category_name"])
            else:
                return "לא הצלחתי להבין את פרטי העדכון. נא לציין שם מוצר וקטגוריה, לדוגמה: 'הוסף את המוצר חולצה כתומה לקטגוריה ביגוד'"

        # יצירת מוצר
        elif "הוסף מוצר" in message_lower:
            product_data = self._extract_product_info(user_message)
            if product_data:
                return self.create_product(product_data)
            else:
                return "לא הצלחתי להבין את פרטי המוצר. נא לציין שם ומחיר, לדוגמה: 'הוסף מוצר חדש בשם חולצה במחיר 70'"
        
        # עדכון מחיר
        elif any(phrase in message_lower for phrase in ["עדכן מחיר", "שנה מחיר", "מחיר חדש"]):
            update_data = self._extract_price_update_info(user_message)
            if update_data:
                return self.update_product_price(update_data["product_name"], update_data["new_price"])
            else:
                return "לא הצלחתי להבין את פרטי העדכון. נא לציין שם מוצר ומחיר חדש, לדוגמה: 'עדכן מחיר למוצר חולצה כתומה ל-199'"
        
        # עדכון מלאי
        elif "עדכן מלאי" in message_lower or "שנה סטטוס" in message_lower:
            stock_data = self._extract_stock_update_info(user_message)
            if stock_data:
                return self.update_product_stock(stock_data["product_name"], stock_data["stock_status"])
            else:
                return "לא הצלחתי להבין את פרטי העדכון. נא לציין שם מוצר וסטטוס חדש, לדוגמה: 'עדכן מלאי למוצר חולצה כתומה לאזל מהמלאי'"
        
        # מחיקת מוצר
        elif "מחק מוצר" in message_lower or "הסר מוצר" in message_lower:
            product_match = re.search(r'(?:מחק|הסר)\s+מוצר\s+(.+?)(?:\s+$|$)', user_message)
            if product_match:
                return self.delete_product(product_match.group(1).strip())
            else:
                return "לא הצלחתי להבין איזה מוצר למחוק. נא לציין שם מוצר, לדוגמה: 'מחק מוצר חולצה כתומה'"
        
        # יצירת קופון
        elif "צור קופון" in message_lower or "קופון חדש" in message_lower:
            coupon_data = self._extract_coupon_info(user_message)
            if coupon_data:
                return self.create_coupon(coupon_data)
            else:
                return (
                    "לא הצלחתי להבין את פרטי הקופון. נא לציין:\n"
                    "1. סכום או אחוז הנחה\n"
                    "2. קוד קופון (אופציונלי)\n\n"
                    "דוגמאות:\n"
                    "• 'צור קופון של 20 אחוז קוד קופון SUMMER2024'\n"
                    "• 'צור קופון של 50 שקל קוד קופון FIXED50'\n"
                    "• 'צור קופון של 30 אחוז' (קוד יווצר אוטומטית)"
                )
        
        # פעולה לא מזוהה
        else:
            return (
                "סוכן הפעולות: אני יכול לעזור עם:\n"
                "1. הוספת מוצר חדש (לדוגמה: 'הוסף מוצר חדש בשם חולצה במחיר 70')\n"
                "2. עדכון מחיר מוצר (לדוגמה: 'עדכן מחיר למוצר חולצה כתומה ל-199')\n"
                "3. עדכון מלאי (לדוגמה: 'עדכן מלאי למוצר חולצה כתומה לאזל מהמלאי')\n"
                "4. מחיקת מוצר (לדוגמה: 'מחק מוצר חולצה כתומה')\n"
                "5. יצירת קופון (לדוגמה: 'צור קופון של 20 אחוז')\n"
                "6. עדכון שם מוצר (לדוגמה: 'שנה שם מוצר חולצה כתומה לחולצה אדומה')\n"
                "7. עדכון תיאור מוצר (לדוגמה: 'עדכן תיאור למוצר חולצה כתומה: חולצת כותנה איכותית')\n"
                "8. עדכון קטגוריה (לדוגמה: 'הוסף את המוצר חולצה כתומה לקטגוריה ביגוד')\n"
                "9. עדכון תמונה ראשית (לדוגמה: 'עדכן תמונה למוצר חולצה אדומה: https://example.com/image.jpg')\n"
                "10. עדכון גלריית תמונות (לדוגמה: 'עדכן גלריה למוצר חולצה אדומה: https://example.com/image1.jpg, https://example.com/image2.jpg')"
            ) 

    def _find_product_id_by_name(self, product_name: str) -> Optional[int]:
        """
        מציאת מזהה מוצר לפי שם
        
        Args:
            product_name: שם המוצר לחיפוש
            
        Returns:
            Optional[int]: מזהה המוצר אם נמצא, None אם לא נמצא
        """
        try:
            # חיפוש המוצר לפי שם
            products = self.wcapi.get("products", params={"search": product_name}).json()
            if not products:
                return None
            
            # מציאת התאמה מדויקת
            for product in products:
                if product["name"].lower() == product_name.lower():
                    return product["id"]
            
            return None
            
        except Exception as e:
            logger.error(f"שגיאה בחיפוש מוצר: {str(e)}")
            return None 