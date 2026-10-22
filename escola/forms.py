from django import forms
from django.forms import inlineformset_factory

from .models import Atividade, Ementa, PreInscricao, Publicacao, RefeicaoDia, Sala


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={"accept": "image/*"}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if isinstance(data, (list, tuple)):
            return [super(MultipleImageField, self).clean(d, initial) for d in data if d]
        return [super().clean(data, initial)] if data else []


class PublicacaoForm(forms.ModelForm):
    fotos = MultipleImageField(
        label="Fotografias", required=False, help_text="Pode escolher várias imagens."
    )

    class Meta:
        model = Publicacao
        fields = ["sala", "titulo", "texto"]
        widgets = {
            "texto": forms.Textarea(attrs={"rows": 8, "placeholder": "Como correu o dia na sala?"}),
        }

    def __init__(self, *args, utilizador, **kwargs):
        super().__init__(*args, **kwargs)
        salas = Sala.objects.geridas_por(utilizador)
        self.fields["sala"].queryset = salas
        if salas.count() == 1:
            self.fields["sala"].empty_label = None
            self.initial.setdefault("sala", salas.first().pk)


class AtividadeForm(forms.ModelForm):
    class Meta:
        model = Atividade
        fields = ["dia_semana", "hora_inicio", "hora_fim", "nome", "descricao"]
        widgets = {
            "hora_inicio": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "hora_fim": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
        }


AtividadeFormSet = inlineformset_factory(
    Sala, Atividade, form=AtividadeForm, extra=3, can_delete=True
)


class EmentaForm(forms.ModelForm):
    class Meta:
        model = Ementa
        fields = ["semana_inicio", "observacoes", "publicada"]
        widgets = {
            "semana_inicio": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "observacoes": forms.Textarea(attrs={"rows": 3}),
        }


class PreInscricaoForm(forms.ModelForm):
    class Meta:
        model = PreInscricao
        fields = [
            "nome_crianca", "data_nascimento", "valencia", "ano_letivo",
            "nome_encarregado", "email", "telefone", "mensagem", "consentimento",
        ]
        widgets = {
            "data_nascimento": forms.DateInput(attrs={"type": "date"}),
            "mensagem": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["consentimento"].required = True
        self.fields["consentimento"].error_messages["required"] = (
            "É necessário autorizar o tratamento dos dados para enviar a pré-inscrição."
        )


RefeicaoFormSet = inlineformset_factory(
    Ementa,
    RefeicaoDia,
    fields=["sopa", "prato", "sobremesa", "lanche", "alergenios"],
    extra=0,
    can_delete=False,
)
