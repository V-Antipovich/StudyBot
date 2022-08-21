from django.urls import path, re_path
from .views import index, upload_gtd, show_gtd


app_name = 'main'
urlpatterns = [
    path('documents/show_gtd', show_gtd, name='show_gtd'),
    #  path('documents/upload_gtd/success', test_view, name='test'),
    path('documents/upload_gtd', upload_gtd, name='upload_gtd'),
    # path('documents', documents, name='documents'),
    # path('test/files',  )
    # path('test', test_multiple_files, name='test_view'),
    path('', index, name='index')
]
