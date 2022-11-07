from django import template


register = template.Library()


# Обращение по ключу-переменной к словарю в шаблоне
def another_dict(dictionary, value):
    return dictionary.get(value)


register.filter('another_dict', another_dict)


def has_role(user, role):
    """
    Определяет, есть ли у пользователя указанная роль
    """
    return user.role and user.role.name == role


register.filter('has_role', has_role)


def get_attr(instance, field):
    """
    Получение значения атрибута объекта по имени атрибута.
    В контексте - получение данных поля справочника по имени этого поля
    """
    return getattr(instance, field.name)


register.filter('get_attr', get_attr)


def cut_id(array):
    """
    Получение массива без первого элемента
    """
    return array[1:]


register.filter('cut_id', cut_id)
