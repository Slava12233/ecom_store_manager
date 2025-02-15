"""
Telegram Bot - מאפשר אינטראקציה עם המערכת דרך טלגרם
"""
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from core.config import settings
from orchestrator import Orchestrator
from utils.logger import logger, log_action, setup_logger
import re
import os
import aiohttp
import asyncio
from datetime import datetime
from agents.action_agent import ActionAgent

# הגדרת קבועים
TEMP_IMAGES_DIR = "temp_images"
CHOOSING_PRODUCT, UPLOADING_PHOTO = range(2)

class Bot:
    def __init__(self):
        """Initialize bot with required components."""
        self.action_agent = ActionAgent()
        
        # יצירת תיקיית תמונות זמניות אם לא קיימת
        if not os.path.exists(TEMP_IMAGES_DIR):
            os.makedirs(TEMP_IMAGES_DIR)
            logger.info(f"נוצרה תיקיית תמונות זמניות: {TEMP_IMAGES_DIR}")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        user = update.effective_user
        logger.info(f"User {user.id} performed start_command with params: username={user.username}, first_name={user.first_name}")
        await update.message.reply_text(
            f"שלום {user.first_name}! 👋\n"
            "אני כאן כדי לעזור לך לנהל את חנות ה-WooCommerce שלך.\n"
            "אתה יכול לשלוח לי הודעות טקסט עם בקשות כמו:\n"
            "• הוספת מוצר חדש\n"
            "• עדכון מחירים\n"
            "• יצירת קופונים\n"
            "• ועוד...\n\n"
            "אתה יכול גם לשלוח לי תמונה כדי לעדכן תמונת מוצר."
        )

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /help is issued."""
        await update.message.reply_text(
            "הנה מה שאני יכול לעזור לך איתו:\n\n"
            "1. ניהול מוצרים:\n"
            "   • הוספת מוצר חדש\n"
            "   • עדכון מחירים\n"
            "   • עדכון מלאי\n"
            "   • עדכון תמונות\n\n"
            "2. ניהול קופונים:\n"
            "   • יצירת קופונים חדשים\n"
            "   • הגדרת הנחות\n\n"
            "3. עדכון תמונות:\n"
            "   • שלח לי תמונה ואציין לאיזה מוצר לשייך אותה\n\n"
            "פשוט שלח לי הודעת טקסט עם הבקשה שלך!"
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming text messages."""
        user = update.effective_user
        message = update.message.text
        
        # שליחת ההודעה ל-ActionAgent וקבלת תשובה
        response = self.action_agent.handle_message(message)
        
        logger.info(f"User {user.id} sent message: {message}")
        logger.info(f"Bot response: {response}")
        
        await update.message.reply_text(response)

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle incoming photos."""
        try:
            user = update.effective_user
            
            # בדיקת הרשאות WordPress
            has_permissions = await self.action_agent._check_wp_permissions()
            if not has_permissions:
                await update.message.reply_text(
                    "שגיאה: אין הרשאות מתאימות ב-WordPress.\n"
                    "אנא ודא שהמשתמש הוא מנהל או עורך ושהסיסמה תקינה."
                )
                return ConversationHandler.END
            
            photo_file = await update.message.photo[-1].get_file()
            
            # וידוא שתיקיית התמונות הזמניות קיימת
            if not os.path.exists(TEMP_IMAGES_DIR):
                os.makedirs(TEMP_IMAGES_DIR, exist_ok=True)
                logger.info(f"נוצרה תיקיית תמונות זמניות: {TEMP_IMAGES_DIR}")
            
            # בדיקת הרשאות כתיבה
            if not os.access(TEMP_IMAGES_DIR, os.W_OK):
                logger.error(f"אין הרשאות כתיבה לתיקייה: {TEMP_IMAGES_DIR}")
                await update.message.reply_text("שגיאה: אין הרשאות כתיבה לתיקיית התמונות הזמניות")
                return ConversationHandler.END
            
            # יצירת שם קובץ ייחודי עם תאריך ושעה
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"{timestamp}_{user.id}.jpg"
            local_path = os.path.join(TEMP_IMAGES_DIR, file_name)
            
            logger.info(f"מנסה להוריד תמונה ל: {local_path}")
            
            # הורדת התמונה
            try:
                await photo_file.download_to_drive(local_path)
                if not os.path.exists(local_path):
                    raise FileNotFoundError("הקובץ לא נוצר אחרי ההורדה")
                logger.info(f"התמונה הורדה בהצלחה ל: {local_path}")
            except Exception as e:
                logger.error(f"שגיאה בהורדת התמונה: {str(e)}")
                await update.message.reply_text("שגיאה בהורדת התמונה. אנא נסה שוב.")
                return ConversationHandler.END
            
            # שמירת הנתיב בקונטקסט
            context.user_data['temp_image_path'] = local_path
            
            logger.info(f"User {user.id} performed photo_upload with params: local_path={local_path}, username={user.username}")
            
            # בקשת שם המוצר מהמשתמש
            await update.message.reply_text(
                "קיבלתי את התמונה! 📸\n"
                "לאיזה מוצר לשייך אותה?",
                reply_markup=ReplyKeyboardRemove(),
            )
            
            return CHOOSING_PRODUCT
            
        except Exception as e:
            logger.error(f"שגיאה כללית בטיפול בתמונה: {str(e)}")
            await update.message.reply_text("שגיאה בטיפול בתמונה. אנא נסה שוב.")
            return ConversationHandler.END

    async def handle_product_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle product name after photo upload."""
        try:
            user = update.effective_user
            product_name = update.message.text
            local_path = context.user_data.get('temp_image_path')
            
            if not local_path or not os.path.exists(local_path):
                await update.message.reply_text("מצטער, אך התמונה לא נשמרה כראוי. אנא נסה שוב.")
                return ConversationHandler.END
            
            logger.info(f"User {user.id} performed photo_assigned with params: product_name={product_name}, local_path={local_path}, username={user.username}")
            
            # עדכון התמונה למוצר
            try:
                result = await self.action_agent.update_product_image(product_name, local_path)
                await update.message.reply_text(result)
            except Exception as e:
                logger.error(f"שגיאה בעדכון תמונת המוצר: {str(e)}")
                await update.message.reply_text(f"שגיאה בעדכון תמונת המוצר: {str(e)}")
            
            # ניקוי הקובץ הזמני
            try:
                os.remove(local_path)
                logger.info(f"הקובץ הזמני {local_path} נמחק בהצלחה")
            except Exception as e:
                logger.warning(f"לא הצלחתי למחוק את הקובץ הזמני {local_path}: {str(e)}")
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"שגיאה כללית בטיפול בשם המוצר: {str(e)}")
            await update.message.reply_text("שגיאה בטיפול בבקשה. אנא נסה שוב.")
            return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel the conversation."""
        # ניקוי קובץ זמני אם קיים
        local_path = context.user_data.get('temp_image_path')
        if local_path and os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception as e:
                logger.warning(f"לא הצלחתי למחוק את הקובץ הזמני {local_path}: {str(e)}")
        
        await update.message.reply_text(
            "בוטל! 🚫\nאתה יכול להתחיל מחדש בכל עת.",
            reply_markup=ReplyKeyboardRemove()
        )
        
        return ConversationHandler.END

    def run(self):
        """Run the bot."""
        try:
            # יצירת האפליקציה
            application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN.get_secret_value()).build()

            # הגדרת ה-handlers
            photo_conv_handler = ConversationHandler(
                entry_points=[MessageHandler(filters.PHOTO, self.handle_photo)],
                states={
                    CHOOSING_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_product_name)],
                },
                fallbacks=[CommandHandler("cancel", self.cancel)],
            )

            # הוספת handlers
            application.add_handler(CommandHandler("start", self.start))
            application.add_handler(CommandHandler("help", self.help))
            application.add_handler(photo_conv_handler)
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

            # הפעלת הבוט
            logger.info("🤖 הבוט מופעל ומוכן לשימוש!")
            application.run_polling(allowed_updates=Update.ALL_TYPES)

        except Exception as e:
            logger.critical(f"שגיאה קריטית בהפעלת הבוט", exc_info=e)
            print(f"❌ שגיאה בהפעלת הבוט: {str(e)}")

def main() -> None:
    """הפעלת הבוט"""
    bot = Bot()
    bot.run()

if __name__ == '__main__':
    main() 