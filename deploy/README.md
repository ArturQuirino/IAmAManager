# Arquitetura alvo — deploy AWS

Este documento registra a **arquitetura alvo** do I Am a Manager na AWS. É a
referência para o que o Terraform em `deploy/terraform/` provisiona e para
onde a infraestrutura deve evoluir. É um projeto pessoal, tráfego baixo: o
objetivo é uma arquitetura **coerente e barata**, não altamente escalável.

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

Tudo roda numa VPC única com duas AZs. Frontend e backend são serviços
Fargate independentes atrás de um Application Load Balancer, que faz o
roteamento por path e termina o TLS. O banco é um RDS PostgreSQL em subnet
privada. As rotinas periódicas (jogos diários, rotação semanal de jogadores)
são tarefas Fargate avulsas disparadas pelo EventBridge Scheduler.

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
| Jobs agendados | EventBridge Scheduler + ECS RunTask | `jobs.tf` | Rotinas periódicas (ver abaixo) |
| Observabilidade | CloudWatch Logs | `ecs.tf`, `jobs.tf` | Logs dos containers (retenção 14 dias) |

## Caminho da requisição

1. O usuário acessa o DNS do ALB (ou um domínio apontado para ele).
2. O ALB encaminha `/api/*` para o target group do backend e todo o resto
   para o frontend (`aws_lb_listener_rule.api`).
3. O backend fala com o RDS pela subnet privada (security group `rds` só
   aceita `5432` vindo do security group `ecs`).
4. Senha do banco e `JWT_SECRET` chegam ao container via Secrets Manager,
   nunca em variável de ambiente em texto plano no Terraform.

## Jobs agendados (Padrão A)

Padrão escolhido: **EventBridge Scheduler → ECS RunTask**, definido em
`jobs.tf`. Cada job roda a **mesma imagem do backend** com um entrypoint
diferente, reaproveitando código, acesso ao banco e segredos:

| Job | Comando | Cron (`jobs_timezone`) |
|---|---|---|
| `daily-matches` | `python -m app.jobs.run_matches` | todo dia 03:00 |
| `weekly-player-rotation` | `python -m app.jobs.rotate_players` | segunda 04:00 |

Por que este padrão:

- **Sem duplicação:** reusa a imagem, os services e o acesso ao RDS. O job
  chama um service (respeita a separação de camadas do `CLAUDE.md` §2.1).
- **Sem superfície nova:** nenhum endpoint HTTP público para disparar rotina.
- **Custo por execução:** a task sobe, executa e morre — paga só os segundos.
- **Resiliência:** o EventBridge Scheduler tem retry nativo (`retry_policy`).

Os crons são avaliados no timezone de `var.jobs_timezone` (padrão
`America/Sao_Paulo`).

> **Dependência de código:** os módulos `app/jobs/run_matches.py` e
> `app/jobs/rotate_players.py` ainda precisam ser implementados no backend.
> Enquanto não existirem, as schedules disparam mas as tasks terminam com erro.

## Como aplicar

```bash
cd deploy/terraform
cp terraform.tfvars.example terraform.tfvars   # ajuste as variáveis
terraform init
terraform plan
terraform apply
```

O build e push das imagens fica em `deploy/scripts/build-and-push.sh`. As
migrations do banco rodam automaticamente no boot do container do backend
(`alembic upgrade head` no `CMD` do `Dockerfile.prod`).

## Pendências conhecidas para "produção de verdade"

Itens fora do provisionamento atual, listados para não serem esquecidos:

- **HTTPS/domínio:** o listener 443 só existe se `certificate_arn` for
  informado. Falta registrar domínio, emitir certificado no ACM e apontar um
  registro (Route53) para o ALB. Sem TLS, o token no `localStorage` trafega em
  texto claro.
- **Migrations no boot:** hoje cada task do backend roda `alembic upgrade head`
  ao subir. Funciona com uma réplica; se algum dia `desired_count > 1`, duas
  tasks correm migration ao mesmo tempo (race). Aceitável no volume atual.
- **Sem NAT gateway (proposital):** as tasks ECS ficam em subnet pública com IP
  público para alcançar ECR e Secrets Manager pela internet gateway. Não mover
  para subnet privada sem antes provisionar um NAT (~US$ 32/mês).

## Variável de ambiente do backend: `APP_ENV`

O backend lê `APP_ENV` (`Settings.app_env`) para decidir seed e modo produção
(`should_seed`, `is_production`). Antes chamava-se `NODE_ENV`, herança de um
template Node; foi renomeada para `APP_ENV` em todo o stack (`settings.py`,
`ecs.tf`, `docker-compose*.yml`, `.env.example`). O `NODE_ENV` que permanece é
apenas o do container do **frontend** (Next.js), onde é legítimo.

## Custo aproximado (24/7, menor porte)

RDS `t4g.micro` (~US$ 12–15) + 2 tasks Fargate 0.25 vCPU/0.5 GB (~US$ 18) +
ALB (~US$ 16) + jobs (centavos) ≈ **US$ 45–55/mês**.
