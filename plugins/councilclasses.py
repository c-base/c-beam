#!/usr/bin/env python

from datetime import datetime

class CouncilACLError(Exception):
    def __init__(self, value):
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)

class CouncilQuorumError(Exception):
    def __init__(self, value):
        self.parameter = value
    def __repr__(self):
        return repr(self.parameter)

class Topic():
    """A python class representing a topic
    
    There are three types of topics:
        0 - ELECTION    - Results in a vote within all board members
        1 - DEMOGRAPH   - Results in a demograph within all attendees
        2 - INFO        - Results in no vote at all
    """
    TYPES = {
            0: 'ELECTION',
            1: 'DEMOGRAPH',
            2: 'INFO',
            }
    def __init__(self, TYPE=0, title="", owner=""):
        """Constructor
        
        Attributes:
            TYPE    - Either one of 0, 1, 2 ( see Topic().__DOC__ )
            title   - Title or subject of this topic
            owner   - Owner or initiator of this topic
        """
        if not TYPE in self.TYPES.keys(): raise AttributeError
        if title == "": raise AttributeError
        if owner == "": raise AttributeError
        self.TYPE = TYPE
        self.title = title
        self.owner = owner
        self.PRO = 0
        self.CONTRA = 0
        self.ABSTENTIONS = 0
        self.__opening = ""
        self.__closing = ""
        self.__state = 0    # 0=ToDo 1=Open 2=Closed

    def __repr__(self):
        retval = "%s | Title:%s | Owner:%s" % (
                self.TYPES[self.TYPE],
                self.title,
                self.owner,
                )
        if self.__state == 2:
            if self.TYPE == 0 or self.TYPE == 1:
                retval = "%s [+:%s|-:%s|~%s]" % (
                        retval,
                        self.PRO,
                        self.CONTRA,
                        self.ABSTENTIONS,
                        )
        return retval

    def get_state(self):
        return self.__state

    def get_voices(self, council=""):
        """Return the number of total available voices in council
        
        Attributes:
            council - Council() - The parent council object of this topic
        
        Returns number of total available voices in council in regardance
        of self.TYPE
        """
        if not isinstance(council, Council): raise AttributeError

        if self.TYPE == 0:
            return len(council.board)
        elif self.TYPE == 1:
            return len(council.attendees)
        elif self.TYPE ==2:
            return 0

    def is_open(self):
        """Return True if this topic is open
        
        Return False if this topic is not open
        """
        if self.__state == 0:
            return False
        elif self.__state == 1:
            return True
        elif self.__state == 2:
            return False

    def open(self, council="" ):
        """Open this topic
        
        Attributes:
            council - Council() - The parent council object of this topic

        Returns 
        """
        if not isinstance(council, Council): raise AttributeError
        if not council.is_open(): return False

        if council.is_open():
            for topic in council.topics:
                if topic.is_open():
                    return False
            if not self.is_open():
                self.__opening = datetime.now()
                self.__state = 1
                return self
        return False

    def close(self, council="" ):
        """Close this topic
        
        Return this topic
        """
        if not isinstance(council, Council): raise AttributeError

        if self.is_open():
            if self.TYPE == 0:
                if not self.validate_vote(council):
                    return (
                            self.get_voices(council),
                            {
                                'PRO': self.PRO,
                                'CONTRA': self.CONTRA,
                                'ABSTENTIONS': self.ABSTENTIONS,
                                },
                            )
            self.__closing = datetime.now()
            self.__state = 2
            return self
        return False

    def validate_vote(self, council="" ):
        """Validate the truthfullness and legalty of this topic's vote
        
        Attributes:
            council - Council() - The parent council object of this topic

        Returns True or False
        """
        if not isinstance(council, Council): raise AttributeError

        total_voices = self.get_voices(council)
        total_votes = self.PRO + self.CONTRA + self.ABSTENTIONS
        if total_votes == total_voices:
            return True
        else:
            return False

    def vote(self, council="", voting={} ):
        """Arrange a voting upon this topic
        
        Attributes:
            council - Council() - The parent council object of this topic
            voting  - dict      - A dict in the format of: {
                                                            'PRO': 0,
                                                            'CONTRA': 0,
                                                            'ABSTENTIONS', 0
                                                            }
        Return this topic
        """
        if not isinstance(voting, dict): raise AttributeError
        if not isinstance(council, Council): raise AttributeError
        if not council.is_open(): return False
        if not self.is_open(): return False
        if voting == {}: return False

        for key in voting.keys():
            if key.upper() == 'PRO':
                if not isinstance(voting[key], int): raise AttributeError
                self.PRO = voting[key]
            elif key.upper() == 'CONTRA':
                if not isinstance(voting[key], int): raise AttributeError
                self.CONTRA = voting[key]
            elif key.upper() == 'ABSTENTIONS':
                if not isinstance(voting[key], int): raise AttributeError
                self.ABSTENTIONS = voting[key]
            else:
                raise AttributeError
        return self


