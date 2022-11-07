from django.contrib.auth import authenticate
from django.test import TestCase
from main.models import GtdMain, GtdGroup, Currency, CustomsHouse, DealType, Exporter, Importer, Country, TnVed, \
    Procedure, RegUser
import datetime


class GtdMainModelTest(TestCase):
    """
    Тестирование работы с моделью ГТД
    """
    @classmethod
    def setUpTestData(cls):
        Currency.objects.create(name='Доллар США', digital_code=840, short_name='USD')
        CustomsHouse.objects.create(house_num='10101020', house_name='т/п Валуйский')
        DealType.objects.create(deal_type='Перемещение товаров на возмездной основе по договору купли-продажи товаров',code='010')
        Country.objects.create(code='RW', russian_name='Руанда', english_name='Rwanda')
        Country.objects.create(code='RU', russian_name='Россия', english_name='Russia')
        Country.objects.create(code='US', russian_name='США', english_name='USA')
        Importer.objects.create(name='ООО "Боже мой"', postal_code='123454321', country=Country.objects.filter(russian_name='Руанда')[0], inn='34820324', ogrn='328495823432')
        Exporter.objects.create(name='Tesla', postal_code='92334284', city='California', street_house='5th Avenue, 45',country=Country.objects.filter(russian_name='США')[0])
        GtdMain.objects.create(
            gtdId='11111111/111121/1111111',
            date=datetime.datetime(2011, 11, 11),
            order_num='1111111',
            total_goods_number=2,
            exporter=Exporter.objects.get(name='Tesla'),
            importer=Importer.objects.get(name='ООО "Боже мой"'),
            trading_country=Country.objects.get(russian_name='США'),
            total_cost=2131334243,
            currency=Currency.objects.get(short_name='USD'),
            total_invoice_amount=32432421,
            currency_rate=34.432,
            deal_type=DealType.objects.get(code='010')
        )
        TnVed.objects.create(
            code='84566693',
            subposition='Бытовые приборы - Климатическое оборудование'
        )
        TnVed.objects.create(
            code='845666321',
            subposition='Бытовые приборы - Стиральные машины'
        )
        Procedure.objects.create(
            code='00',
            name='Отсутствие предшествующей таможенной процедуры'
        )
        Procedure.objects.create(
            code='10',
            name='Экспорт'
        )
        Procedure.objects.create(
            code='31',
            name='Реэкспорт'
        )

    def test_str_gtd(self):
        """
        Тест отображения объекта ГТД для пользователей
        """
        gtd = GtdMain.objects.last()
        self.assertEqual(f'{gtd}', gtd.gtdId)

    def test_recount(self):
        """
        Тест обновления информации в основном разделе ГТД
        """
        gtd = GtdMain.objects.last()
        GtdGroup.objects.create(
            gtd=gtd,
            name='Кондиционер сплит-система',
            tn_ved=TnVed.objects.get(code='84566693'),
            number=1,
            gross_weight=456,
            net_weight=432,
            country=Country.objects.get(russian_name='Россия'),
            procedure=Procedure.objects.get(code='10'),
            prev_procedure=Procedure.objects.get(code='00'),
            customs_cost=32432413,
            fee=324323,
            ndc=0,
            fee_percent=32,
            ndc_percent=0
        )

        GtdGroup.objects.create(
            gtd=gtd,
            name='Кондиционер сплит-система',
            tn_ved=TnVed.objects.get(code='84566693'),
            number=2,
            gross_weight=892,
            net_weight=892,
            country=Country.objects.get(russian_name='США'),
            procedure=Procedure.objects.get(code='31'),
            prev_procedure=Procedure.objects.get(code='10'),
            customs_cost=392432434212,
            fee=9342,
            ndc=0,
            fee_percent=354,
            ndc_percent=0,
        )
        gtd.recount()
        self.assertEqual(gtd.total_cost, 392464866625)
        self.assertEqual(gtd.total_invoice_amount, 11398259369.917519)
        self.assertEqual(gtd.total_goods_number, 2)


class AuthTest(TestCase):
    """
    Тестирование авторизации с моделью пользователя
    """
    def setUp(self) -> None:
        """
        Входные тестовые данные - запись в таблице пользователей
        """
        RegUser.objects.create(
            username='test_admin', is_active=True, first_name='a', last_name='b',
            password='pbkdf2_sha256$390000$ShRQGwb7i56qZgZCT5XiC2$ppAYRg0JNt4m/b/+eBxFra2Golun6CvAq5R9sYpI3fU=',
        )

    def test_successful_auth(self):
        """
        Попытка аутентификации с правильными данными
        """
        user = authenticate(username='test_admin',
                            password='admin')
        self.assertTrue(user is not None and user.is_authenticated)

    def test_wrong_password(self):
        """
        Попытка аутентификации с неправильным паролем
        """
        user = authenticate(username='test-admin', password='admina')
        self.assertFalse(user is not None and user.is_authenticated)

    def test_wrong_username(self):
        """
        Попытка аутентификации с неправильным логином
        """
        user = authenticate(username='test', password='admin')
        self.assertFalse(user is not None and user.is_authenticated)