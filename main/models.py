from django.db import models
from django.contrib.auth.models import AbstractUser
from django.template.defaultfilters import slugify


# Create your models here.

# Роли реализованы в виде групп (уже существующей структуры)
# Пользователи базы
class RegUser(AbstractUser):
    email = models.EmailField(verbose_name='Электронная почта', unique=True)
    done_registration = models.BooleanField(verbose_name='Завершил регистрацию?', default=False)

    class Meta(AbstractUser.Meta):
        pass

    def save(self, *args, **kwargs):
        self.is_active = False
        return super(RegUser, self).save(*args, **kwargs)


# Главная инфа гтд (1 на весь документ)
class GtdMain(models.Model):
    gtdId = models.CharField(max_length=23, verbose_name='Номер гтд')
    customs_house = models.ForeignKey('CustomsHouse', on_delete=models.PROTECT,
                                      verbose_name='id таможенного отделения', related_name="+", null=True, blank=True)
    date = models.DateField(verbose_name='Дата', null=True, blank=True)
    order_num = models.CharField(max_length=7, verbose_name='Порядковый номер',
                                 null=True, blank=True)
    total_goods_number = models.IntegerField(verbose_name='Всего товаров',
                                             null=True, blank=True)
    exporter = models.ForeignKey('Exporter', verbose_name='id Экспортера',
                                 on_delete=models.PROTECT, related_name="+", null=True, blank=True)
    importer = models.ForeignKey('Importer', verbose_name='id импортера',
                                 on_delete=models.PROTECT, related_name="+", null=True, blank=True)
    trading_country = models.ForeignKey('Country', verbose_name='id торгующей страны',
                                        on_delete=models.PROTECT, null=True, blank=True, related_name='+')
    total_cost = models.FloatField(verbose_name='Общая стоимость', null=True, blank=True)
    currency = models.ForeignKey('Currency', verbose_name='id валюты',
                                 on_delete=models.PROTECT, related_name="+", null=True, blank=True)
    total_invoice_amount = models.FloatField(verbose_name='Общая стоимость по счету', null=True, blank=True)
    currency_rate = models.FloatField(verbose_name='Курс валюты', null=True, blank=True)
    deal_type = models.ForeignKey('DealType', verbose_name='id характера сделки',
                                  on_delete=models.PROTECT, related_name="+", null=True, blank=True)
    gtd_file = models.ForeignKey('UploadGtdFile', verbose_name='id xml-документа гтд',
                                 on_delete=models.PROTECT, related_name="+", null=True, blank=True)
    last_edited_user = models.ForeignKey('RegUser', verbose_name='Пользователь, последний внесший изменения',
                                    related_name='+', null=True, blank=True, on_delete=models.PROTECT)
    last_edited_time = models.DateTimeField(verbose_name='Дата и время добавления/последнего редактирования',
                                            null=True, blank=True, auto_now=True)

    class Meta:
        verbose_name = 'Грузовая таможенная декларация'
        verbose_name_plural = 'Грузовые таможенные декларации'
        ordering = ['-date']
        unique_together = ('gtdId', 'customs_house', 'date', 'order_num')


# Отделы таможни - Справочник
class CustomsHouse(models.Model):
    house_num = models.CharField(max_length=8, verbose_name='Номер отдела')
    house_name = models.CharField(max_length=255, verbose_name='Название отдела')

    class Meta:
        verbose_name = 'Таможенный отдел'
        verbose_name_plural = 'Таможенные отделы'

    def __str__(self):
        return self.house_name


