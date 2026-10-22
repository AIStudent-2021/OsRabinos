from django.conf import settings

from .menu import construir_menu


def escola(request):
    return {"ESCOLA": settings.ESCOLA, "MENU": construir_menu(request.path)}
