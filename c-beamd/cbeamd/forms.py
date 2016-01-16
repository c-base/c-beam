from django import forms
from django.contrib.auth import authenticate
#from django.contrib.auth.models import User as DjangoUser
from cbeamd.models import Mission
from cbeamd.models import User

from django.utils.translation import ugettext_lazy as _

class LoginForm( forms.Form ):
    username = forms.CharField( max_length=255 )
    password = forms.CharField( max_length=255, widget=forms.PasswordInput )
    user_cache = None

    def clean( self ):
        #try:
            #username = User.objects.get( username =
#self.cleaned_data['username'] ).username
        #except:
            #raise forms.ValidationError( 'No such user exists.' )
        #print self.cleaned_data['username']
        #self.user_cache = authenticate( username=self.cleaned_data['username'],
#password=self.cleaned_data['password'] )
        #if self.user_cache is None:
            #raise forms.ValidationError( 'No such username/password exists.' )
        #elif not self.user_cache.is_active:
            #raise forms.ValidationError( 'This account has been blocked.' )
        #return self.cleaned_data
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if not user or not user.is_active:
            raise forms.ValidationError(_('Sorry, that login was invalid. '
                                          'Please try again.'), code='invalid_login')
        return self.cleaned_data

    def get_user( self ):
        return self.user_cache

class UserForm( forms.ModelForm ):
    class Meta:
        model = User
        fields = ['nickspell', 'stats_enabled', 'autologout', 'no_google']
        labels = {
            'nickspell': '',
            'stats_enabled': '',
            'autologout': '',
            'no_google': '',
        }
        widgets = {
        }

class MissionForm( forms.ModelForm ):
    class Meta:
        model = Mission
        fields = '__all__'
        widgets = {
                'description': forms.Textarea(attrs={'cols': 80, 'rows': 10})
        }

class StripeForm( forms.Form ):
    speed = forms.IntegerField(required=False)
    pattern = forms.IntegerField(required=False)
    offset = forms.IntegerField(required=False)

class LogActivityForm( forms.Form ):
    activity = forms.CharField()
    ap = forms.IntegerField()

class ActivityLogCommentForm( forms.Form ):
    comment = forms.CharField()
    thanks = forms.CharField(required=False)
    protest = forms.CharField(required=False)
