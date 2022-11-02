import time

from django import forms
from django.contrib.auth import password_validation, get_user_model, authenticate
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

from .models import UploadGtd, RegUser, GtdMain, Exporter, Importer, CustomsHouse, GtdGood, GtdGroup
from .apps import user_registered
from customs_declarations_database.settings import USER_DIR
# from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
# class GtdFileForm(forms.Form):
#     file = forms.FileField()

# User = get_user_model()


class ChangeUserInfoForm(forms.ModelForm):
    email = forms.EmailField(required=True, label='Адрес электронной почты')

    class Meta:
        model = RegUser
        fields = ('username', 'email', 'first_name', 'last_name', 'patronymic',)


class RegisterUserForm(forms.ModelForm):
    email = forms.EmailField(required=True, label='Адрес электронной почты')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput,
                               help_text=password_validation.password_validators_help_text_html())

    class Meta:
        model = RegUser #TODO: устанавливать группу
        fields = ('username', 'email', 'password', 'first_name', 'last_name', 'patronymic', 'groups')
        # exclude = ('is_activated',)

    def clean_password(self):
        psw = self.cleaned_data['password']
        if psw:
            password_validation.validate_password(psw)
        return psw

    def save(self, commit=True):
        user = super().save(commit=False)
        psw = self.cleaned_data['password']
        user.set_password(psw)
        user.is_active = False
        user.is_activated = False
        if commit:
            user.save()
        # user_registered.send(RegisterUserForm, instance=user)
        user_registered.send(RegisterUserForm, instance=user, password=psw)
        return user


# Форма для xml-файлов ГТД
class UploadGtdfilesForm(forms.Form):
    comment = forms.CharField(max_length=255, required=False, label='Комментарий (если требуется)')
    document = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}),
                               validators=[FileExtensionValidator(allowed_extensions=['xml'])], label='Документы')
    on_duplicate = forms.ChoiceField(choices=(('skip', 'Пропускать'), ('update', 'Обновлять')),
                                     label='Если среди загружаемых ГТД встретятся '
                                               'объекты с номерами, уже присутствующими в базе:')


# Форма редактирования шапки ГТД
class GtdUpdateForm(forms.ModelForm):

    class Meta:
        model = GtdMain
        fields = ('gtdId', 'customs_house', 'total_goods_number', 'exporter',
                  'importer', 'trading_country', 'currency', 'total_invoice_amount', 'currency_rate',
                  'deal_type',)
        labels = {
            'customs_house': 'Таможенный отдел',
            'exporter': 'Экспортер',
            'importer': 'Импортер',
            'trading_country': 'Торгующая страна',
            'currency': 'Валюта',
            'deal_type': 'Характер сделки',
        }


# Форма редактирования групп ГТД
class GtdGroupUpdateForm(forms.ModelForm):

    class Meta:
        model = GtdGroup
        exclude = ('gtd', 'last_edited_user',)


# Форма редактирования товаров ГТД
class GtdGoodUpdateForm(forms.ModelForm):

    class Meta:
        model = GtdGood
        # fields = '__all__'
        exclude = ('gtd', 'good_num', 'last_edited_user',)
        labels = {
            'good': 'Товар',
            'group': 'Группа товаров',
            'qualifier': 'Единица измерения',
            'manufacturer': 'Производитель',
        }


# Форма для подготовки к формированию xml для WMS
class ExportComment(forms.Form):
    comment = forms.CharField(widget=forms.Textarea(attrs={'rows': 2, 'cols': 50}), required=False,
                              label='Добавьте комментарий/описание, если требуется')


# class ErpExportComment(forms.Form):
#     comment = forms.CharField(widget=forms.Textarea, required=False,
#                               label='Добавьте комментарий/описание, если требуется')


# Форма выбора диапазона дат
class CalendarDate(forms.Form):
    start_date = forms.DateField(label='Начало диапазона', input_formats=['%d-%m-%Y'],
                                 widget=forms.DateInput(attrs={'type': 'date',
                                                               'class': 'form-control',
                                                               'placeholder': 'dd-mm-YYYY'}))

    end_date = forms.DateField(label='Конец диапазона', input_formats=['%d-%m-%Y'],
                               widget=forms.DateInput(attrs={'type': 'date',
                                                             'class': 'form-control',
                                                             'placeholder': 'dd-mm-YYYY'}
                                                      ))

    # def clean(self):
    #     cleaned_data = super().clean()
    #     start_date = cleaned_data.get('start_date')
    #     end_date = cleaned_data.get('end_date')
    #     if start_date and end_date:
    #         if start_date < end_date:
    #             raise ValidationError('Неправильный диапазон')
        # print(start_date, end_date)
        # print(cleaned_data)
        # if start_date > end_date:
        #     raise ValidationError('Неправильный диапазон дат')
    # def is_valid(self):
    #     condition = super(CalendarDate, self).is_valid()
    #     print(self.cleaned_data)
    #     return condition


# Валидатор дат
def validate_date_range(start, end):
    start = time.strptime(start, '%d-%m-%Y')
    end = time.strptime(end, '%d-%m-%Y')
    if start >= end:
        raise ValidationError('Вы не можете выбрать такой диапазон дат')


# # Форма регистрации пользователя
# class RegisterUserForm(forms.ModelForm):
#     email = forms.EmailField(required=True, label='Адрес электронной почты')
#     password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput,
#                                 help_text=password_validation.password_validators_help_text_html())
#     password2 = forms.CharField(label='Пароль (повторно)', widget=forms.PasswordInput,
#                                 help_text='Введите тот же самый пароль ещё раз для проверки')
#
#     def clean_password1(self):
#         password1 = self.cleaned_data['password1']
#         if password1:
#             password_validation.validate_password(password1)
#         return password1
#
#     def clean(self):
#         super().clean()
#         password1 = self.cleaned_data['password1']
#         password2 = self.cleaned_data['password2']
#         if password1 and password2 and password2 != password1:
#             errors = {'password2': ValidationError("Введенные пароли не совпадают", code='password_mismatch')}
#             raise ValidationError(errors)
#
#     def save(self, commit=True):
#         user = super().save(commit=False)
#         user.set_password(self.cleaned_data['password1'])
#         user.is_active = False
#         user.is_activated = False
#         if commit:
#             user.save()
#         return user
#
#     class Meta:
#         model = RegUser
#         fields = ('username', 'email', 'password1', 'password2',)
