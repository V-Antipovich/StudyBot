from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

from .models import UploadGtd, RegUser
# from .apps import user_registered


class GtdFileForm(forms.Form):
    file = forms.FileField()


class UploadGtdfilesForm(forms.Form):
    comment = forms.CharField(max_length=255, required=False)
    document = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), validators=[FileExtensionValidator(allowed_extensions=['xml'])])


# TODO: Вернуться потом, когда будет работа над юзерами
# class RegisterUserForm(forms.ModelForm):
#     email = forms.EmailField(required=True, label='Адрес электронной почты')
#     password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput,
#                                 help_text=password_validation.password_validators_help_text_html())
#     password2 = forms.CharField(label='Пароль повторно',
#                                 widget=password_validation.password_validators_help_text_html(),
#                                 help_text='Введите тот же самый пароль ещё раз для проверки')
#
#     class Meta:
#         model = RegUser
#         fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
#
#     def clean_password1(self):
#         password1 = self.cleaned_data['password1']
#         if password1:
#             password_validation.validate_password(password1)
#
#     def clean(self):
#         super().clean()
#         password1 = self.cleaned_data['password1']
#         password2 = self.cleaned_data['password2']
#         if password1 and password2 and password2 != password1:
#             errors = {'password2': ValidationError('Введенные пароли не совпадают',
#                                                    code='password_mismatch')}
#             raise ValidationError(errors)
#
#     def save(self, commit=True):
#         user = super().save(commit=True)
#         user.set_password(self.cleaned_data['password1'])
#         if commit:
#             user.save()

