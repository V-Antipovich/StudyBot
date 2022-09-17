from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.db import IntegrityError
from django.urls import reverse_lazy, reverse
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.http import FileResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from .forms import UploadGtdfilesForm, GtdUpdateForm, RegisterUserForm, GtdGoodUpdateForm, GtdGroupUpdateForm
from .models import GtdMain, GtdGroup, GtdGood, UploadGtd, CustomsHouse, Exporter, Country, Currency, Importer, DealType, Procedure, TnVed, Good, GoodsMark, GtdDocument, Document, TradeMark, Manufacturer, MeasureQualifier, DocumentType, UploadGtdFile
from django.views.generic.edit import FormView
import os
from .utilities import parse_gtd, get_tnved_name
from .models import RegUser
from customs_declarations_database.settings import MEDIA_ROOT
from django_sorting_bootstrap.views import SimpleChangeList


# Вспомогательные функции контроля доступа
def superuser_check(user):
    return user.is_superuser


class RegisterUserView(CreateView):
    model = RegUser
    template_name = 'main/register_user.html'
    form_class = RegisterUserForm
    success_url = reverse_lazy('main:show_gtd')


# TODO: справочник документов пока вынести в блок документов - Это не справочник!
# TODO: позже? распределить документы по категориям

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
#        'documents': (Document, 'Документы'),  # Содержит обращение к другим моделям
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
                #needed_data = getattr(field[2].filter(pk=getattr(obj, field[1]))[0], field[3])
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


# TODO: нужен контроллер для добавления пользователей администратором (+ письмо активации)
# Начальная страница
def index(request):
    return render(request, 'main/index.html')


# TODO: убрать после того, как станет не нужен
# Контроллер для тестовой странички
def test_view(request):
    context = {
        'req': request.META #.get('HTTP_REFERER')
    }
    return render(request, 'main/test.html', context)


# TODO: в персональной странице ГТД уже выводить дополнительные поля, которые надо убрать в табличном виде
# Список всех ГТД
class ShowGtdView(LoginRequiredMixin, ListView):
    model = GtdMain
    template_name = 'main/show_gtd.html'
    login_url = reverse_lazy('main:login')
    context_object_name = 'gtds'
#    paginate_by = 40


# Персональная страница ГТД
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
        return context


# Редактировать шапку ГТД
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


# Список документов в выбранной группе ГТД
# class ShowGtdDocumentsInGroup(ListView):
#     template_name = 'main/documents_per_group.html'
#     context_object_name = 'documents'
#     paginate_by = 20
#
#     def get_queryset(self, *args, **kwargs):
#         queryset = GtdDocument.objects.filter(gtd=self.kwargs.get('gtd'), group=self.kwargs.get('group_pk'))
#         final_queryset = []
#         for row in queryset:
#             obj = []
#             for item in row:
#                 if item:
#                     obj.append(item)
#                 else:
#                     obj.append('')
#             final_queryset.append(obj)
#         return final_queryset


# Вывод xml-файла выбранной ГТД
def show_gtd_file(request, filename):
    get_path = os.path.join(MEDIA_ROOT, str(filename))
    return HttpResponse(open(get_path, 'r', encoding='utf-8'), content_type='application/xml')


class CDDLogin(LoginView):
    template_name = 'main/login.html'


@login_required
def profile(request):
    return render(request, 'main/profile.html')


class CDDLogout(LogoutView, LoginRequiredMixin):
    template_name = 'main/logout.html'

# TODO: потом вернемся, при работе с пользователями
# class RegisterUserView(CreateView):
#     model = RegUser
#     template_name = 'main/register_user.html'
#     form_class = RegisterUserForm
#     success_url = reverse_lazy('main:register_done')


class RegisterDoneView(TemplateView):
    template_name = 'main/'


# Загрузка файлов ГТД в формате .xml
# TODO: далекое будущее - многопользовательские коллизии - нужно проверять по полю кто последний трогал документ, если не ты, то предупреждаем
# TODO: далекое будущее - статус черновик/проведен

@login_required(login_url='/accounts/login/')
def upload_gtd(request):
    if request.method == 'POST':
        form = UploadGtdfilesForm(request.POST, request.FILES)
        if form.is_valid():
            on_duplicate = request.POST['on_duplicate']
            # TODO: (Позже) проверка качества контента
            # TODO: (Позже) Более подробно указывать возможные ошибки на страницах ошибки

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
                add_exporter, exp_created = Exporter.objects.update_or_create(
                    name=exporter_info["name"],
                    postal_code=exporter_info["postal_code"],
                    country=Country.objects.get(code=exporter_info["country"]),
                    city=exporter_info["city"],
                    street_house=exporter_info['street_house'],
                    house=exporter_info["house"],
                    region=exporter_info['region']
                )

                # Обновим справочник импортеров
                importer_info = get_gtdmain["importer"]
                add_importer, imp_created = Importer.objects.update_or_create(
                    name=importer_info["name"],
                    inn=importer_info["inn"],
                    ogrn=importer_info["orgn"],
                )
                if imp_created:
                    add_importer.country=Country.objects.get(code=importer_info["country"])
                    add_importer.kpp=importer_info["kpp"]
                    add_importer.postal_code=importer_info["postal_code"]
                    add_importer.city=importer_info["city"]
                    add_importer.street_house=importer_info["street_house"]
                    add_importer.house=importer_info["house"]
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
                    add_tnved, tnved_created = TnVed.objects.update_or_create(
                        code=group["tn_ved"]
                    )
                    if tnved_created:
                        add_tnved.subposition = get_tnved_name(str(group["tn_ved"]))
                        add_tnved.save()

                    add_gtdgroup, gtdgroup_created = GtdGroup.objects.update_or_create(
                        gtd=add_gtdmain,
                        name=group['name'],
                        description=group['desc'],
                        tn_ved=add_tnved,
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
                        add_good, good_created = Good.objects.update_or_create(
                            marking=good_itself['marking'],
                            name=good_itself['name'],
                            trademark=add_trademark,
                            goodsmark=add_goodsmark
                        )

                        # Обновляем справочник производителей (заводов)
                        try_manufacturer = gtd_good['manufacturer']
                        if try_manufacturer:
                            add_manufacturer, manufacturer_created = Manufacturer.objects.update_or_create(
                                manufacturer=gtd_good['manufacturer']
                            )
                        else:
                            add_manufacturer = None

                        # Добавляем Товар ГТД
                        add_gtdgood, gtdgood_created = GtdGood.objects.update_or_create(
                            gtd=add_gtdmain,
                            group=add_gtdgroup,
                            good_num=gtd_good['good_num'],
                        )
                        if gtdgood_created:
                            add_gtdgood.good = add_good
                            add_gtdgood.quantity = gtd_good['quantity']
                            add_gtdgood.qualifier = MeasureQualifier.objects.get(digital_code=gtd_good['qualifier_code'])
                            add_gtdgood.manufacturer = add_manufacturer
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
            }
            return render(request, 'main/upload_gtd_log.html', context)
        # else:
        #     return render(request, 'main/error.html')

    else:
        # TODO: drag'n'drop
        form = UploadGtdfilesForm()
        context = {'form': form}
        return render(request, 'main/upload_gtd.html', context)

# TODO: Обработчик добавления и удаления юзеров
# TODO: Регистрация пользователей должна производиться только админом
# TODO: Контроллеры входа, сброса пароля, смены пароля
