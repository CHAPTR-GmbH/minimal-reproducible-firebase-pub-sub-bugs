PROJECT_ID?=dummy-project
REGION?=europe-west4
install: ## Make requirements file
	@poetry install --with dev
	@poetry export --without-hashes --with dev --format=requirements.txt > requirements.txt

test: ## Run tests
	poetry shell
	@echo Run tests
	python -m pytest app/tests

.PHONY: requirements test
