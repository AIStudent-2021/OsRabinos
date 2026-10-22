import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

DIAS_SEMANA = [
    (0, "Segunda-feira"),
    (1, "Terça-feira"),
    (2, "Quarta-feira"),
    (3, "Quinta-feira"),
    (4, "Sexta-feira"),
]


class SalaQuerySet(models.QuerySet):
    def visiveis_para(self, utilizador):
        """Salas que o utilizador pode consultar."""
        if not utilizador.is_authenticated:
            return self.none()
        if utilizador.is_direcao:
            return self.all()
        if utilizador.is_educador:
            return self.filter(educadores=utilizador).distinct()
        return self.filter(criancas__encarregados=utilizador).distinct()

    def geridas_por(self, utilizador):
        """Salas onde o utilizador pode publicar e editar o horário."""
        if not utilizador.is_authenticated:
            return self.none()
        if utilizador.is_direcao:
            return self.all()
        if utilizador.is_educador:
            return self.filter(educadores=utilizador).distinct()
        return self.none()


class Sala(models.Model):
    class Valencia(models.TextChoices):
        BERCARIO = "bercario", "Berçário"
        CRECHE = "creche", "Creche"
        PRE_ESCOLAR = "pre_escolar", "Pré-escolar"

    class Cor(models.TextChoices):
        AZUL = "azul", "Azul"
        VERDE = "verde", "Verde"
        VERMELHO = "vermelho", "Vermelho"
        ROSA = "rosa", "Rosa"
        AMARELO = "amarelo", "Amarelo"

    nome = models.CharField(max_length=80)
    valencia = models.CharField("valência", max_length=20, choices=Valencia.choices)
    cor = models.CharField(max_length=20, choices=Cor.choices, default=Cor.AZUL)
    educadores = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="salas_educador",
        blank=True,
        limit_choices_to={"papel": "educador"},
    )

    objects = SalaQuerySet.as_manager()

    class Meta:
        ordering = ["valencia", "nome"]

    def __str__(self):
        return f"{self.nome} ({self.get_valencia_display()})"

    def pode_ser_gerida_por(self, utilizador):
        return Sala.objects.geridas_por(utilizador).filter(pk=self.pk).exists()

    def pode_ser_vista_por(self, utilizador):
        return Sala.objects.visiveis_para(utilizador).filter(pk=self.pk).exists()


class Crianca(models.Model):
    nome = models.CharField(max_length=120)
    data_nascimento = models.DateField("data de nascimento", null=True, blank=True)
    sala = models.ForeignKey(Sala, on_delete=models.PROTECT, related_name="criancas")
    encarregados = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="educandos",
        blank=True,
        limit_choices_to={"papel": "encarregado"},
        verbose_name="encarregados de educação",
    )

    class Meta:
        ordering = ["nome"]
        verbose_name = "criança"
        verbose_name_plural = "crianças"

    def __str__(self):
        return self.nome


class Publicacao(models.Model):
    sala = models.ForeignKey(Sala, on_delete=models.CASCADE, related_name="publicacoes")
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="publicacoes"
    )
    titulo = models.CharField("título", max_length=150)
    texto = models.TextField()
    criada_em = models.DateTimeField("criada em", auto_now_add=True)
    atualizada_em = models.DateTimeField("atualizada em", auto_now=True)

    class Meta:
        ordering = ["-criada_em"]
        verbose_name = "publicação"
        verbose_name_plural = "publicações"

    def __str__(self):
        return self.titulo


class FotoPublicacao(models.Model):
    publicacao = models.ForeignKey(Publicacao, on_delete=models.CASCADE, related_name="fotos")
    imagem = models.ImageField(upload_to="publicacoes/%Y/%m/")
    legenda = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "fotografia"
        verbose_name_plural = "fotografias"

    def __str__(self):
        return self.legenda or self.imagem.name


class Atividade(models.Model):
    """Um bloco do horário semanal de uma sala."""

    sala = models.ForeignKey(Sala, on_delete=models.CASCADE, related_name="atividades")
    dia_semana = models.PositiveSmallIntegerField("dia da semana", choices=DIAS_SEMANA)
    hora_inicio = models.TimeField("início")
    hora_fim = models.TimeField("fim")
    nome = models.CharField("atividade", max_length=100)
    descricao = models.CharField("descrição", max_length=200, blank=True)

    class Meta:
        ordering = ["dia_semana", "hora_inicio"]
        verbose_name = "atividade do horário"
        verbose_name_plural = "atividades do horário"

    def __str__(self):
        return f"{self.get_dia_semana_display()} {self.hora_inicio:%H:%M} – {self.nome}"

    def clean(self):
        if self.hora_inicio and self.hora_fim and self.hora_fim <= self.hora_inicio:
            raise ValidationError({"hora_fim": "A hora de fim tem de ser depois da hora de início."})


def segunda_feira(data):
    return data - datetime.timedelta(days=data.weekday())


class Ementa(models.Model):
    semana_inicio = models.DateField("semana de", unique=True, help_text="Segunda-feira da semana.")
    observacoes = models.TextField("observações", blank=True)
    publicada = models.BooleanField(default=True)

    class Meta:
        ordering = ["-semana_inicio"]

    def __str__(self):
        return f"Ementa da semana de {self.semana_inicio:%d/%m/%Y}"

    @property
    def semana_fim(self):
        return self.semana_inicio + datetime.timedelta(days=4)

    def clean(self):
        if self.semana_inicio and self.semana_inicio.weekday() != 0:
            raise ValidationError({"semana_inicio": "Escolha uma segunda-feira."})


