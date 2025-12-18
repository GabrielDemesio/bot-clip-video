.PHONY: help build run stop clean logs shell setup test lint format

# Variables
IMAGE_NAME := video-lesson-splitter
CONTAINER_NAME := video-lesson-splitter
DOCKER_COMPOSE := docker-compose

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Video Lesson Splitter - Makefile Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

setup: ## Create necessary directories
	@echo "$(BLUE)Setting up directories...$(NC)"
	@mkdir -p videos_input lessons_output logs
	@chmod -R 755 videos_input lessons_output logs
	@echo "$(GREEN)✓ Directories created$(NC)"
	@echo "$(YELLOW)Add your videos to: videos_input/$(NC)"

build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	@$(DOCKER_COMPOSE) build
	@echo "$(GREEN)✓ Build completed!$(NC)"

run: ## Run the application (interactive)
	@echo "$(BLUE)Starting Video Lesson Splitter...$(NC)"
	@if [ -z "$$(ls -A videos_input 2>/dev/null)" ]; then \
		echo "$(YELLOW)⚠ No videos found in videos_input/$(NC)"; \
		echo "$(YELLOW)Please add your videos first$(NC)"; \
		exit 1; \
	fi
	@$(DOCKER_COMPOSE) run --rm $(CONTAINER_NAME)

up: ## Run in background
	@echo "$(BLUE)Starting in background...$(NC)"
	@$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✓ Container started$(NC)"
	@echo "$(YELLOW)View logs with: make logs$(NC)"

down: stop ## Alias for stop

stop: ## Stop containers
	@echo "$(BLUE)Stopping containers...$(NC)"
	@$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✓ Containers stopped$(NC)"

restart: stop up ## Restart containers

logs: ## View logs
	@$(DOCKER_COMPOSE) logs -f --tail=100

shell: ## Open shell in container
	@echo "$(BLUE)Opening shell in container...$(NC)"
	@$(DOCKER_COMPOSE) run --rm $(CONTAINER_NAME) /bin/bash

stats: ## Show container resource usage
	@docker stats $(CONTAINER_NAME)

clean: ## Remove containers and volumes
	@echo "$(YELLOW)⚠ This will remove all containers and volumes$(NC)"
	@read -p "Are you sure? (y/N) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(BLUE)Cleaning up...$(NC)"; \
		$(DOCKER_COMPOSE) down -v; \
		echo "$(GREEN)✓ Cleanup completed$(NC)"; \
	else \
		echo "$(YELLOW)Cleanup cancelled$(NC)"; \
	fi

clean-all: ## Remove everything (containers, volumes, images)
	@echo "$(RED)⚠ This will remove EVERYTHING (containers, volumes, images)$(NC)"
	@read -p "Are you sure? (y/N) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(BLUE)Cleaning up...$(NC)"; \
		$(DOCKER_COMPOSE) down -v --rmi all; \
		echo "$(GREEN)✓ Full cleanup completed$(NC)"; \
	else \
		echo "$(YELLOW)Cleanup cancelled$(NC)"; \
	fi

test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	@$(DOCKER_COMPOSE) run --rm $(CONTAINER_NAME) python -m pytest tests/ -v

test-cov: ## Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	@$(DOCKER_COMPOSE) run --rm $(CONTAINER_NAME) python -m pytest tests/ -v --cov=app --cov-report=html

lint: ## Run linter
	@echo "$(BLUE)Running linter...$(NC)"
	@$(DOCKER_COMPOSE) run --rm $(CONTAINER_NAME) python -m flake8 app/

format: ## Format code with black
	@echo "$(BLUE)Formatting code...$(NC)"
	@$(DOCKER_COMPOSE) run --rm $(CONTAINER_NAME) python -m black app/ tests/

check: lint test ## Run linter and tests

rebuild: clean-all build ## Clean everything and rebuild

# Local development (without Docker)
dev-setup: ## Setup local development environment
	@echo "$(BLUE)Setting up local development environment...$(NC)"
	@python -m venv .venv
	@.venv/bin/pip install --upgrade pip
	@.venv/bin/pip install -r requirements.txt
	@echo "$(GREEN)✓ Virtual environment created$(NC)"
	@echo "$(YELLOW)Activate with: source .venv/bin/activate$(NC)"

dev-run: ## Run locally (without Docker)
	@echo "$(BLUE)Running locally...$(NC)"
	@venv/bin/python3 main.py

dev-s3-sync: ## Run interactive S3 sync locally
	@echo "$(BLUE)Starting interactive S3 sync...$(NC)"
	@venv/bin/python3 -m app.cli.s3_sync_cli

dev-test: ## Run tests locally
	@echo "$(BLUE)Running tests locally...$(NC)"
	@venv/bin/python3 -m pytest tests/ -v

venv-run: ## Run with venv python
	@venv/bin/python3 main.py

# Docker Hub
docker-login: ## Login to Docker Hub
	@docker login

docker-push: ## Push image to Docker Hub
	@echo "$(BLUE)Pushing image to Docker Hub...$(NC)"
	@docker tag $(IMAGE_NAME):latest $(DOCKER_USERNAME)/$(IMAGE_NAME):latest
	@docker push $(DOCKER_USERNAME)/$(IMAGE_NAME):latest
	@echo "$(GREEN)✓ Image pushed$(NC)"

docker-pull: ## Pull image from Docker Hub
	@echo "$(BLUE)Pulling image from Docker Hub...$(NC)"
	@docker pull $(DOCKER_USERNAME)/$(IMAGE_NAME):latest
	@echo "$(GREEN)✓ Image pulled$(NC)"

# Info
info: ## Show project information
	@echo "$(BLUE)Project Information$(NC)"
	@echo "  Image Name:      $(IMAGE_NAME)"
	@echo "  Container Name:  $(CONTAINER_NAME)"
	@echo "  Docker Compose:  $(DOCKER_COMPOSE)"
	@echo ""
	@echo "$(BLUE)Directories$(NC)"
	@echo "  Videos Input:    videos_input/"
	@echo "  Lessons Output:  lessons_output/"
	@echo "  Logs:            logs/"
	@echo ""
	@echo "$(BLUE)Docker Status$(NC)"
	@docker images | grep $(IMAGE_NAME) || echo "  No images found"
	@docker ps -a | grep $(CONTAINER_NAME) || echo "  No containers found"

version: ## Show version
	@echo "Video Lesson Splitter v1.0.0"

# Default target
.DEFAULT_GOAL := help
