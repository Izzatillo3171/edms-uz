from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='user_profile'),
    path('profile/password/', views.change_password, name='change_password'),
    
    # Public pages
    path('status/', views.public_status_check, name='public_status_check'),
    path('api/statistics/', views.get_statistics_api, name='get_statistics_api'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Documents
    path('documents/', views.document_list, name='document_list'),
    path('documents/export/excel/', views.export_documents_excel, name='export_documents_excel'),
    path('documents/<int:pk>/', views.document_detail, name='document_detail'),
    path('documents/<int:pk>/print/', views.document_print, name='document_print'),
    path('documents/<int:pk>/export/json/', views.export_document_json, name='export_document_json'),
    path('documents/<int:pk>/accept/', views.accept_document, name='accept_document'),
    path('documents/<int:pk>/reject/', views.reject_document, name='reject_document'),
    path('documents/create/', views.document_create, name='document_create'),
    path('documents/incoming/register/', views.register_incoming, name='register_incoming'),
    
    # Citizen Appeals
    path('appeal/', views.citizen_appeal, name='citizen_appeal'),
    path('appeal/<str:reg_number>/', views.appeal_status, name='appeal_status'),
    
    # Resolutions
    path('documents/<int:document_id>/resolution/create/', views.create_resolution, name='create_resolution'),
    path('resolution/<int:resolution_id>/complete/', views.complete_resolution, name='complete_resolution'),
    path('resolution/<int:resolution_id>/sign/', views.sign_resolution, name='sign_resolution'),
    
    # Admin
    path('users/', views.user_list, name='user_list'),
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.department_create, name='department_create'),
    
    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/open/', views.open_notification, name='open_notification'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
]
