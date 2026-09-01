from django.db import models
from datetime import timedelta
from django.utils import timezone
from typing import Dict, Any


class User(models.Model):
    username = models.CharField(max_length=200, unique=True)
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
    rfid = models.CharField(max_length=200, default="", blank=True)
    push_missions = models.BooleanField(default=True)
    push_boarding = models.BooleanField(default=True)
    push_eta = models.BooleanField(default=True)
    stealthmode = models.DateTimeField(auto_now_add=True, blank=True)
    no_google = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['status']),
            models.Index(fields=['logintime']),
        ]

    def __str__(self) -> str:
        return self.username

    def to_dict(self, stringify_datetimes: bool = False) -> Dict[str, Any]:
        """Convert User instance to dictionary.

        Args:
            stringify_datetimes: If True, convert datetime objects to strings
        """
        data = {
            'id': self.id,
            'username': self.username,
            'status': self.status,
            'logintime': str(self.logintime) if stringify_datetimes else self.logintime,
            'extendtime': str(self.extendtime) if stringify_datetimes else self.extendtime,
            'logouttime': str(self.logouttime) if stringify_datetimes else self.logouttime,
            'eta': self.eta,
            'etatimestamp': str(self.etatimestamp) if stringify_datetimes else self.etatimestamp,
            'etd': self.etd,
            'etdtimestamp': str(self.etdtimestamp) if stringify_datetimes else self.etdtimestamp,
            'nickspell': self.nickspell,
            'reminder': self.reminder,
            'remindertimestamp': str(self.remindertimestamp) if stringify_datetimes else self.remindertimestamp,
            'lastlocation': self.lastlocation,
            'etasub': self.etasub,
            'arrivesub': self.arrivesub,
            'autologout': self.autologout,
            'autologout_in': self.autologout_in(),
            'wlanlogin': self.wlanlogin,
            'ap': self.calc_ap(),
            'stats_enabled': self.stats_enabled,
            'push_missions': self.push_missions,
            'push_boarding': self.push_boarding,
            'push_eta': self.push_eta,
            'rfid': self.rfid,
        }
        return data

    # Backward compatibility
    def dic(self) -> Dict[str, Any]:
        return self.to_dict(stringify_datetimes=False)

    def dic2(self) -> Dict[str, Any]:
        return self.to_dict(stringify_datetimes=True)

    def autologout_in(self):
        autologout_at = self.extendtime + timedelta(minutes=self.autologout)
        autologout_in = autologout_at - timezone.now()

        if self.status == "online" and autologout_in.total_seconds() > 0:
            return (autologout_in.total_seconds() / 60)
        return 0.0

    def online_percentage(self):
        # autologout is a user-editable field; 0 would otherwise take down every
        # view that renders a user list
        if not self.autologout:
            return "0.00"
        return "%.2f" % (self.autologout_in() / self.autologout * 100)

    def calc_ap(self) -> int:
        """Calculate total AP for this user from activities in the last 90 days."""
        from django.db.models import Sum

        ninety_days_ago = timezone.now() - timedelta(days=90)
        result = ActivityLog.objects.filter(
            user=self,
            timestamp__gte=ninety_days_ago
        ).aggregate(total_ap=Sum('ap'))

        return result['total_ap'] or 0


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

    class Meta:
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['activity']),
        ]
        ordering = ['-timestamp']

    def short_str(self) -> str:
        if self.activity.activity_type == "mission completed" and self.mission is not None:
            return f"{self.timestamp.strftime('%H:%M:%S')} {self.user.username}: {self.ap} AP: mission {self.mission.id}: {self.mission.short_description}"
        else:
            return f"{self.timestamp.strftime('%H:%M:%S')} {self.user.username}: {self.ap} AP: {self.activity.activity_text}"

    def notification_str(self) -> str:
        if self.activity.activity_type == "mission completed" and self.mission is not None:
            return f"{self.user.username}: {self.ap} AP: mission {self.mission.id}: {self.mission.short_description}"
        else:
            return f"{self.user.username}: {self.ap} AP: {self.activity.activity_text}"

    def __str__(self) -> str:
        if self.activity.activity_type == "mission completed" and self.mission is not None:
            return f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} {self.user.username} erha:lt {self.ap} AP fu:r mission {self.mission.id}: {self.mission.short_description}"
        else:
            return f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} {self.user.username} erha:lt {self.ap} AP fu:r {self.activity.activity_text}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert ActivityLog instance to dictionary."""
        return {
            'activity': self.activity.activity_text,
            'timestamp': self.timestamp.isoformat()[:26],
            'mission': {},
            'ap': self.ap,
            'user': self.user.to_dict(stringify_datetimes=True),
            'str': self.short_str(),
            'id': self.id,
            'protests': self.protests,
            'thanks': self.thanks,
            'comments': [comment.dic() for comment in self.comments.order_by('-timestamp')],
        }

    # Backward compatibility
    def dic(self) -> Dict[str, Any]:
        return self.to_dict()


class Status(models.Model):
    bar_open = models.BooleanField(default=False)
    airlock_stripe_mode = models.IntegerField(default=1)
    airlock_volume = models.IntegerField(default=42)
