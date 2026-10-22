from django.contrib import admin

from .models import (
    AlbumGaleria,
    Atividade,
    Crianca,
    Ementa,
    FotoGaleria,
    FotoPublicacao,
    Noticia,
    Pagina,
    PreInscricao,
    Publicacao,
    RefeicaoDia,
    Sala,
)

admin.site.site_header = "Os Rabinos · Administração"
admin.site.site_title = "Os Rabinos"
admin.site.index_title = "Gestão da escola"


@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display = ("nome", "valencia", "cor")
    list_filter = ("valencia",)
    filter_horizontal = ("educadores",)


@admin.register(Crianca)
class CriancaAdmin(admin.ModelAdmin):
    list_display = ("nome", "sala", "data_nascimento")
    list_filter = ("sala",)
    search_fields = ("nome",)
    filter_horizontal = ("encarregados",)


class FotoInline(admin.TabularInline):
    model = FotoPublicacao
    extra = 0


@admin.register(Publicacao)
class PublicacaoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "sala", "autor", "criada_em")
    list_filter = ("sala",)
    search_fields = ("titulo", "texto")
    inlines = [FotoInline]


@admin.register(Atividade)
class AtividadeAdmin(admin.ModelAdmin):
    list_display = ("sala", "dia_semana", "hora_inicio", "hora_fim", "nome")
    list_filter = ("sala", "dia_semana")


class RefeicaoInline(admin.TabularInline):
    model = RefeicaoDia
    extra = 0


@admin.register(Ementa)
class EmentaAdmin(admin.ModelAdmin):
    list_display = ("semana_inicio", "publicada")
    inlines = [RefeicaoInline]


@admin.register(Pagina)
class PaginaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "slug", "provisoria", "atualizada_em")
    list_filter = ("provisoria",)
    search_fields = ("titulo", "conteudo")
    view_on_site = True

    def get_view_on_site_url(self, obj=None):
        return f"/{obj.slug}/" if obj else None


@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "data_publicacao", "publicada")
    list_filter = ("publicada",)
    search_fields = ("titulo", "resumo", "conteudo")
    date_hierarchy = "data_publicacao"


class FotoGaleriaInline(admin.TabularInline):
    model = FotoGaleria
    extra = 3


@admin.register(AlbumGaleria)
class AlbumGaleriaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "data", "publicado")
    list_filter = ("publicado",)
    inlines = [FotoGaleriaInline]


@admin.register(PreInscricao)
class PreInscricaoAdmin(admin.ModelAdmin):
    list_display = ("nome_crianca", "valencia", "ano_letivo", "nome_encarregado", "telefone", "criada_em", "tratada")
    list_filter = ("tratada", "valencia", "ano_letivo")
    list_editable = ("tratada",)
    search_fields = ("nome_crianca", "nome_encarregado", "email")
    readonly_fields = ("criada_em",)
