from django.db import models
from datetime import timedelta
from django.utils import timezone


class User(models.Model):
    username = models.CharField(max_length=200)
    status = models.CharField(max_length=20)
    logintime = models.DateTimeField()
    extendtime = models.DateTimeField(auto_now_add=True)
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
    ap = models.IntegerField(default=0)
    stats_enabled = models.BooleanField(default=False)
    rfid = models.CharField(max_length=200, default="")
    push_missions = models.BooleanField(default=True)
    push_boarding = models.BooleanField(default=True)
    push_eta = models.BooleanField(default=True)
    stealthmode = models.DateTimeField(auto_now_add=True, blank=True)
    no_google = models.BooleanField(default=False)

    def __str__(self):
        return self.username

    def dic(self):
        dic = {}
        dic['id'] = self.id
        dic['username'] = self.username
        dic['status'] = self.status
        dic['logintime'] = self.logintime
        dic['extendtime'] = str(self.extendtime)
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
        dic['ap'] = self.calc_ap()
        dic['stats_enabled'] = self.stats_enabled
        dic['push_missions'] = self.push_missions
        dic['push_boarding'] = self.push_boarding
        dic['push_eta'] = self.push_eta
        dic['rfid'] = self.rfid
        return dic

    def dic2(self):
        dic = {}
        dic['id'] = self.id
        dic['username'] = self.username
        dic['status'] = self.status
        dic['logintime'] = str(self.logintime)
        dic['extendtime'] = str(self.extendtime)
        dic['logouttime'] = str(self.logouttime)
        dic['eta'] = self.eta
        dic['etatimestamp'] = str(self.etatimestamp)
        dic['etd'] = self.etd
        dic['etdtimestamp'] = str(self.etdtimestamp)
        dic['nickspell'] = self.nickspell
        dic['reminder'] = self.reminder
        dic['remindertimestamp'] = str(self.remindertimestamp)
        dic['lastlocation'] = self.lastlocation
        dic['etasub'] = self.etasub
        dic['arrivesub'] = self.arrivesub
        dic['autologout'] = self.autologout
        dic['autologout_in'] = self.autologout_in()
        dic['wlanlogin'] = self.wlanlogin
        dic['ap'] = self.calc_ap()
        dic['stats_enabled'] = self.stats_enabled
        dic['push_missions'] = self.push_missions
        dic['push_boarding'] = self.push_boarding
        dic['push_eta'] = self.push_eta
        dic['rfid'] = self.rfid
        return dic

    def autologout_in(self):
        autologout_at = self.extendtime + timedelta(minutes=self.autologout)
        autologout_in = autologout_at - timezone.now()

        if self.status == "online" and autologout_in.total_seconds() > 0:
            return (autologout_in.total_seconds() / 60)
        return 0.0

    def online_percentage(self):
        return "%.2f" % (self.autologout_in() / self.autologout * 100)

    def calc_ap(self):
        sum = 0
        for activity in ActivityLog.objects.filter(user=self).filter(timestamp__gt=timezone.now() - timedelta(days=90)):
            sum += activity.ap
        # TODO fixme
        # if self.ap != sum:
        #    self.ap = sum
        #    self.save()
        return sum


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
    assigned_to = models.ManyToManyField(User, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(blank=True, null=True)
    priority = models.IntegerField(default=3, blank=True, null=True)
    ap = models.IntegerField(default=0)
    repeat_after_days = models.IntegerField(default=-1)
    completed_on = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.short_description

    def dic(self):
        dic = {}
        dic['id'] = self.id
        dic['short_description'] = self.short_description
        dic['description'] = self.description
        dic['status'] = self.status
        dic['created_on'] = self.created_on
        dic['due_date'] = self.due_date
        dic['priority'] = self.priority
        dic['ap'] = self.ap
        dic['assigned_to'] = [user.username for user in self.assigned_to.all()]
        return dic


class MissionLog(models.Model):
    mission = models.OneToOneField(Mission, on_delete=models.DO_NOTHING)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)


class Subscription(models.Model):
    regid = models.CharField(max_length=2000)
    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)

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


class Activity(models.Model):
    activity_type = models.CharField(max_length=200)
    activity_text = models.CharField(max_length=200)

    def __str__(self):
        return self.activity_text


class ActivityLogComment(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    comment = models.CharField(max_length=4000)
    comment_type = models.CharField(max_length=20)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def dic(self):
        return {'timestamp': str(self.timestamp), 'comment': self.comment, 'comment_type': self.comment_type}


class ActivityLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mission = models.ForeignKey(Mission, blank=True, null=True, on_delete=models.CASCADE)
    ap = models.IntegerField(default=0)
    protests = models.IntegerField(default=0)
    thanks = models.IntegerField(default=0)
    comments = models.ManyToManyField(ActivityLogComment, blank=True)

    def short_str(self):
        if self.activity.activity_type == "mission completed" and self.mission is not None:
            return "%s %s: %d AP: mission %d: %s" % (str(self.timestamp)[11:19], self.user.username, self.ap, self.mission.id, self.mission.short_description)
        else:
            return "%s %s: %d AP: %s" % (str(self.timestamp)[11:19], self.user.username, self.ap, self.activity.activity_text)

    def notification_str(self):
        if self.activity.activity_type == "mission completed" and self.mission is not None:
            return "%s: %d AP: mission %d: %s" % (self.user.username, self.ap, self.mission.id, self.mission.short_description)
        else:
            return "%s: %d AP: %s" % (self.user.username, self.ap, self.activity.activity_text)

    def __str__(self):
        if self.activity.activity_type == "mission completed" and self.mission is not None:
            return "%s %s erha:lt %d AP fu:r mission %d: %s" % (str(self.timestamp)[:19], self.user.username, self.ap, self.mission.id, self.mission.short_description)
        else:
            return "%s %s erha:lt %d AP fu:r %s" % (str(self.timestamp)[:19], self.user.username, self.ap, self.activity.activity_text)

    def dic(self):
        dic = {}
        dic['activity'] = self.activity.activity_text
        dic['timestamp'] = str(self.timestamp)[:26]
        dic['mission'] = {}
        dic['ap'] = self.ap
        dic['user'] = self.user.dic2()
        dic['str'] = self.short_str()
        dic['id'] = self.id
        dic['protests'] = self.protests
        dic['thanks'] = self.thanks
        dic['comments'] = [comment.dic()
                           for comment in self.comments.order_by('-timestamp')]
        return dic


class Status(models.Model):
    bar_open = models.BooleanField(default=False)
    airlock_stripe_mode = models.IntegerField(default=1)
    airlock_volume = models.IntegerField(default=42)