class Council():
    """A python class representing a council meeting.
    This class aims to provide toolsets and workflow support for the management of council meetings.
    """
    def __init__(self, title, owner, start, end):
        """Constructor

        Args:
            title   - string    - Title or subject of this council
            start   - string    - Announced time of start as python datetime object
            end     - string    - Announced time of end as python datetime object
            owner   - string    - The owner or initiator of thiscouncil
        """
        self.title = "New Council"
        self.start = start
        self.end = end
        self.owner = owner
        self.attendees = [ owner ]
        self.min_board = 0
        self.board = []
        self.topics = []
        self.__opening = ""
        self.__closing = ""
        self.__state = 0    # 0=ToDo 1=Open 2=Closed

    def __repr__(self):
        state = ''
        if self.is_open():
            state = 'NOW | '
        closed_topics = len( [ topic for topic in self.topics if topic.get_state() == 2] )
        return "%sCouncil:%s | Owner:%s | Start:%s | End:%s | Attendees:%s | Board:%s/%s | Topics:%s/%s)" % (
                state,
                self.title,
                self.owner,
                self.start,
                self.end,
                len(self.attendees),
                len(self.board),
                self.min_board,
                closed_topics,
                len(self.topics),
                )

    def __iter__(self):
        """Yield all topics"""
        for top in self.topics:
            yield top

    def __getitem__(self, item):
        return self.topics[item]

    def get_state(self):
        return self.__state

    def attendee_add(self, attendee=""):
        """Add an attendee to this council meeting
        
        Return list of all attendees
        """
        if attendee == "": raise AttributeError
        if not attendee in self.attendees:
            self.attendees.append(attendee)
            return self.attendees

    def attendee_remove(self, attendee=""):
        """Remove and attendee from this council
        
        Return list of attendees
        """
        if attendee == "": raise AttributeError
        if attendee in self.attendees:
            self.attendees.remove(attendee)
        if attendee in self.board:
            self.board.remove(attendee)
        return self.attendees

    def board_add(self, member=""):
        """Add an attendee of this council to the list of board members
        
        Return list of board members
        """
        if member == "": raise AttributeError
        if member in self.attendees:
            if not member in self.board:
                self.board.append(member)
                return self.board

    def board_remove(self, member=""):
        """Remove a board member from the list of board members
        
        Return list of board members
        """
        if member == "": raise AttributeError
        if member in self.board:
            self.board.remove(member)
            return self.board

    def is_open(self):
        """Return True if this council is currently open
        
        Return False if this council is currently not open
        """
        if self.__state == 0:
            return False
        elif self.__state == 1:
            return True
        elif self.__state == 2:
            return False

    def open(self):
        """Open this council
        
        Return this council
        """
        if self.min_board > 0:
            if len(self.board) < self.min_board:
                raise CouncilQuorumError
        if len(self.topics) == 0:
            return False
        self.__opening = datetime.now()
        self.__state = 1
        return self

    def close(self):
        """Close this council
        
        Retrun this council
        """
        for topic in self.topics:
            if topic.is_open():
                return False

        if self.is_open():
            self.__closing = datetime.now()
            self.__state = 2
            return self
        return False

    def topic_add(self, TYPE=0, title="", owner=""):
        """Add a topic to the list of topics
        
        Return list of topics
        """
        if not TYPE in Topic.TYPES.keys(): raise AttributeError
        if title == "": raise AttributeError
        if owner == "": raise AttributeError
        if not owner in self.attendees: raise CouncilACLError

        try:
            topic = Topic(TYPE, title, owner)
        except:
            return False
        self.topics.append(topic)
        return topic

    def topic_remove(self, topic=""):
        """Remove a topic from the list of topics
        
        Return the list of topics
        """
        if not isinstance(topic, Topic()): raise AttributeError
        if not topic in self.topics:
            return False
        else:
            self.topics.remove(topic)
            return self.topics

    def topic_set_order(self, topics=[]):
        """Reorder list of topics
        
        Arguments:
            topics  - list  - List of all topics in the list of topics and no
                              other topics in the new and preferred order
                              (will replace old topic list)
        
        Return list of topics
        """
        if not isinstance(topics, list): raise AttributeError
        if topics == []: return False
        for topic in topics:
            if not topic in self.topics:
                return False
        for topic in self.topics:
            if not topic in topics:
                return False
        self.topics = topics

if __name__ == '__main__':
    print "Create instance"
    c = Council(
            "Test Meeting",
            "baccenfutter",
            datetime(2012, 4, 14, 20, 30, 00),
            datetime(2012, 4, 14, 23, 59, 59),
            )
    print c

    print "Add attendees and board members"
    print c.attendee_add('baccenfutter')
    print c.attendee_add('cmile')
    print c.attendee_add('dazs')
    print c.attendees

    print c.board_add('baccenfutter')
    print c.board_add('cmile')
    print c.board_add('dazs')
    print c.board

    print
    print "Add topics"
    print c.topic_add(0, 'Test Topic', 'baccenfutter')
    print c.topic_add(1, 'Test flavour', 'cmile')
    print c.topic_add(2, 'Party auf dem T-Feld', 'dazs')
    print c.topics

    print
    print "Notice information in the object representation"
    print c

    print

    print "Iterating over topics"
    print c.open()
    for topic in c:
        print "Open topic"
        print topic.open(c)
        print "Check if open: %s" % topic.is_open()
        print "Check if we have to vote"
        if topic.TYPE == 0:
            vote = {
                    'PRO': 3,
                    'CONTRA': 0,
                    'ABSTENTIONS': 0,
                    }
            print "Voting: " + str(vote)
            topic.vote(c, vote)
        elif topic.TYPE == 1:
            vote = {
                    'PRO': 2,
                    'CONTRA': 1,
                    'ABSTENTIONS': 0,
                    }
            print "Voting: " + str(vote)
            topic.vote(c, vote)
        print "Close topic"
        print topic.close(c)
        print "Chekc if open: %s" % topic.is_open()
    print "Close council"
    print c.close()

    print "Topics can be get using __getitem__"
    topic = c[2]
    print topic
    print "Topics cannot be opend if council is not open"
    print topic.open(c)

