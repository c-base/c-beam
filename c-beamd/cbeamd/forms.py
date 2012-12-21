from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

class LoginForm( forms.Form ):
    username = forms.CharField( max_length=255 )
    password = forms.CharField( max_length=255, widget=forms.PasswordInput )
    user_cache = None

    def clean( self ):
        try:
            username = User.objects.get( username =
self.cleaned_data['username'] ).username
        except:
            raise forms.ValidationError( 'No such user exists.' )
        self.user_cache = authenticate( username=username,
password=self.cleaned_data['password'] )
        if self.user_cache is None:
            raise forms.ValidationError( 'No such username/password exists.' )
        elif not self.user_cache.is_active:
            raise forms.ValidationError( 'This account has been blocked.' )
        return self.cleaned_data

    def get_user( self ):
        return self.user_cache

