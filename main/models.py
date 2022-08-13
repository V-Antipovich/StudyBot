from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.
# Роли
class Role(models.Model):
    role_name = models.CharField(max_length=20, verbose_name='Роль', unique=True, editable=False)

    class Meta:
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'


# Пользователи базы
class RegUser(AbstractUser):
    is_activated = models.BooleanField(default=True, db_index=True, verbose_name='Прошел активацию?')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


# Какие роли есть у данного юзера
class UserRole(models.Model):
    user = models.ForeignKey('RegUser', on_delete=models.PROTECT, verbose_name='id пользователя', related_name="+")
    role = models.ForeignKey('Role', on_delete=models.PROTECT, verbose_name='id роли', related_name="+")


# Главная инфа гтд (1 на весь документ)
class GtdMain(models.Model):
    gtdId = models.CharField(max_length=23, verbose_name='Номер гтд', unique=True)
    customs_house = models.ForeignKey('CustomsHouse', on_delete=models.PROTECT, verbose_name='id таможенного отделения', related_name="+")
    date = models.DateField(verbose_name='Дата')
    order_num = models.CharField(max_length=7, verbose_name='Порядковый номер')
    total_goods_number = models.IntegerField(verbose_name='Всего товаров')
    exporter = models.ForeignKey('Exporter', verbose_name='id Экспортера', on_delete=models.PROTECT, related_name="+")
    importer = models.ForeignKey('Importer', verbose_name='id импортера', on_delete=models.PROTECT, related_name="+")
    trading_country = models.ForeignKey('Country', verbose_name='id торгующей страны', on_delete=models.PROTECT)
    total_cost = models.FloatField(verbose_name='Общая стоимость')
    currency = models.ForeignKey('Currency', verbose_name='id валюты', on_delete=models.PROTECT, related_name="+")
    total_invoice_amount = models.FloatField(verbose_name='Общая стоимость по счету')
    currency_rate = models.FloatField(verbose_name='Курс валюты')
    deal_type = models.ForeignKey('DealType', verbose_name='id характера сделки', on_delete=models.PROTECT, related_name="+")
    gtd_file = models.ForeignKey('UploadGtd', verbose_name='id xml-документа гтд', on_delete=models.PROTECT, related_name="+", null=True, blank=True)

    class Meta:
        verbose_name = 'Грузовая таможенная декларация'
        verbose_name_plural = 'Грузовые таможенные декларации'
        ordering = ['-date']


# Отделы таможни
class CustomsHouse(models.Model):
    house_num = models.CharField(max_length=8, verbose_name='Номер отдела')
    house_name = models.CharField(max_length=255, verbose_name='Название отдела')

    class Meta:
        # verbose_name = 'Таможенный отдел'
        verbose_name_plural = verbose_name = 'Таможенные отделы'


