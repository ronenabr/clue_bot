from __future__ import absolute_import
import unittest


import bot
import clue

import time

import copy

class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)
    def __str__(self):
        return "\t"+"\n\t".join(["%s:%s" % (str(k), str(v)) for k,v in self.__dict__.items()]) + "\n"

class MockUpdate(object):

    def __init__(self, bot, user_id=None, chat_id=None, text=None):
        self.user_id = user_id
        self.chat_id = chat_id
        self.bot = bot
        self.text = None

    def update_text(self, text):
        upcopy = copy.copy(self)
        upcopy.text = text
        return upcopy

    def reply_message(self, *args, **kwargs):
        kwargs["chat_id"] = self.chat_id
        return self.bot.send_message(*args, **kwargs)

    @property
    def message(self):
        return Struct(chat_id=self.chat_id,
                      reply_text=self.reply_message,
                      text=self.text)

    @property
    def effective_user(self):
        return Struct(id=self.user_id)


class MockBot(object):

    def __init__(self):
        self.messages =  []

    def send_message(self,*args,  **kwargs):
        self.messages.append(Struct(args=args, kwargs=kwargs))

    def clear(self):
        self.messages = []

    def __str__(self):
        return "message:\n" + "message:\n".join([str(x) for x in self.messages]) + "\n"

class TestClueBot(unittest.TestCase):

    def setUp(self):
        pass


    def test_test(self):

        bot_obj = MockBot()
        update = MockUpdate(bot_obj, -1,1)
        bot.test(bot_obj,update)


        self.assertEqual(bot_obj.messages[0].kwargs["chat_id"], update.chat_id)
        self.assertEqual(bot_obj.messages[0].kwargs["text"], "I'm a bot, please talk to me!")


    def test_guess(self):

        bot_obj = MockBot()
        chat_id = 10
        group_name = "foo"

        user_id_a = -5
        user_id_b = -10

        user_data_a = {}
        user_data_b = {}

        update_a = MockUpdate(bot_obj, user_id_a, user_id_a)
        update_b = MockUpdate(bot_obj, user_id_b, user_id_b)
        update_common = MockUpdate(bot_obj, user_id_b, chat_id )

        game = clue.ClueGame(chat_id, group_name, tools=["a","b"], rooms=["x","y"], suspects=["m","n"])

        bot.games[chat_id] = game
        bot.user_to_game[user_id_a] = game
        bot.user_to_game[user_id_b] = game

        game.register_user(user_id_a,"a")
        game.register_user(user_id_b,"b")


        bot.guess_or_accuse(bot, update_a)
        bot.guess_or_accuse(bot, update_b)
        bot.guess_or_accuse(bot, update_b)
        bot.guess_or_accuse(bot, update_b)

        print(bot_obj)
        bot_obj.clear()
        time.sleep(7)

        bot.guess_or_accuse(bot, update_b)
        bot.guess_suspect(bot, update_b.update_text("Cancel"), user_data_b)
        print(bot_obj)
        bot_obj.clear()

        bot.guess_or_accuse(bot, update_a)
        print(bot_obj)
        bot_obj.clear()








if __name__ == '__main__':
    unittest.main()

    bot_obj = MockBot()
    update = MockUpdate(bot_obj, -1, 1)