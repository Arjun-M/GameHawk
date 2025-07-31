import logging
from telegram import Update, Sticker, StickerSet
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    ConversationHandler
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
SET_NAME, ADD_STICKERS = range(2)

class StickerBot:
    def __init__(self, token):
        self.updater = Updater(token)
        self.dispatcher = self.updater.dispatcher
        
        # User data structure: {user_id: {'set_name': '', 'set_title': ''}}
        self.user_data = {}
        
        # Setup conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={
                SET_NAME: [MessageHandler(Filters.text & ~Filters.command, self.set_name)],
                ADD_STICKERS: [MessageHandler(Filters.sticker, self.add_sticker)]
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )
        
        self.dispatcher.add_handler(conv_handler)
        self.dispatcher.add_error_handler(self.error_handler)
    
    def start(self, update: Update, context: CallbackContext) -> int:
        """Start the conversation and ask for sticker set name."""
        user = update.message.from_user
        update.message.reply_text(
            "Hi! I'll help you create your own sticker pack.\n\n"
            "Please send me a name for your sticker set (only letters, numbers and underscores).\n\n"
            "Send /cancel to stop."
        )
        
        # Initialize user data
        self.user_data[user.id] = {}
        return SET_NAME
    
    def set_name(self, update: Update, context: CallbackContext) -> int:
        """Store the sticker set name and ask for first sticker."""
        user = update.message.from_user
        set_name = update.message.text.strip()
        
        # Validate set name
        if not set_name.replace('_', '').isalnum():
            update.message.reply_text(
                "Invalid name! Only letters, numbers and underscores are allowed.\n"
                "Please try again."
            )
            return SET_NAME
        
        # Store set name (append _by_botname later)
        self.user_data[user.id]['set_name'] = set_name.lower()
        self.user_data[user.id]['set_title'] = f"{set_name} (by @{context.bot.username})"
        
        update.message.reply_text(
            f"Great! Your sticker set will be named '{set_name}'.\n\n"
            "Now please send me the first sticker for your pack."
        )
        return ADD_STICKERS
    
    def add_sticker(self, update: Update, context: CallbackContext) -> int:
        """Add sticker to the user's pack."""
        user = update.message.from_user
        sticker = update.message.sticker
        
        try:
            # Get the complete set name
            set_name = f"{self.user_data[user.id]['set_name']}_by_{context.bot.username}"
            set_title = self.user_data[user.id]['set_title']
            
            # Check if this is the first sticker
            if 'pack_created' not in self.user_data[user.id]:
                # Create new sticker set
                if sticker.is_animated:
                    context.bot.create_new_sticker_set(
                        user_id=user.id,
                        name=set_name,
                        title=set_title,
                        tgs_sticker=sticker.file_id,
                        emojis=sticker.emoji or '🤔'
                    )
                else:
                    context.bot.create_new_sticker_set(
                        user_id=user.id,
                        name=set_name,
                        title=set_title,
                        png_sticker=sticker.file_id,
                        emojis=sticker.emoji or '🤔'
                    )
                
                self.user_data[user.id]['pack_created'] = True
                update.message.reply_text(
                    f"Sticker pack created!\n\n"
                    f"Name: {set_name}\n"
                    f"Keep sending me stickers to add more to your pack.\n\n"
                    f"Send /cancel when you're done."
                )
            else:
                # Add to existing sticker set
                if sticker.is_animated:
                    context.bot.add_sticker_to_set(
                        user_id=user.id,
                        name=set_name,
                        tgs_sticker=sticker.file_id,
                        emojis=sticker.emoji or '🤔'
                    )
                else:
                    context.bot.add_sticker_to_set(
                        user_id=user.id,
                        name=set_name,
                        png_sticker=sticker.file_id,
                        emojis=sticker.emoji or '🤔'
                    )
                
                update.message.reply_text("Sticker added to your pack!")
            
            return ADD_STICKERS
            
        except Exception as e:
            logger.error(f"Error adding sticker: {e}")
            update.message.reply_text(
                f"Failed to add sticker: {str(e)}\n\n"
                "Please try again or send /cancel to start over."
            )
            return ADD_STICKERS
    
    def cancel(self, update: Update, context: CallbackContext) -> int:
        """Cancel the current operation."""
        user = update.message.from_user
        if user.id in self.user_data:
            set_name = f"{self.user_data[user.id]['set_name']}_by_{context.bot.username}"
            update.message.reply_text(
                f"Operation cancelled.\n\n"
                f"Your sticker pack is available as: {set_name}\n\n"
                f"Send /start to create another pack."
            )
            del self.user_data[user.id]
        else:
            update.message.reply_text("No active operation to cancel.")
        
        return ConversationHandler.END
    
    def error_handler(self, update: Update, context: CallbackContext):
        """Log errors."""
        logger.error(msg="Exception while handling update:", exc_info=context.error)
    
    def run(self):
        """Start the bot."""
        self.updater.start_polling()
        self.updater.idle()

if __name__ == '__main__':
    # Replace with your bot token
    TOKEN = "YOUR_BOT_TOKEN_HERE"
    bot = StickerBot(TOKEN)
    bot.run()
