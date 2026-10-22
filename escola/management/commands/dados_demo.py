"""Cria dados de demonstração. Uso: python manage.py dados_demo"""

import datetime
import io
import random

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw

from contas.models import Utilizador
from escola.models import Atividade, Crianca, Ementa, FotoPublicacao, Publicacao, Sala, segunda_feira

PALAVRA_PASSE = "rabinos2026"

CORES_IMAGEM = ["#2b7bbf", "#9cc433", "#e0392b", "#c03aae", "#f4c62c"]


def imagem_exemplo(semente):
    rng = random.Random(semente)
    img = Image.new("RGB", (800, 600), "#fdfbf5")
    desenho = ImageDraw.Draw(img)
    for _ in range(14):
        x, y = rng.randint(-50, 800), rng.randint(-50, 600)
        r = rng.randint(30, 140)
        desenho.ellipse((x - r, y - r, x + r, y + r), fill=rng.choice(CORES_IMAGEM))
    buffer = io.BytesIO()
    img.save(buffer, "JPEG", quality=80)
    return ContentFile(buffer.getvalue(), name=f"exemplo_{semente}.jpg")


class Command(BaseCommand):
    help = "Cria utilizadores, salas, publicações, horários e ementa de demonstração."

    def criar_utilizador(self, username, nome, apelido, papel, **extra):
        utilizador, criado = Utilizador.objects.get_or_create(
            username=username,
            defaults={"first_name": nome, "last_name": apelido, "papel": papel, **extra},
        )
        if criado:
            utilizador.set_password(PALAVRA_PASSE)
            utilizador.save()
        return utilizador

    @transaction.atomic
    def handle(self, *args, **options):
        if Sala.objects.exists():
            self.stdout.write(self.style.WARNING("Já existem dados. Nada foi alterado."))
            return

        direcao = self.criar_utilizador(
            "direcao", "Maria", "Direção", Utilizador.Papel.DIRECAO, is_staff=True, is_superuser=True
        )
        ana = self.criar_utilizador("ana", "Ana", "Sousa", Utilizador.Papel.EDUCADOR)
        joao = self.criar_utilizador("joao", "João", "Pereira", Utilizador.Papel.EDUCADOR)
        rita = self.criar_utilizador("rita", "Rita", "Lopes", Utilizador.Papel.EDUCADOR)
        pai = self.criar_utilizador("pai", "Pedro", "Almeida", Utilizador.Papel.ENCARREGADO)
        mae = self.criar_utilizador("mae", "Sofia", "Costa", Utilizador.Papel.ENCARREGADO)

        bercario = Sala.objects.create(nome="Sala dos Bebés", valencia="bercario", cor="vermelho")
        creche = Sala.objects.create(nome="Sala Arco-Íris", valencia="creche", cor="verde")
        pre = Sala.objects.create(nome="Sala dos Exploradores", valencia="pre_escolar", cor="rosa")
        bercario.educadores.add(rita)
        creche.educadores.add(ana)
        pre.educadores.add(joao)

        Crianca.objects.create(nome="Tomás Almeida", sala=creche).encarregados.add(pai)
        Crianca.objects.create(nome="Leonor Costa", sala=pre).encarregados.add(mae)
        Crianca.objects.create(nome="Inês Almeida", sala=bercario).encarregados.add(pai)

        publicacoes = [
            (creche, ana, "Pintura com as mãos",
             "Hoje explorámos as cores primárias com pintura de mãos. "
             "Foi uma manhã cheia de gargalhadas (e algumas mãos muito coloridas)!"),
            (creche, ana, "Passeio ao jardim",
             "Aproveitámos o sol para ir ao jardim apanhar folhas de outono. "
             "Amanhã vamos usá-las num trabalho de colagem."),
            (pre, joao, "Projeto: os planetas",
             "Começámos o nosso projeto sobre o Sistema Solar. Cada criança escolheu um planeta "
             "e vamos construir uma maqueta gigante na sala."),
            (bercario, rita, "Hora do conto",
             "Os bebés estiveram muito atentos à história do “Elmer”. Exploraram livros de pano e de texturas."),
        ]
        agora = timezone.now()
        for i, (sala, autor, titulo, texto) in enumerate(publicacoes):
            pub = Publicacao.objects.create(sala=sala, autor=autor, titulo=titulo, texto=texto)
            Publicacao.objects.filter(pk=pub.pk).update(criada_em=agora - datetime.timedelta(hours=20 * i))
            for j in range(3 if i % 2 == 0 else 1):
                FotoPublicacao.objects.create(publicacao=pub, imagem=imagem_exemplo(i * 10 + j))

        rotina = [
            ("08:00", "09:30", "Acolhimento", "Brincadeira livre"),
            ("09:30", "10:00", "Reforço da manhã", "Fruta"),
            ("10:00", "11:30", "Atividade orientada", ""),
            ("11:30", "12:30", "Almoço", ""),
            ("12:30", "15:00", "Descanso", ""),
            ("15:30", "16:00", "Lanche", ""),
        ]
        especiais = {1: "Música", 3: "Expressão motora", 4: "Inglês"}
        for sala in (bercario, creche, pre):
            for dia in range(5):
                for inicio, fim, nome, descricao in rotina:
                    if nome == "Atividade orientada" and dia in especiais and sala != bercario:
                        nome = especiais[dia]
                    Atividade.objects.create(
                        sala=sala,
                        dia_semana=dia,
                        hora_inicio=datetime.time.fromisoformat(inicio),
                        hora_fim=datetime.time.fromisoformat(fim),
                        nome=nome,
                        descricao=descricao,
                    )

        hoje = timezone.localdate()
        if hoje.weekday() >= 5:
            hoje += datetime.timedelta(days=7 - hoje.weekday())
        ementa = Ementa.objects.create(
            semana_inicio=segunda_feira(hoje),
            observacoes="Todas as refeições são confecionadas na nossa cozinha. "
            "Dietas especiais mediante declaração médica.",
        )
        menu = [
            ("Creme de cenoura", "Bacalhau com natas", "Maçã cozida", "Pão com manteiga e leite", "Peixe, leite, glúten"),
            ("Sopa de legumes", "Frango estufado com arroz", "Banana", "Iogurte natural", ""),
            ("Sopa de feijão-verde", "Pescada cozida com batata e brócolos", "Pera", "Pão com queijo", "Peixe, glúten, leite"),
            ("Creme de abóbora", "Esparguete à bolonhesa", "Laranja", "Bolacha Maria e leite", "Glúten, leite"),
            ("Sopa de grão", "Peru grelhado com puré", "Gelatina", "Pão com fiambre", "Leite"),
        ]
        for dia, (sopa, prato, sobremesa, lanche, alergenios) in enumerate(menu):
            ementa.dias.create(
                dia_semana=dia, sopa=sopa, prato=prato, sobremesa=sobremesa,
                lanche=lanche, alergenios=alergenios,
            )

        self.stdout.write(self.style.SUCCESS("Dados de demonstração criados."))
        self.stdout.write(f"Palavra-passe de todos os utilizadores: {PALAVRA_PASSE}")
        self.stdout.write("  direcao  – Direção (acesso total + administração)")
        self.stdout.write("  ana      – Educadora da Sala Arco-Íris")
        self.stdout.write("  joao     – Educador da Sala dos Exploradores")
        self.stdout.write("  rita     – Educadora da Sala dos Bebés")
        self.stdout.write("  pai      – Encarregado (Tomás e Inês)")
        self.stdout.write("  mae      – Encarregada (Leonor)")
