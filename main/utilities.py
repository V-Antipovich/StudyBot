import datetime
from bs4 import BeautifulSoup as Bs
import requests
from django.core.signing import Signer
from django.template.loader import render_to_string
from customs_declarations_database.settings import ALLOWED_HOSTS

signer = Signer()


def send_activation_email(user, password):
    if ALLOWED_HOSTS:
        host = 'http://' + ALLOWED_HOSTS[0]
    else:
        host = 'http://localhost:8000'
    context = {'user': user, 'host': host, 'sign': signer.sign(user.username), 'password': password}
    subject = render_to_string('email/activation_letter_subject.txt', context)
    body_text = render_to_string('email/activation_letter_body.txt', context)
    user.email_user(subject, body_text)


# Парсинг xml-файла ГТД
def parse_gtd(filename):
    """
    Чтение xml-файла, формирование словаря, в котором будет содержаться шапка, группы, товары, документы

    """
    f = open(filename, 'r', encoding='utf-8')
    content = f.read()
    f.close()
    raw_gtd = Bs(content, "xml")
    gtd_groups = []

    # В таблицу ГТД (1 на весь документ)
    # Номер гтд
    locate_gtd_id = content.find("<!--ND=")
    gtd_id = content[locate_gtd_id+7:locate_gtd_id+30]

    # Код таможенного органа (не id)
    customs_house = gtd_id[:8]

    # Дата
    date = gtd_id[9:15]
    date = datetime.date(int('20' + date[4:]), int(date[2:4]), int(date[:2]))

    # таможенный номер гтд
    gtd_number = gtd_id[16:]

    # Порядковый номер гтд
    order_num = gtd_id[9:15]

    # Всего товаров
    total_goods_number = raw_gtd.find('TotalGoodsNumber').text #catESAD_cu: TotalGoodsNumber

    # Экспортер
    raw_exporter = raw_gtd.find('ESADout_CUConsignor')
    exporter = raw_exporter.find('OrganizationName').text #.replace(/(\.)([A-ZА-Я])/g, '$1 $2')    # cat_ru: OrganizationName
    for i in range(len(exporter)-1):
        if exporter[i] == '.' and exporter[i+1].isalpha():
            exporter = exporter[:i+1] + ' ' + exporter[i+1:]

    exporter_postal_code = raw_exporter.find('PostalCode')
    if exporter_postal_code:
        exporter_postal_code = exporter_postal_code.text
    exporter_country_code = raw_exporter.find('CountryCode').text
    exporter_country = raw_exporter.find('CounryName').text
    exporter_city = raw_exporter.find('City').text
    exporter_region = raw_exporter.find('Region')
    if exporter_region:
        exporter_region = exporter_region.text
    exporter_street = raw_exporter.find('StreetHouse').text
    exporter_house = raw_exporter.find('House')
    if exporter_house:
        exporter_house = exporter_house.text

    # Импортер
    raw_importer = raw_gtd.find('ESADout_CUDeclarant')
    importer = raw_importer.find("cat_ru:OrganizationName").text
    importer_orgn = raw_importer.find('OGRN').text
    importer_inn = raw_importer.find("INN").text
    importer_kpp = raw_importer.find('KPP').text
    importer_postal_code = raw_importer.find('PostalCode').text
    importer_country = raw_importer.find('CounryName').text
    importer_country_code = raw_importer.find('CountryCode').text
    importer_city = raw_importer.find('City').text
    importer_street = raw_importer.find('StreetHouse')
    if importer_street:
        importer_street = importer_street.text
    importer_house = raw_importer.find('House')
    if importer_house:
        importer_house = importer_house.text
    # Торгующая страна
    raw_contract_terms = raw_gtd.find('ESADout_CUMainContractTerms')
    trading_country = raw_contract_terms.find("TradeCountryCode").text

    # Общая стоимость
    total_cost = raw_gtd.find('TotalCustCost').text

    # Валюта
    currency = raw_contract_terms.find('ContractCurrencyCode').text

    # Общая стоимость по счету
    total_invoice_amount = raw_contract_terms.find('TotalInvoiceAmount').text

    # Курс валюты
    currency_rate = raw_contract_terms.find('ContractCurrencyRate').text

    # Характер сделки
    deal_type_code = raw_contract_terms.find('DealNatureCode').text

    exporter_all = {
        "name": exporter,
        "postal_code": exporter_postal_code,
        "country": exporter_country_code,
        "city": exporter_city,
        "street_house": exporter_street,
        "house": exporter_house,
        "region": exporter_region,
    }

    importer_all = {
        "name": importer,
        "postal_code": importer_postal_code,
        "country": importer_country_code,
        "city": importer_city,
        "street_house": importer_street,
        "house": importer_house,
        "inn": importer_inn,
        "orgn": importer_orgn,
        "kpp": importer_kpp,
    }

    gtd_main = {
        'gtdId': gtd_id,
        'customs_house': customs_house,
        'date': date,
        'order_num': order_num,
        'total_goods_number': total_goods_number,
        'exporter': exporter_all,
        'importer': importer_all,
        'trading_country': trading_country,
        'total_cost': total_cost,
        'currency': currency,
        'total_invoice_amount': total_invoice_amount,
        'currency_rate': currency_rate,
        'deal_type': deal_type_code,
    }

    # В таблицу с группами товаров (несколько на весь документ) + СОПРОВОДИТЕЛЬНЫЕ ДОКУМЕНТЫ
    raw_groups = raw_gtd.find_all("ESADout_CUGoods")
    for raw_group in raw_groups:
        # Номер товарной группы
        group_number = raw_group.find("GoodsNumeric").text
        name_n_desc = raw_group.find_all('GoodsDescription')
        # group_name = name_n_desc[0].text
        group_name = ''.join([block.text for block in name_n_desc[:2]])
        # group_description = name_n_desc[1].text
        # Подсубпозиция товара (код ТН ВЭД)
        TN_VED = str(int(raw_group.find('GoodsTNVEDCode').text))

        # Масса брутто
        gross_weight = raw_group.find('GrossWeightQuantity').text

        # Масса нетто
        attempt = raw_group.find('NetWeightQuantity2')
        if attempt:
            net_weight = attempt.text
        else:
            net_weight = raw_group.find('NetWeightQuantity').text

        # Страна происхождения
        origin_country = raw_group.find('OriginCountryCode').text

        # Код заявляемой таможенной процедуры
        main_type_code = raw_group.find('MainCustomsModeCode').text

        # Код предыдущей таможенной процедуры
        prev_type_code = raw_group.find('PrecedingCustomsModeCode').text

        # Особенность таможенной процедуры
        transfer_feature_code = raw_group.find('GoodsTransferFeature').text

        # Таможенная стоимость (база для начисления пошлин)
        customs_cost = raw_group.find('CustomsCost').text

        # Пошлина и НДС
        ndc_percent, ndc, fee_percent, fee = 0, 0, 0, 0
        taxes = raw_group.find_all('ESADout_CUCustomsPaymentCalculation')
        for tax in taxes:
            tax_type = tax.find('PaymentModeCode').text
            if tax_type == '1010':
                continue
            elif tax_type == '5010':
                ndc += float(tax.find('PaymentAmount').text)
                ndc_percent += float(tax.find('Rate').text)
            elif tax_type == '2010':
                fee += float(tax.find('PaymentAmount').text)
                fee_percent += float(tax.find('Rate').text)

        # Сопроводительные документы
        gtd_documents = []
        raw_docs = raw_group.find_all('ESADout_CUPresentedDocument')
        for raw_doc in raw_docs:
            # Название документа
            doc_name = raw_doc.find('PrDocumentName')
            if doc_name:
                doc_name = doc_name.text
            else:
                doc_name = 'Документ не предоставлен'

            # Тип документа
            doc_type = int(raw_doc.find('PresentedDocumentModeCode').text)

            # Номер документа
            doc_number = raw_doc.find('PrDocumentNumber')
            if doc_number:
                doc_number = doc_number.text

            # Номер признака представления
            present_code_num = raw_doc.find('DocPresentKindCode').text

            # Дата
            doc_date = raw_doc.find('PrDocumentDate')
            if doc_date:
                doc_date = doc_date.text
            else:
                doc_date = None

            # Дата начала действия
            attempt = raw_doc.find('DocumentBeginActionsDate')
            if attempt:
                doc_begin_date = attempt.text
            else:
                doc_begin_date = None

            # Дата окончания действия
            attempt = raw_doc.find('DocumentEndActionsDate')
            if attempt:
                doc_expire_date = attempt.text
            else:
                doc_expire_date = None
            gtd_document = {
                    'name': doc_name,
                    'number': doc_number,
                    'doc_type': doc_type,
                    'date': doc_date,
                    'begin_date': doc_begin_date,
                    'expire_date': doc_expire_date,
            }
            gtd_documents.append(gtd_document)

        # Товары в ГТД (в цикле)
        gtd_goods = []
        raw_goods = raw_group.find_all('GoodsGroupDescription')
        for raw_good in raw_goods:
            # Название товара
            good_name = raw_good.find('GoodsDescription').text
            if len(good_name) < 10:
                good_name = group_name

            while not good_name[0].isalpha():
                good_name = good_name[1:]

            raw_good_infos = raw_good.find_all('GoodsGroupInformation')
            # Номер товара в группе
            good_group_num = raw_good.find('GroupNum').text
            for raw_good_info in raw_good_infos:
                # Ариткул
                attempt = raw_good_info.find('GoodsMarking')
                if attempt:
                    good_marking = attempt.text
                else:
                    good_marking = raw_good_info.find('GoodsModel')
                    if good_marking:
                        good_marking = good_marking.text
                # Торговый знак
                trade_mark = raw_good_info.find('TradeMark')
                if trade_mark:
                    trade_mark = trade_mark.text
                # Торговая марка
                good_mark = raw_good_info.find('GoodsMark')
                if good_mark:
                    good_mark = good_mark.text
                # Производитель
                manufacturer = raw_good_info.find("Manufacturer")
                if manufacturer:
                    manufacturer = manufacturer.text
                raw_quantity = raw_good_info.find('GoodsGroupQuantity')
                if raw_quantity:
                    quantity = raw_quantity.find('GoodsQuantity')
                    if quantity:
                        quantity = quantity.text
                    qualifier_code = raw_quantity.find('MeasureUnitQualifierCode')
                    if qualifier_code:
                        qualifier_code = qualifier_code.text
                else:
                    quantity = None
                    qualifier_code = None
                gtd_good = {
                    'good': {
                        'marking': good_marking,
                        'name': good_name,
                        'trademark': trade_mark,
                        'brand': good_mark,
                    },
                    'good_num': good_group_num,
                    'quantity': quantity,
                    'qualifier_code': qualifier_code,
                    'manufacturer': manufacturer,
                }
                gtd_goods.append(gtd_good)

        gtd_group = {
            'name': group_name,
            # 'desc': group_description,
            'tn_ved': TN_VED,
            'number': group_number,
            'gross_weight': gross_weight,
            'net_weight': net_weight,
            'country': origin_country,
            'procedure': main_type_code,
            'prev_procedure': prev_type_code,
            'customs_cost': customs_cost,
            'fee': fee,
            'ndc': ndc,
            'fee_percent': fee_percent,
            'ndc_percent': ndc_percent,
            'documents': gtd_documents,
            'goods': gtd_goods,
        }
        gtd_groups.append(gtd_group)
    # print(gtd_main, gtd_groups, sep='\n')
    return gtd_main, gtd_groups


# Если оказалось, что нужного кода ТН ВЭД нет в базе, он парсится
def get_tnved_name(code):
    url = 'https://www.tks.ru/db/tnved/search?searchstr=' + code
    response = requests.get(url)
    soup = Bs(response.text, 'html.parser')
    name = soup.find('ul', {'class': 'tnved'})
    # TODO:
    if name:
        final_name = name.find('li').text[len(code)+5:]
    else:
        url = 'https://www.tks.ru/db/tnved/search?searchstr=' + '0' + code
        response = requests.get(url)
        soup = Bs(response.text, 'html.parser')
        final_name = soup.find('ul', {'class': 'tnved'}).find('li').text[len(code)+6:]
    return final_name
