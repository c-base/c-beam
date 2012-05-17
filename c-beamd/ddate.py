# -*- coding: utf-8 -*-
import datetime, random

def showDayNum(num):
    if((num!=11) and ((num % 10)==1)):
        return(`num` + "st")
    elif((num!=12) and ((num % 10)==2)):
        return(`num` + "nd")
    elif((num!=13) and ((num % 10)==3)):
        return(`num` + "rd")
    else:
        return(`num` + "th")

def isLeapYear(year):
    if (year % 100 != 0) and (year % 4 == 0):
        return True
    elif (year % 100 == 0) and (year % 400 == 0):
        return True
    else:
        return False

def leapYearCorrection(aDay, year):
    if(isLeapYear(year) and (aDay > 60)): 
        return aDay - 1 
    else:
        return aDay

class DDate(object):
    dSeasonNum = 0
    dDayOfWeek = 0
    dDayOfSeason = 0
    dYOLD = 0
    dSeasonHoliday = 0
    dApostleHoliday = 0
    dStTibs = False
#    def __new__(self):
#        pass
    def __init__(self):
        self.dSeasonNum = 0
        self.dDayOfWeek = 0
        self.dDayOfSeason = 0
        self.dYOLD = 0
        self.dSeasonHoliday = False
        self.dApostleHoliday = False
        self.dStTibs = False
    def __str__(self):
        if(self.dStTibs):
                return "ST TIBS DAY!"
        else:
                msg = self.dWeekdays[self.dDayOfWeek] +  \
                        u', the ' + showDayNum(self.dDayOfSeason) + \
                        u' day of ' + self.dSeasons[self.dSeasonNum] + \
                        u' in the YOLD ' + `self.dYOLD` + '.'
                if(self.dSeasonHoliday):
                        msg = msg + u' Celebrate ' + self.dSeasonHolidays[self.dSeasonNum] + '!'
                if(self.dApostleHoliday):
                        msg = msg + u' Celebrate ' + self.dApostleHolidays[self.dSeasonNum] + '!'
                return msg

    dSeasons = ["Chaos", "Discord", "Confusion", "Bureaucracy", "The Aftermath"]
    dWeekdays = ["Sweetmorn", "Boomtime", "Pungenday", "Prickle-Prickle", "Setting Orange"]
    dApostleHolidays = ["Mungday","Mojoday","Syaday","Zaraday","Maladay"]
    dSeasonHolidays = ["Chaoflux", "Discoflux", "Confuflux", "Bureflux", "Afflux"]



    def checkHoliday(self, day):
        if(day==5):
                self.dApostleHoliday = True
        if(day==50):
                self.dSeasonHoliday = True
        
    def fromDate(self, aDate):
        dayOfYear = aDate.timetuple()[7]
        correctedDay = leapYearCorrection(dayOfYear, aDate.year) - 1
        self.dDayOfSeason = (correctedDay % 73) + 1
        self.dDayOfWeek = (correctedDay % 5)
        self.dSeasonNum = (correctedDay / 73)
        self.dYOLD = aDate.year + 1166
        self.dStTibs = isLeapYear(aDate.year) and (dayOfYear == 60)
        self.checkHoliday(self.dDayOfSeason) 

    def today(self):
        pass
        #return self.fromDate(datetime.date.today())

    def fnord(self):
        messages = ['Hail Eris!',
            'All Hail Discordia!',
            'Kallisti!',
            'Fnord.',
            'Or not.',
            'Wibble.',
            'Pzat!',
            'Pi\'tang!',
            'Frink!',
            'Slack!',
            'Praise \'Bob\'!',
            'Or kill me.',
            'Grudnuk demand sustenance!',
            'Keep the Lasagna flying!',
        ]
        return random.choice(messages)
