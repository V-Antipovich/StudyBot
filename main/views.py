from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
# from django.views.generic import TemplateView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.http import FileResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from .forms import UploadGtdfilesForm, GtdUpdateForm, RegisterUserForm, GtdGoodUpdateForm, GtdGroupUpdateForm,\
    CalendarDate, ExportComment
from .models import GtdMain, GtdGroup, GtdGood, UploadGtd, CustomsHouse, Exporter, Country, Currency, Importer, DealType,\
    Procedure, TnVed, Good, GoodsMark, GtdDocument, Document, TradeMark, Manufacturer, MeasureQualifier, DocumentType,\
    UploadGtdFile
from django.views.generic.edit import FormView
import os
from .utilities import parse_gtd, get_tnved_name
from .models import RegUser
from customs_declarations_database.settings import MEDIA_ROOT, USER_DIR
from customs_declarations_database.Constant import under
import xlsxwriter
import mimetypes
from datetime import datetime, timedelta

import xml.etree.ElementTree as ET


# TODO: all todo in extra staff
# Вспомогательные функции контроля доступа - проверка пользователя, является ли он суперпользователем
def superuser_check(user):
    return user.is_superuser


# Декоратор, разрешающий доступ определенным группам
def groups_required(*group_names):
    def in_group(u):
        return u.is_active and (u.is_superuser or u.groups.filter(name='Администратор').exists() or bool(u.groups.filter(name__in=group_names)))
    return user_passes_test(in_group, login_url=reverse_lazy('main:access_denied'))


# Представление регистрации пользователя
class RegisterUserView(CreateView):
    model = RegUser
    template_name = 'main/register_user.html'
    form_class = RegisterUserForm
    success_url = reverse_lazy('main:show_gtd')


class AccessDeniedView(TemplateView):
    template_name = 'main/no_access.html'


