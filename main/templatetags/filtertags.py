from django import template


register = template.Library()


# Обращение по ключу-переменной к словарю в шаблоне
def another_dict(dictionary, value):
    return dictionary.get(value)


register.filter('another_dict', another_dict)
