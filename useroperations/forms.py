from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import ugettext_lazy as _
from captcha.fields import CaptchaField
from django.utils.safestring import mark_safe
from Geoportal.settings import USE_RECAPTCHA
from django.core.exceptions import ValidationError

#Validation error if user use other characters than numbers and the allowed characters
def validate_phone_number(value):
    """
    Custom validator for the phone number field.
    It ensures that the phone number contains only digits and a limited set of characters.
    """
    allowed_characters = set("0123456789()+- ")  # Define the allowed characters here
    invalid_characters = set(value) - allowed_characters

    if invalid_characters:
        raise forms.ValidationError(_("Please enter a valid phone number."))

class FeedbackForm(forms.Form):
    first_name = forms.CharField(max_length=200, label=_("First name"), required=False, widget=forms.TextInput(attrs={'title':_("Please enter your first name.")}))
    family_name = forms.CharField(max_length=200, label=_("Family name"), required=False, widget=forms.TextInput(attrs={'title':_("Please enter your last name.")}))
    email = forms.EmailField(label=_("E-Mail address"),  widget=forms.EmailInput(attrs={'title':_("Please enter your email.")}))
    message = forms.CharField(label=_("Your Message"), widget=forms.Textarea(attrs={"maxlength": 3000, 'title':_("Please enter your message.")}))
    identity = forms.CharField(max_length=255, label=_("identity"), required=False, widget=forms.TextInput(attrs={'title':_("Identity.")}))
    if USE_RECAPTCHA == 0:
        captcha = CaptchaField(label=_("I'm not a robot"))

class RegistrationForm(forms.Form):
    name = forms.CharField(max_length=100, label=_("Username"), widget=forms.TextInput(attrs={'id': 'username','title':_("Please enter your username."),'required': 'required'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'id': 'password','title': _("Please enter a password that is at least 9 characters long, includes at least one uppercase letter, one lowercase letter, and one number."),'required': 'required','pattern': "(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{9,}"}),label=_("Password"))
    passwordconfirm = forms.CharField(widget=forms.PasswordInput(attrs={'id': 'id_passwordconfirm','title': _("Please confirm your password."), 'required': 'required', 'pattern': ".{9,}"}),label=_("Password Confirmation"))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'id': 'email','title':_("Please enter your email.")}))
    organization = forms.CharField(max_length=100, label=_("Organization"), required=False, widget=forms.TextInput(attrs={'title': _("Please enter the organization you are working for.")}))
    department = forms.CharField(max_length=100, label=_("Department"), required=False, widget=forms.TextInput(attrs={'title':_("Please enter the departement you are working in.")}))
    phone = forms.CharField(max_length=100, label=_("Phone"), required=False,widget=forms.TextInput(attrs={'type': 'tel', 'id':'phone_field_id','title': _("Please enter your phone number."), 'pattern': '^\d+$'}), validators=[validate_phone_number])
    description = forms.CharField(max_length=255, label=_("Description"), required=False, widget=forms.TextInput(attrs={'id':'id_description','title':_("Please enter a description."), 'maxlength':'255'}))
    identity = forms.CharField(max_length=255, label=_("identity"), required=False, widget=forms.TextInput(attrs={'title':_("Identity.")}))
    dsgvo = forms.BooleanField(initial=False, label=_("I understand and accept that my data will be automatically processed and securely stored, as it is stated in the general data protection regulation (GDPR)."), required=True, widget=forms.CheckboxInput(attrs={'title':_("Accept privacy policy."), 'required': 'required'}))
    if USE_RECAPTCHA == 0:
        captcha = CaptchaField(label=_("I'm not a robot"))
        
        def __init__(self, *args, **kwargs):
            super(RegistrationForm, self).__init__(*args, **kwargs)
            self.fields['captcha'].widget.attrs.update({
                'title': _('Please confirm that you are not a robot.'),
            })


class LoginForm(forms.Form):
    name = forms.CharField(max_length=100, label=_("Username"), widget=forms.TextInput(attrs={'title':_("Please enter your username."), 'autofocus': 'autofocus'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'id': 'login_password', 'title': _("Please enter your password.")}), label=_("Password"))

class ChangeProfileForm(forms.Form):
    oldpassword = forms.CharField(required=True, widget=forms.PasswordInput(attrs={'id': 'change_profile_oldpassword', 'title': _("Please enter your password.")}), label=_("Current password"))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'id': 'change_profile_password', 'title': _("Please enter a password that is at least 9 characters long, includes at least one uppercase letter, one lowercase letter, and one number."), 'pattern': "(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{9,}"}), label=_("New password"), required=False)
    passwordconfirm = forms.CharField(widget=forms.PasswordInput(attrs={'id': 'change_profile_passwordconfirm', 'title': _("Please confirm your password."), 'pattern':".{9,}"}), label=_("Password confirmation"), required=False)
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'id': 'change_profile_email', 'title':_("Please enter your email.")}))
    organization = forms.CharField(max_length=100, label=_("Organization"), required=False, widget=forms.TextInput(attrs={'title': _("Please enter the organization you are working for.")}))
    department = forms.CharField(max_length=100, label=_("Departement"), required=False, widget=forms.TextInput(attrs={'title':_("Please enter the departement you are working in.")}))
    phone = forms.CharField(max_length=100, label=_("Phone"), required=False,widget=forms.TextInput(attrs={'type': 'tel', 'id':'phone_field_id','title': _("Please enter your phone number.")}), validators=[validate_phone_number])
    description = forms.CharField(max_length=1000, label=_("Description"), required=False, widget=forms.TextInput(attrs={'title':_("Please enter a description.")}))
    preferred_gui = forms.CharField(max_length=100, label=mark_safe(_("Preferred viewer") + ' (<a href="/mediawiki/index.php/PreferredViewer" target="_blank">' + str(_("Info")) + '</a>)'), required=False, widget=forms.Select(choices=[('Geoportal-Hessen','Geoportal-Hessen-Classic'),('Geoportal-Hessen-2019','Geoportal-Hessen-2019')]))
    create_digest = forms.BooleanField(initial=False, label=_("Use HTTP Digest Authentication for secured Services"), required=False, widget=forms.CheckboxInput(attrs={'title':_("Use HTTP Digest Authentication for secured Services.")}))
    dsgvo = forms.BooleanField(initial=False, label=mark_safe(_("I understand and accept that my data will be automatically processed and securely stored, as it is stated in the general data protection regulation (GDPR).") + '(<a href="/article/Datenschutz" target="_blank">' + str(_("privacy policy")) + '</a>)'), required=False, widget=forms.CheckboxInput(attrs={'title':_("Accept privacy policy.")}))

class PasswordResetForm(forms.Form):
    name = forms.CharField(max_length=100, label=_("Username"), widget=forms.TextInput(attrs={'title':_("Please enter your username."), 'autofocus': 'autofocus'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'title':_("Please enter your email.")}))

class DeleteProfileForm(forms.Form):
    helper = FormHelper()

class PasswordResetConfirmForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={'id': 'new_password','title': _("Please enter a password that is at least 9 characters long, includes at least one uppercase letter, one lowercase letter, and one number."),'required': 'required','pattern': "(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{9,}", 'autofocus': 'autofocus'}),label=_("New password"))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'id': 'confirm_password', 'title': _("Please confirm your new password."), 'required': 'required', 'pattern': "(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{9,}"}), label=_("Confirm new password"))

