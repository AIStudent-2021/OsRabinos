from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("contactos/", views.contactos, name="contactos"),
    path("ementa/", views.ementa, name="ementa"),
    path("noticias/", views.noticias, name="noticias"),
    path("noticias/<int:pk>/", views.noticia_detalhe, name="noticia_detalhe"),
    path("noticias/<int:pk>/imagem/", views.imagem_noticia, name="imagem_noticia"),
    path("galeria/", views.galeria, name="galeria"),
    path("galeria/<int:pk>/", views.album_galeria, name="album_galeria"),
    path("galeria/foto/<int:pk>/", views.foto_galeria, name="foto_galeria"),
    path("pre-inscricoes/", views.pre_inscricao, name="pre_inscricao"),
    path("documentos/<slug:slug>/", views.documento_pagina, name="documento_pagina"),
    # Área reservada
    path("painel/", views.painel, name="painel"),
    path("publicacoes/nova/", views.publicacao_nova, name="publicacao_nova"),
    path("publicacoes/<int:pk>/", views.publicacao_detalhe, name="publicacao_detalhe"),
    path("publicacoes/<int:pk>/editar/", views.publicacao_editar, name="publicacao_editar"),
    path("publicacoes/<int:pk>/apagar/", views.publicacao_apagar, name="publicacao_apagar"),
    path("fotos/<int:pk>/", views.foto_publicacao, name="foto_publicacao"),
    path("horarios/", views.horarios, name="horarios"),
    path("horarios/<int:pk>/", views.horario_sala, name="horario_sala"),
    path("horarios/<int:pk>/editar/", views.horario_editar, name="horario_editar"),
    path("gestao/ementas/", views.ementas_gerir, name="ementas_gerir"),
    path("gestao/ementas/nova/", views.ementa_nova, name="ementa_nova"),
    path("gestao/ementas/<int:pk>/editar/", views.ementa_editar, name="ementa_editar"),
    path("gestao/ementas/<int:pk>/apagar/", views.ementa_apagar, name="ementa_apagar"),
    # Páginas editáveis (Projeto Educativo, Mensalidades, …). Tem de ficar em último.
    path("<slug:slug>/", views.pagina, name="pagina"),
]