class Exporter(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название компании')
    postal_code = models.CharField(max_length=20, verbose_name='Почтовый индекс', null=True, blank=True)
    country = models.ForeignKey('Country', on_delete=models.PROTECT, verbose_name='id страны', related_name="+", null=True, blank=True)
    city = models.CharField(max_length=100, verbose_name='Город', null=True, blank=True)
    street_house = models.CharField(max_length=100, verbose_name='Улица (и/или дом)', null=True, blank=True)
    house = models.CharField(max_length=100, verbose_name='Дом', null=True, blank=True)
    region = models.CharField(max_length=100, verbose_name='Регион', null=True, blank=True)

    class Meta:
        verbose_name = 'Экспортер'
        verbose_name_plural = 'Экспортеры'
        unique_together = ('name', 'postal_code')


class Importer(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название компании')
    postal_code = models.CharField(max_length=20, verbose_name='Почтовый индекс', null=True, blank=True)
    country = models.ForeignKey('Country', on_delete=models.PROTECT, verbose_name='id страны', related_name="+")
    city = models.CharField(max_length=100, verbose_name='Город', null=True, blank=True)
    street_house = models.CharField(max_length=100, verbose_name='Улица (и/или дом)', null=True, blank=True)
    house = models.CharField(max_length=100, verbose_name='Дом', null=True, blank=True)
    inn = models.CharField(max_length=15, verbose_name='ИНН')
    ogrn = models.CharField(max_length=20, verbose_name='ОГРН')
    kpp = models.CharField(max_length=20, verbose_name='КПП')

    class Meta:
        verbose_name = 'Импортер'
        verbose_name_plural = 'Импортеры'


# Государства
class Country(models.Model):
    code = models.CharField(max_length=2, verbose_name='Код страны')
    russian_name = models.CharField(max_length=150, verbose_name='Название на русском')
    english_name = models.CharField(max_length=150, verbose_name='Название на английском')

    class Meta:
        verbose_name = 'Страна'
        verbose_name_plural = 'Страны'


# Валюты
class Currency(models.Model):
    digital_code = models.CharField(max_length=3, verbose_name='Цифровой код', null=True, blank=True)
    short_name = models.CharField(max_length=3, verbose_name='Обозначение')
    name = models.CharField(max_length=100, verbose_name='Название')

    class Meta:
        verbose_name = 'Валюта'
        verbose_name_plural = 'Валюты'


# Характер сделки
class DealType(models.Model):
    code = models.CharField(max_length=3, verbose_name='Код характера сделки')
    deal_type = models.TextField(verbose_name='Характер сделки')

    class Meta:
        verbose_name = 'Характер сделки'
        verbose_name_plural = 'Классификатор характера сделки'


# Группы товаров в ГТД
class GtdGroup(models.Model):
    gtd = models.ForeignKey('GtdMain', on_delete=models.PROTECT, verbose_name='id ГТД', related_name="+")
    tn_ved = models.ForeignKey('TnVed', on_delete=models.PROTECT, verbose_name='id кода товарной группы ТН ВЭД', related_name="+")
    number = models.IntegerField(verbose_name='Номер товарной группы')
    gross_weight = models.FloatField(verbose_name='Масса брутто')
    net_weight = models.FloatField(verbose_name='Масса нетто')
    country = models.ForeignKey('Country', on_delete=models.PROTECT, verbose_name='id страны происхождения', related_name="+")
    procedure = models.ForeignKey('Procedure', on_delete=models.PROTECT, verbose_name='id завляемой таможенной процедуры', related_name="+")
    prev_procedure = models.ForeignKey('Procedure', on_delete=models.PROTECT, verbose_name='id предыдущей таможенной процедуры', related_name="+")
    customs_cost = models.FloatField(verbose_name='Таможенная стоимость')
    fee = models.FloatField(verbose_name='Сумма пошлины')
    ndc = models.FloatField(verbose_name='Сумма НДС')
    fee_percent = models.FloatField(verbose_name='Процентная ставка пошлины')
    ndc_percent = models.FloatField(verbose_name='Процентная ставка НДС')

    class Meta:
        verbose_name = 'Группа товаров в ГТД'
        verbose_name_plural = 'Группы товаров в ГТД'


# Классификатор товаров ТН ВЭД
class TnVed(models.Model):
    code = models.CharField(max_length=12, verbose_name='Номер группы')
    subposition = models.TextField(verbose_name='Подсубпозиция')

    class Meta:
        verbose_name = 'ТН ВЭД'
        verbose_name_plural = verbose_name


# Таможенные процедуры
class Procedure(models.Model):
    code = models.CharField(max_length=2, verbose_name='Код таможенной процедуры')
    name = models.CharField(max_length=255, verbose_name='Таможенная процедура')

    class Meta:
        verbose_name = 'Вид таможенной процедуры'
        verbose_name_plural = 'Классификатор видов таможенных процедур'


# Справочник товаров
class Good(models.Model):
    marking = models.CharField(max_length=20, verbose_name='Артикул')
    name = models.CharField(max_length=256, verbose_name='Товар')
    trademark = models.ForeignKey('TradeMark', on_delete=models.PROTECT, verbose_name='id товарного знака', related_name="+")
    brand = models.ForeignKey('GoodsMark', on_delete=models.PROTECT, verbose_name='id торговой марки', related_name="+")

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'


# Товарный знак
class TradeMark(models.Model):
    trademark = models.CharField(max_length=100, verbose_name='Товарный знак')


# Бренд - торговая марка
class GoodsMark(models.Model):
    brand = models.CharField(max_length=100, verbose_name='Торговая марка')


# Заводы (производители)
class Manufacturer(models.Model):
    manufacturer = models.CharField(max_length=100, verbose_name='Производитель')


# Товары из ГТД
class GtdGood(models.Model):
    gtd = models.ForeignKey('GtdMain', on_delete=models.PROTECT, verbose_name='id ГТД', related_name="+")
    group = models.ForeignKey('GtdGroup', on_delete=models.PROTECT, verbose_name='id группы товаров', related_name="+")
    good = models.ForeignKey('Good', on_delete=models.PROTECT, verbose_name='id товара', related_name="+")
    good_num = models.IntegerField(verbose_name='Номер товара в группе')
    quantity = models.IntegerField(verbose_name='Количество')
    manufacturer = models.ForeignKey('Manufacturer', on_delete=models.PROTECT, related_name="+", verbose_name='id производителя')

    class Meta:
        verbose_name = 'Товар в ГТД'
        verbose_name_plural = 'Товары в ГТД'


# Документы
class Document(models.Model):
    document_name = models.CharField(max_length=50, verbose_name='Название документа')
    date = models.DateField(verbose_name='Дата')
    begin_date = models.DateField(verbose_name='Дата начала действия')
    expire_date = models.DateField(verbose_name='Дата окончания действия')


# Код представления документа
class PresentCode(models.Model):
    code = models.CharField(max_length=4, verbose_name='Код представления')
    name = models.CharField(max_length=256, verbose_name='Наименование')

    class Meta:
        verbose_name = verbose_name_plural = 'Представление документа'


# Документы группы в гтд
class GtdDocument(models.Model):
    gtd = models.ForeignKey('GtdMain', on_delete=models.PROTECT, verbose_name='id ГТД', related_name="+")
    group = models.ForeignKey('GtdGroup', on_delete=models.PROTECT, verbose_name='id группы товаров', related_name="+")
    document = models.ForeignKey('Document', on_delete=models.PROTECT, verbose_name='id документа')
    present_code = models.ForeignKey('PresentCode', on_delete=models.PROTECT, related_name="+",
                                     verbose_name="id признака представления")


#  TODO: нужно добавить возможность скидывать несколько файлов
#  TODO: нужно поле, которое покажет id пользователя, который скинул файл (потом)
class UploadGtd(models.Model):
    description = models.CharField(max_length=255, blank=True, verbose_name='Краткий комментарий')
    document = models.FileField(upload_to='gtd/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # Надо чтобы в таблице с главной инфой ГТД было еще поле со ссылкой на файл xml

    class Meta:
        ordering = ['uploaded_at']
