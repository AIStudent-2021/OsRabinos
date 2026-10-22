from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Utilizador


@admin.register(Utilizador)
class UtilizadorAdmin(UserAdmin):
    list_display = ("username", "first_name", "last_name", "email", "papel", "is_active")
    list_filter = ("papel", "is_active", "is_staff")
    fieldsets = UserAdmin.fieldsets + (
        ("Os Rabinos", {"fields": ("papel", "telefone")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Os Rabinos", {"fields": ("first_name", "last_name", "email", "papel", "telefone")}),
    )
