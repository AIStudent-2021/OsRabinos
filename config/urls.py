from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("entrar/", auth_views.LoginView.as_view(), name="login"),
    path("sair/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "palavra-passe/alterar/",
        auth_views.PasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "palavra-passe/alterada/",
        auth_views.PasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
    path("", include("escola.urls")),
]
