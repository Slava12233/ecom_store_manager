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
git clone [repository-url]
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

## הפעלה

הפעל את השרת:
```bash
python src/main.py
```

הגישה לממשק תהיה זמינה ב-`http://localhost:8000`

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