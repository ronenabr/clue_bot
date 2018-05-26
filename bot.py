from telegram.ext import Updater, CommandHandler, ConversationHandler, RegexHandler, Filters, MessageHandler
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from enum import IntEnum

import logging
import random

from clue import ClueGame



logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  level=logging.INFO)

server_updater = Updater(token='507313417:AAGRTVRJJ6hA_c_TXZzM-x3bIz4jNV-MWqA')
dispatcher = server_updater.dispatcher


from functools import wraps

BOT_LINK = "http://t.me/clue_test_bot"

games = {}
user_to_game = {}


def group_only(func):
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        user_id = update.effective_user.id
        chat_id = update.message.chat_id

        if user_id == chat_id:
            bot.send_message(chat_id=update.message.chat_id, text="You can post this command only from game group")
            return
        if chat_id not in games:
            bot.send_message(chat_id=update.message.chat_id, text="No active game for group")
        return func(games[chat_id], bot, update, *args, **kwargs)

    return wrapped

def user_only(func):
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        user_id = update.effective_user.id
        chat_id = update.message.chat_id

        if user_id != chat_id:
            bot.send_message(chat_id=update.message.chat_id, text="In order to post this command you must address the bot directly.\nTry resending in %s" % (BOT_LINK))
            return
        if user_id not in user_to_game:
            bot.send_message(chat_id=update.message.chat_id, text="No active game for user")
        return func(user_to_game[user_id], user_id, bot, update, *args, **kwargs)
    return wrapped



update_history = []
def test(bot, update):
    update_history.append(update)
    updates = bot.get_updates()
    print("Starting")
    print([u.message.text for u in updates])    
    bot.send_message(chat_id=update.message.chat_id, text="I'm a bot, please talk to me!")
dispatcher.add_handler(CommandHandler('test', test))


def intro(bot, update):
    user_id = update.effective_user.id
    chat_id = update.message.chat_id

    if user_id == chat_id:
        bot.send_message(chat_id=update.message.chat_id, text="You can post this command only from game group")
        return

    bot.send_message(chat_id=update.message.chat_id, text="Hello everybody. Welcome to `THE CLUE`. Please everybody say /hi")

    group_name = update.message.chat.title

    games[chat_id] = ClueGame(chat_id, group_name)
    user_to_game[user_id] = games[chat_id]


@group_only
def register_user(game, bot, update):
    fullname = update.effective_user.full_name
    uid = update.effective_user.id 
    bot.send_message(chat_id=update.message.chat_id, text="Hi, %s, welcome to our little game" % (fullname) )
    user_to_game[uid] = game

    game.register_user(uid, fullname)

@group_only
def make_murder(game, bot, update):
    game.start_game()

    text = "Someone commited a murder! Alas! \nHe used one of the follwing tools:\n\t\t{0} \n" \
    "It was in room:\n\t\t{1} \n" \
    "And the murdrer might be...\n\t\t{2}".format("\n\t\t".join(game._tools),"\n\t\t".join(game._rooms),"\n\t\t".join([str(u) for u in game._suspects]))
    bot.send_message(chat_id=update.message.chat_id, text=text)
    bot.send_message(chat_id=update.message.chat_id, text="In order to guess, send me /guess privatly.")

@user_only
def get_cards(game, user_id,  bot, update):
    if game.state != ClueGame.Status.Running:
        update.message.reply_text("Can not get cards before game starts")
        return
    user = game.get_user(user_id)
    update.message.reply_text("Your cards are \n %s" % "\n\t".join(user.deck))


class ChooseState(IntEnum):
    TYPE = 0
    PLAYER = 1
    TOOL = 2
    ROOM = 3
    FINAL = 4
    CANCEL = 10

@user_only
def guess_cancel(game, user_id, bot, update, user_data):
    user_data.clear()
    
    update.message.reply_text(
        "Cancel choice")
    return ConversationHandler.END


