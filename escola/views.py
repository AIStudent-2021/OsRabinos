import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import AtividadeFormSet, EmentaForm, PreInscricaoForm, PublicacaoForm, RefeicaoFormSet
from .models import (
    DIAS_SEMANA,
    AlbumGaleria,
    Ementa,
    FotoGaleria,
    FotoPublicacao,
    Noticia,
    Pagina,
    Publicacao,
    Sala,
    segunda_feira,
)


def _semana_a_mostrar():
    """Semana atual; ao fim de semana mostra já a semana seguinte."""
    hoje = timezone.localdate()
    if hoje.weekday() >= 5:
        hoje += datetime.timedelta(days=7 - hoje.weekday())
    return segunda_feira(hoje)


def _ementa_da_semana(semana):
    return (
        Ementa.objects.filter(semana_inicio=semana, publicada=True)
        .prefetch_related("dias")
        .first()
    )


# --- Páginas públicas ---------------------------------------------------------


def _noticias_publicadas():
    return Noticia.objects.filter(publicada=True, data_publicacao__lte=timezone.now())


def _servir_ficheiro(campo):
    """Entrega um ficheiro público guardado em MEDIA_ROOT (galeria, notícias, documentos)."""
    if not campo:
        raise Http404
    try:
        ficheiro = campo.open("rb")
    except FileNotFoundError:
        raise Http404
    resposta = FileResponse(ficheiro)
    resposta["Cache-Control"] = "public, max-age=86400"
    return resposta


def inicio(request):
    ementa = _ementa_da_semana(_semana_a_mostrar())
    refeicao_hoje = None
    if ementa:
        hoje = timezone.localdate()
        refeicao_hoje = next((d for d in ementa.dias.all() if d.data == hoje), None)
    return render(
        request,
        "escola/inicio.html",
        {
            "ementa": ementa,
            "refeicao_hoje": refeicao_hoje,
            "noticias": _noticias_publicadas()[:3],
        },
    )


def contactos(request):
    return render(request, "escola/contactos.html")


def pagina(request, slug):
    return render(request, "escola/pagina.html", {"pagina": get_object_or_404(Pagina, slug=slug)})


def documento_pagina(request, slug):
    return _servir_ficheiro(get_object_or_404(Pagina, slug=slug).documento)


def noticias(request):
    pagina_atual = Paginator(_noticias_publicadas(), 9).get_page(request.GET.get("pagina"))
    return render(request, "escola/noticias.html", {"pagina": pagina_atual})


def noticia_detalhe(request, pk):
    noticia = get_object_or_404(_noticias_publicadas(), pk=pk)
    outras = _noticias_publicadas().exclude(pk=pk)[:3]
    return render(request, "escola/noticia_detalhe.html", {"noticia": noticia, "outras": outras})


def imagem_noticia(request, pk):
    return _servir_ficheiro(get_object_or_404(_noticias_publicadas(), pk=pk).imagem)


def galeria(request):
    albuns = AlbumGaleria.objects.filter(publicado=True).prefetch_related("fotos")
    return render(request, "escola/galeria.html", {"albuns": albuns})


def album_galeria(request, pk):
    album = get_object_or_404(AlbumGaleria.objects.filter(publicado=True), pk=pk)
    return render(request, "escola/album.html", {"album": album})


def foto_galeria(request, pk):
    foto = get_object_or_404(FotoGaleria.objects.filter(album__publicado=True), pk=pk)
    return _servir_ficheiro(foto.imagem)


def pre_inscricao(request):
    form = PreInscricaoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(
            request,
            "Pré-inscrição recebida. Obrigado! A secretaria entrará em contacto consigo brevemente.",
        )
        return redirect("pre_inscricao")
    return render(request, "escola/pre_inscricao.html", {"form": form})


def ementa(request):
    semana = _semana_a_mostrar()
    if pedido := request.GET.get("semana"):
        try:
            semana = segunda_feira(datetime.date.fromisoformat(pedido))
        except ValueError:
            pass
    return render(
        request,
        "escola/ementa.html",
        {
            "ementa": _ementa_da_semana(semana),
            "semana": semana,
            "semana_fim": semana + datetime.timedelta(days=4),
            "anterior": semana - datetime.timedelta(days=7),
            "seguinte": semana + datetime.timedelta(days=7),
            "hoje": timezone.localdate(),
        },
    )


# --- Área reservada: publicações ----------------------------------------------


@login_required
def painel(request):
    salas = Sala.objects.visiveis_para(request.user)
    publicacoes = (
        Publicacao.objects.filter(sala__in=salas)
        .select_related("sala", "autor")
        .prefetch_related("fotos")
    )
    sala_ativa = None
    if sala_id := request.GET.get("sala"):
        sala_ativa = get_object_or_404(salas, pk=sala_id)
        publicacoes = publicacoes.filter(sala=sala_ativa)

    pagina = Paginator(publicacoes, 10).get_page(request.GET.get("pagina"))
    return render(
        request,
        "escola/painel.html",
        {
            "salas": salas,
            "sala_ativa": sala_ativa,
            "pagina": pagina,
            "pode_publicar": Sala.objects.geridas_por(request.user).exists(),
        },
    )


def _publicacao_visivel(request, pk):
    publicacao = get_object_or_404(Publicacao.objects.select_related("sala", "autor"), pk=pk)
    if not publicacao.sala.pode_ser_vista_por(request.user):
        raise Http404
    return publicacao


def _publicacao_editavel(request, pk):
    publicacao = _publicacao_visivel(request, pk)
    if not publicacao.sala.pode_ser_gerida_por(request.user):
        raise PermissionDenied
    return publicacao


