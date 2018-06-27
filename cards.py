# -*- coding: utf-8 -*-

import os
from enum import IntEnum
import time
import yaml

from telegram.error import TimedOut


class CardItem():
    class CardType(IntEnum):
        SUSPECT = 1
        ROOM = 2
        TOOL = 3

    def send_photo(self):
        return dict(caption=self.name, photo=self.file_id)

    def __init__(self, name, file, type, bot, chat_id, file_id=None):
        self.name = name
        self.file = file
        self.type = CardItem.CardType(type)
        if file_id is not None:
            self.file_id = file_id
            return
        file_uploaded = False
        while file_uploaded == False:
            try:
                msg = bot.send_photo(chat_id=chat_id, photo=open(self.file, "rb"), disable_notification=True)
                file_uploaded = True
            except TimedOut:
                print("Timeout exceeded for %s. Retry" % name)

        self.file_id = msg.photo[0].file_id

    def __str__(self):
        return self.name

    def __repr__(self):
        return "{%s - %s}" % (self.name, self.file_id)

    def __eq__(self,other):
        if isinstance(other, CardItem):
            return other.name == self.name
        return other == self.name

    def __hash__(self):
        return hash(self.name)


def subdir_initilizer(subdir, type, bot, user_id):
    items = []
    data_file = os.path.join(subdir,"data.yaml")
    filenames = []
    if os.path.isfile(data_file):
        yml = yaml.load(open(data_file,"r"))
        for line in yml:
            items.append(CardItem(bot=bot, chat_id=user_id, **line))
            filenames.append(line["file"])

    for item in os.listdir(subdir):
        if item[-4:].lower() in [".jpg", ".png", ".gif"]:
            path = os.path.join(subdir, item)
            if path in filenames:
                continue
            name = item[:-4]
            items.append(CardItem(name, path, type, bot, user_id))
            print(items[-1].__repr__)
            time.sleep(3)
    yml = yaml.dump([dict(name=i.name, file=i.file, file_id=i.file_id, type=int(i.type)) for i in items])
    with open(os.path.join(subdir,"data.yaml"),"w") as f:
        f.write(yml)
    return items


def directory_initilizer(base_dir, bot, user_id ):


    return {
        "tools" : subdir_initilizer(os.path.join(base_dir, "tools"), CardItem.CardType.TOOL, bot, user_id ),
        "rooms": subdir_initilizer(os.path.join(base_dir, "rooms"), CardItem.CardType.ROOM, bot, user_id),
        "suspects": subdir_initilizer(os.path.join(base_dir, "suspects"), CardItem.CardType.SUSPECT, bot, user_id),
    }

if __name__  == '__main__':
    script_path = os.path.dirname(os.path.realpath(__file__))
    print(directory_initilizer(os.path.join(script_path, "images")))
