# Variables
PYTHON := python3
PIP := pip
VENV := .venv
VENV_BIN := $(VENV)/bin
PYTHON_VENV := $(VENV_BIN)/python

# Frontend variables
FRONTEND_DIR := frontend
NPM := npm

# Colors for output
BLUE := \033[36m
RESET := \033[0m

.PHONY: help install install-be install-fe dev dev-be dev-fe check check-be check-fe docker-dev docker-dev-up docker-dev-down docker-dev-build docker-prod docker-prod-up docker-prod-down docker-prod-build db-index clean

help: ## Show this help message
	@echo "$(BLUE)MyPage48 Project Management Commands:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2}'

## --- Setup ---

install: install-be install-fe ## Install all dependencies

install-be: ## Install backend dependencies
	@echo "$(BLUE)Installing backend dependencies...$(RESET)"
	$(PYTHON) -m venv $(VENV)
	$(VENV_BIN)/$(PIP) install -r requirements/base.txt -r requirements/dev.txt

install-fe: ## Install frontend dependencies
	@echo "$(BLUE)Installing frontend dependencies...$(RESET)"
	cd $(FRONTEND_DIR) && $(NPM) install

## --- Development ---

dev: ## Run both backend and frontend in development mode
	@echo "$(BLUE)Starting backend and frontend...$(RESET)"
	./scripts/start-all-dev.sh

dev-be: ## Run only backend in development mode
	@echo "$(BLUE)Starting backend...$(RESET)"
	./scripts/start-dev.sh

dev-fe: ## Run only frontend in development mode
	@echo "$(BLUE)Starting frontend...$(RESET)"
	cd $(FRONTEND_DIR) && $(NPM) run dev

## --- Database ---

db-index: ## Create MongoDB indexes
	@echo "$(BLUE)Creating database indexes...$(RESET)"
	$(PYTHON_VENV) scripts/create_indexes.py

## --- Quality Control ---

check: check-be check-fe ## Run all quality checks (backend and frontend)

check-be: ## Run backend linting, formatting, and tests
	@echo "$(BLUE)Running backend quality checks...$(RESET)"
	./scripts/lint-format.sh
	$(VENV_BIN)/pytest

check-fe: ## Run frontend type-check, format, and lint
	@echo "$(BLUE)Running frontend quality checks...$(RESET)"
	cd $(FRONTEND_DIR) && $(NPM) run check && $(NPM) run format && $(NPM) run lint

## --- Docker ---

docker-dev: ## Build and start development docker containers
	@echo "$(BLUE)Building and starting development docker containers...$(RESET)"
	docker compose -f docker-compose.yml up -d --build

docker-dev-up: ## Start development docker containers (no build)
	@echo "$(BLUE)Starting development docker containers...$(RESET)"
	docker compose -f docker-compose.yml up -d

docker-dev-down: ## Stop development docker containers
	@echo "$(BLUE)Stopping development docker containers...$(RESET)"
	docker compose -f docker-compose.yml down

docker-dev-build: ## Build development docker containers
	@echo "$(BLUE)Building development docker containers...$(RESET)"
	docker compose -f docker-compose.yml build

## --- Docker Production ---

docker-prod: ## Build and start production docker containers
	@echo "$(BLUE)Building and starting production docker containers...$(RESET)"
	docker compose -f docker-compose.prod.yml up -d --build

docker-prod-up: ## Start production docker containers (no build)
	@echo "$(BLUE)Starting production docker containers...$(RESET)"
	docker compose -f docker-compose.prod.yml up -d

docker-prod-down: ## Stop production docker containers
	@echo "$(BLUE)Stopping production docker containers...$(RESET)"
	docker compose -f docker-compose.prod.yml down

docker-prod-build: ## Build production docker containers
	@echo "$(BLUE)Building production docker containers...$(RESET)"
	docker compose -f docker-compose.prod.yml build

## --- Cleanup ---

clean: ## Clean up temporary files, caches, and environments
	@echo "$(BLUE)Cleaning up...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".svelte-kit" -exec rm -rf {} +
	find . -type d -name "node_modules" -exec rm -rf {} +
	rm -rf $(VENV)
	@echo "Cleanup complete."
