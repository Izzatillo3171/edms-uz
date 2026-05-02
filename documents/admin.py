from django.contrib import admin
from .models import User, Department, Document, Notification, Resolution

# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'department', 'full_name', 'phone')
    list_filter = ('role', 'department')
    search_fields = ('username', 'email', 'full_name')

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('reg_number', 'title', 'status', 'created_at', 'author')
    list_filter = ('status', 'created_at')
    search_fields = ('reg_number', 'title')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('message',)

@admin.register(Resolution)
class ResolutionAdmin(admin.ModelAdmin):
    list_display = ('document', 'text', 'created_at', 'author')
    search_fields = ('text',)