# Представление обработки справочников
def handbook(request):
    choice = request.GET.get('choice', 'default')

    # Словарь со всеми справочниками системы
    # Ключ - параметр url, Значение - (<Модель этого справочника>, <Название справочника для пользователей>)
    avaliable_handbooks = {
        'customs_houses': (CustomsHouse, 'Отделы таможни'),
        'exporters': (Exporter, 'Экспортеры'),  # Содержит обращение к другим моделям
        'importers': (Importer, 'Импортеры'),  # Содержит обращение к другим моделям
        'countries': (Country, 'Государства'),
        'currencies': (Currency, 'Валюты'),
        'deal_types': (DealType, 'Классификатор характера сделки'),
        'tn_ved': (TnVed, 'Классификатор ТН ВЭД'),
        'procedures': (Procedure, 'Таможенные процедуры'),
        'goods': (Good, 'Товары'),
        'trade_marks': (TradeMark, 'Товарные знаки'),  # Содержит обращение к другим моделям
        'goods_marks': (GoodsMark, 'Торговые марки'),  # Содержит обращение к другим моделям
        'manufacturers': (Manufacturer, 'Производители (заводы)'),
        'qualifiers': (MeasureQualifier, 'Единицы измерения'),
        'doc_types': (DocumentType, 'Классификатор типов документов'),
    }

    # Некоторые справочники содержат FK, которые для фронта надо подменять
    # Словарь с зависимыми моделями
    # Ключи - поля FK, которые встречаются в моделях из avaliable_handbooks
    # Значения - (<Модель, с которой через FK отношение m2o>,
    #             <Поле из этой модели, чье значение требуется>,
    #             <Порядковый номер поля в списке полей этой модели>)
    dependent_models = {
        'country_id': (Country, 'russian_name', 2),
        'goodsmark_id': (GoodsMark, 'goodsmark', 1),
        'trademark_id': (TradeMark, 'trademark', 1),
      #  'doc_type_id': (DocumentType, 'code', 1),
    }
    # По умолчанию на странице справочников будет открыт справочник товаров
    if choice == 'default':
        choice = 'goods'
    # По параметру ссылки получаем название и модель справочника
    get_handbook = avaliable_handbooks[choice]
    handbook_name = get_handbook[1]
    handbook_class = get_handbook[0]

    handbook_objects = handbook_class.objects.all()

    # Доступ к полям модели справочника
    meta = handbook_class._meta
    get_fields = meta.get_fields()

    # Массив для хранения служебной инфы для махинаций с атрибутами
    fields_system_data = []
    # Массив для имен колонок таблицы - как они будут отображаться на фронте
    fields_verbose_names = []

    for field in get_fields:
        methods = dir(field)
        # Служебное поле PK не включаем
        if '_check_primary_key' not in methods:
            # Обработаем FK - Выведем данные непосредственно из связанной таблицы
            if '_related_query_name' in methods:
                # Достаем данные связанной модели
                dependent_tuple = dependent_models[field.attname]

                dependent_model = dependent_tuple[0]
                dependent_objects = dependent_model.objects

                # Для имени колонки возьмем один объект из связанной модели
                dependent_object = dependent_models[field.attname][0].objects.last()
                needed_field = dependent_tuple[1]

                # Объекты массива служебной инфы
                # (<Bool: поле внешнего ключа?>, <Имя поля>,
                # <Объекты связанной модели>, <Нужное поле из связанной модели>)
                sys_attrs = (True, field.attname, dependent_objects, needed_field)

                # Имя поля для пользователя в связанной модели
                verbose_name = dependent_object._meta.get_fields()[dependent_tuple[2]].verbose_name

            else:
                # (<Bool: поле внешнего ключа?>, <имя поля для фронта>)
                sys_attrs = (False, field.attname)

                verbose_name = field.verbose_name

            fields_system_data.append(sys_attrs)
            fields_verbose_names.append(verbose_name)

    # Собираем непосредственно данные справочника
    handbook_data = []
    for obj in handbook_objects:
        attrs = []
        # Для каждого атрибута пройдемся по его полям
        for field in fields_system_data:
            if field[0]:
                needed_pk = getattr(obj, field[1])
                needed_raw_obj = field[2].filter(pk=needed_pk)
                if needed_raw_obj.exists():
                    needed_data = getattr(needed_raw_obj[0], field[3])
                else:
                    needed_data = ''
                # Если поле внешнего ключа, обращаемся к связанной модели и получаем данные оттуда
                # Временная заглушка
                #  needed_data = getattr(field[2].filter(pk=getattr(obj, field[1]))[0], field[3])
            else:
                # В противном случае просто обращаемся к значению нужного поля
                needed_data = getattr(obj, field[1])
                if not needed_data:
                    needed_data = ''
            attrs.append(needed_data)
        handbook_data.append(attrs)

    context = {
        'choice': choice,
        'handbook_name': handbook_name,
        'verbose_names': fields_verbose_names,
        'values': handbook_data,
        'avaliable_handbooks': list(avaliable_handbooks.items()),
        }
    return render(request, 'main/handbook.html', context)


# Начальная страница
# TODO: нормальный вид
def index(request):
    return redirect('main:profile')
    # return render(request, 'main/index.html')


# Список всех ГТД
class ShowGtdView(LoginRequiredMixin, ListView):
    model = GtdMain
    template_name = 'main/show_gtd.html'
    login_url = reverse_lazy('main:login')
    context_object_name = 'gtds'
    # paginate_by = 10

    def get_paginate_by(self, queryset):
        try:
            self.paginate_by = int(self.request.GET.get('paginate_by', 10))
        except ValueError:
            logger.error('Some stupid person use not int for paginate_by')
            # pass # TODO: сделать что-то с заглушкой
        return self.paginate_by


# Представление персональной страницы ГТД
class GtdDetailView(DetailView):
    model = GtdMain
    template_name = 'main/per_gtd.html'
    context_object_name = 'gtd'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        groups = GtdGroup.objects.filter(gtd_id=self.kwargs.get('pk'))
        context['groups'] = groups
        open_goods = self.request.GET.get('group')
        context['are_goods_shown'] = open_goods
        if open_goods:
            context['goods'] = GtdGood.objects.filter(gtd_id=self.kwargs.get('pk'), group=open_goods)
            context['number'] = GtdGroup.objects.filter(pk=open_goods)[0].number
            # context['user'] = self.request.user.f
        return context


