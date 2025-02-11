from django.urls import path
from .views import upload_gtd, show_gtd_file, CDDLogin, CDDLogout, GtdGoodDeleteView,\
    GtdDetailView, update_gtd, GtdDeleteView, Profile, handbook_xlsx, HandbookUpdateView,\
    eco_fee, to_wms, AccessDeniedView, to_erp, StatisticsMenu, GtdGroupDeleteView, users_list,\
    statistics_report_gtd_per_exporter, statistics_report_goods_imported, report_xlsx, ChangeUserInfoView,\
    RegUserPasswordChangeView, RegisterUserView, RegisterDoneView, user_activate, show_gtd_list, HandbookDeleteView,\
    GtdGroupUpdateView, GtdGoodUpdateView, GtdGoodCreateView, GtdGroupCreateView, HandbookListView, HandbookCreateView,\
    UserUpdateView, UserDeleteView, CDDPasswordResetView, CDDPasswordResetDoneView, CDDPasswordResetCompleteView,\
    CDDPasswordResetConfirmView


app_name = 'main'
urlpatterns = [
    path('handbook_xlsx/<path:filename>', handbook_xlsx, name='handbook_xlsx'),
    # path('handbook/<str:choice>', handbook, name='handbook'),
    path('handbook/<str:handbook>/delete/<int:pk>', HandbookDeleteView.as_view(), name='delete_handbook_entry'),
    path('handbook/<str:handbook>/create', HandbookCreateView.as_view(), name='create_handbook_entry'),
    path('handbook/<str:handbook>/update/<int:pk>', HandbookUpdateView.as_view(), name='update_handbook'),
    path('handbook/<str:handbook>/', HandbookListView.as_view(), name='handbook'),
    path('accounts/password/reset/done', CDDPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('accounts/password/reset/confirm/<uidb64>/<token>/', CDDPasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('accounts/password/reset/complete', CDDPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('accounts/password/reset/', CDDPasswordResetView.as_view(), name='password_reset'),
    path('accounts/register/activate/<str:sign>/', user_activate, name='register_activate'),
    path('accounts/register/done/', RegisterDoneView.as_view(), name='register_done'),
    path('accounts/register/', RegisterUserView.as_view(), name='register'),
    path('accounts/password/change', RegUserPasswordChangeView.as_view(), name='password_change'),
    path('accounts/profile/change', ChangeUserInfoView.as_view(), name='profile_change'),
    path('accounts/profile/', Profile.as_view(), name='profile'),
    path('accounts/login/', CDDLogin.as_view(), name='login'),
    path('accounts/logout/', CDDLogout.as_view(), name='logout'),
    path('statistics/goods_imported', statistics_report_goods_imported, name='report_goods_imported'),
    path('statistics/gtd_per_exporter', statistics_report_gtd_per_exporter, name='statistics_gtd_per_exporter'),
    path('statistics/menu', StatisticsMenu.as_view(), name='statistics_menu'),
    path('eco_fee', eco_fee, name='eco_fee'),
    path('report_xlsx/<path:folder>/<path:filename>', report_xlsx, name='report_xlsx'),
    path('documents/delete_gtd_good/<int:pk>', GtdGoodDeleteView.as_view(), name='delete_gtd_good'),
    path('documents/delete_gtd_group/<int:pk>', GtdGroupDeleteView.as_view(), name='delete_gtd_group'),
    path('documents/update_gtd_group/<int:pk>', GtdGroupUpdateView.as_view(), name='update_gtd_group'),
    path('documents/update_gtd_good/<int:pk>', GtdGoodUpdateView.as_view(), name='update_gtd_good'),
    path('documents/create_good/<int:pk>', GtdGoodCreateView.as_view(), name='create_gtd_good'),
    path('documents/create_gtd_group/<int:pk>', GtdGroupCreateView.as_view(), name='create_gtd_group'),
    path('documents/update_gtd/<int:pk>', update_gtd, name='update_gtd'),
    path('documents/delete_gtd/<int:pk>', GtdDeleteView.as_view(), name='delete_gtd'),
    path('documents/show_gtd/file/<path:filename>', show_gtd_file, name='show_gtd_file'),
    path('erp/<int:pk>', to_erp, name='to_erp'),
    path('wms/<int:pk>', to_wms, name='to_wms'),
    path('documents/show_gtd/<int:pk>', GtdDetailView.as_view(), name='per_gtd'),
    path('documents/upload_gtd', upload_gtd, name='upload_gtd'),
    path('access_denied', AccessDeniedView.as_view(), name='access_denied'),
    path('users/delete/<int:pk>', UserDeleteView.as_view(), name='user_delete'),
    path('users/update/<int:pk>', UserUpdateView.as_view(), name='user_update'),
    path('users', users_list, name='users'),
    path('', show_gtd_list, name='show_gtd'),
]
