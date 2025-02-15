# E-commerce Store Manager

מערכת חכמה לניהול חנות אי-קומרס המבוססת על AI.

## תכונות עיקריות

- אינטגרציה עם WooCommerce
- סוכני AI חכמים לניהול המוצרים והמכירות
- ממשק Telegram לניהול מרחוק
- ניתוח מתקדם של נתוני מכירות

## דרישות מערכת

- Python 3.8+
- pip
- וירטואלית env (מומלץ)

## התקנה

1. שכפל את המאגר:
```bash
git clone https://github.com/Slava12233/ecom_store_manager.git
cd ecom_store_manager
```

2. צור והפעל סביבה וירטואלית:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# או
venv\Scripts\activate  # Windows
```

3. התקן את החבילות הנדרשות:
```bash
pip install -r requirements.txt
```

4. העתק את קובץ `.env.example` ל-`.env` והגדר את המשתנים הנדרשים:
```bash
cp .env.example .env
```

## הגדרת בוט טלגרם

1. צור בוט חדש בטלגרם:
   - פתח שיחה עם [@BotFather](https://t.me/BotFather)
   - שלח את הפקודה `/newbot`
   - עקוב אחר ההוראות לבחירת שם ומזהה לבוט
   - העתק את טוקן הבוט שתקבל

2. הוסף את טוקן הבוט לקובץ `.env`:
```
TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
```

## הפעלה

יש שתי דרכים להפעיל את המערכת:

### 1. הפעלת שרת REST API:
```bash
python src/main.py
```
הגישה לממשק תהיה זמינה ב-`http://localhost:8000`

### 2. הפעלת בוט טלגרם:
```bash
python src/bot.py
```

## שימוש בבוט

1. התחל שיחה עם הבוט בטלגרם
2. שלח `/start` לקבלת הודעת פתיחה
3. שלח `/help` לקבלת רשימת הפקודות האפשריות

דוגמאות לפקודות:
- `תראה לי את המוצרים`
- `הצג דוח מכירות`
- `צור קופון של 20 אחוז`
- `הוסף מוצר חדש בשם חולצה במחיר 99`

## פיתוח

1. התקן חבילות פיתוח נוספות:
```bash
pip install -r requirements-dev.txt  # אם קיים
```

2. הפעל בדיקות:
```bash
pytest
```

## רישיון

MIT 