# Представление редактирования шапки ГТД
def update_gtd(request, pk):
    obj = get_object_or_404(GtdMain, pk=pk)
    if request.method == 'POST':
        obj.last_edited_user = request.user
        form = GtdUpdateForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('main:per_gtd', pk=pk)
    else:
        form = GtdUpdateForm(instance=obj)
        context = {
            'form': form,
            'gtd': obj,
        }
        return render(request, 'main/update_gtd.html', context)


# Функция для редактирования группы товаров
def update_gtd_group(request, pk):
    obj = get_object_or_404(GtdGroup, pk=pk)
    if request.method == 'POST':
        obj.last_edited_user = request.user
        form = GtdGroupUpdateForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('main:per_gtd', pk=obj.gtd.pk)
    else:
        form = GtdGroupUpdateForm(instance=obj)
        context = {
            'form': form,
            'group': obj,
        }
        return render(request, 'main/update_gtd_group.html', context)


# Редактировать товар из группы ГТД
def update_gtd_good(request, pk):
    obj = get_object_or_404(GtdGood, pk=pk)
    if request.method == 'POST':
        obj.last_edited_user = request.user
        form = GtdGoodUpdateForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('main:per_gtd', pk=obj.gtd.pk)
    else:
        form = GtdGoodUpdateForm(instance=obj)
        context = {
            'form': form,
            'good': obj,
        }
        return render(request, 'main/update_gtd_good.html', context)


# Страница удаления ГТД
class GtdDeleteView(DeleteView):
    model = GtdMain
    template_name = 'main/delete_gtd.html'
    success_url = reverse_lazy('main:show_gtd')
    context_object_name = 'gtd'


# Экологический сбор: выбор периода, сбор данных о ГТД из этого периода, содержащих ТН ВЭД, подлежащие эко сбору

@groups_required('Бухгалтер')
def eco_fee(request):
    if request.method == 'GET':
        form = CalendarDate()
        context = {
            'form': form,
            'message': ''
        }
        return render(request, 'main/ecological_fee_build.html', context)
    else:
        form = CalendarDate(request.POST)
        if form.is_valid():
            start = datetime.strptime(form.data['start_date'], "%Y-%m-%d")
            end = datetime.strptime(form.data['end_date'], "%Y-%m-%d")
            gtds_range = GtdMain.objects.filter(date__range=[start, end])

            all_groups = GtdGroup.objects.filter(gtd_id__in=gtds_range, tn_ved__has_environmental_fee=True)

            by_tnved = {'expanded': {}, 'total': {}}
            for group in all_groups:
                gtdId = group.gtd.gtdId
                tn_ved = group.tn_ved.code
                rate = group.tn_ved.collection_rate
                standart = group.tn_ved.recycling_standart
                weight = group.net_weight
                row = [rate, standart, weight, rate*weight*standart/100000]

                if tn_ved in by_tnved:
                    if gtdId in by_tnved['expanded'][tn_ved]:
                        by_tnved['expanded'][tn_ved][gtdId][2] += weight
                        by_tnved['expanded'][tn_ved][gtdId][3] += row[3]
                    else:
                        by_tnved['expanded'][tn_ved][gtdId] = row
                    by_tnved['total'][tn_ved][2] += weight
                    by_tnved['total'][tn_ved][3] += row[3]
                else:
                    by_tnved['expanded'][tn_ved] = {}

                    by_tnved['expanded'][tn_ved][gtdId] = row
                    by_tnved['total'][tn_ved] = row

            filename = f"eco {request.user.pk} {start.strftime('%d-%m-%Y')}-{end.strftime('%d-%m-%Y')}.xlsx"
            path = os.path.join(MEDIA_ROOT, 'reports/eco', filename)
            workbook = xlsxwriter.Workbook(path)
            worksheet = workbook.add_worksheet()
            i = 1
            worksheet.write(0, 0, 'ТН ВЭД')
            worksheet.write(0, 1, 'Ставка за тонну')
            worksheet.write(0, 2, 'Норматив утилизации')
            worksheet.write(0, 3, 'Масса нетто')
            worksheet.write(0, 4, 'Сумма')
            t = by_tnved['total']
            for k in t:
                worksheet.write(i, 0, k)
                worksheet.write(i, 1, t[k][0])
                worksheet.write(i, 2, t[k][1])
                worksheet.write(i, 3, t[k][2])
                worksheet.write(i, 4, t[k][3])
                i += 1

            workbook.close()
            context = {
                'form': CalendarDate(),
                'show': True,
                'start': start,
                'end': end,
                'filename': filename,
                'total': by_tnved['total'],
                'expanded': by_tnved['expanded'],
            }
            # return render(request, 'main/ecological_fee_build.html', context)
        else:
            form = CalendarDate()
            context = {
                'form': form,
                'message': 'Некорректный диапазон. Попробуйте ещё раз.',
            }
        return render(request, 'main/ecological_fee_build.html', context)


