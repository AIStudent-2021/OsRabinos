"""Menu principal do site.

Cada item é ("Título", destino) ou ("Título", [subitens]).
O destino é o nome de um URL ("ementa") ou "/slug/" para uma Pagina editável no admin.
"""

from django.urls import reverse

MENU = [
    ("A Escola", [
        ("História", "/historia/"),
        ("Natureza Jurídica", "/natureza-juridica/"),
        ("Projeto Educativo", "/projeto-educativo/"),
        ("Regulamento Interno", "/regulamento-interno/"),
        ("Equipa", "/equipa/"),
        ("Política de Privacidade", "/politica-de-privacidade/"),
    ]),
    ("Secretaria", [
        ("Horário", "/horario/"),
        ("Calendário Escolar", "/calendario-escolar/"),
        ("Ementas", "ementa"),
        ("Mensalidades", "/mensalidades/"),
        ("Material e Enxoval", "/material-e-enxoval/"),
        ("Recrutamento", "/recrutamento/"),
        ("Pré-inscrições", "pre_inscricao"),
    ]),
    ("Ensino", [
        ("Berçário", "/bercario/"),
        ("Creche", "/creche/"),
        ("Pré-Escolar", "/pre-escolar/"),
        ("Atividades Extracurriculares", "/atividades-extracurriculares/"),
    ]),
    ("Projetos", "/projetos/"),
    ("Galeria", "galeria"),
    ("Notícias", "noticias"),
    ("Contactos", "contactos"),
]


def _url(destino):
    return destino if destino.startswith("/") else reverse(destino)


def construir_menu(caminho_atual):
    """Devolve o menu com os URLs resolvidos e o item ativo marcado."""

    def ativo(url):
        return caminho_atual == url or (url != "/" and caminho_atual.startswith(url))

    menu = []
    for titulo, destino in MENU:
        if isinstance(destino, list):
            itens = [{"titulo": t, "url": _url(d)} for t, d in destino]
            for item in itens:
                item["ativo"] = ativo(item["url"])
            menu.append({"titulo": titulo, "itens": itens, "ativo": any(i["ativo"] for i in itens)})
        else:
            url = _url(destino)
            menu.append({"titulo": titulo, "url": url, "ativo": ativo(url)})
    return menu
