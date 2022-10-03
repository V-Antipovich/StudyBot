import time

from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

from .models import UploadGtd, RegUser, GtdMain, Exporter, Importer, CustomsHouse, GtdGood, GtdGroup
# from .apps import user_registered


class GtdFileForm(forms.Form):
    file = forms.FileField()


class UploadGtdfilesForm(forms.Form):
    comment = forms.CharField(max_length=255, required=False, label='Комментарий (если требуется)')
    document = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}),
                               validators=[FileExtensionValidator(allowed_extensions=['xml'])], label='Документы')
    on_duplicate = forms.ChoiceField(choices=(('skip', 'Пропускать'), ('update', 'Обновлять')),
                                     label='Если среди загружаемых ГТД встретятся '
                                               'объекты с номерами, уже присутствующими в базе:')


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


class GtdGroupUpdateForm(forms.ModelForm):

    class Meta:
        model = GtdGroup
        exclude = ('gtd', 'last_edited_user',)


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


class CalendarDate(forms.Form):
    start_date = forms.DateField(label='Начало диапазона',
                                 widget=forms.DateInput(attrs={'type': 'date',
                                                             'class': 'form-control',
                                                             'placeholder': 'Начало диапазона'}))
    end_date = forms.DateField(label='Окончание',
                               widget=forms.DateInput(attrs={'type': 'date',
                                                             'class': 'form-control',
                                                             'placeholder': 'Конец диапазона'}))

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date > end_date:
            raise ValidationError('Неправильный диапазон дат')
    

def validate_date_range(start, end):
    start = time.strptime(start, '%Y-%m-%d')
    end = time.strptime(end, '%Y-%m-%d')
    if start >= end:
        raise ValidationError('Вы не можете выбрать такой диапазон дат')

# TODO: Вернуться потом к написанию нормальной формы для регистрации, когда будет работа над юзерами
# TODO: прямо сейчас сесть писать нормальную рабочую форму для регистрации.
# class TestRegForm(forms.ModelForm):
#     password = forms.CharField(label='Пароль', widget=forms.PasswordInput)
#     password2 = forms.CharField(label='Повторите пароль', widget=forms.PasswordInput)
#
#     class Meta:
#         model = RegUser
#         fields = ('username', 'email')
#
#     def clean_password2(self):
#         cd = self.cleaned_data
#         if cd['password'] != cd['password2']:
#             raise forms.ValidationError('Пароли не совпадают')
#         return cd['password2']
class RegisterUserForm(forms.ModelForm):
    email = forms.EmailField(required=True, label='Адрес электронной почты')
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput,
                                help_text=password_validation.password_validators_help_text_html())
    password2 = forms.CharField(label='Пароль (повторно)', widget=forms.PasswordInput,
                                help_text='Введите тот же самый пароль ещё раз для проверки')

    def clean_password1(self):
        password1 = self.cleaned_data['password1']
        if password1:
            password_validation.validate_password(password1)
        return password1

    def clean(self):
        super().clean()
        password1 = self.cleaned_data['password1']
        password2 = self.cleaned_data['password2']
        if password1 and password2 and password2 != password1:
            errors = {'password2': ValidationError("Введенные пароли не совпадают", code='password_mismatch')}
            raise ValidationError(errors)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.is_active = False
        user.is_activated = False
        if commit:
            user.save()
        return user

    class Meta:
        model = RegUser
        fields = ('username', 'email', 'password1', 'password2',)
