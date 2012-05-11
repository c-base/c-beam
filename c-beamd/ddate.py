# -*- coding: utf-8 -*-
#Taken from pyChao - Python IRC-Bot
#Released under GPL-3 (at least that's what their cooglegode site says)
import datetime

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
    seasonNum = 0
    dayOfWeek = 0
    dayOfSeason = 0
    YOLD = 0
    seasonHoliday = 0
    apostleHoliday = 0
    stTibs = False

    seasons = ["Chaos", "Discord", "Confusion", "Bureaucracy", "The Aftermath"]
    weekdays = ["Sweetmorn", "Boomtime", "Pungenday", "Prickle-Prickle", "Setting Orange"]
    apostleHolidays = ["Mungday","Mojoday","Syaday","Zaraday","Maladay"]
    seasonHolidays = ["Chaoflux", "Discoflux", "Confuflux", "Bureflux", "Afflux"]

    def __init__(self):
        self.seasonNum = 0
        self.dayOfWeek = 0
        self.dayOfSeason = 0
        self.YOLD = 0
        self.seasonHoliday = False
        self.apostleHoliday = False
        self.stTibs = False

    def __str__(self):
        if(self.dStTibs):
            return "ST TIBS DAY!"
        else:
            msg = self.weekdays[self.dayOfWeek] +  \
                    u', the ' + showDayNum(self.dayOfSeason) + \
                    u' day of ' + self.seasons[self.seasonNum] + \
                    u' in the YOLD ' + `self.YOLD` + '.'
                if(self.seasonHoliday):
                    msg = msg + u' Celebrate ' + self.seasonHolidays[self.seasonNum] + '!'
                if(self.apostleHoliday):
                    msg = msg + u' Celebrate ' + self.apostleHolidays[self.seasonNum] + '!'
                return msg

    def checkHoliday(self, day):
        if(day==5):
            self.apostleHoliday = True
        if(day==50):
            self.seasonHoliday = True

    @classmethod
    def fromDate(klass, aDate):
        dayOfYear = aDate.timetuple()[7]
        correctedDay = leapYearCorrection(dayOfYear, aDate.year) - 1
        dd = klass.new()
        dd.dayOfSeason = (correctedDay % 73) + 1
        dd.dayOfWeek = (correctedDay % 5)
        dd.seasonNum = (correctedDay / 73)
        dd.YOLD = aDate.year + 1166
        dd.stTibs = isLeapYear(aDate.year) and (dayOfYear == 60)
        dd.checkHoliday(dd.dayOfSeason) 

    @classmethod
    def today(klass):
        return fromDate(date.today())
