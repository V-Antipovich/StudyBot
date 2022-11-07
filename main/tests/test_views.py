from django.contrib.auth import get_user_model
from django.test import TestCase, Client, RequestFactory
from main.models import RegUser, Currency, CustomsHouse, Exporter, Importer, Country, GtdMain, DealType
from django.urls import reverse
from main.views import CDDLogin
import datetime


class LoginViewTest(TestCase):
    """
    Тест страницы входа
    """
    def setUp(self) -> None:
        """
        Входные данные - пользователь и фабрика запросов
        """
        self.user = get_user_model().objects.create(
            username='test',
            password='pbkdf2_sha256$390000$ShRQGwb7i56qZgZCT5XiC2$ppAYRg0JNt4m/b/+eBxFra2Golun6CvAq5R9sYpI3fU=',
            is_active=True,
        )
        self.user.save()
        self.factory = RequestFactory()
        self.c = Client()

    def test_login_get_code(self):
        """
        Тест на правильный код ответа
        """
        request = self.factory.get(reverse('main:login'))
        resp = CDDLogin.as_view()(request)
        self.assertEqual(resp.status_code, 200)

    def test_login_post(self):
        """
        Тест на наличие перенаправления после отправки формы
        """
        resp = self.c.post(reverse('main:login'), {'username': 'test', 'password': 'admin'})
        self.assertEqual(resp.status_code, 302)


