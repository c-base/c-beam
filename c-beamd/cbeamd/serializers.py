from django.contrib.auth.models import User
from rest_framework import serializers
from .models import User as CBeamUser, Mission, ActivityLog, Status


class UserSerializer(serializers.ModelSerializer):
    """Serializer for C-Beam User model."""
    autologout_in = serializers.SerializerMethodField()
    online_percentage = serializers.SerializerMethodField()
    ap = serializers.SerializerMethodField()

    class Meta:
        model = CBeamUser
        fields = [
            'id', 'username', 'status', 'logintime', 'extendtime', 'logouttime',
            'eta', 'etatimestamp', 'etd', 'etdtimestamp', 'nickspell', 'reminder',
            'remindertimestamp', 'lastlocation', 'etasub', 'arrivesub', 'autologout',
            'autologout_in', 'wlanlogin', 'ap', 'stats_enabled', 'rfid',
            'push_missions', 'push_boarding', 'push_eta', 'stealthmode', 'no_google',
            'online_percentage'
        ]
        read_only_fields = ['id', 'autologout_in', 'online_percentage', 'ap']

    def get_autologout_in(self, obj):
        return obj.autologout_in()

    def get_online_percentage(self, obj):
        return obj.online_percentage()

    def get_ap(self, obj):
        return obj.calc_ap()


class MissionSerializer(serializers.ModelSerializer):
    """Serializer for Mission model."""
    assigned_users = serializers.SerializerMethodField()

    class Meta:
        model = Mission
        fields = [
            'id', 'short_description', 'long_description', 'status', 'ap',
            'assigned_to', 'assigned_users', 'created_on', 'completed_on',
            'repeat_after_days'
        ]
        read_only_fields = ['id', 'created_on', 'completed_on']

    def get_assigned_users(self, obj):
        return [user.username for user in obj.assigned_to.all()]


class ActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for ActivityLog model."""
    user = serializers.CharField(source='user.username', read_only=True)
    activity = serializers.CharField(source='activity.activity_text', read_only=True)

    class Meta:
        model = ActivityLog
        fields = [
            'id', 'user', 'activity', 'ap', 'timestamp', 'mission',
            'thanks', 'protests'
        ]
        read_only_fields = ['id', 'timestamp']


class StatusSerializer(serializers.ModelSerializer):
    """Serializer for Status model."""

    class Meta:
        model = Status
        fields = ['bar_open']
