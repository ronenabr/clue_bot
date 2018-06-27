# -*- coding: utf-8 -*-

import unittest
import clue


class TestClue(unittest.TestCase):

    def test_clue(self):
        c = clue.ClueGame(123, "foo")
        for i in range(10):
            c.register_user(i, str(i))
        
        c.start_game()

        # Check deck
        deck = []
        for uid, u in c._users.items():
            deck.extend(u._deck)

        self.assertEqual(set(deck), set(c._deck))

        user, what = c.suggest(0, "1", clue.TOOLS[0], clue.ROOMS[0])

        if user is not None:
            self.assertGreater(len(what), 0)


if __name__ == '__main__':
    unittest.main()
''