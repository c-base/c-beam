#!/usr/bin/env python

import datetime

class Council():
    """A python class representing a council meeting."""
    def __init__(self, title, owner):
        self.title = "New Council"
        self.start = datetime.datetime.now()
        self.end = []
        self.owner = ""
        self.attendees = []
        self.min_board = 0
        self.board = []
        self.topics = []
        self.__opening = ""
        self.__closing = ""
        self.__correct = ""

    def __unicode__(self):
        return "Council:%s | Owner:%s | Start:%s | End:%s | Attendees:%s | Boad:%s/%s | Topics:%s)" % (
                self.title,
                self.owner,
                self.start,
                self.end,
                len(self.attendees),
                len(self.board),
                self.min_board,
                len(self.topics),
                )

    def __iter__(self):
        """Iterate over all topics."""
        for top in self.topics:
            yield top

    def attendee_add(self, attendee=""):
        if attendee == "": raise AttributeError
        if not attendee in self.attendees:
            self.attendees.append(attendee)

    def attendee_remove(self, attendee=""):
        if attendee == "": raise AttributeError
        if attendee in self.attendees:
            self.attendees.remove(attendee)
        if attendee in self.boad:
            self.boad.remove(attendee)

    def board_add(self, member=""):
        if member == "": raise AttributeError
        if member in self.attendees:
            if not member in self.board:
                self.board.append(member)

    def board_remove(self, member=""):
        if member == "": raise AttributeError
        if member in self.board:
            self.board.remove(member)

    def open(self):
        if len(self.board) > self.min_board:
            now = datetime.datetime.now()
            if now > self.start:
                self.__opening = now
                return True
        return False

    def is_open(self):
        if self.__opening == "" and self.__closing == "":
            return False
        if not self.__opening == and not self.__closing == "":
            return False
        else:
            return True

    def close(self):
        if self.is_open:
            self.__closing == datetime.datetime.now()
            return True
        return False==

if __name__ == '__main__':
    c = Council("Test Meeting", "baccenfutter")
    c.add_topic("")
