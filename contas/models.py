from django.contrib.auth.models import AbstractUser
from django.db import models


class Utilizador(AbstractUser):
    class Papel(models.TextChoices):
        DIRECAO = "direcao", "Direção"
        EDUCADOR = "educador", "Educador(a)"
        ENCARREGADO = "encarregado", "Encarregado(a) de Educação"

    papel = models.CharField(
        max_length=20, choices=Papel.choices, default=Papel.ENCARREGADO
    )
    telefone = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = "utilizador"
        verbose_name_plural = "utilizadores"

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_direcao(self):
        return self.papel == self.Papel.DIRECAO or self.is_superuser

    @property
    def is_educador(self):
        return self.papel == self.Papel.EDUCADOR

    @property
    def is_encarregado(self):
        return self.papel == self.Papel.ENCARREGADO

    @property
    def pode_gerir_ementa(self):
        return self.is_direcao
