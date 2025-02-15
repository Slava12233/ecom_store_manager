"""
Telegram Bot - מאפשר אינטראקציה עם המערכת דרך טלגרם
"""
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from core.config import settings
from orchestrator import Orchestrator

# הגדרת לוגר
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# יצירת מופע של ה-Orchestrator
orchestrator = Orchestrator()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """שליחת הודעת פתיחה כשמשתמש מתחיל שיחה"""
    user = update.effective_user
    welcome_message = (
        f"שלום {user.first_name}! 👋\n\n"
        "אני העוזר האישי שלך לניהול החנות. אני יכול לעזור לך עם:\n"
        "📊 מידע על מוצרים ומכירות\n"
        "🛍️ יצירה ועדכון של מוצרים\n"
        "🎫 ניהול קופונים והנחות\n"
        "📈 מחקר שוק ומתחרים\n\n"
        "פשוט כתוב/י לי מה את/ה צריך/ה!"
    )
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """שליחת הודעת עזרה"""
    help_text = (
        "הנה כמה דוגמאות לפקודות שאני מבין:\n\n"
        "📦 מוצרים:\n"
        "• תראה לי את המוצרים\n"
        "• הוסף מוצר חדש בשם X במחיר Y\n\n"
        "💰 מכירות:\n"
        "• הצג דוח מכירות\n"
        "• הצג דוח מכירות לחודש האחרון\n\n"
        "🎫 קופונים:\n"
        "• מה הקופונים הפעילים?\n"
        "• צור קופון של X אחוז\n"
        "• צור קופון של Y שקל\n\n"
        "📊 מחקר שוק:\n"
        "• תבדוק מחקר על מתחרים\n"
        "• השוואת מחירים למוצרים דומים"
    )
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """טיפול בהודעות טקסט מהמשתמש"""
    try:
        # קבלת הודעת המשתמש
        user_message = update.message.text
        
        # שליחת ההודעה ל-Orchestrator וקבלת תשובה
        response = orchestrator.handle_user_message(user_message)
        
        # שליחת התשובה למשתמש
        await update.message.reply_text(response)
        
    except Exception as e:
        error_message = f"סליחה, נתקלתי בשגיאה: {str(e)}"
        logger.error(f"Error handling message: {str(e)}")
        await update.message.reply_text(error_message)

def main() -> None:
    """הפעלת הבוט"""
    try:
        # יצירת אפליקציית הבוט
        application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN.get_secret_value()).build()

        # הוספת handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        # הפעלת הבוט
        print("🤖 הבוט מופעל ומוכן לשימוש!")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        print(f"❌ שגיאה בהפעלת הבוט: {str(e)}")

if __name__ == '__main__':
    main() 