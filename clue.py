

ROOMS = ["Kitchen", "Bedroom", "Library"]
TOOLS = ["Club", "Secers", "Chair"]
import random 


class Clue(object):

    class Status(Enum):
        Init = 1
        Running = 2
        Ended = 3
        OK = 100

    class User(object) :
        def __init__(self, id, name):
            self._id = id
            self._name = name
            self._deck = []
            self._known = []

        def set_deck(self, deck):
            self._deck = deck

        @property
        def deck(self):
            return self.deck
        
        def tell(self, what):
            self._known.append(what)

        def __str__(self):
            return self._name

    def __init__(self, chat_id, group_name, tools = None, rooms = None):
        self._chat_id = chat_id
        self.group_name = group_name
        self.state = Clue.Status.Init
        self._tools = tools
        if tools is None:
            self._tools = tools
        self._rooms = rooms
        if rooms is None:
            self._tools = tools

        self._users = {}
        self._suggestions =  ()
        
    def register_user(self, user_id, name):
        if self.state == Clue.Status.Init:
            self._users[user_id] = Clue.User(user_id, name)
            return Clue.Status.OK
        return self.state

    def start_game(self):
        if self.state != Clue.Status.Init:
            return self.state

        #For now, I do not necceserly wants the list of suspects to overlap list of users. 
        self._suspects = [str(self._users[k]) for k in self._users.keys()]

        self._murder_info = (random.choice(self._tools), random.choice(self._rooms), random.choice(self._suspects))
        self._deck = []

        self._deck.extend([t for t in self._tools if t != self._murder_info[0]])
        self._deck.extend([t for t in self._rooms if t != self._murder_info[1]])
        self._deck.extend([t for t in self._suspects if t != self._murder_info[2]])
        
        random.shuffle(self._deck)
        cards_per_user = len(self._deck)//len(self._users)
        extra_cards = len(self._deck)%len(self._users)
        deck_index = 0
        for i, (_, u) in enumerate(self._users.items()):
            deck_offset = deck_index + cards_per_user + 1 if extra_cards < i else 0
            u.set_deck(self._deck[deck_index:deck_offset])
        
        self._game_order = list(self._users.keys())
        random.shuffle(self._game_order)
        self.current_index = 0

        self.state = Clue.Status.Running

        return self.Status.OK

    def accuse(self, suspect, tool, room):
        if (tool, room, suspect) == self._murder_info:
            return True
        return False

    def suggest(self, user_id, suspect, tool, room):
        if (tool, room, suspect) == self._murder_info:
            return -1, []
        current_index = self._game_order.index(user_id)
        suggestion = set((suspect, tool, room))

        for i in range(len(self._game_order)):
            j = (i + current_index) % len(self._game_order)
            user = self._users[self._game_order[j]]
            intersection = suggestion.intersection(set(user.deck))
            if len(intersection) > 0:
                return user, list(intersection)
            
        print("Something bad has happend")
        return -1, []
    
    def tell(self, who, to, what):
        #check
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
        
