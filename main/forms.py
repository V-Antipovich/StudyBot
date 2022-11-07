import time

from django import forms
from django.contrib.auth import password_validation
from django.core.validators import FileExtensionValidator

from .models import RegUser, GtdMain, Exporter, Importer, CustomsHouse, GtdGood, GtdGroup, TnVed, Country,\
    Procedure, Good, MeasureQualifier, Manufacturer, Currency, DealType, TradeMark, GoodsMark, DocumentType, Role
from .apps import user_registered


class ChangeUserInfoForm(forms.ModelForm):
    """
    Форма редактирования данных пользователя
    """
    email = forms.EmailField(required=True, label='Адрес электронной почты')
    first_name = forms.CharField(min_length=4, label='Имя')
    last_name = forms.CharField(min_length=3, label='Фамилия'),
    patronymic = forms.CharField(min_length=5, label='Отчество')

    class Meta:
        """
        Метакласс, определяющий модель, записи которой обрабатываются формой,
        а также поля, которые будут присутствовать в форме
        """
        model = RegUser
        fields = ('username', 'email', 'first_name', 'last_name', 'patronymic')


class RegisterUserForm(forms.ModelForm):
    """
    Форма регистрации пользователя администратором
    """
    email = forms.EmailField(required=True, label='Адрес электронной почты')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput,
                               help_text=password_validation.password_validators_help_text_html())
    role = forms.ModelChoiceField(queryset=Role.objects.all(), label='Роль')

    class Meta:
        """
        Метакласс, определяющий модель, записи которой создаются/редактируются формой, и поля формы
        """
        model = RegUser
        fields = ('username', 'email', 'password', 'first_name', 'last_name', 'patronymic', 'role')

    def clean_password(self):
        """
        Очистка и проверка пароля
        """
        psw = self.cleaned_data['password']
        if psw:
            password_validation.validate_password(psw)
        return psw

    def save(self, commit=True):
        """
        Переопределение метода сохранения с отправкой сигнала для формирования письма
        """
        user = super().save(commit=False)
        psw = self.cleaned_data['password']
        user.set_password(psw)
        user.is_active = False
        user.is_activated = False
        if commit:
            user.save()
        # Сигнал отсылать письмо
        user_registered.send(RegisterUserForm, instance=user, password=psw)
        return user


class UploadGtdfilesForm(forms.Form):
    """
    Форма для загрузки xml- файлов
    """
    comment = forms.CharField(max_length=255, required=False, label='Комментарий (если требуется)')
    document = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}),
                               validators=[FileExtensionValidator(['xml'])], label='Документы в формате .xml')
    on_duplicate = forms.ChoiceField(choices=(('skip', 'Пропускать'), ('update', 'Обновлять')),
                                     label='Если среди загружаемых ГТД встретятся '
                                           'объекты с номерами, уже присутствующими в базе:')


class GtdUpdateForm(forms.ModelForm):
    """
    Форма редактирования основной информации ГТД (в шапке)
    """
    customs_house = forms.ModelChoiceField(queryset=CustomsHouse.objects.order_by('house_name'), empty_label=None)
    exporter = forms.ModelChoiceField(queryset=Exporter.objects.order_by('name'), empty_label=None)
    importer = forms.ModelChoiceField(queryset=Importer.objects.order_by('name'), empty_label=None)
    deal_type = forms.ModelChoiceField(queryset=DealType.objects.order_by('code'), empty_label=None)

    class Meta:
        """
        Метакласс, определяющий модель, записи которой создаются/редактируются формой,
        список полей формы и подписи к полям
        """
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


class GtdGroupCreateUpdateForm(forms.ModelForm):
    """
    Форма для редактирования групп (разделов) ГТД
    """
    tn_ved = forms.ModelChoiceField(queryset=TnVed.objects.order_by('code'), label='ТН ВЭД', empty_label=None)
    number = forms.IntegerField(min_value=1, label='Номер товарной группы')
    gross_weight = forms.FloatField(min_value=0, label='Масса брутто')
    net_weight = forms.FloatField(min_value=0, label='Масса нетто')
    country = forms.ModelChoiceField(queryset=Country.objects.all(), label='Страна', empty_label=None)
    procedure = forms.ModelChoiceField(queryset=Procedure.objects.all(), empty_label=None,
                                       label='Заявляемая таможенная процедура')
    prev_procedure = forms.ModelChoiceField(queryset=Procedure.objects.all(), empty_label=None,
                                            label='Предыдущая таможенная процедура')
    customs_cost = forms.FloatField(min_value=0, label='Таможенная стоимость')
    fee = forms.FloatField(min_value=0, label='Сумма пошлины')
    fee_percent = forms.FloatField(min_value=0, label='Процентная ставка пошлины')
    ndc = forms.FloatField(min_value=0, label='Сумма НДС')
    ndc_percent = forms.FloatField(min_value=0, label='Процент НДС')

    class Meta:
        """
        Метакласс, определяющий модель, записи которой создаются/редактируются формой, и поля этой модели,
        не входящие в форму
        """
        model = GtdGroup
        exclude = ('gtd', 'last_edited_user',)


class GtdGoodCreateUpdateForm(forms.ModelForm):
    """
    Форма для редактирования товаров из определенной ГТД
    """
    good = forms.ModelChoiceField(queryset=Good.objects.all(), label='Товар', empty_label=None)
    good_num = forms.IntegerField(min_value=1, label='Номер товара в группе')
    quantity = forms.FloatField(min_value=0, label='Количество')
    qualifier = forms.ModelChoiceField(queryset=MeasureQualifier.objects.order_by('russian_code'), label='Единица измерения', empty_label=None)
    manufacturer = forms.ModelChoiceField(queryset=Manufacturer.objects.all(), label='Производитель (завод)', empty_label=None)

    class Meta:
        """
        Метакласс, определяющий модель, записи которой добавляются/редактируются формой,
        и поля модели, не входящие в форму
        """
        model = GtdGood
        exclude = ('gtd', 'group', 'last_edited_user',)


class ExportComment(forms.Form):
    """
    Форма опционального комментария перед формированием xml файла
    """
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


# Форма для поиска на странице
class SearchForm(forms.Form):
    paginate_by = forms.ChoiceField(help_text='По сколько записей располагать на странице', choices=(
        (10, '10'),
        (50, '50'),
        (100, '100'),
        (200, '200'),
    ), label='Пагинация')
    key = forms.CharField(required=False, max_length=100, label='Ключевое слово')


class HandbookSearchForm(forms.Form):
    paginate_by = forms.ChoiceField(help_text='По сколько записей располагать на странице', choices=(
        (50, '50'),
        (100, '100'),
        (250, '250'),
    ), label='Пагинация')
    key = forms.CharField(required=False, max_length=100, label='Ключевое слово')


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
    digital_code = forms.CharField(widget=forms.TextInput(attrs={'type': 'number'}))

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
