# -*- coding: utf-8 -*-

import random
from enum import Enum
from time import time
from datetime import timedelta
from threading import Lock

ROOMS = ["Leaving Room", "Bedroom", "Library", "Dining room"]
TOOLS = ["GARNERA",
         "OTTIL",
         "LAGRAD",
         "FJÄLLA",
         "TVÄRS",
         "AVSIKTLIG",
         "VARDAGEN",
         "GUBBRÖRA"]

SUSPECTS = ["Ronen", "Oded", "Fox", "Frorixh"]

NUMBER_OF_SECONDS_BETWEEN_TURNS = 0.5 * 60
GUESS_TIMEOUT_TIME_S = 1 * 60;

class ClueGame(object):
    class Status(Enum):
        Init = 1
        Running = 2
        Ended = 3
        OK = 100

    class User(object):


        def __init__(self, id, name, game):
            self._id = id
            self._name = name
            self._deck = []
            self._playing = True
            self._known = []
            self._last_token_given = 0
            self._prev_time = 0
            self._game = game
            self._lock = Lock()

        @property
        def id(self):
            return self._id

        @property
        def name(self):
                return self._name

        @property
        def deck(self):
            return self._deck

        @property
        def can_play(self):
            # with self._lock:
                if not self._playing:
                    return False

                if time() - self._last_token_given > NUMBER_OF_SECONDS_BETWEEN_TURNS:
                    self._prev_time = self._last_token_given
                    self._last_token_given = time()
                    return True

                return False

        def time_to_wait(self):
            with self._lock:
                return timedelta(seconds=NUMBER_OF_SECONDS_BETWEEN_TURNS - (time() - self._last_token_given))

        def cancel_guess(self):
            with self._lock:
                self._last_token_given = self._prev_time

        def set_deck(self, deck):
            self._deck = deck

        def tell(self, what):
            self._known.append(what)

        def losing(self):
            with self._lock:
                self._playing = False

        def __str__(self):
            return "{0}".format(self._name)

    def __init__(self, chat_id, group_name, tools=None, rooms=None, suspects=None):
        self._chat_id = chat_id
        self.group_name = group_name
        self.state = ClueGame.Status.Init
        self._tools = tools
        if tools is None:
            self._tools = TOOLS
        self._rooms = rooms
        if rooms is None:
            self._rooms = ROOMS
        self._default_suspects = suspects

        self._users = {}
        self._suggestions = ()

        self._suspects = []
        self._murder_info = None
        self._deck = []
        self._game_order = []
        self.current_index = 0

        self._lock = Lock()

        self._guess_lock = Lock()
        self._user_gussing = None
        self._start_guessing = None

    def start_guess(self, user_id):
        with self._guess_lock:
            print("Start guessing", user_id, self._user_gussing, time() - self._start_guessing if self._start_guessing else 0)
            if self._user_gussing is None:
                self._user_gussing = user_id
                self._start_guessing = time()
                return True
            if self._user_gussing == user_id:
                self._start_guessing = time()
                return True
            if time() - self._start_guessing > GUESS_TIMEOUT_TIME_S:
                self._user_gussing = user_id
                self._start_guessing = time()
                return True

            return False

    def cont_guess(self, user_id):
        print(user_id, self._user_gussing, time() - self._start_guessing if self._start_guessing else 0)

        with self._guess_lock:
            if self._user_gussing is None:
                return False
            if self._user_gussing == user_id:
                self._start_guessing = time()
                return True
            return False

    def end_guess(self, user_id):
        print(user_id, self._user_gussing, time() - self._start_guessing if self._start_guessing else 0)

        with self._guess_lock:
            if self._user_gussing is not None and self._user_gussing == user_id:
                self._user_gussing = None
                self._start_guessing = None
                print("Guess RESET")
                return True
            return False

    def register_user(self, user_id, name):
        with self._lock:
            if self.state == ClueGame.Status.Init:
                self._users[user_id] = ClueGame.User(user_id, name, self)
                return ClueGame.Status.OK
            return self.state

    def start_game(self):
        with self._lock:
            if self.state != ClueGame.Status.Init:
                return self.state

            # For now, I do not necceserly wants the list of suspects to overlap list of users.
            # self._suspects = [str(self._users[k]) for k in self._users.keys()]
            self._suspects = self._default_suspects
            print(self._tools)

            self._murder_info = (random.choice(self._tools), random.choice(self._rooms), random.choice(self._suspects))
            self._deck = []

            self._deck.extend([t for t in self._tools if t != self._murder_info[0]])
            self._deck.extend([t for t in self._rooms if t != self._murder_info[1]])
            self._deck.extend([t for t in self._suspects if t != self._murder_info[2]])

            random.shuffle(self._deck)
            cards_per_user = len(self._deck) // len(self._users)
            extra_cards = len(self._deck) % len(self._users)
            print(cards_per_user, extra_cards, len(self._users))
            deck_index = 0
            for i, (_, u) in enumerate(self._users.items()):
                extra_card = 1 if extra_cards > i else 0
                deck_offset = deck_index + cards_per_user + extra_card
                print(deck_offset - deck_index)
                u.set_deck(self._deck[deck_index:deck_offset])
                deck_index = deck_offset

            self._game_order = list(self._users.keys())
            random.shuffle(self._game_order)
            self.current_index = 0

            self.state = ClueGame.Status.Running

            return self.Status.OK

    def accuse(self, suspect, tool, room):
        if (tool, room, suspect) == self._murder_info:
            return True
        return False

    def suggest(self, user_id, suspect, tool, room):
        if (tool, room, suspect) == self._murder_info:
            return None, []
        current_index = self._game_order.index(user_id)
        suggestion = set((suspect, tool, room))

        for i in range(len(self._game_order)):
            j = (1 + i + current_index) % len(self._game_order)
            user = self._users[self._game_order[j]]
            intersection = suggestion.intersection(set(user.deck))
            if len(intersection) > 0:
                return user, list(intersection)

        print("Something bad has happened")
        return None, []

    def tell(self, who, to, what):
        # check
        if not what in who._deck:
            print("Some error with {0} telling {1}".format(who, what))
        to.tell(what)

    def next(self, who):
        current = self._users[self._game_order[self.current_index]]
        if who != current:
            return None
        self.current_index += 1
        user = self._users[self._game_order[self.current_index]]

        return user

    def get_user(self, uid):
        return self._users[uid]
