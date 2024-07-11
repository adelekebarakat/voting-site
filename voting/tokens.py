from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six

class PasswordSetTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp) +
            six.text_type(user.has_set_password)
        )

password_set_token = PasswordSetTokenGenerator()