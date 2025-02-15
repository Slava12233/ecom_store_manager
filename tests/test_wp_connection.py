import os
import sys
import requests
import base64
import json
from dotenv import load_dotenv

# טעינת משתני הסביבה
load_dotenv(override=True)  # מוסיף override=True כדי לוודא טעינה מחדש

def test_wp_connection():
    # בדיקת חיבור בסיסית
    try:
        wp_url = os.getenv('WC_STORE_URL')
        wp_user = os.getenv('WP_USERNAME')
        wp_pass = os.getenv('WP_PASSWORD')
        
        # הדפסת הסיסמה המוסתרת חלקית לבדיקה
        if wp_pass:
            masked_pass = wp_pass[:4] + '*' * (len(wp_pass) - 8) + wp_pass[-4:]
            print(f"סיסמה שנטענה (מוסתרת): {masked_pass}")
        
        response = requests.get(wp_url, verify=False)
        print(f"בדיקת חיבור בסיסית: {response.status_code}")
    except Exception as e:
        print(f"שגיאה בבדיקת חיבור בסיסית: {str(e)}")

    # בדיקת הרשאות
    try:
        check_url = f"{wp_url}/wp-json/wp/v2/users/me"
        credentials = f"{wp_user}:{wp_pass}"
        auth_string = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        
        headers = {
            'Authorization': f'Basic {auth_string}',
            'Accept': 'application/json'
        }
        
        print(f"\nבודק URL: {check_url}")
        print(f"משתמש: {wp_user}")
        print(f"כותרות: {headers}")
        
        response = requests.get(
            check_url,
            headers=headers,
            verify=False,
            timeout=10
        )
        
        print(f"\nקוד תשובה: {response.status_code}")
        print(f"כותרות תשובה: {dict(response.headers)}")
        
        if response.status_code == 200:
            user_data = response.json()
            print("\n=== מידע על המשתמש ===")
            print(f"מזהה: {user_data.get('id')}")
            print(f"שם משתמש: {user_data.get('name')}")
            print(f"תפקידים: {user_data.get('roles', [])}")
            print(f"האם מנהל על: {user_data.get('is_super_admin', False)}")
            print(f"\nתוכן מלא: {json.dumps(user_data, indent=2, ensure_ascii=False)}")
        else:
            print(f"תוכן תשובה: {response.text}")
        
    except Exception as e:
        print(f"שגיאה בבדיקת הרשאות: {str(e)}")

if __name__ == "__main__":
    test_wp_connection() 