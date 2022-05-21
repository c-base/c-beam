import datetime


class HandTranslate:

    def __init__(self):
        self._command_list = {"highFive": [4, 4, 4, 4, 4],
                              "Victory": [0, 4, 4, 0, 0],
                              "Time": [0, 0, 0, 0, 0],
                              "Devil": [0, 4, 0, 0, 4],
                              "Bird": [0, 0, 4, 0, 0],
                              "DrEvil": [0, 0, 0, 0, 4]
                              }
        self._finger_name = ["thump", "index", "middle", "ring", "pinkie"]
        self._version = 0.02

    def getVersion(self):
        return self._version

    def getHandHelp(self):
        return "Hand help text blub"

    def getHandCommands(self):
        return self._command_list.keys()

    def translate(self, command):

        if command not in self._command_list:
            raise NotImplementedError("Command not implemented")

        rlist = []
        clist = []

        if command == "Time":
            clist = self._getTimeArray()
        else:
            clist = self._command_list[command]

        for i in range(5):
            rlist.append(("hand/" + self._finger_name[i], clist[i]))

        return rlist

    def _getTimeArray(self):
        now = datetime.datetime.now()
        intval = now.hour * 100 + now.minute
        intarray = []

        while intval:
            intarray.append(intval % 5)
            intval = intval / 5

        return intarray
