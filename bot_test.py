from __future__ import absolute_import
import unittest

from telegram.ext import Updater

from ptbtest import UserGenerator
from ptbtest import ChatGenerator
from ptbtest import MessageGenerator
from ptbtest import Mockbot

import bot

class TestClueBot(unittest.TestCase):

    def setUp(self):
        self.bot = Mockbot()
        self.cg = ChatGenerator()
        self.ug = UserGenerator()
        self.mg = MessageGenerator(self.bot)
        self.updater = Updater(bot=self.bot)

    def test_test(self):

        bot.set_dispatchr(self.updater)
        self.updater.start_polling()

        user = self.ug.get_user(first_name="Test", last_name="The Bot")
        chat = self.cg.get_chat(user=user)
        update = self.mg.get_message(user=user, chat=chat, text="/test")
        self.bot.insertUpdate(update)

        self.assertEqual(len(self.bot.sent_messages), 1)
        sent = self.bot.sent_messages[0]
        self.assertEqual(sent['method'], "sendMessage")
        self.assertEqual(sent['text'], "I'm a bot, please talk to me!")
        self.updater.stop()


if __name__ == '__main__':
    unittest.main()