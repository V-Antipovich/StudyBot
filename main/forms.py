import time

from django import forms
from django.contrib.auth import password_validation, get_user_model, authenticate
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

from .models import UploadGtd, RegUser, GtdMain, Exporter, Importer, CustomsHouse, GtdGood, GtdGroup, TnVed, Country, \
    Procedure, Good, MeasureQualifier, Manufacturer
from .apps import user_registered


value_cannot_be_negative = 'Это значение не может быть отрицательным'


class PaginateForm(forms.Form):
    # paginate_by = forms.IntegerField(help_text='Кол-во записей на странице')
    paginate_by = forms.ChoiceField(help_text='По сколько записей располагать на странице', choices=(
        (1, '10'),
        (2, '25'),
        (3, '50'),
        (4, '100'),
    ))

    def clean(self):
        cleaned_data = super().clean()
        paginate_by = cleaned_data['paginate_by']
        if type(paginate_by) != int and paginate_by <= 0:
            self.add_error('paginate_by', 'Число должно быть целым и положительным')


# TODO: Отдельная форма для админов, где можно редачить и роль
# Редактирование данных пользователя
class ChangeUserInfoForm(forms.ModelForm):
    email = forms.EmailField(required=True, label='Адрес электронной почты')

    class Meta:
        model = RegUser
        fields = ('username', 'email', 'first_name', 'last_name', 'patronymic',)


# Форма регистрации пользователя
class RegisterUserForm(forms.ModelForm):
    email = forms.EmailField(required=True, label='Адрес электронной почты')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput,
                               help_text=password_validation.password_validators_help_text_html())

    class Meta:
        model = RegUser
        fields = ('username', 'email', 'password', 'first_name', 'last_name', 'patronymic', 'groups')

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
        user_registered.send(RegisterUserForm, instance=user, password=psw)  # Сигнал отсылать письмо
        return user


# Форма для xml-файлов ГТД
class UploadGtdfilesForm(forms.Form):
    comment = forms.CharField(max_length=255, required=False, label='Комментарий (если требуется)')
    document = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}),
                               validators=[FileExtensionValidator(allowed_extensions=['xml'])], label='Документы')
    on_duplicate = forms.ChoiceField(choices=(('skip', 'Пропускать'), ('update', 'Обновлять')),
                                     label='Если среди загружаемых ГТД встретятся '
                                               'объекты с номерами, уже присутствующими в базе:')


# class GtdGoodCreateForm(forms.ModelForm):
#
#     class Meta:
#         model = GtdGood


