from django.shortcuts import render, redirect
from django.db import IntegrityError
from .forms import UploadGtdForm
from .models import GtdMain, GtdGroup, GtdGood, UploadGtd, CustomsHouse, Exporter, Country, Currency, Importer, DealType, Procedure, TnVed, Good, GoodsMark, GtdDocument, Document, TradeMark, Manufacturer, MeasureQualifier, DocumentType
from django.conf import settings
import os
from .utilities import parse_gtd, get_tnved_name


# Create your views here.


def test_view(request):
    return render(request, 'main/test.html')


def index(request):
    return render(request, 'main/index.html')


"""
def documents(request):
    return render(request, 'main/documents.html')
"""


# Сначала просто будем выводить все xml для скачивания, позже добавим другую инфу (как распарсим файлы)
def show_gtd(request):
    gtd_files = GtdMain.objects.all()
    context = {'gtd_files': gtd_files}
    # TODO: Выводить из модели GtdMain
    return render(request, 'main/show_gtd.html', context)  # Заглушка: вывод не тех данных


def upload_gtd(request):
        if request.method == 'POST':
            form = UploadGtdForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                last_one = UploadGtd.objects.last()  # TODO: это костыль, который надо убрать при добавлении ролей
                last_file = last_one.document
                path = os.path.join(settings.MEDIA_ROOT, str(last_file))
                # Получили словарь с распарсенной гтд
                get_gtdmain, get_gtdgroups = parse_gtd(path)

                # Работа с GtdMain - основная инфа в шапке ГТД

            # Обновим справочник экспортеров если требуется
                exporter_info = get_gtdmain["exporter"]
                add_exporter, exp_created = Exporter.objects.get_or_create(
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
                add_importer, imp_created = Importer.objects.get_or_create(
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
                """if not GtdMain.objects.filter(gtdId=get_gtdmain["gtdId"]).exists():
                    GtdMain = ()"""
                add_gtdmain, gtdmain_created = GtdMain.objects.get_or_create(
                    gtdId=get_gtdmain["gtdId"],
                    customs_house=CustomsHouse.objects.get(house_num=get_gtdmain["customs_house"]),
                    date=get_gtdmain["date"],
                    order_num=get_gtdmain["order_num"]
                )
                if gtdmain_created:
                    add_gtdmain.total_goods_number = get_gtdmain["total_goods_number"]
                    add_gtdmain.exporter = Exporter.objects.get(name=exporter_info['name'])
                    add_gtdmain.importer = Importer.objects.get(name=importer_info['name'])
                    add_gtdmain.trading_country = Country.objects.get(code=get_gtdmain["trading_country"])
                    add_gtdmain.total_cost = get_gtdmain["total_cost"]
                    add_gtdmain.currency = Currency.objects.get(short_name=get_gtdmain["currency"])
                    add_gtdmain.total_invoice_amount = get_gtdmain["total_invoice_amount"]
                    add_gtdmain.currency_rate = get_gtdmain["currency_rate"]
                    add_gtdmain.deal_type = DealType.objects.get(code=get_gtdmain["deal_type"])
                    add_gtdmain.gtd_file = last_one
                    add_gtdmain.save()

                # Теперь в цикле надо пройтись по группам ГТД.
                # gtd_id = GtdMain.objects.get(gtdId=get_gtdmain["gtdId"])
                for group in get_gtdgroups:
                    # Заносим группу, если такой ещё не было

                    # Проверяем ТН ВЭД
                    add_tnved, tnved_created = TnVed.objects.get_or_create(
                        code=group["tn_ved"]
                    )
                    if tnved_created:
                        add_tnved.subposition = get_tnved_name(str(group["tn_ved"]))
                        add_tnved.save()

                    add_gtdgroup, gtdgroup_created = GtdGroup.objects.get_or_create(
                        gtd=add_gtdmain,
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
                            add_trademark, trademark_created = TradeMark.objects.get_or_create(
                                trademark=try_trademark
                            )
                        else:
                            add_trademark = None

                        # Обновляем справочник торговых марок
                        try_goodsmark = good_itself['brand']
                        if try_goodsmark:
                            add_goodsmark, goodsmark_created = GoodsMark.objects.get_or_create(
                                goodsmark=try_goodsmark
                            )
                        else:
                            add_goodsmark = None

                        # Обновляем таблицу товаров
                        add_good, good_created = Good.objects.get_or_create(
                            marking=good_itself['marking'],
                            name=good_itself['name'],
                            trademark=add_trademark,
                            goodsmark=add_goodsmark
                        )

                        # Обновляем справочник производителей (заводов)
                        try_manufacturer = gtd_good['manufacturer']
                        if try_manufacturer:
                            add_manufacturer, manufacturer_created = Manufacturer.objects.get_or_create(
                                manufacturer=gtd_good['manufacturer']
                            )
                        else:
                            add_manufacturer = None

                        # Добавляем Товар ГТД
                        add_gtdgood, gtdgood_created = GtdGood.objects.get_or_create(
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
                        add_document, document_created = Document.objects.get_or_create(
                            name=gtd_document['name'],
                            doc_type=DocumentType.objects.get(code=gtd_document['doc_type']),
                            number=gtd_document['number'],
                            date=gtd_document['date'],
                            begin_date=gtd_document['begin_date'],
                            expire_date=gtd_document['expire_date']
                        )
                        add_gtddocument, gtddocument_created = GtdDocument.objects.get_or_create(
                            gtd=add_gtdmain,
                            group=add_gtdgroup,
                            document=add_document,
                        )
                context = {
                    # "one": request.POST,
                    # "two": request.POST,
                    # "three": last_one,
                    # 'path': path,
                    'main': add_gtdmain,
                    #  'get': add_gtdmain,
                    'exp': add_exporter  # Exporter.objects.get(name=exporter_info['name'])
                }
                return render(request, 'main/test.html',
                              context)  # TODO: Заглушка, потребуется переадресация на другую страницу

        else:
            form = UploadGtdForm()
            context = {'form': form}
            return render(request, 'main/upload_gtd.html', context)
