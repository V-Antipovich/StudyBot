from django import template


register = template.Library()


# Обращение по ключу-переменной к словарю в шаблоне
def another_dict(dictionary, value):
    return dictionary.get(value)


register.filter('another_dict', another_dict)


def has_role(user, role):
    return user.role and user.role.name == role


register.filter('has_role', has_role)


def get_attr(instance, field):
    return getattr(instance, field.name)


register.filter('get_attr', get_attr)


def cut_id(array):
    return array[1:]


register.filter('cut_id', cut_id)


def mid(a, b):
    return int((a+b)/2)


register.filter('mid', mid)