class ShowGtdListViewTest(TestCase):
    """
    Тестируем работоспособность страницы списка ГТД
    """
    def setUp(self) -> None:
        """
        Заносим в базу эксземпляры некоторых моделей для формирования ГТД
        """
        Currency.objects.create(name='Доллар США', digital_code=840, short_name='USD')
        CustomsHouse.objects.create(house_num='10101020', house_name='т/п Валуйский')
        DealType.objects.create(deal_type='Перемещение товаров на возмездной основе по договору купли-продажи товаров',
                                code='010')
        Country.objects.create(code='RW', russian_name='Руанда', english_name='Rwanda')
        Country.objects.create(code='RU', russian_name='Россия', english_name='Russia')
        Country.objects.create(code='US', russian_name='США', english_name='USA')
        Importer.objects.create(name='ООО "Боже мой"', postal_code='123454321',
                                country=Country.objects.filter(russian_name='Руанда')[0], inn='34820324',
                                ogrn='328495823432')
        Exporter.objects.create(name='Tesla', postal_code='92334284', city='California', street_house='5th Avenue, 45',
                                country=Country.objects.filter(russian_name='США')[0])
        Exporter.objects.create(name='ЭЭЭ "Наше место"', postal_code='32424234', city='jsnfksdfa', street_house='aerfarf',
                                country=Country.objects.filter(russian_name='США')[0])
        Exporter.objects.create(name='ААА "Паук на руке"', postal_code='32424234', city='jsnfksdfa',
                                street_house='aerfarf',
                                country=Country.objects.filter(russian_name='США')[0])
        GtdMain.objects.create(gtdId='11111111/111121/1111111',
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
        GtdMain.objects.create(
            gtdId='22222222/131121/2222222',
            date=datetime.datetime(2011, 11, 13),
            order_num='2222222',
            total_goods_number=2,
            exporter=Exporter.objects.get(name='ЭЭЭ "Наше место"'),
            importer=Importer.objects.get(name='ООО "Боже мой"'),
            trading_country=Country.objects.get(russian_name='США'),
            total_cost=324329424234,
            currency=Currency.objects.get(short_name='USD'),
            total_invoice_amount=23482395,
            currency_rate=59.432,
            deal_type=DealType.objects.get(code='010')
        )
        GtdMain.objects.create(
            gtdId='33333333/151121/3333333',
            date=datetime.datetime(2011, 11, 15),
            order_num='3333333',
            total_goods_number=2,
            exporter=Exporter.objects.get(name='ААА "Паук на руке"'),
            importer=Importer.objects.get(name='ООО "Боже мой"'),
            trading_country=Country.objects.get(russian_name='США'),
            total_cost=57547623423,
            currency=Currency.objects.get(short_name='USD'),
            total_invoice_amount=2139092183,
            currency_rate=34.432,
            deal_type=DealType.objects.get(code='010')
        )
        GtdMain.objects.create(
            gtdId='44444444/151121/4444444',
            date=datetime.datetime(2011, 11, 15),
            order_num='3333333',
            total_goods_number=2,
            exporter=Exporter.objects.get(name='ААА "Паук на руке"'),
            importer=Importer.objects.get(name='ООО "Боже мой"'),
            trading_country=Country.objects.get(russian_name='США'),
            total_cost=57547623423,
            currency=Currency.objects.get(short_name='USD'),
            total_invoice_amount=2139092183,
            currency_rate=34.432,
            deal_type=DealType.objects.get(code='010')
        )
        GtdMain.objects.create(
            gtdId='55555555/151121/5555555',
            date=datetime.datetime(2011, 11, 16),
            order_num='3333333',
            total_goods_number=2,
            exporter=Exporter.objects.get(name='ААА "Паук на руке"'),
            importer=Importer.objects.get(name='ООО "Боже мой"'),
            trading_country=Country.objects.get(russian_name='США'),
            total_cost=57547623423,
            currency=Currency.objects.get(short_name='USD'),
            total_invoice_amount=2139092183,
            currency_rate=34.432,
            deal_type=DealType.objects.get(code='010')
        )
        GtdMain.objects.create(
            gtdId='66666666/161121/6666666',
            date=datetime.datetime(2011, 11, 9),
            order_num='3333333',
            total_goods_number=2,
            exporter=Exporter.objects.get(name='ААА "Паук на руке"'),
            importer=Importer.objects.get(name='ООО "Боже мой"'),
            trading_country=Country.objects.get(russian_name='США'),
            total_cost=34489243,
            currency=Currency.objects.get(short_name='USD'),
            total_invoice_amount=2139092183,
            currency_rate=34.432,
            deal_type=DealType.objects.get(code='010')
        )
        RegUser.objects.create(
            username='test',
            password='pbkdf2_sha256$390000$ShRQGwb7i56qZgZCT5XiC2$ppAYRg0JNt4m/b/+eBxFra2Golun6CvAq5R9sYpI3fU=',
            is_active=True,
        )
        self.c = Client()
        self.factory = RequestFactory()
        self.c.login(username='test', password='admin')
        self.user = RegUser.objects.last()

    def test_unaithorized_user(self):
        """
        Проверка перенаправления на страницу регистрации при
        заходе как неавторизованный пользователь
        """
        self.c.logout()
        response = self.c.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/accounts/login/?next=/')

    def test_get_start_page_with_login(self):
        """
        Тест захода на страницу как авторизованный пользователь
        """

        response = self.c.get('/')
        self.assertEqual(response.status_code, 200)

    def test_accessing_full_gtd_list(self):
        """
        Проверка получения всех ГТД при отсутствии фильтров
        """
        response = self.c.get('/')
        gtds = response.context['gtds']
        self.assertEqual(len([gtd for gtd in gtds]), 6)

    def test_filter_by_kw(self):
        """
        Тест количества ГТД на странице после применения фильтрации
        """
        response = self.c.get('/?paginate_by=10&key=АА&start_date=&end_date=')
        gtds = response.context['gtds']
        self.assertEqual(len([gtd for gtd in gtds]), 4)

    def test_filter_by_time(self):
        """
        Тест количества ГТД, заключенных в заданный временной диапазон
        """

        response = self.c.get('/?paginate_by=10&key=&start_date=11-11-2011&end_date=15-11-2011')
        gtds = response.context['gtds']
        self.assertEqual(len([(gtd, gtd.date) for gtd in gtds]), 4)