@user_only
def guess_or_accuse(game, user_id, bot, update):
    reply_keyboard = [['Suggest', "Accuse"], ["Cancel"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    update.message.reply_text(
        "Please choose `Guess` if you want to take a normal turn, or `Accuse` if you'd like to try to solve the game \n (Warning: this will end the game for you!)",
        reply_markup=markup)

    return ChooseState.PLAYER

@user_only
def guess_person(game, user_id, bot, update, user_data):
    text = update.message.text
    if text == "Cancel":
        return guess_cancel(bot, update, user_data)
    user_data["type"]  = text
    print(user_data)
    reply_keyboard = [[str(u) for u in game._suspects], ["Cancel"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    update.message.reply_text(
        "Please choose the player commited murder",
        reply_markup=markup)

    return ChooseState.TOOL

@user_only
def guess_tool(game, user_id, bot, update, user_data):
    text = update.message.text
    if text == "Cancel":
        return guess_cancel(bot, update, user_data)
    user_data["player"] = text
    print(user_data)

    reply_keyboard = [game._tools, ["Cancel"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    update.message.reply_text(
        "Please choose the tool of murder",
        reply_markup=markup)

    return ChooseState.ROOM

@user_only
def guess_room(game, user_id, bot, update, user_data):
    text = update.message.text
    if text == "Cancel":
        return guess_cancel(bot, update, user_data)
    user_data["tool"] = text
    print(user_data)

    reply_keyboard = [game._rooms, ["Cancel"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    update.message.reply_text(
        "Please choose the room where the murder as commited",
        reply_markup=markup)

    return ChooseState.FINAL

@user_only
def guess_final(game, user_id, bot, update, user_data):
    text = update.message.text
    if text == "Cancel":
        return guess_cancel(bot, update, user_data)
    user_data["room"] = text
    print(user_data)

    update.message.reply_text(
        "Choise have been done! ")

    suggestor = game.get_user(user_id)

    if user_data["type"] == "Suggest":
        who_will_show, what = game.suggest(user_id, user_data["player"],
                     user_data["tool"], user_data["room"])

        bot.send_message(chat_id=game._chat_id,
                         text="%s has suggested: %s, %s, %s " % (suggestor.name, user_data["player"],
                     user_data["tool"], user_data["room"]))

        if who_will_show is not None:
            reply_keyboard = [["Show: " + w for w in list(what)]]
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
            bot.send_message(chat_id=who_will_show.id,
                             text="Please choose card to show", reply_markup=markup)
            dispatcher.user_data[who_will_show.id]["show_to"] = user_id

    if user_data["type"] == "Accuse":
        res = game.accuse(user_data["player"],
                     user_data["tool"],
                    user_data["room"])

        bot.send_message(chat_id=game._chat_id,
                         text="%s has accused : %s, %s, %s " % (suggestor.name, user_data["player"],
                                                                user_data["tool"],
                                                                user_data["room"]))

        if res:
            bot.send_message(chat_id=game._chat_id,
                         text="%s has WON!!" % (suggestor.name))
        else:
            bot.send_message(chat_id=game._chat_id,
                         text="%s has LOST!!" % (suggestor.name))
            game._users[user_id]

    return ConversationHandler.END

@user_only
def show_card(game, user_id, bot, update, user_data):
    user = game.get_user(user_id)
    text = update.message.text.split(":", 1)[1]
    bot.send_message(chat_id=user_data["show_to"],
                     text="%s has shown you %s" % (user.name, text))

    other_user = game.get_user(user_data["show_to"])
    bot.send_message(chat_id=game._chat_id,
                     text="%s has shown %s a card" % (user.name, other_user.name))


@group_only
def endgame(bot, update):
    pass #TODO: implement

dispatcher.add_handler(CommandHandler('intro', intro))
dispatcher.add_handler(CommandHandler('hi', register_user))
dispatcher.add_handler(CommandHandler('kill', make_murder))

dispatcher.add_handler(RegexHandler('^Show: ', show_card, pass_user_data=True))


conv_handler = ConversationHandler(
    entry_points=[CommandHandler("guess", guess_or_accuse)],
    states={
        ChooseState.PLAYER: [MessageHandler(Filters.text, guess_person, pass_user_data=True)],
        ChooseState.TOOL: [MessageHandler(Filters.text, guess_tool, pass_user_data=True)],
        ChooseState.ROOM: [MessageHandler(Filters.text, guess_room, pass_user_data=True)],
        ChooseState.FINAL: [MessageHandler(Filters.text, guess_final, pass_user_data=True)]
    },
    fallbacks=[RegexHandler('^Cancel$', guess_cancel, pass_user_data=True)]
)
dispatcher.add_handler(conv_handler)

server_updater.start_polling()
server_updater.idle()