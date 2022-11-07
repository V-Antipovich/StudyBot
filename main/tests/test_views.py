# Правильный ли выдаст массив из ГТД при запросе в общий список
# Правильные ли данные после парсинга какой-то xml-ки
# Заслать файл другого расширения в файл
from django.contrib.auth import get_user_model, authenticate
from django.test import TestCase, Client
from customs_declarations_database.settings import ALLOWED_HOSTS
from main.models import RegUser
from django.urls import reverse_lazy, reverse
from main.templates import main


class EnterTest(TestCase):
    def setUp(self):
        RegUser.objects.create(
            username='test_admin', is_active=True, first_name='a', last_name='b',
            password='pbkdf2_sha256$390000$ShRQGwb7i56qZgZCT5XiC2$ppAYRg0JNt4m/b/+eBxFra2Golun6CvAq5R9sYpI3fU=',
        )
        self.login_url = reverse('main:login')
        self.c = Client()


    def test_get_login_page(self):
        resp = self.c.get('', follow=True)
        self.assertEqual(resp.status_code, 200)
        # print(self.client)
        print(resp.context)
        # print(type(resp_post))
        # print(resp_post.content)
        # self.assertContains(resp_post, 'log')
        # resp_wrong = self.c.post(self.login_url, {'username': 'sfsdf', 'password': 'dszjfnsdjkf'})
        # print(resp_wrong.method)
        # self.assertRedirects()
        # self.assertTemplateUsed(resp_post, 'main/login.html')

#
# class UploadGtdTest(TestCase):
#     def setUp(self) -> None:
#         self.c = Client()
#
#     def test_start_page(self):
#         """
#         Проверка входа на начальную страницу
#         под незарегистрированным пользователем
#         """
#         response = self.c.get('/')
#         self.assertEqual(response.status_code, 302)
#         self.assertEqual(response.url, '/accounts/login/?next=/')
        # print(response)
        # self.assertNotEqual('/', response.url)
    # def test_login(self):


# class AuthTest(TestCase):
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         RegUser.objects.create(
#             username='test_admin',
#             is_active=True,
#             password='pbkdf2_sha256$390000$ShRQGwb7i56qZgZCT5XiC2$ppAYRg0JNt4m/b/+eBxFra2Golun6CvAq5R9sYpI3fU=',
#             first_name='a',
#             last_name='b',
#         )
#
#     def setUp(self):
#         self.c = Client()
#     # def test_login(self):
#
#     def test_login(self):
#         resp = self.c.post('/accounts/login/', {'username': 'test_admin', 'password': 'admin'})
#         print(resp)
