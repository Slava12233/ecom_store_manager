"""
Telegram Bot - מאפשר אינטראקציה עם המערכת דרך טלגרם
"""
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from core.config import settings
from orchestrator import Orchestrator
from utils.logger import logger, log_action, setup_logger
from utils.message_manager import MessageManager
import re
import os
import aiohttp
import asyncio
from datetime import datetime

# הגדרת קבועים
TEMP_IMAGES_DIR = "temp_images"
CHOOSING_PRODUCT, UPLOADING_PHOTO = range(2)

class Bot:
    def __init__(self):
        """Initialize bot with required components."""
        self.orchestrator = Orchestrator()
        self.message_manager = MessageManager()
        
        # יצירת תיקיית תמונות זמניות אם לא קיימת
        if not os.path.exists(TEMP_IMAGES_DIR):
            os.makedirs(TEMP_IMAGES_DIR)
            logger.info(f"נוצרה תיקיית תמונות זמניות: {TEMP_IMAGES_DIR}")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        user = update.effective_user
        logger.info(f"User {user.id} performed start_command with params: username={user.username}, first_name={user.first_name}")
        
        welcome_message = (
            f"שלום {user.first_name}! 👋\n"
            "אני כאן כדי לעזור לך לנהל את חנות ה-WooCommerce שלך.\n\n"
            f"{self.message_manager.get_help_message('products')}\n\n"
            "שלח /help לקבלת רשימה מלאה של הפקודות הזמינות."
        )
        
        await update.message.reply_text(welcome_message)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /help is issued."""
        # קבלת קטגוריה ספציפית אם צוינה
        args = context.args
        category = args[0] if args else None
        
        help_message = self.message_manager.get_help_message(category)
        await update.message.reply_text(help_message)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming text messages."""
        user = update.effective_user
        message = update.message.text
        
        try:
            # שליחת הודעת עיבוד
            processing_message = self.message_manager.get_status_message('processing')
            await update.message.reply_text(processing_message)
            
            # שליחת ההודעה ל-Orchestrator וקבלת תשובה
            response = await self.orchestrator.handle_user_message(message)
            
            # שליחת התשובה למשתמש
            await update.message.reply_text(response)
            
            logger.info(f"User {user.id} message handled successfully: {message[:50]}...")
            
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            error_message = self.message_manager.get_error_message('general_error')
            await update.message.reply_text(error_message)

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle incoming photos."""
        try:
            user = update.effective_user
            photo = update.message.photo[-1]  # Get the largest photo
            
            # יצירת שם קובץ ייחודי
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"{user.id}_{timestamp}.jpg"
            local_path = os.path.join(TEMP_IMAGES_DIR, file_name)
            
            # הורדת התמונה
            photo_file = await context.bot.get_file(photo.file_id)
            await photo_file.download_to_drive(local_path)
            
            # שמירת הנתיב בקונטקסט
            context.user_data['temp_image_path'] = local_path
            
            # בקשת שם המוצר מהמשתמש
            await update.message.reply_text(
                self.message_manager.get_status_message('waiting_for_input') + "\n" +
                "לאיזה מוצר לשייך את התמונה?"
            )
            
            return CHOOSING_PRODUCT
            
        except Exception as e:
            logger.error(f"Error handling photo: {str(e)}")
            error_message = self.message_manager.get_error_message('general_error')
            await update.message.reply_text(error_message)
            return ConversationHandler.END

    async def handle_product_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle product name after photo upload."""
        try:
            user = update.effective_user
            product_name = update.message.text
            local_path = context.user_data.get('temp_image_path')
            
            if not local_path or not os.path.exists(local_path):
                error_message = self.message_manager.get_error_message('not_found', item='תמונה')
                await update.message.reply_text(error_message)
                return ConversationHandler.END
            
            logger.info(f"User {user.id} assigning photo to product: {product_name}")
            
            # עדכון התמונה למוצר
            try:
                result = await self.orchestrator.update_product_image(product_name, local_path)
                await update.message.reply_text(result)
            except Exception as e:
                logger.error(f"Error updating product image: {str(e)}")
                error_message = self.message_manager.get_error_message('general_error')
                await update.message.reply_text(error_message)
            
            # ניקוי הקובץ הזמני
            try:
                os.remove(local_path)
                logger.info(f"Temporary file {local_path} deleted successfully")
            except Exception as e:
                logger.warning(f"Could not delete temporary file {local_path}: {str(e)}")
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error handling product name: {str(e)}")
            error_message = self.message_manager.get_error_message('general_error')
            await update.message.reply_text(error_message)
            return ConversationHandler.END

    def run(self):
        """Start the bot."""
        try:
            # יצירת אפליקציה
            application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN.get_secret_value()).build()
            
            # הוספת הנדלרים
            application.add_handler(CommandHandler("start", self.start))
            application.add_handler(CommandHandler("help", self.help))
            
            # הנדלר לטיפול בתמונות
            conv_handler = ConversationHandler(
                entry_points=[MessageHandler(filters.PHOTO, self.handle_photo)],
                states={
                    CHOOSING_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_product_name)]
                },
                fallbacks=[],
            )
            application.add_handler(conv_handler)
            
            # הנדלר לטיפול בהודעות טקסט
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            
            # הפעלת הבוט
            application.run_polling()

        except Exception as e:
            logger.critical(f"שגיאה קריטית בהפעלת הבוט", exc_info=e)
            print(f"❌ שגיאה בהפעלת הבוט: {str(e)}")

def main() -> None:
    """הפעלת הבוט"""
    bot = Bot()
    bot.run()

if __name__ == '__main__':
    main() 