# Вывод xml-файла выбранной ГТД
def show_gtd_file(request, filename):
    get_path = os.path.join(MEDIA_ROOT, str(filename))
    return HttpResponse(open(get_path, 'r', encoding='utf-8'), content_type='application/xml')


# Представление для генерации xml-файла
# @login_required
@groups_required('Сотрудник таможенного отдела')
def to_wms(request, pk):
    gtd = GtdMain.objects.filter(pk=pk)[0]
    if request.method == 'POST':
        form = ExportComment(request.POST)
        if form.is_valid():
            gtdId = gtd.gtdId.replace('/', '_')
            gtd_date = gtd.date
            comment = request.POST['comment']
            goods = GtdGood.objects.filter(gtd_id=pk)

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
            number.text = gtdId
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
            filename = f'wms {request.user.pk} {gtdId}.xml'
            filepath = os.path.join(USER_DIR, 'wms/', filename)  # TODO: перенести в функционал модели (толстая модель)
            with open(filepath, 'wb') as wms_file:
                wms_file.write(wms_data)

            gtd.exported_to_wms = True
            gtd.save()
            return redirect('main:success', pk=pk)

    else:
        form = ExportComment()

        context = {
            'form': form,
            'gtd': gtd,
        }
        return render(request, 'main/wms.html', context)


# Формирование файла для ERP
@groups_required('Бухгалтер')
def to_erp(request, pk): #TODO: лог пользователю в профиль
    gtd = GtdMain.objects.filter(pk=pk)[0]
    if request.method == 'POST':
        form = ExportComment(request.POST)
        if form.is_valid():
            comment = request.POST['comment']

            goods = GtdGood.objects.filter(gtd_id=pk) # TODO: повторяющиеся товары в пределах одной группы надо суммировать
            # TODO: перенести в функционал модели (толстая модель)
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
            value_date.text = gtd.date.strftime("%d-%m-%Y %H-%M-%S")

            prop_warehouse = ET.SubElement(struct, 'Property')
            prop_warehouse.set('name', 'Склад')
            value_warehouse = ET.SubElement(prop_warehouse, 'Value')
            value_warehouse.set('xsi:type', 'xs:string')
            value_warehouse.text = 'Склад Хлебниково'

            prop_name = ET.SubElement(struct, 'Property')
            prop_name.set('name', 'Ответственный')
            value_name = ET.SubElement(prop_name, 'Ответственный')
            value_name.set('xsi:type', 'xs:string')
            value_name.text = f'{ request.user.last_name } {request.user.first_name} {request.user.patronymic}'

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
                value_gtd.text = f"{gtd.gtdId}/{good.group.number}"

            erp_data = ET.tostring(struct, encoding='utf-8', method='xml')
            filename = f'erp {request.user.pk} {gtd.gtdId.replace("/", "_") }.xml'
            filepath = os.path.join(USER_DIR, 'erp/', filename)

            with open(filepath, 'wb') as erp_file:
                erp_file.write(erp_data)
            gtd.exported_to_erp = True
            gtd.save()
            context = {
                'gtd': gtd,
            }
            return redirect('main:success', pk=pk)
            # return render(request, 'main/successful_outcome.html', context)
    else:
        form = ExportComment()
        context = {
            'form': form,
            'gtd': gtd,
        }
        return render(request, 'main/erp.html', context)


