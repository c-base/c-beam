from django.db import models

class AvailableUsers(models.Model):
    username = models.CharField(max_length=200)
    #logintime = models.CharField(max_length=200)
    def __str__(self):
        return self.username

class ETA(models.Model):
    username = models.CharField(max_length=200)
    eta = models.CharField(max_length=200)
    def __str__(self):
        return "%s (%s)" % (self.username, self.eta)
