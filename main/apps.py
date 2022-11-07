from django.apps import AppConfig
from django.dispatch import Signal
from .utilities import send_activation_email


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'


user_registered = Signal(['instance'])


# Обработчик сигнала
def user_registered_dispatcher(sender, **kwargs):
    """
    Обработчик сигнала о регистрации пользователя,
    вызывающий функцию отправки письма
    """
    send_activation_email(kwargs['instance'], kwargs['password'])


user_registered.connect(user_registered_dispatcher)
