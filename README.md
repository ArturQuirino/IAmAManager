# I Am a Manager

Simulador de manager de futebol. Monorepo com **backend FastAPI** (`backend/`) e **frontend Next.js 14** (`frontend/`), orquestrados por Docker Compose e implantados via Terraform em AWS ECS (`deploy/`).

Você monta um elenco, define táticas, gere as categorias de base e disputa as competições — cujas rodadas são resolvidas por uma simulação de partidas que roda diariamente.

## Stack

| Camada | Tecnologias |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic, JWT (python-jose), bcrypt (passlib) |
| Frontend | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, next-intl |
| Banco | PostgreSQL 15 |
| Infra | Docker Compose (dev/prod local), Terraform + AWS ECS (`deploy/`) |

Idiomas suportados na interface e nas mensagens de erro: **Português (pt-BR), Inglês (en) e Espanhol (es)**.

## Estrutura do repositório

```
backend/     API FastAPI (routers → services → models/schemas). Migrações Alembic e testes pytest.
frontend/    App Next.js (app/, components/, hooks/, lib/, messages/ para i18n).
deploy/      Terraform + scripts de deploy (AWS ECS).
docs/        Documentação de regras de negócio, competição, simulação de partidas, telas, etc.
CLAUDE.md    Regras de desenvolvimento obrigatórias do projeto.
docker-compose.yml       Ambiente de desenvolvimento (com hot-reload).
docker-compose.prod.yml  Build de produção local.
```

## Pré-requisitos

- **Docker** e **Docker Compose** (caminho recomendado — sobe tudo com um comando).
- Para rodar sem Docker: **Python 3.12+**, **Node.js 18+** e um **PostgreSQL 15** acessível.

## Configuração inicial

Copie o exemplo de variáveis de ambiente e ajuste se necessário:

```bash
cp .env.example .env
```

Os valores padrão de `.env.example` já funcionam para desenvolvimento local com Docker. Pontos importantes:

- `JWT_SECRET` — use o padrão só em dev. **Em produção, venha de um secret manager.**
- `RUN_SEED=true` — popula o banco com dados iniciais no primeiro boot do backend.
- `SCHEDULER_ENABLED` / `MATCHDAY_HOUR` / `MATCHDAY_MINUTE` — controlam o job diário que joga uma rodada de cada divisão no horário configurado (24h).

> Nunca commite o `.env` (ele é git-ignored). Toda nova variável de configuração deve entrar no `.env.example` com um valor de exemplo seguro.

## Rodando o projeto completo (recomendado)

Com Docker Compose sobem os três serviços — Postgres, backend e frontend:

```bash
docker compose up --build
```

Serviços disponíveis:

| Serviço | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend (API) | http://localhost:3001/api |
| Docs da API (Swagger) | http://localhost:3001/docs |
| PostgreSQL | localhost:5432 |

No boot, o backend aplica as migrações Alembic (`alembic upgrade head`) e roda o seed. O frontend faz proxy de `/api/*` para o backend (`BACKEND_INTERNAL_URL`), então a partir do browser você acessa tudo por `http://localhost:3000`.

Para parar:

```bash
docker compose down          # mantém os dados do Postgres
docker compose down -v       # também apaga o volume do banco (reset total)
```

### Produção local

Para testar o build de produção (imagens otimizadas, sem hot-reload):

```bash
docker compose -f docker-compose.prod.yml up --build
```

## Rodando cada parte separadamente (sem Docker)

Útil para depurar um serviço isoladamente. Você precisa de um PostgreSQL rodando; ajuste `POSTGRES_HOST=localhost` no `.env` (o padrão `postgres` é o nome do serviço na rede do Compose).

### Backend

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate      # Windows (Git Bash); no Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt   # runtime + stack de testes

alembic upgrade head                # aplica as migrações
uvicorn app.main:app --reload --port 3000
```

- API: http://localhost:3000/api · Swagger: http://localhost:3000/docs
- `requirements.txt` traz só as dependências de runtime; `requirements-dev.txt` inclui também o pytest.

### Frontend

```bash
cd frontend
npm install
```

Aponte o proxy para o backend local (o padrão do `.env` usa a rede do Docker). Crie um `frontend/.env.local`:

```
BACKEND_INTERNAL_URL=http://localhost:3000
```

Depois:

```bash
npm run dev
```

Frontend em http://localhost:3000.

## Migrações de banco (Alembic)

Toda mudança de schema é feita **sempre** por uma migração (nunca editando o banco na mão):

```bash
cd backend
alembic revision --autogenerate -m "descricao_da_mudanca"   # gera a migração
alembic upgrade head                                         # aplica
alembic downgrade -1                                         # reverte a última
```

Cada migração precisa de `upgrade` **e** `downgrade` funcionais.

## Testes e qualidade

Rode e mantenha verde antes de finalizar qualquer mudança.

**Backend** (a partir de `backend/`, com a `.venv` ativa):

```bash
pytest                       # suíte completa
pytest --cov=app             # com cobertura (alvo: >=80% em services/)
```

**Frontend** (a partir de `frontend/`):

```bash
npm run test                 # Vitest + Testing Library
npm run build                # valida types + build de produção
```

> `next lint` não está configurado neste projeto — use `npm run build` para validar o frontend.

## Documentação

O diretório [`docs/`](docs/) detalha as regras do jogo e a arquitetura funcional: [regras de negócio](docs/business-rules.md), [competição](docs/competition.md), [simulação de partidas](docs/match-simulation.md), [autenticação](docs/authentication.md), [usuários e times](docs/users-and-teams.md), [jogadores](docs/players.md) e [telas](docs/screens.md).

As regras de desenvolvimento obrigatórias (arquitetura em camadas, i18n, segurança, limites de complexidade, workflow) estão em [`CLAUDE.md`](CLAUDE.md) — leitura obrigatória antes de contribuir.

## Deploy

A infraestrutura AWS (ECS + Terraform) e os scripts de deploy ficam em [`deploy/`](deploy/). Consulte [`deploy/README.md`](deploy/README.md).

## Licença

Veja [LICENSE](LICENSE).
