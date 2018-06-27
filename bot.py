#!/usr/bin/env python3
#  -*- coding: utf-8 -*-


from telegram.ext import Updater, CommandHandler, ConversationHandler, RegexHandler, Filters, MessageHandler
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import TimedOut
import time
from datetime import timedelta
from enum import IntEnum


from bot_token import bot_token

import logging
import os

from clue import ClueGame
import cards


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  level=logging.INFO)



from functools import wraps


games = {}
user_to_game = {}


def group_only(func):
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        print("group_only")
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
            bot.send_message(chat_id=update.message.chat_id, text="In order to post this command you must address the bot directly.\nTry resending in %s" % (bot.name))
            return
        if user_id not in user_to_game:
            bot.send_message(chat_id=update.message.chat_id, text="No active game for user")
        return func(user_to_game[user_id], user_id, bot, update, *args, **kwargs)
    return wrapped

LIST_OF_ADMINS = None
def get_admin_ids(bot, chat_id):
    """Returns a list of admin IDs for a given chat. Results are cached for 1 hour."""
    admins =  [admin.user.id for admin in bot.get_chat_administrators(chat_id)]
    print(admins, [admin.user.name for admin in bot.get_chat_administrators(chat_id)])
    return admins


def restricted(func):
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        global  LIST_OF_ADMINS

        if update.message.chat_id == update.effective_user.id:
            bot.send_message(chat_id=update.message.chat_id, text="You can post this command only from game group")
            return
        if LIST_OF_ADMINS is None:
            LIST_OF_ADMINS = get_admin_ids(bot, update.message.chat_id)
        user_id = update.effective_user.id
        if user_id not in LIST_OF_ADMINS:
            print("Unauthorized access denied for {}.".format(user_id))
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


def send_card(bot, chat_id, card):

    file_uploaded = False
    while file_uploaded == False:
        try:
            bot.send_photo(chat_id=chat_id, **card.send_photo())
            file_uploaded = True
        except TimedOut:
            print("Timeout exceeded for %s. Retry" % card.name)
            time.sleep(0.5)
@restricted
def intro(bot, update):
    user_id = update.effective_user.id
    chat_id = update.message.chat_id

    if user_id == chat_id:
        bot.send_message(chat_id=update.message.chat_id, text="You can post this command only from game group")
        return

    bot.send_message(chat_id=update.message.chat_id, text="Please wait while I'm setting up the game")


    #msg = bot.send_photo(chat_id=update.message.chat_id, photo=open("img.png", "rb"), caption="foo bar")
    group_name = update.message.chat.title

    cards_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "images")
    game_cards = cards.directory_initilizer(cards_dir, bot, user_id)
    games[chat_id] = ClueGame(chat_id, group_name, **game_cards)
    user_to_game[user_id] = games[chat_id]

    bot.send_message(chat_id=update.message.chat_id, text="Hello everybody. Welcome to `THE CLUE`. Please everybody say /hi")



@group_only
def register_user(game, bot, update):
    fullname = update.effective_user.full_name
    uid = update.effective_user.id 
    bot.send_message(chat_id=update.message.chat_id, text="Hi, %s, welcome to our little game" % (fullname) )
    user_to_game[uid] = game

    game.register_user(uid, fullname)

instruction_text = """
How to play?
========

All the commands should be send to me, your lovely bot privately.   You can ask me...

 • Type `/cards`  to see the cards your are holding
 • If you will ask me for `/suspects`, I'll remind you who was here while the murder was committed.
 • Ask for  `/weapons` to see which items we found around here. 
 what different rooms we have in our house.
 • And finally, I can list for you the `/rooms` we have around here. 
 • If you think you know Who, Where and with what the murder was done, you can always `/guess`.
 • And finally, I can remind you these instructions if you ask for `/help`. 

"""
@restricted
@group_only
def make_murder(game, bot, update):
    game.start_game()

    text1 = "Someone commited a murder! Alas! \nHe used one of the following tools: \n\t\t%s "
    text2 = "It was in room:  \n\t\t%s"
    text3 = "And the murdrer might be... \n\t\t%s"

    bot.send_message(chat_id=update.message.chat_id, text=text1 % "\n\t\t".join(map(str,game._tools)))

    bot.send_message(chat_id=update.message.chat_id, text=text2 % "\n\t\t".join(map(str,game._rooms)))

    bot.send_message(chat_id=update.message.chat_id, text=text3 % "\n\t\t".join(map(str,game._suspects)))

    bot.send_message(chat_id=update.message.chat_id, text=instruction_text)
    bot.send_message(chat_id=update.message.chat_id,
                     text="You can address me at %s. \nPlease ask me for /cards now."
                          "(Privately. You don't won't everybody to see) " % bot.name)

@user_only
def get_cards(game, user_id,  bot, update):
    if game.state != ClueGame.Status.Running:
        update.message.reply_text("Can't get cards before game starts")
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
    if not game.cont_guess(user_id):
        return
    game.end_guess(user_id)

    user_data.clear()
    game.get_user(user_id).cancel_guess()
    
    update.message.reply_text(
        "Cancel choice")
    return ConversationHandler.END


