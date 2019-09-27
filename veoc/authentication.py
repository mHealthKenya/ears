from .models import contact

class UserBackend(object):
    """
    Authenticate using e-mail account.
    """
    def authenticate(self, username=None, password=None):
        try:
            user = contact.objects.get(email_address=username)
            if contact.objects.get(phone_number=password):
                return user
            return None
        except contact.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return contact.objects.get(pk=user_id)
        except contact.DoesNotExist:
            return None
