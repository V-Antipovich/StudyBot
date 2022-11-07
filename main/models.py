import os
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import AbstractUser

import xml.etree.ElementTree as ElTree
from customs_declarations_database.settings import USER_DIR


class RegUser(AbstractUser):
    """
    Модель пользователя. Добавлены поля подтверждения активаци, почта, отчество и роль
    """
    is_activated = models.BooleanField(verbose_name='Завершил регистрацию?', default=False)
    email = models.EmailField(verbose_name='Электронная почта', unique=True)
    patronymic = models.CharField(verbose_name='Отчество', max_length=255, null=True, blank=True)
    role = models.ForeignKey('Role', verbose_name='Роль', related_name='+', on_delete=models.SET_NULL, null=True)

    class Meta(AbstractUser.Meta):
        pass


class Role(models.Model):
    """
    Роли для разграничения доступа к определенным элементам сайта
    """
    name = models.CharField(max_length=200, verbose_name='Роль')

    def __str__(self):
        """
        Информация о классе будет отображаться в виде названия роли
        """
        return self.name


class GtdMain(models.Model):
    """
    Модель шапки (основной информации) ГТД. В качестве полей модель содержит самые главные поля шапки
    """
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
        """
        Метакласс, определяющий поведение класса GtdMain
        """
        verbose_name = 'Грузовая таможенная декларация'
        verbose_name_plural = 'Грузовые таможенные декларации'
        ordering = ['-date']
        unique_together = ('gtdId', 'customs_house', 'date', 'order_num')

    def recount(self):
        """
        Программное вычисление полей стоимости и количества групп товаров
        """
        groups = GtdGroup.objects.filter(gtd_id=self.pk)

        self.total_cost = sum(group.customs_cost for group in groups)
        self.total_invoice_amount = self.total_cost / self.currency_rate
        self.total_goods_number = groups.count()
        self.save()

    def export_to_erp(self, comment, user):
        """
        Функция генерации xml-файла по данной гтд и помещение в папку,
        откуда файл смогут экспортировать в ERP
        """
        goods = GtdGood.objects.filter(gtd_id=self.pk)
        gtd_id = self.gtdId
        struct = ElTree.Element('Structure')
        struct.set('xmlns', 'http://v8.1c.ru/8.1/data/core')
        struct.set('xmlns:xs', 'http://www.w3.org/2001/XMLSchema')
        struct.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')

        prop_guid = ElTree.SubElement(struct, 'Property')
        prop_guid.set('name', 'GIUD')

        value_guid = ElTree.SubElement(prop_guid, 'Value')
        value_guid.set('xsi:type', 'xs:string')
        value_guid.text = str(self.pk)

        prop_ptiu = ElTree.SubElement(struct, 'Property')
        prop_ptiu.set('name', 'НомерПТиУ')
        value_ptiu = ElTree.SubElement(prop_ptiu, 'Value')
        value_ptiu.set('xsi:type', 'xs:string')
        value_ptiu.text = gtd_id

        prop_date = ElTree.SubElement(struct, 'Property')
        prop_date.set('name', 'Дата')
        value_date = ElTree.SubElement(prop_date, 'Value')
        value_date.set('xsi:type', 'xs:string')
        value_date.text = self.date.strftime("%d-%m-%Y %H-%M-%S")

        prop_warehouse = ElTree.SubElement(struct, 'Property')
        prop_warehouse.set('name', 'Склад')
        value_warehouse = ElTree.SubElement(prop_warehouse, 'Value')
        value_warehouse.set('xsi:type', 'xs:string')
        value_warehouse.text = 'Склад Хлебниково'

        prop_name = ElTree.SubElement(struct, 'Property')
        prop_name.set('name', 'Ответственный')
        value_name = ElTree.SubElement(prop_name, 'Ответственный')
        value_name.set('xsi:type', 'xs:string')
        value_name.text = f'{user.last_name} {user.first_name} {user.patronymic}'

        prop_comment = ElTree.SubElement(struct, 'Property')
        prop_comment.set('name', 'Комментарий')
        value_comment = ElTree.SubElement(prop_comment, 'Value')
        value_comment.set('xsi:type', 'xs:string')
        value_comment.text = comment

        prop_status = ElTree.SubElement(struct, 'Property')
        prop_status.set('name', 'Статус')
        value_status = ElTree.SubElement(prop_status, 'Value')
        value_status.set('xsi:type', 'xs:string')
        value_status.text = 'К поступлению'

        prop_goods = ElTree.SubElement(struct, 'Property')
        prop_goods.set('name', 'Товары')
        value_goods = ElTree.SubElement(prop_goods, 'Value')
        value_goods.set('xsi:type', 'Array')

        for good in goods:
            value_structure = ElTree.SubElement(value_goods, 'Value')
            value_structure.set('xsi:type', 'Structure')

            property_marking = ElTree.SubElement(value_structure, 'Property')
            property_marking.set('name', 'Номенклатура')
            value_marking = ElTree.SubElement(property_marking, 'Value')
            value_marking.set('xsi:type', 'xs:string')
            value_marking.text = good.good.marking

            property_count = ElTree.SubElement(value_structure, 'Property')
            property_count.set('name', 'Количество')
            value_count = ElTree.SubElement(property_count, 'Value')
            value_count.set('xsi:type', 'xs:decimal')
            value_count.text = str(good.quantity)

            property_gtd = ElTree.SubElement(value_structure, 'Property')
            property_gtd.set('name', 'ГТД')
            value_gtd = ElTree.SubElement(property_gtd, 'Value')
            value_gtd.set('xsi:type', 'xs:string')
            value_gtd.text = f"{self.gtdId}/{good.group.number}"

        erp_data = ElTree.tostring(struct, encoding='utf-8', method='xml')
        filename = f'erp {user.pk} { gtd_id.replace("/", "_")}.xml'
        filepath = os.path.join(USER_DIR, 'erp/', filename)

        with open(filepath, 'wb') as erp_file:
            erp_file.write(erp_data)
        self.exported_to_erp = True
        self.save()

        erp_exp = ErpExport.objects.create(
            gtd=self,
            user=user,
            comment=comment,
            filename=filename
        )
        erp_exp.save()

    def export_to_wms(self, comment, user):
        """
        Функция формирования XML-файла, предназначенного для последующего экспорта в WMS
        """
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

        doc = ElTree.Element('DOC')
        doc_in = ElTree.SubElement(doc, 'DOC_IN')
        number = ElTree.SubElement(doc_in, 'NUMBER')
        number.text = gtd_id
        date = ElTree.SubElement(doc_in, 'DATE')
        date.text = gtd_date.strftime("%Y-%m-%d")
        in_date = ElTree.SubElement(doc_in, 'IN_DATE')
        in_date.text = (gtd_date + timedelta(days=5)).strftime("%Y-%m-%d T%H-%M-%S")
        description = ElTree.SubElement(doc_in, 'DSC')
        description.text = comment
        for good, good_attrs in unique_goods.items():
            content = ElTree.SubElement(doc_in, 'CONTENT')
            code = ElTree.SubElement(content, 'CODE')
            code.set('CODE_ID', good)
            count = ElTree.SubElement(code, 'CNT')
            count.text = str(good_attrs[0])
            unit_name = ElTree.SubElement(code, 'UNIT_NAME')
            unit_name.text = good_attrs[1]

        wms_data = ElTree.tostring(doc, encoding='utf-8', method='xml')
        filename = f'wms {user.pk} {gtd_id}.xml'
        filepath = os.path.join(USER_DIR, 'wms/', filename)
        with open(filepath, 'wb') as wms_file:
            wms_file.write(wms_data)

        self.exported_to_wms = True
        self.save()

        wms_exp = WmsExport.objects.create(
            gtd=self,
            user=user,
            comment=comment,
            filename=filename
        )
        wms_exp.save()

    def new_version(self):
        """
        В документе произошли изменения,
        поэтому больше нельзя считать последние файлы экспорта этой модели в базу
        """

        self.exported_to_erp = False
        self.exported_to_wms = False
        self.recount()

    def __str__(self):
        """
        Информация о классе представляется в виде номера ГТД
        """
        return self.gtdId


