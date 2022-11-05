from django import template


register = template.Library()


# Обращение по ключу-переменной к словарю в шаблоне
def another_dict(dictionary, value):
    return dictionary.get(value)


register.filter('another_dict', another_dict)


def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


register.filter('has_group', has_group)


def get_attr(instance, field):
    return getattr(instance, field.name)


register.filter('get_attr', get_attr)


def cut_id(array):
    return array[1:]


register.filter('cut_id', cut_id)
