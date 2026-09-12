# Arquitetura & deploy — I Am a Manager

Este documento registra as **duas arquiteturas alvo** do projeto, em dois tiers:

- **Tier portfólio (atual, ≈ $0/mês):** PaaS free tiers que escalam a zero.
  É a arquitetura recomendada hoje — projeto pessoal, sem monetização, usado
  como portfólio, com pouquíssimos usuários e que pode ficar ocioso.
- **Tier scale-up (AWS):** ECS Fargate + ALB + RDS, provisionado por Terraform
  em `deploy/terraform/`. É o alvo **quando o produto começar a se pagar** —
  robusto, mas custa ~US$ 45–55/mês rodando 24/7. Não é o ativo hoje.

Os dois tiers rodam o **mesmo código** sem mudanças: o frontend faz proxy
same-origin de `/api/*` (ver `frontend/next.config.js`) e o backend é um
container stateless que honra `$PORT`.

---

# Tier portfólio — Cloud Run + Vercel + Neon (≈ $0/mês)

## Visão geral

```
Usuários ──HTTPS──> Vercel (Next.js) ──/api/* (rewrite)──> Cloud Run (FastAPI, escala a zero)
                                                                  │
                                                                  ▼
                                                          Neon (Postgres serverless)
                                                                  ▲
Cloud Scheduler ──cron──> Cloud Run Job (imagem do backend) ──────┘
```

## Componentes

| Camada | Serviço | Papel |
|---|---|---|
| Frontend | **Vercel** (Hobby, grátis) | Next.js nativo; env `BACKEND_INTERNAL_URL` → URL do Cloud Run. O `rewrites()` mantém tudo same-origin (`/api`), sem CORS |
| Backend | **Google Cloud Run** (escala a zero) | Reusa `backend/Dockerfile.prod`; paga por request (~$0 no volume); cold start ~1–3s |
| Banco | **Neon** (Postgres serverless, grátis) | Autosuspende quando ocioso e resume ao conectar — ideal para "fica dias sem acesso" |
| Jobs | **Scheduler interno (atual)** / Cloud Scheduler → Cloud Run Job (alvo) | O backend já possui um scheduler diário em processo; o job externo ainda requer um entrypoint próprio |
| Migrations | **Cloud Run Job** (`alembic upgrade head`) | Passo separado no deploy (não a cada cold start) |
| Segredos | **GCP Secret Manager** (ou envs) | `JWT_SECRET`, connection string do Neon |

## Caminho da requisição

1. O browser chama `/api/...` **same-origin** no domínio da Vercel.
2. O `rewrites()` do Next (`frontend/next.config.js`) faz proxy para
   `${BACKEND_INTERNAL_URL}/api/...` → serviço do Cloud Run. **Sem CORS**, e o
   token em `localStorage` continua funcionando.
3. O Cloud Run (acorda se estiver ocioso) fala com o Neon pela connection string.

## Deploy (alto nível)

Feito por console/`gcloud` + Vercel (opcionalmente Terraform GCP no futuro):

1. **Neon:** criar projeto, pegar a connection string, rodar as migrations
   (`alembic upgrade head`) uma vez e o seed manualmente se quiser dados.