class CustomsHouse(models.Model):
    """
    Модель справочника таможенных отделов
    """

    house_num = models.CharField(max_length=8, verbose_name='Номер отдела')
    house_name = models.CharField(max_length=255, verbose_name='Название отдела')

    class Meta:
        """
        Метакласс, задающий отображение названия модели для пользователей
        """
        verbose_name = 'Таможенный отдел'
        verbose_name_plural = 'Таможенные отделы'

    def __str__(self):
        """
        Строковое представление объекта модели - название отдела
        """
        return self.house_name


class Exporter(models.Model):
    """
    Модель справочника экспортеров
    """
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
        """
        Метакласс, задающий название модели для человека
        и поля, которые должны быть уникальными, взятые вместе
        """
        verbose_name = 'Экспортер'
        verbose_name_plural = 'Экспортеры'
        unique_together = ('name', 'postal_code', 'city', 'street_house')

    def __str__(self):
        """
        Строковое представление - название компании
        """
        return self.name


# Импортеры - Справочник
class Importer(models.Model):
    """
    Модель справочника импортеров
    """
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
        """
        Метакласс, определяющий человеческое название модели
        и уникальные взятые вместе поля
        """
        verbose_name = 'Импортер'
        verbose_name_plural = 'Импортеры'
        unique_together = ('name', 'postal_code',)

    def __str__(self):
        """
        Строковое представление - название компании
        """
        return self.name