@login_required
def publicacao_detalhe(request, pk):
    publicacao = _publicacao_visivel(request, pk)
    return render(
        request,
        "escola/publicacao_detalhe.html",
        {
            "publicacao": publicacao,
            "pode_editar": publicacao.sala.pode_ser_gerida_por(request.user),
        },
    )


@login_required
def publicacao_nova(request):
    if not Sala.objects.geridas_por(request.user).exists():
        raise PermissionDenied
    return _publicacao_formulario(request, Publicacao(autor=request.user))


@login_required
def publicacao_editar(request, pk):
    return _publicacao_formulario(request, _publicacao_editavel(request, pk))


def _publicacao_formulario(request, publicacao):
    nova = publicacao.pk is None
    form = PublicacaoForm(
        request.POST or None, request.FILES or None, instance=publicacao, utilizador=request.user
    )
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            publicacao = form.save()
            remover = request.POST.getlist("remover_fotos")
            for foto in publicacao.fotos.filter(pk__in=remover):
                foto.imagem.delete(save=False)
                foto.delete()
            for imagem in form.cleaned_data["fotos"]:
                FotoPublicacao.objects.create(publicacao=publicacao, imagem=imagem)
        messages.success(request, "Publicação criada." if nova else "Publicação atualizada.")
        return redirect("publicacao_detalhe", pk=publicacao.pk)
    return render(
        request, "escola/publicacao_form.html", {"form": form, "publicacao": publicacao, "nova": nova}
    )


@login_required
@require_POST
def publicacao_apagar(request, pk):
    publicacao = _publicacao_editavel(request, pk)
    for foto in publicacao.fotos.all():
        foto.imagem.delete(save=False)
    publicacao.delete()
    messages.success(request, "Publicação apagada.")
    return redirect("painel")


@login_required
def foto_publicacao(request, pk):
    """Entrega a fotografia apenas a quem pode ver a sala (as fotos não são públicas)."""
    foto = get_object_or_404(FotoPublicacao.objects.select_related("publicacao__sala"), pk=pk)
    if not foto.publicacao.sala.pode_ser_vista_por(request.user):
        raise Http404
    try:
        ficheiro = foto.imagem.open("rb")
    except FileNotFoundError:
        raise Http404
    resposta = FileResponse(ficheiro)
    resposta["Cache-Control"] = "private, max-age=3600"
    return resposta


# --- Área reservada: horários -------------------------------------------------


@login_required
def horarios(request):
    salas = Sala.objects.visiveis_para(request.user)
    if len(salas) == 1:
        return redirect("horario_sala", pk=salas[0].pk)
    return render(request, "escola/horarios.html", {"salas": salas})


@login_required
def horario_sala(request, pk):
    sala = get_object_or_404(Sala.objects.visiveis_para(request.user), pk=pk)
    atividades = list(sala.atividades.all())
    dias = [
        {"nome": nome, "atividades": [a for a in atividades if a.dia_semana == numero]}
        for numero, nome in DIAS_SEMANA
    ]
    return render(
        request,
        "escola/horario_sala.html",
        {
            "sala": sala,
            "dias": dias,
            "pode_editar": sala.pode_ser_gerida_por(request.user),
            "outras_salas": Sala.objects.visiveis_para(request.user).exclude(pk=sala.pk),
        },
    )


@login_required
def horario_editar(request, pk):
    sala = get_object_or_404(Sala.objects.geridas_por(request.user), pk=pk)
    formset = AtividadeFormSet(request.POST or None, instance=sala)
    if request.method == "POST" and formset.is_valid():
        formset.save()
        messages.success(request, "Horário guardado.")
        return redirect("horario_sala", pk=sala.pk)
    return render(request, "escola/horario_form.html", {"sala": sala, "formset": formset})


# --- Área reservada: gestão da ementa -----------------------------------------


def _exigir_gestor_ementa(request):
    if not request.user.pode_gerir_ementa:
        raise PermissionDenied


@login_required
def ementas_gerir(request):
    _exigir_gestor_ementa(request)
    return render(request, "escola/ementas_gerir.html", {"ementas": Ementa.objects.all()[:30]})


@login_required
def ementa_nova(request):
    _exigir_gestor_ementa(request)
    form = EmentaForm(request.POST or None, initial={"semana_inicio": _semana_a_mostrar()})
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            ementa = form.save()
            for numero, _ in DIAS_SEMANA:
                ementa.dias.create(dia_semana=numero)
        messages.success(request, "Ementa criada. Preencha agora as refeições de cada dia.")
        return redirect("ementa_editar", pk=ementa.pk)
    return render(request, "escola/ementa_form.html", {"form": form, "nova": True})


@login_required
def ementa_editar(request, pk):
    _exigir_gestor_ementa(request)
    ementa_obj = get_object_or_404(Ementa, pk=pk)
    form = EmentaForm(request.POST or None, instance=ementa_obj)
    formset = RefeicaoFormSet(request.POST or None, instance=ementa_obj)
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        with transaction.atomic():
            form.save()
            formset.save()
        messages.success(request, "Ementa guardada.")
        return redirect(f"{reverse('ementa')}?semana={ementa_obj.semana_inicio:%Y-%m-%d}")
    return render(
        request,
        "escola/ementa_form.html",
        {"form": form, "formset": formset, "ementa": ementa_obj, "nova": False},
    )


@login_required
@require_POST
def ementa_apagar(request, pk):
    _exigir_gestor_ementa(request)
    get_object_or_404(Ementa, pk=pk).delete()
    messages.success(request, "Ementa apagada.")
    return redirect("ementas_gerir")
