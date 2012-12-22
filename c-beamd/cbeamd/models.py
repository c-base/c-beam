from django.db import models

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

    
    def __str__(self):
        return self.username

class LTE(models.Model):
    day = models.CharField(max_length=2)
    username = username = models.CharField(max_length=200)
    eta = models.CharField(max_length=200)

    def __str__(self):
        return '%s %s %s' % (self.username, self.day, self.eta)

class Mission(models.Model):
    short_description = models.CharField(max_length=200)
    description = models.CharField(max_length=2000)
    #assigned_to = User()
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
         return self.short_description