class Country(models.Model):
    """
    Модель справочника стран
    """
    code = models.CharField(max_length=2, verbose_name='Код страны')
    russian_name = models.CharField(max_length=150, verbose_name='Название страны на русском')
    english_name = models.CharField(max_length=150, verbose_name='Название страны на английском')

    class Meta:
        """
        Метакласс, определяющий название модели для человека
        """
        verbose_name = 'Страна'
        verbose_name_plural = 'Страны'

    def __str__(self):
        """
        Строковое представление - название страны
        """
        return self.russian_name


class Currency(models.Model):
    """
    Модель справочника валют
    """
    digital_code = models.CharField(max_length=3, verbose_name='Цифровой код', null=True, blank=True)
    short_name = models.CharField(max_length=3, verbose_name='Обозначение')
    name = models.CharField(max_length=100, verbose_name='Название')

    class Meta:
        """
        Метакласс, задающий название модели для человека
        """
        verbose_name = 'Валюта'
        verbose_name_plural = 'Валюты'

    def __str__(self):
        """
        Строковое представление - буквенное обозначение валюты
        """
        return self.short_name


# Характер сделки - Справочник
class DealType(models.Model):
    """
    Модель справочника характеров сделок
    """
    code = models.CharField(max_length=3, verbose_name='Код характера сделки')
    deal_type = models.TextField(verbose_name='Характер сделки')

    class Meta:
        """
        Метакласс, определяющий название модели для человека
        """
        verbose_name = 'Характер сделки'
        verbose_name_plural = 'Классификатор характера сделки'

    def __str__(self):
        """
        Строковое представление - код
        """
        return self.code


# Группы товаров в ГТД
class GtdGroup(models.Model):
    """
    Модель группы (раздела) ГТД
    """
    gtd = models.ForeignKey('GtdMain', on_delete=models.CASCADE, verbose_name='id ГТД', related_name="+")
    name = models.TextField(verbose_name='Название', null=True, blank=True)
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
        """
        Метакласс, задающий название модели для человека
        """
        verbose_name = 'Группа товаров в ГТД'
        verbose_name_plural = 'Группы товаров в ГТД'

    def __str__(self):
        """
        Строковое представление - номер группы
        """
        return str(self.number)


class TnVed(models.Model):
    """
    Модель справочника кодов ТН ВЭД - Товарой номенклатуры внешнеэкономической деятельности
    """
    code = models.CharField(max_length=18, verbose_name='Номер группы')
    subposition = models.TextField(verbose_name='Подсубпозиция', null=True, blank=True)
    has_environmental_fee = models.BooleanField(verbose_name='Облагается ли экологическим сбором?',
                                                null=True, blank=True, default=False)
    recycling_standart = models.FloatField(verbose_name='Норма утилизации', null=True, blank=True, max_length=255)
    collection_rate = models.FloatField(verbose_name='Ставка сбора', null=True, blank=True, max_length=255)

    class Meta:
        """
        Метакласс, определяющий название модели для человека
        """
        verbose_name = 'ТН ВЭД'
        verbose_name_plural = verbose_name

    def __str__(self):
        """
        Строковое представление - код ТН ВЭД
        """
        return str(self.code)


