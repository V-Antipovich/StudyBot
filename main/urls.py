from django.urls import path
from .views import index, upload_gtd, ShowGtdView, test_view, ShowGtdGroups, show_gtd_file, ShowGtdGoodsInGroup, ShowGtdDocumentsInGroup


app_name = 'main'
urlpatterns = [
    path('documents/show_gtd/docs/<int:gtd>/<int:group_pk>', ShowGtdDocumentsInGroup.as_view(), name='documents_per_group'),
    path('documents/show_gtd/goods/<int:gtd>/<int:group_pk>', ShowGtdGoodsInGroup.as_view(), name='goods_per_group'),
    path('documents/show_gtd/file/<path:filename>', show_gtd_file, name='show_gtd_file'),
    path('documents/show_gtd/groups/<int:pk>', ShowGtdGroups.as_view(), name='groups_per_gtd'),
    path('documents/show_gtd', ShowGtdView.as_view(), name='show_gtd'),
    path('documents/upload_gtd', upload_gtd, name='upload_gtd'),
    path('test', test_view, name='test'),
    path('', index, name='index')
]
