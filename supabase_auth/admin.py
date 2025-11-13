from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['uid', 'email', 'name', 'phone_number']
    search_fields = ['email', 'name', 'uid']
    readonly_fields = ['uid']