class SuccessfulOutcome(TemplateView):
    template_name = 'main/successful_outcome.html'

    def get_context_data(self, pk, **kwargs):
        context_data = super(SuccessfulOutcome, self).get_context_data(**kwargs)
        context_data['gtd'] = GtdMain.objects.filter(pk=pk)[0]
        return context_data


class StatisticsMenu(TemplateView):
    template_name = 'main/statistic_reports_menu.html'


@groups_required('Аналитик')
def statistics_report_gtd_per_exporter(request):
    if request.method == 'POST':
        form = CalendarDate(request.POST)
        if form.is_valid():
            start = datetime.strptime(form.data['start_date'], "%Y-%m-%d")
            end = datetime.strptime(form.data['end_date'], "%Y-%m-%d")
            gtds_range = GtdMain.objects.filter(date__range=[start, end])
            exporters = {}
            for gtd in gtds_range:
                exp = gtd.exporter.name
                if exp in exporters:
                    exporters[exp] += 1
                else:
                    exporters[exp] = 1
            exporters = list(exporters.items())
            exporters.sort(key=lambda x: x[0])
            filename = f"gtds_per_exporter {request.user.pk} {start.strftime('%d-%m-%Y')}-{end.strftime('%d-%m-%Y')}.xlsx"
            path = os.path.join(MEDIA_ROOT, 'reports/statistics', filename)
            workbook = xlsxwriter.Workbook(path)
            worksheet = workbook.add_worksheet()
            i = 1
            worksheet.write(0, 0, 'Поставщик')
            worksheet.write(0, 1, 'Количество ГТД')
            for exp in exporters:
                worksheet.write(i, 0, exp[0])
                worksheet.write(i, 1, exp[1])
                i += 1
            workbook.close()
            context = {
                'form': CalendarDate(),
                'exporters': exporters,
                'show': True,
                'filename': filename,
                'start': start,
                'end': end,
            }
            return render(request, 'main/statistics_report_gtd_per_exporter.html', context)
        else:
            form = CalendarDate()
            context = {
                'form': form,
                'message': 'Некорректный диапазон. Попробуйте ещё раз.',
            }
            return render(request, 'main/statistics_report_gtd_per_exporter.html', context)
    else:
        form = CalendarDate()
        context = {
            'form': form,
            'message': '',
        }
        return render(request, 'main/statistics_report_gtd_per_exporter.html', context)


@groups_required('Аналитик')
def statistics_report_goods_imported(request):
    if request.method == 'POST':
        form = CalendarDate(request.POST)
        if form.is_valid():
            start = datetime.strptime(form.data['start_date'], "%Y-%m-%d")
            end = datetime.strptime(form.data['end_date'], "%Y-%m-%d")

            gtds = GtdMain.objects.filter(date__range=[start, end])
            goods = GtdGood.objects.filter(gtd__in=gtds)

            unique_goods = {}
            for good in goods:
                marking = good.good.marking
                if marking in unique_goods:
                    unique_goods[marking][1] += good.quantity
                else:
                    unique_goods[marking] = [good.good.name, good.quantity]
            unique_goods = sorted(list(unique_goods.items()), key=lambda x: x[0])

            filename = f"goods_imported {request.user.pk} {start.strftime('%d-%m-%Y')}-{end.strftime('%d-%m-%Y')}.xlsx"
            path = os.path.join(MEDIA_ROOT, 'reports/statistics', filename)
            workbook = xlsxwriter.Workbook(path)
            worksheet = workbook.add_worksheet()
            i = 1
            worksheet.write(0, 0, 'Артикул')
            worksheet.write(0, 1, 'Имя товара')
            worksheet.write(0, 2, 'Количество')
            for good in unique_goods:
                worksheet.write(i, 0, good[0])
                worksheet.write(i, 1, good[1][0])
                worksheet.write(i, 2, good[1][1])
                i += 1
            workbook.close()
            context = {
                'form': CalendarDate(),
                'start': start,
                'end': end,
                'show': True,
                'goods': unique_goods,
                'filename': filename,
                # 'goods': goods,
                # 'gtds': gtds,
            }
            return render(request, 'main/statistics_report_goods_imported.html', context)
        else:
            context = {
                'form': CalendarDate(),
                'message': 'Некорректный диапазон. Попробуйте ещё раз.',
            }
            return render(request, 'main/statistics_report_goods_imported.html', context)
    else:
        form = CalendarDate()
        context = {
            'form': form,
            'message': '',
        }
        return render(request, 'main/statistics_report_goods_imported.html', context)