class Procedure(models.Model):
    """
    Модель справочника типов таможенных процедур
    """
    code = models.CharField(max_length=2, verbose_name='Код таможенной процедуры')
    name = models.CharField(max_length=255, verbose_name='Таможенная процедура')

    class Meta:
        """
        Метакласс, определяющий название модели для человека
        """
        verbose_name = 'Вид таможенной процедуры'
        verbose_name_plural = 'Классификатор видов таможенных процедур'

    def __str__(self):
        """
        Строковое представление - код таможенной процедуры
        """
        return str(self.code)


class Good(models.Model):
    """
    Модель справочника товаров
    """
    marking = models.CharField(max_length=50, verbose_name='Артикул', unique=True)
    name = models.TextField(verbose_name='Товар')
    goodsmark = models.ForeignKey('GoodsMark', on_delete=models.SET_NULL, verbose_name='Торговая марка',
                                  related_name="+", null=True, blank=True)
    trademark = models.ForeignKey('TradeMark', on_delete=models.SET_NULL, verbose_name='Товарный знак',
                                  related_name="+", null=True, blank=True)

    class Meta:
        """
        Метакласс, определяющий название модели для человека
        """
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        """
        Строковое представление - артикул товара
        """
        return str(self.marking)


class TradeMark(models.Model):
    """
    Модель справочника товарных знаков
    """
    trademark = models.CharField(max_length=100, verbose_name='Товарный знак')

    class Meta:
        """
        Метакласс, определяющий название модели для человека
        """
        verbose_name = 'Товарный знак'
        verbose_name_plural = 'Товарные знаки'

    def __str__(self):
        """
        Строковое отображение - сам товарный знак
        """
        return self.trademark


class GoodsMark(models.Model):
    """
    Модель справочника торговых марок (брендов)
    """
    goodsmark = models.CharField(max_length=100, verbose_name='Торговая марка')

    class Meta:
        """
        Метакласс, определяющий название модели для человека
        """
        verbose_name = 'Торговая марка'
        verbose_name_plural = 'Торговые марки'

    def __str__(self):
        """
        Строковое отображение - сама торговая марка
        """
        return self.goodsmark


class Manufacturer(models.Model):
    """
    Модель справочника производителей (заводов)
    """
    manufacturer = models.CharField(max_length=255, verbose_name='Производитель')

    class Meta:
        """
        Метакласс, определяющий название модели для человека
        """
        verbose_name = 'Производитель'
        verbose_name_plural = 'Производители'

    def __str__(self):
        """
        Строковое отображение - сам производитель
        """
        return str(self.manufacturer)


class MeasureQualifier(models.Model):
    """
    Модель справочника единиц измерения
    """
    digital_code = models.CharField(max_length=4, verbose_name='Код', unique=True)
    name = models.CharField(max_length=100, verbose_name='Наименование')
    russian_symbol = models.CharField(max_length=255, null=True, blank=True,
                                      verbose_name='Русское условное обозначение')
    russian_code = models.CharField(max_length=100, verbose_name='Русское кодовое обозначение', null=True, blank=True)
    english_symbol = models.CharField(max_length=255, null=True, blank=True,
                                      verbose_name='Международное условное обозначение')
    english_code = models.CharField(max_length=20, null=True, blank=True,
                                    verbose_name='Международное кодовое обозначение')

    class Meta:
        """
        Метакласс, определяющий название модели для человека
        """
        verbose_name = 'Единица измерения'
        verbose_name_plural = 'Единицы измерения'

    def __str__(self):
        """
        Строковое отображение - русское сокращенное обозначение, для иностранных - наименование
        """
        if self.russian_code:
            return str(self.russian_code)
        else:
            return str(self.name)


class GtdGood(models.Model):
    """
    Товары, принадлежащие определенным ГТД
    """
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
                                         verbose_name='Пользователь, последний внесший изменения',
                                         null=True, blank=True)

    class Meta:
        """
        Метакласс, определяющий название модели для человека
        """
        verbose_name = 'Товар в ГТД'
        verbose_name_plural = 'Товары в ГТД'


class Document(models.Model):
    """
    Модель документов
    """
    name = models.CharField(max_length=255, verbose_name='Название документа')
    doc_type = models.ForeignKey('DocumentType', verbose_name='Id типа документа', related_name="+",
                                 null=True, blank=True, on_delete=models.SET_NULL)
    number = models.CharField(max_length=255, verbose_name='Номер документа', null=True)
    date = models.DateField(verbose_name='Дата', blank=True, null=True)
    begin_date = models.DateField(verbose_name='Дата начала действия', blank=True, null=True)
    expire_date = models.DateField(verbose_name='Дата окончания действия', blank=True, null=True)

    class Meta:
        """
        Метакласс, определяющий название модели для человека
        """
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'

    def __str__(self):
        """
        Строковое отображение - название документа
        """
        return self.name


