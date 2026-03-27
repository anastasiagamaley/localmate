# ─────────────────────────────────────────────────────────────────────────────
# LocalMate — AWS Infrastructure (Terraform)
# Services: ECS Fargate + RDS PostgreSQL + ElastiCache Redis + ALB
# Estimated cost: ~$20–30/month after Free Tier expires
# Free Tier covers: RDS t3.micro (12mo), ElastiCache t3.micro (12mo)
# ─────────────────────────────────────────────────────────────────────────────

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment to store state in S3 (recommended for team)
  # backend "s3" {
  #   bucket = "localmate-terraform-state"
  #   key    = "prod/terraform.tfstate"
  #   region = "eu-central-1"
  # }
}

provider "aws" {
  region = var.aws_region
}

# ─── Data ────────────────────────────────────────────────────────────────────

data "aws_availability_zones" "available" {}

locals {
  name   = "localmate"
  env    = var.environment
  prefix = "${local.name}-${local.env}"

  # All 8 microservices with their ports
  services = {
    gateway  = { port = 8000, cpu = 256, memory = 512, count = 2 }
    auth     = { port = 8001, cpu = 256, memory = 512, count = 2 }
    users    = { port = 8002, cpu = 256, memory = 512, count = 2 }
    search   = { port = 8003, cpu = 512, memory = 1024, count = 2 }
    tokens   = { port = 8004, cpu = 256, memory = 512, count = 2 }
    vendors  = { port = 8005, cpu = 256, memory = 512, count = 1 }
    worker   = { port = 0,    cpu = 256, memory = 512, count = 1 }
    frontend = { port = 3000, cpu = 256, memory = 512, count = 2 }
  }
}

# ─── VPC ─────────────────────────────────────────────────────────────────────

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = { Name = "${local.prefix}-vpc" }
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  tags = { Name = "${local.prefix}-public-${count.index}" }
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  tags = { Name = "${local.prefix}-private-${count.index}" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${local.prefix}-igw" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  tags = { Name = "${local.prefix}-rt-public" }
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# ─── Security Groups ──────────────────────────────────────────────────────────

resource "aws_security_group" "alb" {
  name   = "${local.prefix}-alb-sg"
  vpc_id = aws_vpc.main.id
  ingress { from_port = 80;  to_port = 80;  protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"] }
  ingress { from_port = 443; to_port = 443; protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"] }
  egress  { from_port = 0;   to_port = 0;   protocol = "-1";  cidr_blocks = ["0.0.0.0/0"] }
}

resource "aws_security_group" "ecs" {
  name   = "${local.prefix}-ecs-sg"
  vpc_id = aws_vpc.main.id
  ingress {
    from_port       = 0
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  # Allow services to talk to each other
  ingress {
    from_port = 0
    to_port   = 65535
    protocol  = "tcp"
    self      = true
  }
  egress { from_port = 0; to_port = 0; protocol = "-1"; cidr_blocks = ["0.0.0.0/0"] }
}

resource "aws_security_group" "rds" {
  name   = "${local.prefix}-rds-sg"
  vpc_id = aws_vpc.main.id
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }
}

resource "aws_security_group" "redis" {
  name   = "${local.prefix}-redis-sg"
  vpc_id = aws_vpc.main.id
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }
}

# ─── RDS PostgreSQL ───────────────────────────────────────────────────────────

resource "aws_db_subnet_group" "main" {
  name       = "${local.prefix}-db-subnet"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_db_instance" "postgres" {
  identifier        = "${local.prefix}-postgres"
  engine            = "postgres"
  engine_version    = "16.3"
  instance_class    = "db.t3.micro"   # Free Tier eligible (12 months)
  allocated_storage = 20
  storage_type      = "gp2"

  db_name  = "localmate"
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false
  skip_final_snapshot    = var.environment != "prod"

  tags = { Name = "${local.prefix}-postgres" }
}

# ─── ElastiCache Redis ────────────────────────────────────────────────────────

resource "aws_elasticache_subnet_group" "main" {
  name       = "${local.prefix}-redis-subnet"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${local.prefix}-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"   # Free Tier eligible (12 months)
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.redis.id]

  tags = { Name = "${local.prefix}-redis" }
}

# ─── ECR Repositories ────────────────────────────────────────────────────────

resource "aws_ecr_repository" "services" {
  for_each = local.services
  name     = "${local.prefix}-${each.key}"

  image_scanning_configuration { scan_on_push = true }
  tags = { Name = "${local.prefix}-${each.key}" }
}

# ─── ECS Cluster ─────────────────────────────────────────────────────────────

resource "aws_ecs_cluster" "main" {
  name = "${local.prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# ─── ALB ─────────────────────────────────────────────────────────────────────

resource "aws_lb" "main" {
  name               = "${local.prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
}

resource "aws_lb_target_group" "gateway" {
  name        = "${local.prefix}-gateway-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
  }
}

resource "aws_lb_target_group" "frontend" {
  name        = "${local.prefix}-frontend-tg"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path     = "/"
    interval = 30
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}

resource "aws_lb_listener_rule" "api" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.gateway.arn
  }

  condition {
    path_pattern { values = ["/api/*", "/auth/*", "/users/*", "/search/*", "/tokens/*", "/vendors/*"] }
  }
}

# ─── IAM for ECS ─────────────────────────────────────────────────────────────

resource "aws_iam_role" "ecs_task_execution" {
  name = "${local.prefix}-ecs-execution-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ─── CloudWatch Log Groups ────────────────────────────────────────────────────

resource "aws_cloudwatch_log_group" "services" {
  for_each          = local.services
  name              = "/ecs/${local.prefix}/${each.key}"
  retention_in_days = 7
}