def report_xlsx(request, folder, filename):
    filepath = os.path.join(MEDIA_ROOT, 'reports/', folder, filename)
    path = open(filepath, 'rb')
    mime_type, _ = mimetypes.guess_type(filepath)
    response = HttpResponse(path, content_type=mime_type)
    response['Content-Disposition'] = f"attachment; filename={filename}"
    return response


@login_required
def profile(request):
    context = {'user': request.user, 'groups': request.user.groups}
    return render(request, 'main/profile.html', context)


# Авторизация
class CDDLogin(LoginView):
    template_name = 'main/login.html'


# Выход из аккаунта
class CDDLogout(LogoutView, LoginRequiredMixin):
    template_name = 'main/logout.html'


# class RegisterUserView(CreateView):
#     model = RegUser
#     template_name = 'main/register_user.html'
#     form_class = RegisterUserForm
#     success_url = reverse_lazy('main:register_done')


# class RegisterDoneView(TemplateView):
#     template_name = 'main/'


# Загрузка файлов ГТД в формате .xml


# @login_required(login_url='/accounts/login/')
# @user_passes_test(is_accountant)

@groups_required('Сотрудник таможенного отдела')
def upload_gtd(request):
    if request.method == 'POST':
        form = UploadGtdfilesForm(request.POST, request.FILES)
        if form.is_valid():
            on_duplicate = request.POST['on_duplicate']

            uploaded_gtd = UploadGtd(
                description=request.POST['comment']
            )
            uploaded_gtd.save()
            files = request.FILES.getlist('document')
            file_objects = []
            for file in files:
                uploaded_gtd_file = UploadGtdFile(
                    uploaded_gtd=uploaded_gtd,
                    document=file
                )
                uploaded_gtd_file.save()
                file_objects.append(uploaded_gtd_file)

            uploaded_gtd.files_num = len(file_objects)
            uploaded_gtd.save()

            all_files = len(files)
            log = {
                'skip': [],
                'new': [],
                'update': [],
            }
            for gtd in file_objects:

                last_file = gtd.document

                path = os.path.join(MEDIA_ROOT, str(last_file))
                # Получили словарь с распарсенной гтд
                get_gtdmain, get_gtdgroups = parse_gtd(path)
                # Сначала проверим, надо ли вообще добавлять ГТД, если таковая имеется.
                obj = GtdMain.objects.filter(gtdId=get_gtdmain['gtdId'])
                if obj.exists():
                    if on_duplicate == 'skip':
                        log['skip'].append(obj[0]) #get_gtdmain['gtdId'])
                        continue
                    else:
                        where_to_put = 'update'
                        # log[where_to_put].append(get_gtdmain['gtdId'])
                else:
                    where_to_put = 'new'
                    # Работа с GtdMain - основная инфа в шапке ГТД

                # Обновим справочник экспортеров если требуется
                exporter_info = get_gtdmain["exporter"]
                # add_exporter, exp_created = Exporter.objects.update_or_create(
                #     name=exporter_info["name"],
                #     postal_code=exporter_info["postal_code"],
                #     country=Country.objects.get(code=exporter_info["country"]),
                #     city=exporter_info["city"],
                #     street_house=exporter_info['street_house'],
                #     house=exporter_info["house"],
                #     region=exporter_info['region']
                # )
                add_exporter = Exporter.objects.filter(name=exporter_info["name"], postal_code=exporter_info["postal_code"])
                if add_exporter.exists():
                    add_exporter = add_exporter[0]
                else:
                    add_exporter = Exporter.objects.create(
                        name=exporter_info["name"],
                        postal_code=exporter_info["postal_code"],
                        country=Country.objects.get(code=exporter_info["country"]),
                        city=exporter_info["city"],
                        street_house=exporter_info['street_house'],
                        house=exporter_info["house"],
                        region=exporter_info['region']
                    )
                    add_exporter.save()

                # Обновим справочник импортеров
                importer_info = get_gtdmain["importer"]
                add_importer, imp_created = Importer.objects.update_or_create(
                    name=importer_info["name"],
                    inn=importer_info["inn"],
                    ogrn=importer_info["orgn"],
                )
                if imp_created:
                    add_importer.country = Country.objects.get(code=importer_info["country"])
                    add_importer.kpp = importer_info["kpp"]
                    add_importer.postal_code = importer_info["postal_code"]
                    add_importer.city = importer_info["city"]
                    add_importer.street_house = importer_info["street_house"]
                    add_importer.house = importer_info["house"]
                    add_importer.save()

                # Добавим непосредственно главную инфу гтд
                add_gtdmain, gtdmain_created = GtdMain.objects.update_or_create(
                    gtdId=get_gtdmain["gtdId"],
                    customs_house=CustomsHouse.objects.get(house_num=get_gtdmain["customs_house"]),
                    date=get_gtdmain["date"],
                    order_num=get_gtdmain["order_num"]
                )
                if gtdmain_created:
                    add_gtdmain.total_goods_number = get_gtdmain["total_goods_number"]
                    add_gtdmain.exporter = Exporter.objects.filter(name=exporter_info['name'])[0]
                    add_gtdmain.importer = Importer.objects.get(name=importer_info['name'])
                    add_gtdmain.trading_country = Country.objects.get(code=get_gtdmain["trading_country"])
                    add_gtdmain.total_cost = get_gtdmain["total_cost"]
                    add_gtdmain.currency = Currency.objects.get(short_name=get_gtdmain["currency"])
                    add_gtdmain.total_invoice_amount = get_gtdmain["total_invoice_amount"]
                    add_gtdmain.currency_rate = get_gtdmain["currency_rate"]
                    add_gtdmain.deal_type = DealType.objects.get(code=get_gtdmain["deal_type"])
                    add_gtdmain.gtd_file = gtd
                    add_gtdmain.last_edited = request.user
                    add_gtdmain.save()
                log[where_to_put].append(add_gtdmain)  # get_gtdmain['gtdId'])

                # Теперь в цикле надо пройтись по группам ГТД.
                # gtd_id = GtdMain.objects.get(gtdId=get_gtdmain["gtdId"])
                for group in get_gtdgroups:
                    # Заносим группу, если такой ещё не было
                    # Проверяем ТН ВЭД
                    code = group["tn_ved"]
                    if code[0] == '0':
                        code = code[1:]
                    tn_ved = TnVed.objects.filter(code=code)

                    # add_tnved, tnved_created = TnVed.objects.update_or_create(
                    #     code=group["tn_ved"]
                    # )
                    if len(tn_ved) == 0:
                        code = group["tn_ved"]
                        met = False
                        rec_standart = None
                        col_rate = None
                        for item in under:
                            if met:
                                break
                            for c in item:
                                if code.find(c) == 0:
                                    met = True
                                    vals = under[item]
                                    rec_standart = vals[0]
                                    col_rate = vals[1]
                                    break
                        add_tnved = TnVed.objects.create(
                            code=code,
                            subposition=get_tnved_name(code),
                            has_environmental_fee=met,
                            recycling_standart=rec_standart,
                            collection_rate=col_rate,
                        )
                        # add_tnved.subposition = get_tnved_name(str(group["tn_ved"]))
                        add_tnved.save()
                    add_gtdgroup, gtdgroup_created = GtdGroup.objects.update_or_create(
                        gtd=add_gtdmain,
                        name=group['name'],
                        # description=group['desc'],
                        tn_ved=TnVed.objects.filter(code=str(group['tn_ved']))[0],
                        number=group["number"],
                        gross_weight=group['gross_weight'],
                        net_weight=group['net_weight'],
                        country=Country.objects.get(code=group['country']),
                        procedure=Procedure.objects.get(code=group['procedure']),
                        prev_procedure=Procedure.objects.get(code=group['prev_procedure']),
                        customs_cost=group["customs_cost"],
                        fee=group["fee"],
                        ndc=group['ndc'],
                        fee_percent=group['fee_percent'],
                        ndc_percent=group['ndc_percent']
                    )

                    # Заносим в цикле товары внутри группы
                    get_goods = group["goods"]
                    for gtd_good in get_goods:
                        good_itself = gtd_good["good"]

                        # Обновляем справочник товарных знаков
                        try_trademark = good_itself['trademark']
                        if try_trademark:
                            add_trademark, trademark_created = TradeMark.objects.update_or_create(
                                trademark=try_trademark
                            )
                        else:
                            add_trademark = None

                        # Обновляем справочник торговых марок
                        try_goodsmark = good_itself['brand']
                        if try_goodsmark:
                            add_goodsmark, goodsmark_created = GoodsMark.objects.update_or_create(
                                goodsmark=try_goodsmark
                            )
                        else:
                            add_goodsmark = None

                        # Обновляем таблицу товаров
                        # add_good, good_created = Good.objects.update_or_create(
                        #     marking=good_itself['marking'],
                        #     name=good_itself['name'],
                        #     trademark=add_trademark,
                        #     goodsmark=add_goodsmark
                        # )
                        add_good = Good.objects.filter(marking=good_itself['marking'])
                        if not add_good.exists():
                            add_good = Good.objects.create(
                                marking=good_itself['marking'],
                                name=good_itself['name'],
                                trademark=add_trademark,
                                goodsmark=add_goodsmark
                            )
                        else:
                            add_good = add_good[0]

                        # Обновляем справочник производителей (заводов)
                        try_manufacturer = gtd_good['manufacturer']
                        if try_manufacturer:
                            add_manufacturer, manufacturer_created = Manufacturer.objects.update_or_create(
                                manufacturer=gtd_good['manufacturer']
                            )
                        else:
                            add_manufacturer = None

                        # Добавляем Товар ГТД
                        add_gtdgood = GtdGood.objects.filter(gtd_id=add_gtdmain.pk, group_id=add_gtdgroup.pk, good_num=gtd_good['good_num'])
                        if not add_gtdgood.exists():
                            add_gtdgood = GtdGood.objects.create(
                                gtd=add_gtdmain,
                                group=add_gtdgroup,
                                good_num=gtd_good['good_num'],
                                good=Good.objects.get(pk=add_good.pk),
                                quantity=gtd_good['quantity'],
                                qualifier=MeasureQualifier.objects.get(digital_code=gtd_good['qualifier_code']),
                                manufacturer=add_manufacturer
                            )
                            add_gtdgood.save()

                    # Заносим в цикле документы в справочник
                    gtd_documents = group['documents']

                    for gtd_document in gtd_documents:
                        add_document, document_created = Document.objects.update_or_create(
                            name=gtd_document['name'],
                            doc_type=DocumentType.objects.get(code=gtd_document['doc_type']),
                            number=gtd_document['number'],
                            date=gtd_document['date'],
                            begin_date=gtd_document['begin_date'],
                            expire_date=gtd_document['expire_date']
                        )
                        add_gtddocument, gtddocument_created = GtdDocument.objects.update_or_create(
                            gtd=add_gtdmain,
                            group=add_gtdgroup,
                            document=add_document,
                        )
            skipped = len(log['skip'])
            updated = len(log['update'])
            new = len(log['new'])
            context = {
                'log': log,
                'skipped': skipped,
                'updated': updated,
                'new': new,
                'all': skipped + updated + new,
                'test': get_goods,
            }
            return render(request, 'main/upload_gtd_log.html', context)
        # else:
        #     return render(request, 'main/error.html')

    else:
        form = UploadGtdfilesForm()
        context = {'form': form}
        return render(request, 'main/upload_gtd.html', context)

# TODO: Обработчик добавления и удаления юзеров
# TODO: Регистрация пользователей должна производиться только админом
# TODO: Контроллеры входа, сброса пароля, смены пароля
