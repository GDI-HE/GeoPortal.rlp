from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

class CustomPasswordValidator:
    def validate(self, password, user=None):
        if len(password) < 9:
            raise ValidationError(_("Password must be at least 9 characters long."))
        if not any(char.isdigit() for char in password):
            raise ValidationError(_("Password must contain at least one digit."))
        if not any(char.isupper() for char in password):
            raise ValidationError(_("Password must contain at least one uppercase letter."))
        if not any(char.islower() for char in password):
            raise ValidationError(_("Password must contain at least one lowercase letter."))

    def get_help_text(self):
        return _("Your password must contain at least 9 characters, one digit, one uppercase letter, and one lowercase letter.")
