# Os Rabinos · Plataforma da escola

Site e área reservada do **Os Rabinos** (berçário, creche e pré-escolar no Porto).

## Funcionalidades

| Módulo | Quem usa | O que faz |
|---|---|---|
| **Site público** | Todos | Início, Sobre nós, Contactos e Ementa semanal |
| **Diário** | Educadores publicam, pais leem | Publicações diárias por sala, com várias fotografias |
| **Horários** | Educadores / Direção editam | Horário semanal de cada sala |
| **Ementa** | Direção | Ementa da semana (sopa, prato, sobremesa, lanche, alergénios) |
| **Administração** | Direção | Utilizadores, salas, crianças e encarregados (`/admin/`) |

### Perfis e permissões

- **Direção**: acesso total, gere a ementa e a administração.
- **Educador(a)**: publica e edita o horário **apenas nas suas salas**.
- **Encarregado(a) de Educação**: vê **apenas** as publicações e horários das salas dos seus educandos.

As fotografias das crianças **não são públicas**: ficam na pasta `privado/` e só são entregues
a utilizadores com sessão iniciada e com acesso à sala (RGPD).

## Instalação (desenvolvimento)

Requer Python 3.12 ou superior.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py dados_demo      # opcional: dados de exemplo
python manage.py runserver
```

Abrir <http://localhost:8000>.

### Contas de demonstração

Criadas por `dados_demo`, todas com a palavra-passe `rabinos2026`:

| Utilizador | Perfil |
|---|---|
| `direcao` | Direção (também entra em `/admin/`) |
| `ana` | Educadora da Sala Arco-Íris |
| `joao` | Educador da Sala dos Exploradores |
| `rita` | Educadora da Sala dos Bebés |
| `pai` | Encarregado (Tomás e Inês) |
| `mae` | Encarregada (Leonor) |

Para criar a primeira conta real: `python manage.py createsuperuser`.

## Como usar

1. A **direção** entra em `/admin/` e cria as salas, os educadores, os encarregados e as crianças
   (cada criança fica ligada a uma sala e aos seus encarregados).
2. Os **educadores** entram em *Diário → Nova publicação* e em *Horários → Editar horário*.
3. A **direção** publica a ementa em *Gestão → Nova ementa*.
4. Os **pais** entram com as credenciais dadas pela escola e veem o diário da sala.

## Testes

```bash
python manage.py test
```

## Estrutura

```
config/      configuração do Django (settings, urls)
contas/      modelo de utilizador com perfil (direção / educador / encarregado)
escola/      salas, crianças, publicações, horários e ementas
templates/   páginas HTML (em português)
static/      CSS e imagens (logótipo e banner)
```

## Produção

Antes de colocar online:

- Definir `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0` e `DJANGO_ALLOWED_HOSTS`.
- Usar PostgreSQL em vez de SQLite e correr `python manage.py collectstatic`.
- Usar HTTPS e fazer cópias de segurança da base de dados e da pasta `privado/`.
- Obter o consentimento das famílias para a publicação de imagens.
