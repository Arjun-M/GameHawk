from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputTextMessageContent, InlineQueryResultArticle
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, InlineQueryHandler
import uuid
from xo import XOGameManager
import os

token = os.getenv('TOKEN')

game_manager = XOGameManager()

def start(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("Play X-O", callback_data='game_xo')]]
    update.message.reply_text("Welcome to *Game Hawk Bot*,\n\nYour gateway to an exciting world of *incredible games* on Telegram.",parse_mode = "Markdown" , reply_markup=InlineKeyboardMarkup(keyboard))

def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == 'game_xo':
        game_manager.choose_mode(query)
    elif data == 'xo_computer':
        game_manager.choose_symbol(query, context)
    elif data in ['choose_X', 'choose_O']:
        game_manager.set_player_symbol(query, context, data)
    elif data.startswith('level_'):
        game_manager.set_difficulty(query, context, data)
    elif data.startswith('rounds_'):
        game_manager.start_game(query, context, data)
    elif data.startswith('invite_accept_'):
        game_manager.accept_invite(query, context, data)

def inline_query(update: Update, context: CallbackContext):
    game_manager.handle_inline_query(update, context)

def move(update: Update, context: CallbackContext):
    game_manager.player_move(update, context)

def friendmove(update: Update, context: CallbackContext):
    game_manager.friend_move(update, context)

def main():
    updater = Updater( token , use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(InlineQueryHandler(inline_query))
    dp.add_handler(CallbackQueryHandler(button, pattern='^game_xo$|^xo_computer$|^choose_X$|^choose_O$|^level_.*$|^rounds_.*$|^invite_accept_.*$'))
    dp.add_handler(CallbackQueryHandler(move, pattern='^move_'))
    dp.add_handler(CallbackQueryHandler(friendmove, pattern='^friendmove_.*$'))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
