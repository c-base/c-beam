from django.db import models
from datetime import timedelta
from django.utils import timezone

class User(models.Model):
    username = models.CharField(max_length=200)
    status = models.CharField(max_length=20)
    logintime = models.DateTimeField()
    logouttime = models.DateTimeField()
    eta = models.CharField(max_length=200, blank=True)
    etatimestamp = models.DateTimeField(auto_now_add=True)
    etd = models.CharField(max_length=200, blank=True)
    etdtimestamp = models.DateTimeField(auto_now_add=True)
    nickspell = models.CharField(max_length=200, blank=True)
    reminder = models.CharField(max_length=200, blank=True)
    remindertimestamp = models.DateTimeField(auto_now_add=True, blank=True)
    lastlocation = models.CharField(max_length=200, blank=True)
    etasub = models.BooleanField(default=False)
    arrivesub = models.BooleanField(default=False)
    autologout = models.IntegerField(default=600)
    wlanlogin = models.BooleanField(default=False)

    def __str__(self):
        return self.username

    def dic(self):
        dic = {}
        dic['id'] = self.id
        dic['username'] = self.username
        dic['status'] = self.status
        dic['logintime'] = self.logintime
        dic['logouttime'] = self.logouttime
        dic['eta'] = self.eta
        dic['etatimestamp'] = self.etatimestamp
        dic['etd'] = self.etd
        dic['etdtimestamp'] = self.etdtimestamp
        dic['nickspell'] = self.nickspell
        dic['reminder'] = self.reminder
        dic['remindertimestamp'] = self.remindertimestamp
        dic['lastlocation'] = self.lastlocation
        dic['etasub'] = self.etasub
        dic['arrivesub'] = self.arrivesub
        dic['autologout'] = self.autologout
        dic['autologout_in'] = self.autologout_in()
        dic['wlanlogin'] = self.wlanlogin
        return dic

    def autologout_in(self):
        autologout_at = self.logintime + timedelta(minutes=self.autologout)
        autologout_in = autologout_at - timezone.now()
        return (autologout_in.total_seconds()/60)


class LTE(models.Model):
    day = models.CharField(max_length=2)
    username = username = models.CharField(max_length=200)
    eta = models.CharField(max_length=200)

    def __str__(self):
        return '%s %s %s' % (self.username, self.day, self.eta)

class Mission(models.Model):
    short_description = models.CharField(max_length=200)
    description = models.CharField(max_length=2000)
    status = models.CharField(max_length=200)
    #assigned_to = User()
    created_on = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(blank=True)
    priority = models.IntegerField(default=3, blank=True)

    def __str__(self):
         return self.short_description

    def dic(self):
        dic = {}
        print self.id
        dic['id'] = self.id
        dic['short_description'] = self.short_description
        dic['description'] = self.description
        dic['status'] = self.status
        dic['created_on'] = self.created_on
        dic['due_date'] = self.due_date
        dic['priority'] = self.priority
        return dic

class Subscription(models.Model):
    regid = models.CharField(max_length="2000")
    user = models.OneToOneField(User, primary_key=True)

    def __str__(self):
        return "%s: %s" % (self.user.username, self.regid)

class Event(models.Model):
    uid = models.CharField(max_length=200)
    start = models.CharField(max_length=20)
    end = models.CharField(max_length=20)
    title = models.CharField(max_length=200)


class UserStatsEntry(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    usercount = models.IntegerField(default=0)
    etacount = models.IntegerField(default=0)

    def __str__(self):
        return "%s: %d" % (str(self.timestamp), self.usercount)

