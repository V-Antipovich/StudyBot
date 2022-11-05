import time

from django import forms
from django.contrib.auth import password_validation, get_user_model, authenticate
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

from .models import UploadGtd, RegUser, GtdMain, Exporter, Importer, CustomsHouse, GtdGood, GtdGroup, TnVed, Country, \
    Procedure, Good, MeasureQualifier, Manufacturer, Currency, DealType, TradeMark, GoodsMark, DocumentType
from .apps import user_registered


value_cannot_be_negative = 'Это значение не может быть отрицательным'


# Валидатор дат
def validate_date_range(start, end):
    start = time.strptime(start, '%d-%m-%Y')
    end = time.strptime(end, '%d-%m-%Y')
    if start >= end:
        raise ValidationError('Вы не можете выбрать такой диапазон дат')


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
    gross_weight = forms.FloatField(min_value=0, label='Масса брутто')
    net_weight = forms.FloatField(min_value=0, label='Масса нетто')
    country = forms.ModelChoiceField(queryset=Country.objects.all(), label='Страна', empty_label=None)
    procedure = forms.ModelChoiceField(queryset=Procedure.objects.all(), label='Заявляемая таможенная процедура', empty_label=None)
    prev_procedure = forms.ModelChoiceField(queryset=Procedure.objects.all(), label='Предыдущая таможенная процедура', empty_label=None)
    customs_cost = forms.FloatField(min_value=0, label='Таможенная стоимость')
    fee = forms.FloatField(min_value=0, label='Сумма пошлины')
    fee_percent = forms.FloatField(min_value=0, label='Процентная ставка пошлины')
    ndc = forms.FloatField(min_value=0, label='Сумма НДС')
    ndc_percent = forms.FloatField(min_value=0, label='Процент НДС')

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


# Форма для подготовки к формированию xml для WMS
class ExportComment(forms.Form):
    comment = forms.CharField(widget=forms.Textarea(attrs={'rows': 1, 'cols': 50}), required=False,
                              label='Добавьте комментарий/описание, если требуется')


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


class CustomsHouseHandbookCreateUpdateForm(forms.ModelForm):
    house_num = forms.CharField(min_length=6, max_length=8, required=True)

    class Meta:
        model = CustomsHouse
        fields = '__all__'


class ExporterHandbookCreateUpdateForm(forms.ModelForm):
    country = forms.ModelChoiceField(queryset=Country.objects.order_by('russian_name'), label='Страна', empty_label=None)
    postal_code = forms.IntegerField(min_value=1000, max_value=9999999999999999999, required=True)

    class Meta:
        model = Exporter
        fields = '__all__'


class ImporterHandbookCreateUpdateForm(forms.ModelForm):
    country = forms.ModelChoiceField(queryset=Country.objects.order_by('russian_name'), label='Страна', empty_label=None)
    postal_code = forms.CharField(min_length=3, max_length=20, widget=forms.TextInput(attrs={'type': 'number'})) #IntegerField(min_value=1000, max_value=9999999999999999999, required=True)
    inn = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'type': 'number'}))
    # orgn = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'type': 'number'}))
    kpp = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'type': 'number'}))

    class Meta:
        model = Importer
        exclude = ('orgn',)


class CountryHandbookCreateUpdateForm(forms.ModelForm):
    code = forms.CharField(max_length=2)

    class Meta:
        model = Country
        fields = '__all__'


class CurrencyHandbookCreateUpdateForm(forms.ModelForm):

    class Meta:
        model = Currency
        fields = '__all__'


class DealTypeHandbookCreateUpdateForm(forms.ModelForm):

    class Meta:
        model = DealType
        fields = '__all__'


class TnVedHandbookCreateUpdateForm(forms.ModelForm):

    class Meta:
        model = TnVed
        fields = '__all__'


class ProcedureHandbookCreateUpdateForm(forms.ModelForm):

    class Meta:
        model = Procedure
        fields = '__all__'


class GoodHandbookCreateUpdateForm(forms.ModelForm):
    goodsmark = forms.ModelChoiceField(queryset=GoodsMark.objects.order_by('goodsmark'), empty_label=None)
    trademark = forms.ModelChoiceField(queryset=TradeMark.objects.order_by('trademark'), empty_label=None)

    class Meta:
        model = Good
        fields = '__all__'


class TradeMarkHandbookCreateUpdateForm(forms.ModelForm):

    class Meta:
        model = TradeMark
        fields = '__all__'


class GoodsMarkHandbookCreateUpdateForm(forms.ModelForm):

    class Meta:
        model = GoodsMark
        fields = '__all__'


class ManufacturerHandbookCreateUpdateForm(forms.ModelForm):

    class Meta:
        model = Manufacturer
        fields = '__all__'


class MeasureQualifierHandbookCreateUpdateForm(forms.ModelForm):

    class Meta:
        model = MeasureQualifier
        fields = '__all__'


class DocumentTypeHandbookCreateUpdateForm(forms.ModelForm):

    class Meta:
        model = DocumentType
        fields = '__all__'
