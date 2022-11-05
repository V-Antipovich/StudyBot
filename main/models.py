import os
from datetime import timedelta

from django.core.validators import MinValueValidator
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.template.defaultfilters import slugify
from decimal import Decimal
import xml.etree.ElementTree as ET

# Create your models here.

# Роли реализованы в виде групп (уже существующей структуры)
# Пользователи базы


from customs_declarations_database.settings import USER_DIR


class RegUser(AbstractUser):
    is_activated = models.BooleanField(verbose_name='Завершил регистрацию?', default=False)
    email = models.EmailField(verbose_name='Электронная почта', unique=True)
    patronymic = models.CharField(verbose_name='Отчество', max_length=255, null=True, blank=True)
    # email_verified = models.BooleanField(default=False)
    # roles = models.ManyToManyField("JobTitle", verbose_name='Должность', related_name='+', blank=True)

    class Meta(AbstractUser.Meta):
        pass


# Главная инфа гтд (1 на весь документ)
class GtdMain(models.Model):  # TODO: при любом изменении поменять wms и erp на false?
    gtdId = models.CharField(max_length=23, verbose_name='Номер гтд', unique=True)
    customs_house = models.ForeignKey('CustomsHouse', on_delete=models.SET_NULL,
                                      verbose_name='id таможенного отделения', related_name="+", null=True, blank=True)
    date = models.DateField(verbose_name='Дата', null=True, blank=True)
    order_num = models.CharField(max_length=7, verbose_name='Порядковый номер',
                                 null=True, blank=True)
    total_goods_number = models.IntegerField(verbose_name='Всего товаров',
                                             null=True, blank=True)
    exporter = models.ForeignKey('Exporter', verbose_name='id Экспортера',
                                 on_delete=models.SET_NULL, related_name="+", null=True, blank=True)
    importer = models.ForeignKey('Importer', verbose_name='id импортера',
                                 on_delete=models.SET_NULL, related_name="+", null=True, blank=True)
    trading_country = models.ForeignKey('Country', verbose_name='id торгующей страны',
                                        on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    total_cost = models.FloatField(verbose_name='Общая стоимость', null=True, blank=True)
    currency = models.ForeignKey('Currency', verbose_name='id валюты',
                                 on_delete=models.SET_NULL, related_name="+", null=True, blank=True)
    total_invoice_amount = models.FloatField(verbose_name='Общая стоимость по счету', null=True, blank=True)
    currency_rate = models.FloatField(verbose_name='Курс валюты', null=True, blank=True)
    deal_type = models.ForeignKey('DealType', verbose_name='id характера сделки',
                                  on_delete=models.SET_NULL, related_name="+", null=True, blank=True)
    gtd_file = models.ForeignKey('UploadGtdFile', verbose_name='id xml-документа гтд',
                                 on_delete=models.SET_NULL, related_name="+", null=True, blank=True)
    last_edited_user = models.ForeignKey('RegUser', verbose_name='Пользователь, последний внесший изменения',
                                    related_name='+', null=True, blank=True, on_delete=models.SET_NULL)
    last_edited_time = models.DateTimeField(verbose_name='Дата и время добавления/последнего редактирования',
                                            null=True, blank=True, auto_now=True)
    exported_to_wms = models.BooleanField(verbose_name='Был выполнен экспорт в WMS?', default=False)
    exported_to_erp = models.BooleanField(verbose_name='Был выполнен экспорт в ERP?', default=False)

    class Meta:
        verbose_name = 'Грузовая таможенная декларация'
        verbose_name_plural = 'Грузовые таможенные декларации'
        ordering = ['-date']
        unique_together = ('gtdId', 'customs_house', 'date', 'order_num')

    def recount(self):
        groups = GtdGroup.objects.filter(gtd_id=self.pk)

        self.total_cost = sum(group.customs_cost for group in groups)
        self.total_invoice_amount = self.total_cost / self.currency_rate
        self.total_goods_number = groups.count()
        self.save()

    # TODO: Guid это id из базы; ПТиУ это номер ГТД
    def export_to_erp(self, comment, user):
        goods = GtdGood.objects.filter(gtd_id=self.pk)
        gtd_id = self.gtdId
        struct = ET.Element('Structure')
        struct.set('xmlns', 'http://v8.1c.ru/8.1/data/core')
        struct.set('xmlns:xs', 'http://www.w3.org/2001/XMLSchema')
        struct.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')

        prop_guid = ET.SubElement(struct, 'Property')
        prop_guid.set('name', 'prop_guid')

        value_guid = ET.SubElement(prop_guid, 'Value')
        value_guid.set('xsi:type', 'xs:string')
        value_guid.text = '937d9e95-5519-11ed-8070-00155db05a26'

        prop_ptiu = ET.SubElement(struct, 'Property')
        prop_ptiu.set('name', 'НомерПТиУ')
        value_ptiu = ET.SubElement(prop_ptiu, 'Value')
        value_ptiu.set('xsi:type', 'xs:string')
        value_ptiu.text = 'ER-00061362'

        prop_date = ET.SubElement(struct, 'Property')
        prop_date.set('name', 'Дата')
        value_date = ET.SubElement(prop_date, 'Value')
        value_date.set('xsi:type', 'xs:string')
        value_date.text = self.date.strftime("%d-%m-%Y %H-%M-%S")  # gtd.date.strftime("%d-%m-%Y %H-%M-%S")

        prop_warehouse = ET.SubElement(struct, 'Property')
        prop_warehouse.set('name', 'Склад')
        value_warehouse = ET.SubElement(prop_warehouse, 'Value')
        value_warehouse.set('xsi:type', 'xs:string')
        value_warehouse.text = 'Склад Хлебниково'

        prop_name = ET.SubElement(struct, 'Property')
        prop_name.set('name', 'Ответственный')
        value_name = ET.SubElement(prop_name, 'Ответственный')
        value_name.set('xsi:type', 'xs:string')
        value_name.text = f'{user.last_name} {user.first_name} {user.patronymic}'

        prop_comment = ET.SubElement(struct, 'Property')
        prop_comment.set('name', 'Комментарий')
        value_comment = ET.SubElement(prop_comment, 'Value')
        value_comment.set('xsi:type', 'xs:string')
        value_comment.text = comment

        prop_status = ET.SubElement(struct, 'Property')
        prop_status.set('name', 'Статус')
        value_status = ET.SubElement(prop_status, 'Value')
        value_status.set('xsi:type', 'xs:string')
        value_status.text = 'К поступлению'

        prop_goods = ET.SubElement(struct, 'Property')
        prop_goods.set('name', 'Товары')
        value_goods = ET.SubElement(prop_goods, 'Value')
        value_goods.set('xsi:type', 'Array')

        for good in goods:
            value_structure = ET.SubElement(value_goods, 'Value')
            value_structure.set('xsi:type', 'Structure')

            property_marking = ET.SubElement(value_structure, 'Property')
            property_marking.set('name', 'Номенклатура')
            value_marking = ET.SubElement(property_marking, 'Value')
            value_marking.set('xsi:type', 'xs:string')
            value_marking.text = good.good.marking

            property_count = ET.SubElement(value_structure, 'Property')
            property_count.set('name', 'Количество')
            value_count = ET.SubElement(property_count, 'Value')
            value_count.set('xsi:type', 'xs:decimal')
            value_count.text = str(good.quantity)

            property_gtd = ET.SubElement(value_structure, 'Property')
            property_gtd.set('name', 'ГТД')
            value_gtd = ET.SubElement(property_gtd, 'Value')
            value_gtd.set('xsi:type', 'xs:string')
            value_gtd.text = f"{self.gtdId}/{good.group.number}"

        erp_data = ET.tostring(struct, encoding='utf-8', method='xml')
        filename = f'erp {user.pk} { gtd_id.replace("/", "_")}.xml'
        filepath = os.path.join(USER_DIR, 'erp/', filename)

        with open(filepath, 'wb') as erp_file:
            erp_file.write(erp_data)
        # gtd.exported_to_erp = True
        # gtd.save()
        self.exported_to_erp = True
        self.save()

    def export_to_wms(self, comment, user):
        # TODO: дата в формате Г_М_д
        gtd_id = self.gtdId.replace('/', '_')

        gtd_date = self.date
        goods = GtdGood.objects.filter(gtd_id=self.pk)

        unique_goods = {}
        for good in goods:
            marking = good.good.marking
            quantity = good.quantity
            qualifier = good.qualifier
            if marking in unique_goods:
                unique_goods[marking][0] += quantity
            else:
                unique_goods[marking] = [quantity, qualifier.russian_symbol]

        doc = ET.Element('DOC')
        doc_in = ET.SubElement(doc, 'DOC_IN')
        number = ET.SubElement(doc_in, 'NUMBER')
        number.text = gtd_id
        date = ET.SubElement(doc_in, 'DATE')
        date.text = gtd_date.strftime("%d-%m-%Y")
        in_date = ET.SubElement(doc_in, 'IN_DATE')
        in_date.text = (gtd_date + timedelta(days=5)).strftime("%d-%m-%Y T%H-%M-%S")
        description = ET.SubElement(doc_in, 'DSC')
        description.text = comment
        for good, good_attrs in unique_goods.items():
            content = ET.SubElement(doc_in, 'CONTENT')
            code = ET.SubElement(content, 'CODE')
            code.set('CODE_ID', good)
            count = ET.SubElement(code, 'CNT')
            count.text = str(good_attrs[0])
            unit_name = ET.SubElement(code, 'UNIT_NAME')
            unit_name.text = good_attrs[1]

        wms_data = ET.tostring(doc, encoding='utf-8', method='xml')
        filename = f'wms {user.pk} {gtd_id}.xml'
        filepath = os.path.join(USER_DIR, 'wms/', filename)
        with open(filepath, 'wb') as wms_file:
            wms_file.write(wms_data)

        self.exported_to_wms = True
        self.save()

    def new_version(self):
        self.exported_to_erp = False
        self.exported_to_wms = False
        self.save()

    def __str__(self):
        return self.gtdId


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
    country = models.ForeignKey('Country', on_delete=models.SET_NULL,
                                verbose_name='Страна', related_name="+", null=True, blank=True)
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
    country = models.ForeignKey('Country', on_delete=models.SET_NULL,
                                verbose_name='Страна', related_name="+", null=True, blank=True)
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
        unique_together = ('name', 'postal_code',)

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
    # name = models.CharField(verbose_name='Название', max_length=255, null=True, blank=True)
    name = models.TextField(verbose_name='Название', null=True, blank=True)
    # description = models.TextField(verbose_name='Описание', null=True, blank=True)
    tn_ved = models.ForeignKey('TnVed', on_delete=models.SET_NULL, null=True,
                               verbose_name='id кода товарной группы ТН ВЭД', related_name="+")
    number = models.IntegerField(verbose_name='Номер товарной группы')
    gross_weight = models.FloatField(verbose_name='Масса брутто')
    net_weight = models.FloatField(verbose_name='Масса нетто')
    country = models.ForeignKey('Country', on_delete=models.SET_NULL, null=True,
                                verbose_name='id страны происхождения', related_name="+")
    procedure = models.ForeignKey('Procedure', on_delete=models.SET_NULL, null=True,
                                  verbose_name='id завляемой таможенной процедуры', related_name="+")
    prev_procedure = models.ForeignKey('Procedure', on_delete=models.SET_NULL, null=True,
                                       verbose_name='id предыдущей таможенной процедуры', related_name="+")
    customs_cost = models.FloatField(verbose_name='Таможенная стоимость')
    fee = models.FloatField(verbose_name='Сумма пошлины')
    ndc = models.FloatField(verbose_name='Сумма НДС')
    fee_percent = models.FloatField(verbose_name='Процентная ставка пошлины')
    ndc_percent = models.FloatField(verbose_name='Процентная ставка НДС')
    last_edited_user = models.ForeignKey('RegUser', on_delete=models.SET_NULL, related_name='+', null=True, blank=True,
                                         verbose_name='Пользователь, последний вносивший изменения')

    class Meta:
        verbose_name = 'Группа товаров в ГТД'
        verbose_name_plural = 'Группы товаров в ГТД'
        # unique_together = ('gtd', 'number')

    def __str__(self):
        return str(self.number)


# Классификатор товаров ТН ВЭД - Справочник
class TnVed(models.Model):
    code = models.CharField(max_length=18, verbose_name='Номер группы')
    subposition = models.TextField(verbose_name='Подсубпозиция', null=True, blank=True)
    has_environmental_fee = models.BooleanField(verbose_name='Облагается ли экологическим сбором?',
                                                null=True, blank=True, default=False)
    recycling_standart = models.FloatField(verbose_name='Норма утилизации', null=True, blank=True, max_length=255)
    collection_rate = models.FloatField(verbose_name='Ставка сбора', null=True, blank=True, max_length=255)

    class Meta:
        verbose_name = 'ТН ВЭД'
        verbose_name_plural = verbose_name

    def __str__(self):
        return str(self.code)


# Таможенные процедуры - Справочник
class Procedure(models.Model):
    code = models.CharField(max_length=2, verbose_name='Код таможенной процедуры')
    name = models.CharField(max_length=255, verbose_name='Таможенная процедура')

    class Meta:
        verbose_name = 'Вид таможенной процедуры'
        verbose_name_plural = 'Классификатор видов таможенных процедур'

    def __str__(self):
        return str(self.code)


# Товары - Справочник
class Good(models.Model):
    marking = models.CharField(max_length=50, verbose_name='Артикул', unique=True)
    name = models.TextField(verbose_name='Товар')
    goodsmark = models.ForeignKey('GoodsMark', on_delete=models.SET_NULL, verbose_name='Торговая марка',
                                  related_name="+", null=True, blank=True)
    trademark = models.ForeignKey('TradeMark', on_delete=models.SET_NULL, verbose_name='Товарный знак',
                                  related_name="+", null=True, blank=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return str(self.marking)


# Товарный знак - Справочник
class TradeMark(models.Model):
    trademark = models.CharField(max_length=100, verbose_name='Товарный знак')

    class Meta:
        verbose_name = 'Товарный знак'
        verbose_name_plural = 'Товарные знаки'

    def __str__(self):
        return self.trademark


# Бренд/торговая марка - Справочник
class GoodsMark(models.Model):
    goodsmark = models.CharField(max_length=100, verbose_name='Торговая марка')

    class Meta:
        verbose_name = 'Торговая марка'
        verbose_name_plural = 'Торговые марки'

    def __str__(self):
        return self.goodsmark


# Заводы (производители) - Справочник
class Manufacturer(models.Model):
    manufacturer = models.CharField(max_length=255, verbose_name='Производитель')

    class Meta:
        verbose_name = 'Производитель'
        verbose_name_plural = 'Производители'

    def __str__(self):
        return str(self.manufacturer)


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

    def __str__(self):
        if self.russian_code:
            return str(self.russian_code)
        else:
            return str(self.name)


# Товары из ГТД
class GtdGood(models.Model):
    gtd = models.ForeignKey('GtdMain', on_delete=models.CASCADE,
                            verbose_name='id ГТД', related_name="+")
    group = models.ForeignKey('GtdGroup', on_delete=models.CASCADE,
                              verbose_name='id группы товаров', related_name="+")
    good = models.ForeignKey('Good', on_delete=models.SET_NULL,
                             verbose_name='id товара', related_name="+", null=True, blank=True)
    good_num = models.IntegerField(verbose_name='Номер товара в группе')
    quantity = models.FloatField(verbose_name='Количество', null=True, blank=True)
    qualifier = models.ForeignKey('MeasureQualifier', on_delete=models.SET_NULL,
                                  related_name="+", verbose_name='id единицы измерения', null=True, blank=True)
    manufacturer = models.ForeignKey('Manufacturer', on_delete=models.SET_NULL,
                                     related_name="+", verbose_name='id производителя', null=True, blank=True)
    last_edited_user = models.ForeignKey('RegUser', on_delete=models.SET_NULL, related_name='+',
                                         verbose_name='Пользователь, последний внесший изменения', null=True, blank=True)

    class Meta:
        verbose_name = 'Товар в ГТД'
        verbose_name_plural = 'Товары в ГТД'


# Документы - Справочник
class Document(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название документа')
    doc_type = models.ForeignKey('DocumentType', verbose_name='Id типа документа', related_name="+",
                                 null=True, blank=True, on_delete=models.SET_NULL)
    number = models.CharField(max_length=255, verbose_name='Номер документа', null=True)
    date = models.DateField(verbose_name='Дата', blank=True, null=True)
    begin_date = models.DateField(verbose_name='Дата начала действия', blank=True, null=True)
    expire_date = models.DateField(verbose_name='Дата окончания действия', blank=True, null=True)

    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'

    def __str__(self):
        return self.name


# Тип документов
class DocumentType(models.Model):
    code = models.CharField(max_length=8, verbose_name='Код типа документа')
    name = models.TextField(verbose_name='Тип документа')

    class Meta:
        verbose_name = 'Тип документа'
        verbose_name_plural = 'Типы документов'

    def __str__(self):
        return self.code


# Документы группы в гтд
class GtdDocument(models.Model):
    gtd = models.ForeignKey('GtdMain', on_delete=models.CASCADE, verbose_name='id ГТД', related_name="+")
    group = models.ForeignKey('GtdGroup', on_delete=models.CASCADE, verbose_name='id группы товаров', related_name="+")
    document = models.ForeignKey('Document', on_delete=models.CASCADE, verbose_name='id документа', related_name="+")

    class Meta:
        verbose_name = 'Документ в ГТД'
        verbose_name_plural = 'Документы в ГТД'
        unique_together = ('gtd', 'group', 'document')


class UploadGtd(models.Model):
    description = models.CharField(max_length=255, blank=True, verbose_name='Краткий комментарий')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    files_num = models.IntegerField(verbose_name='Количество прикрепленных файлов', null=True, blank=True)
    who_uploaded = models.ForeignKey('RegUser', blank=True, null=True, on_delete=models.SET_NULL,
                                     related_name='+', verbose_name='Пользователь, загрузивший файл(ы)')

    class Meta:
        verbose_name = 'Загруженная ГТД'
        verbose_name_plural = 'Загруженные ГТД'
        ordering = ['uploaded_at']


class UploadGtdFile(models.Model):
    uploaded_gtd = models.ForeignKey('UploadGtd', on_delete=models.CASCADE, related_name='+',
                                     verbose_name='id партии загруженных ГТД')
    document = models.FileField(upload_to='gtd/')
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        verbose_name = 'Загруженный файл ГТД'
        verbose_name_plural = 'Загруженные файлы ГТД'


class WmsExport(models.Model): #TODO: добавить поле юзера
    gtd = models.ForeignKey('GtdMain', on_delete=models.CASCADE, verbose_name='id ГТД', related_name='+')
    comment = models.TextField(verbose_name='Комментарий', null=True, blank=True)
    filename = models.CharField(verbose_name='Имя файла', max_length=255)
    date = models.DateTimeField(auto_now_add=True)
# TODO: добавить модель для ERP

class Handbook(models.Model):
    name = models.CharField(verbose_name='Название', max_length=255, unique=True)
    is_actual_table = models.BooleanField(verbose_name='Актуальная таблица', default=False)

    def __str__(self):
        return self.name