class DocumentType(models.Model):
    """
    Модель справочника типов документов
    """
    code = models.CharField(max_length=8, verbose_name='Код типа документа')
    name = models.TextField(verbose_name='Тип документа')

    class Meta:
        """
        Метакласс, определяющий название модели для человека
        """
        verbose_name = 'Тип документа'
        verbose_name_plural = 'Типы документов'

    def __str__(self):
        """
        Строковое отображение - код типа документа
        """
        return self.code


class GtdDocument(models.Model):
    """
    Документы, принадлежащие определенной группе (разделу) ГТД
    """
    gtd = models.ForeignKey('GtdMain', on_delete=models.CASCADE, verbose_name='id ГТД', related_name="+")
    group = models.ForeignKey('GtdGroup', on_delete=models.CASCADE, verbose_name='id группы товаров', related_name="+")
    document = models.ForeignKey('Document', on_delete=models.CASCADE, verbose_name='id документа', related_name="+")

    class Meta:
        """
        Метакласс, определяющий название модели для человека
        """
        verbose_name = 'Документ в ГТД'
        verbose_name_plural = 'Документы в ГТД'
        unique_together = ('gtd', 'group', 'document')


class UploadGtd(models.Model):
    """
    Записи, свидетельствующие о загрузке в базу какого-то количества ГТД
    """
    description = models.CharField(max_length=255, blank=True, verbose_name='Краткий комментарий')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    files_num = models.IntegerField(verbose_name='Количество прикрепленных файлов', null=True, blank=True)
    who_uploaded = models.ForeignKey('RegUser', blank=True, null=True, on_delete=models.SET_NULL,
                                     related_name='+', verbose_name='Пользователь, загрузивший файл(ы)')

    class Meta:
        """
        Метакласс, определяющий название модели для человека
        а также порядок следования записей
        """
        verbose_name = 'Загруженная ГТД'
        verbose_name_plural = 'Загруженные ГТД'
        ordering = ['uploaded_at']


class UploadGtdFile(models.Model):
    """
    Модель, записи которой хранят информацию о файле документа ГТД, который был загружен в систему
    """
    uploaded_gtd = models.ForeignKey('UploadGtd', on_delete=models.CASCADE, related_name='+',
                                     verbose_name='id партии загруженных ГТД')
    document = models.FileField(upload_to='gtd/')
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        """
        Метакласс, определяющий название модели для человека
        """
        verbose_name = 'Загруженный файл ГТД'
        verbose_name_plural = 'Загруженные файлы ГТД'


class WmsExport(models.Model):
    """
    Модель, сохраняющая информацию о cформированных по определенным ГТД xml-файлых для WMS
    """
    gtd = models.ForeignKey('GtdMain', on_delete=models.CASCADE, verbose_name='id ГТД', related_name='+')
    comment = models.TextField(verbose_name='Комментарий', null=True, blank=True)
    filename = models.CharField(verbose_name='Имя файла', max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey('RegUser', on_delete=models.SET_NULL, verbose_name='Пользователь, выполнивший экспорт',
                             related_name='+', null=True)


class ErpExport(models.Model):
    """
    Модель, содержащая информацию о сформированных по определенной ГТД xml-файлов для ERP
    """
    gtd = models.ForeignKey('GtdMain', on_delete=models.CASCADE, verbose_name='id ГТД', related_name='+')
    comment = models.TextField(verbose_name='Комментарий', default='')
    filename = models.CharField(verbose_name='Имя файла', max_length=255)
    datetime = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey('RegUser', on_delete=models.SET_NULL,
                             verbose_name='Пользователь, выполнивший экспорт', null=True)


class Handbook(models.Model):
    """
    Модель списка справочников
    """
    name = models.CharField(verbose_name='Название', max_length=255, unique=True)
    is_actual_table = models.BooleanField(verbose_name='Актуальная таблица', default=False)

    def __str__(self):
        """
        Строковое отображение - название справочника
        """
        return self.name
