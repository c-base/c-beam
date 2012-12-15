from django.db import models

class User(models.Model):
    username = models.CharField(max_length=200)
    status = models.CharField(max_length=20)
    logintime = models.DateTimeField()
    logouttime = models.DateTimeField()
    eta = models.CharField(max_length=200)
    etatimestamp = models.DateTimeField(auto_now_add=True)
    nickspell = models.CharField(max_length=200)
    reminder = models.CharField(max_length=200)
    
    def __str__(self):
        return self.username