# Экспортеры - Справочник
class Exporter(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название компании')
    postal_code = models.CharField(max_length=20, verbose_name='Почтовый индекс', null=True, blank=True)
    country = models.ForeignKey('Country', on_delete=models.PROTECT,
                                verbose_name='id страны', related_name="+", null=True, blank=True)
    city = models.CharField(max_length=100, verbose_name='Город', null=True, blank=True)
    street_house = models.CharField(max_length=100, verbose_name='Улица (и/или дом)',
                                    null=True, blank=True)
    house = models.CharField(max_length=100, verbose_name='Дом', null=True, blank=True)
    region = models.CharField(max_length=100, verbose_name='Регион', null=True, blank=True)

    class Meta:
        verbose_name = 'Экспортер'
        verbose_name_plural = 'Экспортеры'
        unique_together = ('name', 'postal_code', 'city', 'street_house')

    def __str__(self):
        return self.name


# Импортеры - Справочник
class Importer(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название компании', unique=True)
    postal_code = models.CharField(max_length=20, verbose_name='Почтовый индекс', null=True, blank=True)
    country = models.ForeignKey('Country', on_delete=models.PROTECT,
                                verbose_name='id страны', related_name="+", null=True, blank=True)
    city = models.CharField(max_length=100, verbose_name='Город', null=True, blank=True)
    street_house = models.CharField(max_length=100,
                                    verbose_name='Улица (и/или дом)', null=True, blank=True)
    house = models.CharField(max_length=100, verbose_name='Дом', null=True, blank=True)
    inn = models.CharField(max_length=15, verbose_name='ИНН', unique=True)
    ogrn = models.CharField(max_length=20, verbose_name='ОГРН', unique=True)
    kpp = models.CharField(max_length=20, verbose_name='КПП', null=True, blank=True)

    class Meta:
        verbose_name = 'Импортер'
        verbose_name_plural = 'Импортеры'

    def __str__(self):
        return self.name


# Государства - Справочник
class Country(models.Model):
    code = models.CharField(max_length=2, verbose_name='Код страны')
    russian_name = models.CharField(max_length=150, verbose_name='Название страны на русском')
    english_name = models.CharField(max_length=150, verbose_name='Название страны на английском')

    class Meta:
        verbose_name = 'Страна'
        verbose_name_plural = 'Страны'

    def __str__(self):
        return self.russian_name


# Валюты - Справочник
class Currency(models.Model):
    digital_code = models.CharField(max_length=3, verbose_name='Цифровой код', null=True, blank=True)
    short_name = models.CharField(max_length=3, verbose_name='Обозначение')
    name = models.CharField(max_length=100, verbose_name='Название')

    class Meta:
        verbose_name = 'Валюта'
        verbose_name_plural = 'Валюты'

    def __str__(self):
        return self.short_name


# Характер сделки - Справочник
class DealType(models.Model):
    code = models.CharField(max_length=3, verbose_name='Код характера сделки')
    deal_type = models.TextField(verbose_name='Характер сделки')

    class Meta:
        verbose_name = 'Характер сделки'
        verbose_name_plural = 'Классификатор характера сделки'

    def __str__(self):
        return self.code


# Группы товаров в ГТД
class GtdGroup(models.Model):
    gtd = models.ForeignKey('GtdMain', on_delete=models.CASCADE, verbose_name='id ГТД', related_name="+")
    name = models.CharField(verbose_name='Название', max_length=255, null=True, blank=True)
    description = models.TextField(verbose_name='Описание', null=True, blank=True)
    tn_ved = models.ForeignKey('TnVed', on_delete=models.PROTECT,
                               verbose_name='id кода товарной группы ТН ВЭД', related_name="+")
    number = models.IntegerField(verbose_name='Номер товарной группы')
    gross_weight = models.FloatField(verbose_name='Масса брутто')
    net_weight = models.FloatField(verbose_name='Масса нетто')
    country = models.ForeignKey('Country', on_delete=models.PROTECT,
                                verbose_name='id страны происхождения', related_name="+")
    procedure = models.ForeignKey('Procedure', on_delete=models.PROTECT,
                                  verbose_name='id завляемой таможенной процедуры', related_name="+")
    prev_procedure = models.ForeignKey('Procedure', on_delete=models.PROTECT,
                                       verbose_name='id предыдущей таможенной процедуры', related_name="+")
    customs_cost = models.FloatField(verbose_name='Таможенная стоимость')
    fee = models.FloatField(verbose_name='Сумма пошлины')
    ndc = models.FloatField(verbose_name='Сумма НДС')
    fee_percent = models.FloatField(verbose_name='Процентная ставка пошлины')
    ndc_percent = models.FloatField(verbose_name='Процентная ставка НДС')

    class Meta:
        verbose_name = 'Группа товаров в ГТД'
        verbose_name_plural = 'Группы товаров в ГТД'
        unique_together = ('gtd', 'number')


# Классификатор товаров ТН ВЭД - Справочник
class TnVed(models.Model):
    code = models.CharField(max_length=18, verbose_name='Номер группы')
    subposition = models.TextField(verbose_name='Подсубпозиция', null=True, blank=True)

    class Meta:
        verbose_name = 'ТН ВЭД'
        verbose_name_plural = verbose_name


# Таможенные процедуры - Справочник
class Procedure(models.Model):
    code = models.CharField(max_length=2, verbose_name='Код таможенной процедуры')
    name = models.CharField(max_length=255, verbose_name='Таможенная процедура')

    class Meta:
        verbose_name = 'Вид таможенной процедуры'
        verbose_name_plural = 'Классификатор видов таможенных процедур'


# Товары - Справочник
class Good(models.Model):
    marking = models.CharField(max_length=50, verbose_name='Артикул', null=True, blank=True)
    name = models.TextField(verbose_name='Товар')
    goodsmark = models.ForeignKey('GoodsMark', on_delete=models.PROTECT, verbose_name='id торговой марки',
                                  related_name="+", null=True, blank=True)
    trademark = models.ForeignKey('TradeMark', on_delete=models.PROTECT, verbose_name='id товарного знака',
                                  related_name="+", null=True, blank=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'


# Товарный знак - Справочник
class TradeMark(models.Model):
    trademark = models.CharField(max_length=100, verbose_name='Товарный знак')

    class Meta:
        verbose_name = 'Товарный знак'
        verbose_name_plural = 'Товарные знаки'


# Бренд/торговая марка - Справочник
class GoodsMark(models.Model):
    goodsmark = models.CharField(max_length=100, verbose_name='Торговая марка')

    class Meta:
        verbose_name = 'Торговая марка'
        verbose_name_plural = 'Торговые марки'


# Заводы (производители) - Справочник
class Manufacturer(models.Model):
    manufacturer = models.CharField(max_length=255, verbose_name='Производитель')

    class Meta:
        verbose_name = 'Производитель'
        verbose_name_plural = 'Производители'


# Единицы измерения - Справочник
class MeasureQualifier(models.Model):
    digital_code = models.CharField(max_length=4, verbose_name='Код', unique=True)
    name = models.CharField(max_length=100, verbose_name='Наименование')
    russian_symbol = models.CharField(max_length=255, verbose_name='Русское условное обозначение', null=True, blank=True)
    russian_code = models.CharField(max_length=100, verbose_name='Русское кодовое обозначение', null=True, blank=True)
    english_symbol = models.CharField(max_length=255, verbose_name='Международное условное обозначение', null=True, blank=True)
    english_code = models.CharField(max_length=20, verbose_name='Международное кодовое обозначение', null=True, blank=True)

    class Meta:
        verbose_name = 'Единица измерения'
        verbose_name_plural = 'Единицы измерения'


# Товары из ГТД
class GtdGood(models.Model):
    gtd = models.ForeignKey('GtdMain', on_delete=models.CASCADE,
                            verbose_name='id ГТД', related_name="+")
    group = models.ForeignKey('GtdGroup', on_delete=models.CASCADE,
                              verbose_name='id группы товаров', related_name="+")
    good = models.ForeignKey('Good', on_delete=models.PROTECT,
                             verbose_name='id товара', related_name="+", null=True, blank=True)
    good_num = models.IntegerField(verbose_name='Номер товара в группе')
    quantity = models.FloatField(verbose_name='Количество', null=True, blank=True)
    qualifier = models.ForeignKey('MeasureQualifier', on_delete=models.PROTECT,
                                  related_name="+", verbose_name='id единицы измерения', null=True, blank=True)
    manufacturer = models.ForeignKey('Manufacturer', on_delete=models.PROTECT,
                                     related_name="+", verbose_name='id производителя', null=True, blank=True)

    class Meta:
        verbose_name = 'Товар в ГТД'
        verbose_name_plural = 'Товары в ГТД'
        unique_together = ('gtd', 'group', 'good_num')


# Документы - Справочник
class Document(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название документа')
    doc_type = models.ForeignKey('DocumentType', verbose_name='Id типа документа', related_name="+",
                                 null=True, blank=True, on_delete=models.PROTECT)
    number = models.CharField(max_length=255, verbose_name='Номер документа', null=True)
    date = models.DateField(verbose_name='Дата', blank=True, null=True)
    begin_date = models.DateField(verbose_name='Дата начала действия', blank=True, null=True)
    expire_date = models.DateField(verbose_name='Дата окончания действия', blank=True, null=True)

    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'


# TODO: Добавить модель типов документов
# Тип документов
class DocumentType(models.Model):
    code = models.CharField(max_length=8, verbose_name='Код типа документа')
    name = models.TextField(verbose_name='Название документа')

    class Meta:
        verbose_name = 'Тип документа'
        verbose_name_plural = 'Типы документов'


# Документы группы в гтд
class GtdDocument(models.Model):
    gtd = models.ForeignKey('GtdMain', on_delete=models.CASCADE, verbose_name='id ГТД', related_name="+")
    group = models.ForeignKey('GtdGroup', on_delete=models.CASCADE, verbose_name='id группы товаров', related_name="+")
    document = models.ForeignKey('Document', on_delete=models.CASCADE, verbose_name='id документа', related_name="+")

    class Meta:
        verbose_name = 'Документ в ГТД'
        verbose_name_plural = 'Документы в ГТД'
        unique_together = ('gtd', 'group', 'document')


#  TODO: нужно поле, которое покажет id пользователя, который скинул файл (потом)
class UploadGtd(models.Model):
    description = models.CharField(max_length=255, blank=True, verbose_name='Краткий комментарий')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    files_num = models.IntegerField(verbose_name='Количество прикрепленных файлов', null=True, blank=True)
    who_uploaded = models.ForeignKey('RegUser', blank=True, null=True, on_delete=models.PROTECT,
                                     related_name='+', verbose_name='Пользователь, загрузивший файл(ы)')

    class Meta:
        verbose_name = 'Загруженная ГТД'
        verbose_name_plural = 'Загруженные ГТД'
        ordering = ['uploaded_at']


class UploadGtdFile(models.Model):
    uploaded_gtd = models.ForeignKey('UploadGtd', on_delete=models.PROTECT, verbose_name='id партии загруженных ГТД')
    document = models.FileField(upload_to='gtd/')
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        verbose_name = 'Загруженный файл ГТД'
        verbose_name_plural = 'Загруженные файлы ГТД'
