import pytest
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from cbeamd.models import User, Activity, ActivityLog


class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username='testuser',
            status='online',
            logintime=timezone.now(),
            logouttime=timezone.now() + timedelta(hours=1),
            autologout=600
        )

    def test_user_creation(self):
        """Test that a user can be created and has correct default values"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.status, 'online')
        self.assertEqual(self.user.autologout, 600)

    def test_to_dict_method(self):
        """Test the to_dict method returns correct data"""
        data = self.user.to_dict()
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['status'], 'online')
        self.assertIn('id', data)

    def test_to_dict_with_stringify(self):
        """Test the to_dict method with stringify_datetimes=True"""
        data = self.user.to_dict(stringify_datetimes=True)
        self.assertIsInstance(data['logintime'], str)
        self.assertIsInstance(data['extendtime'], str)

    def test_calc_ap_method(self):
        """Test the calc_ap method calculates AP correctly"""
        # Create activity and activity log
        activity = Activity.objects.create(
            activity_type='test',
            activity_text='Test activity'
        )

        ActivityLog.objects.create(
            activity=activity,
            user=self.user,
            ap=10
        )

        ActivityLog.objects.create(
            activity=activity,
            user=self.user,
            ap=5
        )

        # Create old activity (more than 90 days ago)
        old_time = timezone.now() - timedelta(days=100)
        old_log = ActivityLog.objects.create(
            activity=activity,
            user=self.user,
            ap=100
        )
        old_log.timestamp = old_time
        old_log.save()

        total_ap = self.user.calc_ap()
        self.assertEqual(total_ap, 15)  # Only recent activities (10 + 5)


class ActivityLogModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username='testuser',
            status='online',
            logintime=timezone.now(),
            logouttime=timezone.now() + timedelta(hours=1)
        )
        self.activity = Activity.objects.create(
            activity_type='test',
            activity_text='Test activity'
        )

    def test_activity_log_creation(self):
        """Test that activity logs can be created"""
        log = ActivityLog.objects.create(
            activity=self.activity,
            user=self.user,
            ap=10
        )

        self.assertEqual(log.ap, 10)
        self.assertEqual(log.user.username, 'testuser')
        self.assertEqual(log.activity.activity_text, 'Test activity')

    def test_short_str_method(self):
        """Test the short_str method formats correctly"""
        log = ActivityLog.objects.create(
            activity=self.activity,
            user=self.user,
            ap=10
        )

        short_str = log.short_str()
        self.assertIn('testuser', short_str)
        self.assertIn('10 AP', short_str)
        self.assertIn('Test activity', short_str)