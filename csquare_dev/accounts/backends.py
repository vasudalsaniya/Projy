from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailBackend(ModelBackend):
    """
    Custom authentication backend to login using Email instead of Username.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # 'username' here is just the name of the argument from the form.
        # We will treat it as an email.
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            return None
        
        # Check the password and ensure the user is allowed to login (is_active)
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None