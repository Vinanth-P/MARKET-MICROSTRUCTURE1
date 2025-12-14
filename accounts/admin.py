from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'usage_percentage', 'created_at']
    list_filter = ['plan', 'created_at']
    search_fields = ['user__username', 'user__email']
