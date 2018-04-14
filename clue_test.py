import unittest
import clue

class TestStringMethods(unittest.TestCase):
    def test_clue(self):
        c = clue.Clue(123, "foo")
        for i in range(10):
            c.register_user(i,str(i))
        
        #Check deck
        deck = []
        for uid, u in c._users.items():
            deck.extend(u._deck)
        self.assertEqual(deck, c._deck)

        uid, what = c.suggest("1", clue.TOOLS[0], clue.ROOMS[0])
        if uid>0:
            self.assertGreater(len(what),0)