@user_only
def guess_or_accuse(game, user_id, bot, update):
    import ipdb; ipdb.set_trace()
    if not game.get_user(user_id).can_play:
        update.message.reply_text(
            "You can't play right now. Please wait {time}".format(time=str(game.get_user(user_id).time_to_wait())))
        return ConversationHandler.END

    if not game.start_guess(user_id):
        update.message.reply_text("You can't guess now. Someone else is guessing.")
        game.get_user(user_id).cancel_guess()
        return

    reply_keyboard = [['Suggest', "Accuse"], ["Cancel"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    update.message.reply_text(
        "Please choose `Guess` if you want to take a normal turn, or `Accuse` if you'd like to try to solve the game \n (Warning: this will end the game for you!)",
        reply_markup=markup)

    return ChooseState.PLAYER


def list_to_list_set(l):
    l_set = []
    for i in range(0, len(l), 3):
        l_set.append(map(str, l[i:i+3]))
    return l_set


@user_only
def guess_person(game, user_id, bot, update, user_data):
    if not game.cont_guess(user_id):
        update.message.reply_text("You can't guess now. Guessing took too long?.")
        return

    text = update.message.text
    if text == "Cancel":
        return guess_cancel(bot, update, user_data)
    user_data["type"]  = text
    print(user_data)
    reply_keyboard = [*list_to_list_set(game._suspects), ["Cancel"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    update.message.reply_text(
        "Please choose the murderer",
        reply_markup=markup)

    return ChooseState.TOOL

@user_only
def guess_tool(game, user_id, bot, update, user_data):
    if not game.cont_guess(user_id):
        update.message.reply_text("You can't guess now. Guessing took too long?.")
        return

    text = update.message.text
    if text == "Cancel":
        return guess_cancel(bot, update, user_data)
    user_data["player"] = text
    print(user_data)

    reply_keyboard = [*list_to_list_set(game._tools), ["Cancel"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    update.message.reply_text(
        "Please choose the murder weapon",
        reply_markup=markup)

    return ChooseState.ROOM

@user_only
def guess_room(game, user_id, bot, update, user_data):
    if not game.cont_guess(user_id):
        update.message.reply_text("You can't guess now. Guessing took too long?.")
        return

    text = update.message.text
    if text == "Cancel":
        return guess_cancel(bot, update, user_data)
    user_data["tool"] = text
    print(user_data)

    reply_keyboard = [*list_to_list_set(game._rooms), ["Cancel"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    update.message.reply_text(
        "Please choose the room where the murder was committed",
        reply_markup=markup)

    return ChooseState.FINAL

@user_only
def guess_final(game, user_id, bot, update, user_data):
    if not game.cont_guess(user_id):
        update.message.reply_text("You can't guess now. Guessing took too long?.")
        return

    text = update.message.text
    if text == "Cancel":
        return guess_cancel(bot, update, user_data)
    user_data["room"] = text
    print(user_data)

    update.message.reply_text(
        "Your choice has been made! ")

    suggestor = game.get_user(user_id)

    if user_data["type"] == "Suggest":
        who_will_show, what = game.suggest(user_id, user_data["player"],
                     user_data["tool"], user_data["room"])

        bot.send_message(chat_id=game._chat_id,
                         text="%s has suggested: %s, %s, %s " % (suggestor.name, user_data["player"],
                     user_data["tool"], user_data["room"]))

        if who_will_show is not None:
            if who_will_show != suggestor:
                reply_keyboard = [["Show: " + w for w in list(what)]]
                markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
                bot.send_message(chat_id=who_will_show.id,
                                 text="Please choose a card to show", reply_markup=markup)
                dispatcher.user_data[who_will_show.id]["show_to"] = user_id
            else:
                bot.send_message(chat_id=suggestor.id,
                                 text="No one has a card to show you.")

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
                         text="%s has WON THE GAME!!!" % (suggestor.name))
        else:
            bot.send_message(chat_id=game._chat_id,
                         text="%s has LOST and is removed from the game!" % (suggestor.name))
            game._users[user_id].losing()

    game.end_guess(user_id)
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

@user_only
def show_my_cards(game, user_id, bot, update):
    user = game.get_user(user_id)
    bot.send_message(chat_id=user.id, text="Your cards are \n")
    for c in user.deck:
        send_card(bot,user_id,c)


@user_only
def show_me_rooms(game, user_id, bot, update):
    bot.send_message(chat_id=user_id, text="Possible rooms are \n")
    for c in game._rooms:
        send_card(bot,user_id,c)


@user_only
def show_me_suspecs(game, user_id, bot, update):
    bot.send_message(chat_id=user_id, text="The Suspects are \n")
    for c in game._suspects:
        send_card(bot,user_id,c)


@user_only
def show_me_tools(game, user_id, bot, update):
    bot.send_message(chat_id=user_id, text="Possible weapons are \n")
    for c in game._tools:
        send_card(bot,user_id,c)

@group_only
def endgame(bot, update):
    pass  # TODO: implement

@user_only
def get_help(game, user_id,  bot, update):
    bot.send_message(chat_id=user_id, text=instruction_text)


def set_dispatchr(server_updater):

    dispatcher = server_updater.dispatcher

    dispatcher.add_handler(CommandHandler('test', test))

    dispatcher.add_handler(CommandHandler('intro', intro))
    dispatcher.add_handler(CommandHandler('hi', register_user))
    dispatcher.add_handler(CommandHandler('kill', make_murder))
    dispatcher.add_handler(CommandHandler('cards', show_my_cards))

    dispatcher.add_handler(CommandHandler('suspects', show_me_suspecs))
    dispatcher.add_handler(CommandHandler('weapons', show_me_tools))
    dispatcher.add_handler(CommandHandler('rooms', show_me_rooms))

    dispatcher.add_handler(CommandHandler('help', get_help))


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


if __name__ == '__main__':
    server_updater = Updater(token=bot_token,
                             request_kwargs=dict(connect_timeout=15.0, read_timeout=20, con_pool_size=5))
    set_dispatchr(server_updater)
    server_updater.start_polling()
    server_updater.idle()
