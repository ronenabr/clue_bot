from telegram.ext import Updater, CommandHandler
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

import logging
import random

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  level=logging.INFO)

server_updater = Updater(token='507313417:AAGRTVRJJ6hA_c_TXZzM-x3bIz4jNV-MWqA')
dispatcher = server_updater.dispatcher


from functools import wraps

BOT_LINK = "http://t.me/clue_test_bot"

def group_only(func):
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        print("In wrapper")
        user_id = update.effective_user.id
        chat_id = update.message.chat_id

        if user_id == chat_id:
            bot.send_message(chat_id=update.message.chat_id, text="You can post this command only from game group")
            return
        return func(bot, update, *args, **kwargs)
    return wrapped

def user_only(func):
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        user_id = update.effective_user.id
        chat_id = update.message.chat_id

        if user_id != chat_id:
            bot.send_message(chat_id=update.message.chat_id, text="In order to post this command you must address the bot directly.\nTry resending in %s" % (BOT_LINK))
            return
        return func(bot, update, *args, **kwargs)
    return wrapped



update_history = []
def test(bot, update):
    update_history.append(update)
    updates = bot.get_updates()
    print("Starting")
    print([u.message.text for u in updates])    
    bot.send_message(chat_id=update.message.chat_id, text="I'm a bot, please talk to me!")
dispatcher.add_handler(CommandHandler('test', test))

@group_only
def intro(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Hello everybody. Welcome to `THE CLUE`. Please everybody say /hi")


active_users = {}
tools = ["Hose", "Club", "Sword"]
rooms = ["Badroom", "Kitchen", "Closets"]
murder_info = None 

@group_only
def register_user(bot, update):
    fullname = update.effective_user.full_name
    uid = update.effective_user.id 
    bot.send_message(chat_id=update.message.chat_id, text="Hi, %s, welcome to our little game" % (fullname) )
    active_users[uid] = fullname

@group_only
def make_murder(bot, update):
    #TODO: kill works onlu once a game. 
    global murder_info
    murder_info = (random.choice(tools), random.choice(rooms), random.choice(list(active_users.keys())))
    text = "Someone commited a murder! Alas! \nHe used one of the follwing tools:\n\t\t{0} \n" \
    "It was in room:\n\t\t{1} \n" \
    "And the murdrer might be...\n\t\t{2}".format("\n\t\t".join(tools),"\n\t\t".join(rooms),"\n\t\t".join(active_users.values()))
    bot.send_message(chat_id=update.message.chat_id, text=text)
    bot.send_message(chat_id=update.message.chat_id, text="In order to guess, send me /guess privatly.")

reply_keyboard = [['Age', 'Favourite colour'],
                  ['Number of siblings', 'Something else...'],
                  ['Done']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

@user_only
def guess(bot, update):
    print(update.message.chat_id ,update.effective_user.id)
    if update.message.chat_id == update.effective_user.id:
        if not update.effective_user.id in active_users:
            bot.send_message(chat_id=update.message.chat_id, text="I don't know you. Please join a game")
        update.message.reply_text(
         "Hi! My name is Doctor Botter. I will hold a more complex conversation with you. "
          "Why don't you tell me something about yourself?",
          reply_markup=markup)
    else:
        bot.send_message(chat_id=update.message.chat_id, text="In order to make a guess, send me a private message at {0}".format(BOT_LINK))

@group_only
def endgame(bot, update):
    pass #TODO: implement

dispatcher.add_handler(CommandHandler('intro', intro))
dispatcher.add_handler(CommandHandler('hi', register_user))
dispatcher.add_handler(CommandHandler('kill', make_murder))
dispatcher.add_handler(CommandHandler('guess', guess))

server_updater.start_polling()
server_updater.idle()