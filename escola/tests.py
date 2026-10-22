import datetime
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from contas.models import Utilizador
from escola.models import Crianca, Ementa, FotoPublicacao, Publicacao, Sala

from .management.commands.dados_demo import imagem_exemplo

MEDIA_TESTES = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_TESTES)
class PermissoesTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TESTES, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        P = Utilizador.Papel
        cls.direcao = Utilizador.objects.create_user("direcao", password="x", papel=P.DIRECAO)
        cls.ana = Utilizador.objects.create_user("ana", password="x", papel=P.EDUCADOR)
        cls.joao = Utilizador.objects.create_user("joao", password="x", papel=P.EDUCADOR)
        cls.pai = Utilizador.objects.create_user("pai", password="x", papel=P.ENCARREGADO)

        cls.sala_a = Sala.objects.create(nome="A", valencia="creche")
        cls.sala_b = Sala.objects.create(nome="B", valencia="pre_escolar")
        cls.sala_a.educadores.add(cls.ana)
        cls.sala_b.educadores.add(cls.joao)
        Crianca.objects.create(nome="Tomás", sala=cls.sala_a).encarregados.add(cls.pai)

        cls.pub_a = Publicacao.objects.create(sala=cls.sala_a, autor=cls.ana, titulo="Dia A", texto="...")
        cls.pub_b = Publicacao.objects.create(sala=cls.sala_b, autor=cls.joao, titulo="Dia B", texto="...")
        cls.foto_b = FotoPublicacao.objects.create(publicacao=cls.pub_b, imagem=imagem_exemplo(1))

    def test_paginas_publicas(self):
        for nome in ("inicio", "sobre", "contactos", "ementa", "login"):
            self.assertEqual(self.client.get(reverse(nome)).status_code, 200, nome)

    def test_painel_exige_sessao(self):
        resposta = self.client.get(reverse("painel"))
        self.assertRedirects(resposta, f"{reverse('login')}?next={reverse('painel')}")

    def test_encarregado_so_ve_sala_do_filho(self):
        self.client.force_login(self.pai)
        resposta = self.client.get(reverse("painel"))
        self.assertContains(resposta, "Dia A")
        self.assertNotContains(resposta, "Dia B")
        self.assertEqual(self.client.get(reverse("publicacao_detalhe", args=[self.pub_b.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("foto_publicacao", args=[self.foto_b.pk])).status_code, 404)

    def test_fotos_nao_acessiveis_sem_sessao(self):
        resposta = self.client.get(reverse("foto_publicacao", args=[self.foto_b.pk]))
        self.assertEqual(resposta.status_code, 302)

    def test_educador_ve_foto_da_sua_sala(self):
        self.client.force_login(self.joao)
        resposta = self.client.get(reverse("foto_publicacao", args=[self.foto_b.pk]))
        self.assertEqual(resposta.status_code, 200)

    def test_encarregado_nao_publica(self):
        self.client.force_login(self.pai)
        self.assertEqual(self.client.get(reverse("publicacao_nova")).status_code, 403)
        self.assertEqual(self.client.get(reverse("publicacao_editar", args=[self.pub_a.pk])).status_code, 403)

    def test_educador_publica_com_fotos_na_sua_sala(self):
        self.client.force_login(self.ana)
        foto = SimpleUploadedFile("f.jpg", imagem_exemplo(2).read(), content_type="image/jpeg")
        resposta = self.client.post(
            reverse("publicacao_nova"),
            {"sala": self.sala_a.pk, "titulo": "Novo", "texto": "Olá", "fotos": [foto]},
        )
        pub = Publicacao.objects.get(titulo="Novo")
        self.assertRedirects(resposta, reverse("publicacao_detalhe", args=[pub.pk]))
        self.assertEqual(pub.autor, self.ana)
        self.assertEqual(pub.fotos.count(), 1)

    def test_educador_nao_publica_noutra_sala(self):
        self.client.force_login(self.ana)
        resposta = self.client.post(
            reverse("publicacao_nova"), {"sala": self.sala_b.pk, "titulo": "X", "texto": "Y"}
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Publicacao.objects.filter(titulo="X").exists())
        self.assertEqual(self.client.post(reverse("publicacao_apagar", args=[self.pub_b.pk])).status_code, 404)

    def test_educador_edita_horario_so_da_sua_sala(self):
        self.client.force_login(self.ana)
        self.assertEqual(self.client.get(reverse("horario_editar", args=[self.sala_a.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("horario_editar", args=[self.sala_b.pk])).status_code, 404)

    def test_so_direcao_gere_ementa(self):
        self.client.force_login(self.ana)
        self.assertEqual(self.client.get(reverse("ementas_gerir")).status_code, 403)

        self.client.force_login(self.direcao)
        segunda = datetime.date(2026, 10, 19)
        resposta = self.client.post(reverse("ementa_nova"), {"semana_inicio": "2026-10-19", "publicada": "on"})
        ementa = Ementa.objects.get(semana_inicio=segunda)
        self.assertRedirects(resposta, reverse("ementa_editar", args=[ementa.pk]))
        self.assertEqual(ementa.dias.count(), 5)

        resposta = self.client.post(reverse("ementa_nova"), {"semana_inicio": "2026-10-21"})
        self.assertContains(resposta, "Escolha uma segunda-feira.")

    def test_ementa_publica_mostra_pratos(self):
        ementa = Ementa.objects.create(semana_inicio=datetime.date(2026, 10, 19))
        ementa.dias.create(dia_semana=0, prato="Bacalhau com natas")
        resposta = self.client.get(reverse("ementa"), {"semana": "2026-10-21"})
        self.assertContains(resposta, "Bacalhau com natas")