2. **Backend (Cloud Run):** build da imagem via `backend/Dockerfile.prod`, push
   para o Artifact Registry, deploy com envs `APP_ENV=production`,
   `RUN_SEED=false`, `JWT_SECRET`, `POSTGRES_*`/URL do Neon. Sobrescrever o
   comando do **serviço** para só `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   (sem alembic no hot path).
3. **Migrations:** criar um **Cloud Run Job** com comando `alembic upgrade head`
   e executá-lo a cada deploy que tenha migration nova.
4. **Frontend (Vercel):** importar o repo (`frontend/`), setar
   `BACKEND_INTERNAL_URL` = URL do serviço Cloud Run.
5. **Ciclo diário:** no estado atual, habilitar `SCHEDULER_ENABLED=true` no
   serviço faz o backend executar o ciclo de partidas diariamente no horário de
   `MATCHDAY_HOUR`/`MATCHDAY_MINUTE`. Em uma plataforma que escala a zero, essa
   estratégia não garante a execução; antes do deploy definitivo, crie um
   entrypoint de job que invoque `MatchdayService.run_due_matchday()` e agende-o
   no Cloud Scheduler.

## Custo

**≈ $0/mês** dentro dos free tiers (Vercel Hobby, Cloud Run scale-to-zero, Neon
free). Alternativa de jobs 100% grátis e sem GCP extra: `.github/workflows/`
com `cron` + `workflow_dispatch` rodando `python -m app.jobs.*` contra o Neon.

---

# Tier scale-up — AWS (ECS Fargate + ALB + RDS)

Provisionado por Terraform em `deploy/terraform/`. Alvo para quando o uso
crescer e justificar custo fixo em troca de robustez.

## Visão geral

```
Usuários ──HTTPS──> ALB ──/api/*──> Backend (Fargate, FastAPI)
                     │                      │
                     └──resto────> Frontend │
                                  (Fargate)  │
                                             ▼
                                      RDS PostgreSQL (subnet privada)
                                             ▲
EventBridge Scheduler ──cron──> Job (ECS RunTask, imagem do backend)
```

## Componentes

| Componente | Recurso AWS | Arquivo Terraform | Papel |
|---|---|---|---|
| Rede | VPC, subnets pública/privada, IGW | `vpc.tf` | Isolamento; ECS na pública, RDS na privada |
| Entrada | Application Load Balancer | `alb.tf` | URL única, TLS, roteamento `/api/*` → backend |
| Frontend | ECS Service (Fargate) | `ecs.tf` | Next.js, porta 3000 |
| Backend | ECS Service (Fargate) | `ecs.tf` | FastAPI, porta 3000 |
| Banco | RDS PostgreSQL | `rds.tf` | Persistência; `publicly_accessible = false` |
| Imagens | ECR | `ecr.tf` | Registries de frontend e backend |
| Segredos | Secrets Manager | `secrets.tf` | `JWT_SECRET`, senha do banco |
| Jobs agendados | EventBridge Scheduler + ECS RunTask | `jobs.tf` | Rotinas periódicas |
| Observabilidade | CloudWatch Logs | `ecs.tf`, `jobs.tf` | Logs dos containers (retenção 14 dias) |

## Jobs agendados (Padrão A, ainda incompleto)

**EventBridge Scheduler → ECS RunTask** (`jobs.tf`). A infraestrutura está
declarada, mas os módulos configurados como entrypoint ainda não existem. Cada job roda a mesma
imagem do backend com um entrypoint diferente, reusando código, acesso ao banco
e segredos, sem expor endpoint. Crons no timezone de `var.jobs_timezone`.

| Job | Comando | Cron |
|---|---|---|
| `daily-matches` | `python -m app.jobs.run_matches` | todo dia 03:00 |
| `weekly-player-rotation` | `python -m app.jobs.rotate_players` | segunda 04:00 |

## Como aplicar

```bash
cd deploy/terraform
cp terraform.tfvars.example terraform.tfvars   # ajuste as variáveis
terraform init
terraform plan
terraform apply
```

Build/push das imagens em `deploy/scripts/build-and-push.sh`. As migrations
rodam no boot do container do backend (`alembic upgrade head` no `CMD`).

## Pendências para "produção de verdade" (AWS)

- **HTTPS/domínio:** o listener 443 só existe se `certificate_arn` for
  informado. Falta domínio + certificado ACM + registro (Route53) para o ALB.
- **Migrations no boot:** cada task roda `alembic upgrade head` ao subir; com
  `desired_count > 1` haveria corrida. Aceitável no volume atual.
- **Sem NAT gateway (proposital):** tasks ECS ficam em subnet pública com IP
  público para alcançar ECR/Secrets pela IGW. Não mover para subnet privada sem
  antes provisionar um NAT (~US$ 32/mês).

## Custo (24/7, menor porte)

RDS `t4g.micro` (~US$ 12–15) + 2 tasks Fargate 0.25 vCPU/0.5 GB (~US$ 18) +
ALB (~US$ 16) + jobs (centavos) ≈ **US$ 45–55/mês**.

---

# Notas compartilhadas pelos dois tiers

## Variável de ambiente do backend: `APP_ENV`

O backend lê `APP_ENV` (`Settings.app_env`) para decidir seed e modo produção
(`should_seed`, `is_production`). Antes chamava-se `NODE_ENV`, herança de um
template Node; foi renomeada para `APP_ENV` em todo o stack. O `NODE_ENV` que
permanece é apenas o do container do **frontend** (Next.js), onde é legítimo.

## Estado das rotinas periódicas

A lógica de jogo está implementada: `MatchdayService` simula a próxima rodada
de todas as divisões, conclui e renova temporadas quando necessário e atualiza
a base a cada sete dias de jogo. O processamento é idempotente por data através
do `GameClock`. O backend também oferece um scheduler interno configurável e,
somente em desenvolvimento, `POST /api/dev/run-matchday` para disparo manual.

A pendência está na integração dos jobs externos: `jobs.tf` ainda aponta para
`app.jobs.run_matches` e `app.jobs.rotate_players`, módulos que não existem.
Além disso, a lógica atual concentra partidas e rotação da base em um único
ciclo diário, enquanto o Terraform ainda descreve dois jobs separados. Antes
de ativar os schedules de Cloud Run ou EventBridge, é preciso escolher um único
modelo e criar o(s) entrypoint(s) fino(s) correspondente(s). Até lá:

- ambientes com processo permanentemente ativo podem usar
  `SCHEDULER_ENABLED=true`;
- ambientes que escalam a zero não devem depender do scheduler interno;
- os schedules do Terraform AWS não devem ser ativados, pois as tasks encerram
  com erro ao tentar importar os módulos ausentes.

## Migração portfólio → scale-up

Quando o uso justificar: aplicar o Terraform em `deploy/terraform/`, migrar os
dados do Neon para o RDS (`pg_dump`/`pg_restore`), apontar o frontend para o ALB
(ou manter a Vercel só como CDN do frontend) e desativar os recursos do Cloud
Run. O código não muda — só a infraestrutura.
