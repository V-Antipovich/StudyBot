from django.urls import path, re_path
from .views import index, upload_gtd, ShowGtdView, test_view


app_name = 'main'
urlpatterns = [
    path('documents/show_gtd', ShowGtdView.as_view(), name='show_gtd'),
    #  path('documents/upload_gtd/success', test_view, name='test'),
    path('documents/upload_gtd', upload_gtd, name='upload_gtd'),
    path('test', test_view, name='test'),
    path('', index, name='index')
]
