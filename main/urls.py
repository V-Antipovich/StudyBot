from django.urls import path
from .views import index, upload_gtd, ShowGtdView, show_gtd_file, CDDLogin, CDDLogout, handbook,\
    GtdDetailView, update_gtd, GtdDeleteView, RegisterUserView, profile, update_gtd_good, update_gtd_group,\
    eco_fee, eco_fee_xlsx, to_wms, AccessDeniedView, to_erp, SuccessfulOutcome, StatisticsMenu,\
    statistics_report_gtd_per_exporter, gtd_per_exporter_xlsx, statistics_report_goods_imported,\
    report_goods_imported_xlsx


app_name = 'main'
urlpatterns = [
    path('handbook', handbook, name='handbook'),
   # path('register_user/done/', RegisterDoneView.as_view(), name='register_done'),
   # path('register_user/', RegisterUserView.as_view(), name='register'),
    path('accounts/profile/', profile, name='profile'),
    path('accounts/register', RegisterUserView.as_view(), name='register'),
    path('accounts/login/', CDDLogin.as_view(), name='login'),
    path('accounts/logout/', CDDLogout.as_view(), name='logout'),
    # path('eco_fee/xlsx/<path:filename>', show_eco, name='eco_xlsx'),
    path('statistics/goods_imported/<path:filename>', report_goods_imported_xlsx, name='report_goods_imported_file'),
    path('statistics/goods_imported', statistics_report_goods_imported, name='report_goods_imported'),
    path('statistics/gtd_per_exporter/<path:filename>', gtd_per_exporter_xlsx, name='gtd_per_exporter_file'),
    path('statistics/gtd_per_exporter', statistics_report_gtd_per_exporter, name='statistics_gtd_per_exporter'),
    path('statistics/menu', StatisticsMenu.as_view(), name='statistics_menu'),
    path('eco_fee/file/<path:filename>', eco_fee_xlsx, name='eco_fee_file'),
    path('eco_fee', eco_fee, name='eco_fee'),
    path('documents/update_gtd_group/<int:pk>', update_gtd_group, name='update_gtd_group'),
    path('documents/update_gtd_good/<int:pk>', update_gtd_good, name='update_gtd_good'),
    path('documents/update_gtd/<int:pk>', update_gtd, name='update_gtd'),
    path('documents/delete_gtd/<int:pk>', GtdDeleteView.as_view(), name='delete_gtd'),
    path('documents/show_gtd/file/<path:filename>', show_gtd_file, name='show_gtd_file'),
    path('success_gtd<int:pk>', SuccessfulOutcome.as_view(), name='success'),
    path('erp/<int:pk>', to_erp, name='to_erp'),
    path('wms/<int:pk>', to_wms, name='to_wms'),
    path('documents/show_gtd/<int:pk>', GtdDetailView.as_view(), name='per_gtd'),
    path('documents/show_gtd', ShowGtdView.as_view(), name='show_gtd'),
    path('documents/upload_gtd', upload_gtd, name='upload_gtd'),
    path('access_denied', AccessDeniedView.as_view(), name='access_denied'),
    path('', index, name='index')
]