class RefeicaoDia(models.Model):
    ementa = models.ForeignKey(Ementa, on_delete=models.CASCADE, related_name="dias")
    dia_semana = models.PositiveSmallIntegerField("dia", choices=DIAS_SEMANA)
    sopa = models.CharField(max_length=150, blank=True)
    prato = models.CharField("prato principal", max_length=200, blank=True)
    sobremesa = models.CharField(max_length=150, blank=True)
    lanche = models.CharField(max_length=150, blank=True)
    alergenios = models.CharField("alergénios", max_length=200, blank=True)

    class Meta:
        ordering = ["dia_semana"]
        unique_together = [("ementa", "dia_semana")]
        verbose_name = "refeição do dia"
        verbose_name_plural = "refeições do dia"

    def __str__(self):
        return self.get_dia_semana_display()

    @property
    def data(self):
        return self.ementa.semana_inicio + datetime.timedelta(days=self.dia_semana)


# --- Conteúdos públicos do site -----------------------------------------------

# Endereços já usados por outras páginas; uma Pagina não pode usar estes slugs.
SLUGS_RESERVADOS = {
    "admin", "entrar", "sair", "palavra-passe", "ementa", "contactos", "painel", "publicacoes",
    "fotos", "horarios", "gestao", "noticias", "galeria", "pre-inscricoes", "documentos", "static",
}


class Pagina(models.Model):
    """Página informativa editável pela direção (Projeto Educativo, Mensalidades, …)."""

    slug = models.SlugField(
        "endereço", unique=True, help_text="Parte final do endereço, ex.: projeto-educativo"
    )
    titulo = models.CharField("título", max_length=120)
    introducao = models.CharField("introdução", max_length=300, blank=True)
    conteudo = models.TextField(
        "conteúdo",
        blank=True,
        help_text="Aceita HTML: <h2>, <p>, <ul>, <table>, <strong>…",
    )
    documento = models.FileField(upload_to="documentos/", blank=True)
    documento_titulo = models.CharField(
        "texto do botão do documento", max_length=120, blank=True, default="Descarregar documento (PDF)"
    )
    provisoria = models.BooleanField(
        "conteúdo provisório", default=False, help_text="Mostra um aviso de que a página está por rever."
    )
    atualizada_em = models.DateTimeField("atualizada em", auto_now=True)

    class Meta:
        ordering = ["titulo"]
        verbose_name = "página"
        verbose_name_plural = "páginas"

    def __str__(self):
        return self.titulo

    def clean(self):
        if self.slug in SLUGS_RESERVADOS:
            raise ValidationError({"slug": "Este endereço já é usado pelo site. Escolha outro."})


class Noticia(models.Model):
    titulo = models.CharField("título", max_length=150)
    resumo = models.CharField(max_length=300)
    conteudo = models.TextField("conteúdo", help_text="Aceita HTML.")
    imagem = models.ImageField(upload_to="noticias/", blank=True)
    data_publicacao = models.DateTimeField("data de publicação", default=timezone.now)
    publicada = models.BooleanField(default=True)

    class Meta:
        ordering = ["-data_publicacao"]
        verbose_name = "notícia"
        verbose_name_plural = "notícias"

    def __str__(self):
        return self.titulo


class AlbumGaleria(models.Model):
    titulo = models.CharField("título", max_length=120)
    descricao = models.CharField("descrição", max_length=300, blank=True)
    data = models.DateField(default=datetime.date.today)
    publicado = models.BooleanField(default=True)

    class Meta:
        ordering = ["-data"]
        verbose_name = "álbum da galeria"
        verbose_name_plural = "álbuns da galeria"

    def __str__(self):
        return self.titulo


class FotoGaleria(models.Model):
    album = models.ForeignKey(AlbumGaleria, on_delete=models.CASCADE, related_name="fotos")
    imagem = models.ImageField(
        upload_to="galeria/%Y/",
        help_text="A galeria é pública: use apenas fotografias com autorização das famílias.",
    )
    legenda = models.CharField(max_length=200, blank=True)
    ordem = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["ordem", "pk"]
        verbose_name = "fotografia da galeria"
        verbose_name_plural = "fotografias da galeria"

    def __str__(self):
        return self.legenda or self.imagem.name


class PreInscricao(models.Model):
    nome_crianca = models.CharField("nome da criança", max_length=150)
    data_nascimento = models.DateField("data de nascimento (ou data prevista)")
    valencia = models.CharField("valência pretendida", max_length=20, choices=Sala.Valencia.choices)
    ano_letivo = models.CharField("ano letivo pretendido", max_length=9, help_text="Ex.: 2027/2028")
    nome_encarregado = models.CharField("nome do encarregado de educação", max_length=150)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    mensagem = models.TextField("observações", blank=True)
    consentimento = models.BooleanField(
        "autorizo o tratamento destes dados para efeitos de pré-inscrição"
    )
    criada_em = models.DateTimeField("recebida em", auto_now_add=True)
    tratada = models.BooleanField(default=False)

    class Meta:
        ordering = ["-criada_em"]
        verbose_name = "pré-inscrição"
        verbose_name_plural = "pré-inscrições"

    def __str__(self):
        return f"{self.nome_crianca} ({self.get_valencia_display()})"
