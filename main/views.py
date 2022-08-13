from django.shortcuts import render, redirect
from django.core.exceptions import ObjectDoesNotExist
from .forms import UploadGtdForm
from .models import GtdMain, GtdGroup, GtdGood, UploadGtd, CustomsHouse, Exporter, Country, Currency, Importer, DealType
from django.conf import settings
import os
import re
from .utilities import parse_gtd


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
    gtd_files = UploadGtd.objects.all()
    context = {'gtd_files': gtd_files}
    # TODO: Выводить из модели GtdMain
    return render(request, 'main/show_gtd.html', context)  # Заглушка: вывод не тех данных


def upload_gtd(request):
    if request.method == 'POST':
        form = UploadGtdForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            last_one = UploadGtd.objects.last()
            last_file = last_one.document
            path = os.path.join(settings.MEDIA_ROOT, str(last_file))
            # Получили словарь с распарсенной гтд
            get_gtdmain = parse_gtd(path)

            # Работа с GtdMain - основная инфа в шапке ГТД
            # Обновим справочник экспортеров если требуется
            #  TODO: вероятно, придется фиксить повторяющихся экспортеров (путаница с городами, странами и регионами)
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

            # Обновим справочник импортеров если требуется
            importer_info = get_gtdmain["importer"]
            add_importer, imp_created = Importer.objects.get_or_create(
                name=importer_info["name"],
                postal_code=importer_info["postal_code"],
                country=Country.objects.get(code=importer_info["country"]),
                city=importer_info["city"],
                street_house=importer_info["street_house"],
                house=importer_info["house"],
                inn=importer_info["inn"],
                ogrn=importer_info["orgn"],
                kpp=importer_info["kpp"]
            )

            # Теперь добавляем главную инфу гтд, если номера документа еще нет в базе.
            if not GtdMain.objects.filter(gtdId=get_gtdmain["gtdId"]).exists():
                add_gtdmain = GtdMain(
                    gtdId=get_gtdmain["gtdId"],
                    customs_house=CustomsHouse.objects.get(house_num=get_gtdmain["customs_house"]),
                    date=get_gtdmain["date"],
                    order_num=get_gtdmain["order_num"],
                    total_goods_number=get_gtdmain["total_goods_number"],
                    exporter=Exporter.objects.get(name=exporter_info["name"]),
                    importer=Importer.objects.get(name=importer_info["name"]),
                    trading_country=Country.objects.get(code=get_gtdmain["trading_country"]),
                    total_cost=get_gtdmain["total_cost"],
                    currency=Currency.objects.get(short_name=get_gtdmain["currency"]),
                    total_invoice_amount=get_gtdmain["total_invoice_amount"],
                    currency_rate=get_gtdmain["currency_rate"],
                    deal_type=DealType.objects.get(code=get_gtdmain["deal_type"]),
                    gtd_file=last_one
                )
                add_gtdmain.save()
            context = {
                "one": request.POST,
                "two": request.POST,
                "three": last_one,
                'path': path,
                'export': add_exporter,
                #'gtd': add_gtdmain
            }
            return render(request, 'main/test.html', context)  # TODO: Заглушка, потребуется переадресация на другую страницу
    else:
        form = UploadGtdForm()
    context = {'form': form}
    return render(request, 'main/upload_gtd.html', context)
