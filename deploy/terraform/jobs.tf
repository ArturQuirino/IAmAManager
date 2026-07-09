# Scheduled batch jobs (Pattern A): EventBridge Scheduler -> ECS RunTask.
#
# Each job runs the *backend image* with a different entrypoint, sharing the
# same code, database access and secrets. A job is a one-off Fargate task: it
# starts, calls a service, and exits. No long-running process, no public
# endpoint to trigger it. EventBridge Scheduler fires it on a cron and retries
# on failure.
#
# NOTE: the container commands below expect the modules `app.jobs.run_matches`
# and `app.jobs.rotate_players` to exist in the backend. Until they are
# implemented the schedules will fire but the tasks will exit non-zero.

locals {
  jobs = {
    daily-matches = {
      command     = ["python", "-m", "app.jobs.run_matches"]
      schedule    = "cron(0 3 * * ? *)"   # every day at 03:00 (var.jobs_timezone)
      description = "Simulate the scheduled matches for the day"
    }
    weekly-player-rotation = {
      command     = ["python", "-m", "app.jobs.rotate_players"]
      schedule    = "cron(0 4 ? * MON *)" # every Monday at 04:00 (var.jobs_timezone)
      description = "Rotate the youth-base players for the week"
    }
  }
}

resource "aws_cloudwatch_log_group" "jobs" {
  name              = "/ecs/${local.name_prefix}-jobs"
  retention_in_days = 14
}

resource "aws_ecs_task_definition" "jobs" {
  for_each = local.jobs

  family                   = "${local.name_prefix}-job-${each.key}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.fargate_cpu
  memory                   = var.fargate_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name    = "job"
    image   = "${aws_ecr_repository.backend.repository_url}:${var.image_tag}"
    command = each.value.command

    environment = [
      { name = "POSTGRES_HOST", value = aws_db_instance.main.address },
      { name = "POSTGRES_PORT", value = "5432" },
      { name = "POSTGRES_DB", value = var.db_name },
      { name = "POSTGRES_USER", value = var.db_username },
    ]

    secrets = [{
      name      = "POSTGRES_PASSWORD"
      valueFrom = aws_secretsmanager_secret.db_password.arn
    }]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.jobs.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = each.key
      }
    }

    essential = true
  }])
}

# Role assumed by EventBridge Scheduler to launch the job tasks.
resource "aws_iam_role" "scheduler" {
  name = "${local.name_prefix}-scheduler"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "scheduler.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "scheduler_run_task" {
  name = "${local.name_prefix}-scheduler-run-task"
  role = aws_iam_role.scheduler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "ecs:RunTask"
        Resource = [for job in aws_ecs_task_definition.jobs : "${job.arn_without_revision}:*"]
        Condition = {
          ArnLike = { "ecs:cluster" = aws_ecs_cluster.main.arn }
        }
      },
      {
        Effect   = "Allow"
        Action   = "iam:PassRole"
        Resource = [aws_iam_role.ecs_execution.arn, aws_iam_role.ecs_task.arn]
        Condition = {
          StringEquals = { "iam:PassedToService" = "ecs-tasks.amazonaws.com" }
        }
      }
    ]
  })
}

resource "aws_scheduler_schedule" "jobs" {
  for_each = local.jobs

  name        = "${local.name_prefix}-${each.key}"
  description = each.value.description
  group_name  = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression          = each.value.schedule
  schedule_expression_timezone = var.jobs_timezone

  target {
    arn      = aws_ecs_cluster.main.arn
    role_arn = aws_iam_role.scheduler.arn

    ecs_parameters {
      task_definition_arn = aws_ecs_task_definition.jobs[each.key].arn
      launch_type         = "FARGATE"
      platform_version    = "LATEST"
      task_count          = 1

      # Public subnet + public IP so the task can pull the image from ECR and
      # read secrets, mirroring the long-running services. The ECS security
      # group already allows egress to RDS.
      network_configuration {
        subnets          = aws_subnet.public[*].id
        security_groups  = [aws_security_group.ecs.id]
        assign_public_ip = true
      }
    }

    retry_policy {
      maximum_retry_attempts = 2
    }
  }
}