# Форма редактирования шапки ГТД
class GtdUpdateForm(forms.ModelForm):

    class Meta:
        model = GtdMain
        fields = ('customs_house', 'total_goods_number', 'exporter',
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
class GtdGroupCreateUpdateForm(forms.ModelForm):
    tn_ved = forms.ModelChoiceField(queryset=TnVed.objects.order_by('code'), label='ТН ВЭД', empty_label=None)
    number = forms.IntegerField(min_value=1, label='Номер товарной группы')
    gross_weight = forms.FloatField(min_value=0, label='Масса брутто') #, error_messages=value_cannot_be_negative)
    net_weight = forms.FloatField(min_value=0, label='Масса нетто') #, error_messages=value_cannot_be_negative)
    country = forms.ModelChoiceField(queryset=Country.objects.all(), label='Страна', empty_label=None)
    procedure = forms.ModelChoiceField(queryset=Procedure.objects.all(), label='Заявляемая таможенная процедура', empty_label=None)
    prev_procedure = forms.ModelChoiceField(queryset=Procedure.objects.all(), label='Предыдущая таможенная процедура', empty_label=None)
    customs_cost = forms.FloatField(min_value=0, label='Таможенная стоимость') #, error_messages=value_cannot_be_negative)
    fee = forms.FloatField(min_value=0, label='Сумма пошлины') #, error_messages=value_cannot_be_negative)
    fee_percent = forms.FloatField(min_value=0, label='Процентная ставка пошлины') #, error_messages=value_cannot_be_negative)
    ndc = forms.FloatField(min_value=0, label='Сумма НДС')  #, error_messages=value_cannot_be_negative)
    ndc_percent = forms.FloatField(min_value=0, label='Процент НДС')  #, error_messages=value_cannot_be_negative)

    class Meta:
        model = GtdGroup
        exclude = ('gtd', 'last_edited_user',)


# Форма для редактирования товаров ГТД
class GtdGoodCreateUpdateForm(forms.ModelForm):
    good = forms.ModelChoiceField(queryset=Good.objects.all(), label='Товар', empty_label=None)
    good_num = forms.IntegerField(min_value=1, label='Номер товара в группе')
    quantity = forms.FloatField(min_value=0, label='Количество')
    qualifier = forms.ModelChoiceField(queryset=MeasureQualifier.objects.order_by('russian_code'), label='Единица измерения', empty_label=None)
    manufacturer = forms.ModelChoiceField(queryset=Manufacturer.objects.all(), label='Производитель (завод)', empty_label=None)

    class Meta:
        model = GtdGood
        exclude = ('gtd', 'group', 'last_edited_user',)


    # def __init__(self):
    #     super(GtdGroupUpdateForm, self).__init__()
    #     # Сортируем для удобства коды ТН ВЭД
    #     self.fields['tn_ved'].queryset = TnVed.objects.order_by('code')
    #
    #     # Убираем у всех ModelChoicefield возможность оставлять пустую строку
    #     for fieldname in ('tn_ved', 'country', 'procedure', 'prev_procedure',):
    #         self.fields[fieldname].empty_label = None

# class GtdGroupUpdateForm(forms.ModelForm):
#     # gtd = forms.ModelChoiceField(disabled=True)
#
#     class Meta:
#         model = GtdGroup
#         exclude = ('last_edited_user',)
#         labels = {
#             # 'gtd': 'ГТД',
#             'tn_ved': 'Код ТН ВЭД',
#             'country': 'Страна',
#             'procedure': 'Таможенная процедура',
#             'prev_procedure': 'Предыдущая таможенная процедура',
#         }
#         widgets = {
#             # 'gtd': forms.TextInput(attrs={'disabled': True})
#             # 'gtd': forms.HiddenInput()  # forms.TextInput(attrs={'readonly': 'read'})
#         }
#
#     def __init__(self, gtd=None, *args, **kwargs):
#         super(GtdGroupUpdateForm, self).__init__(*args, **kwargs)
#
#         if gtd:
#             self.fields['gtd'] = forms.ModelChoiceField(
#                 GtdMain.objects.all(), initial=gtd, disabled=True, label='ГТД'
#             )
#             # self.fields['gtd'].
#         # Сортируем для удобства коды ТН ВЭД
#         self.fields['tn_ved'].queryset = TnVed.objects.order_by('code')
#
#         # Убираем у всех ModelChoicefield возможность оставлять пустую строку
#         for fieldname in ('tn_ved', 'country', 'procedure', 'prev_procedure',):
#             self.fields[fieldname].empty_label = None


# class GtdGroupCreateForm(forms.ModelForm):
#
#     class Meta:
#         model = GtdGroup
#         exclude = ('last_edited_user',)
#         widgets = {
#             'gtd': forms.HiddenInput()
#         }
#
#     def __init__(self, *args, **kwargs):
#         super(GtdGroupCreateForm, self).__init__(*args, **kwargs)
#         # if gtd_pk:
#         #     self.fields['gtd'] = forms.ModelChoiceField(GtdMain.objects.filter(pk=gtd_pk), disabled=True, empty_label=None)
#         for fieldname in ('tn_ved', 'country', 'procedure', 'prev_procedure',):
#             self.fields[fieldname].empty_label = None


# Форма редактирования товаров ГТД
# class GtdGoodUpdateForm(forms.ModelForm):
#
#     class Meta:
#         model = GtdGood
#         exclude = ('gtd', 'good_num', 'last_edited_user',)
#         labels = {
#             'good': 'Товар',
#             'group': 'Группа товаров',
#             'qualifier': 'Единица измерения',
#             'manufacturer': 'Производитель',
#         }
#
#     def __init__(self, gtd, *args, **kwargs):
#         super(GtdGoodUpdateForm, self).__init__(*args, **kwargs)
#         # Фильтруем выбор групп
#         self.fields['group'].queryset = GtdGroup.objects.filter(gtd=gtd.pk)
#
#         # Убираем у всех ModelChoicefield возможность оставлять пустую строку
#         for fieldname in ('group', 'good', 'quantity', 'qualifier', 'manufacturer'):
#             self.fields[fieldname].empty_label = None


# Форма для подготовки к формированию xml для WMS
class ExportComment(forms.Form):
    comment = forms.CharField(widget=forms.Textarea(attrs={'rows': 1, 'cols': 50}), required=False,
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
