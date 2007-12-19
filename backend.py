from django_cas import verify, populate_user
from models import User

class CASBackend(object):
    def authenticate(self, ticket, service):
        username = verify(ticket, service)
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                # Password doesn't matter, it won't be used
                password = User.objects.make_random_password()
                user = User.objects.create_user(username, '', password)
                populate_user(user)
                user.save()
            else:
                # User has logged in before
                if not (user.first_name and user.last_name and user.email):
                    populate_user(user)
                    user.save()
            return user
        return None
    
    def get_user(self, user_id):
        """Retrieve the user's entry in the User model if it exists."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
