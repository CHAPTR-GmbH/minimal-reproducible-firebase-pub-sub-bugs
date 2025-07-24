
#####################################################################################
################   THIS FILE IS THE MAIN HANDLE FOR ALL THE COMMANDS   ##############
#####################################################################################

## Check if all executables are available
EXECUTABLES = gcloud grep awk printf pnpm pip pipx java terraform terragrunt pre-commit
EXECUTABLES = gcloud grep awk printf
K := $(foreach exec,$(EXECUTABLES),\
        $(if $(shell which $(exec)),some string,$(error "No $(exec) in PATH")))



############################# 	 	   HELPERS 		   #############################
# Help
define print_help_for
	grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(1) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36mmake %-20s\033[0m%s\n", $$1, $$2}'
endef

help: ## show help
	@printf "\033[36mhelp: \033[0m\n"
	@$(foreach make,$(MAKEFILE_LIST),$(call print_help_for,$(make));)
	@printf "\n"


test:
	# Python tests
	docker exec -i minimal-reproducible-firebase-pub-sub-bugs-firebase-1 bash -c '\
		cd /home/node/functions/python/ && \
		source ./venv/bin/activate && \
		export FIRESTORE_EMULATOR_HOST="localhost:8080" && \
		export STORAGE_EMULATOR_HOST="http://127.0.0.1:9199" && \
		export PUBSUB_EMULATOR_HOST="localhost:8085" && \
		export GCLOUD_PROJECT="demo-local-development" && \
        export CLOUD_TASKS_EMULATOR_HOST="localhost:9499" && \
		export FIREBASE_AUTH_EMULATOR_HOST="localhost:9099" && \
		python3.12 -m pytest "app/tests" \
		 $(PYTEST_ARGS) \
		 --junitxml=coveragejunit.xml \
		 --cov-report=xml:coverage.xml \
		 --cov=app'

	# Copy coverage to host to be used by github actions reporting
	docker cp minimal-reproducible-firebase-pub-sub-bugs-firebase-1:/home/node/functions/python/coveragejunit.xml ./functions/python
	docker cp minimal-reproducible-firebase-pub-sub-bugs-firebase-1:/home/node/functions/python/coverage.xml ./functions/python

############################# 	 	   COMPOSE 		   #############################
## Copy google cloud credentials from host to repo so we can use it in images
## Linux, macOS: $HOME/.config/gcloud/application_default_credentials.json
## Windows: %APPDATA%\gcloud\application_default_credentials.json


compose: ## Run docker compose
	@echo "Lifting docker compose services"
	@if [ "$$(uname -s)" = "Darwin" ]; then \
		echo "Detected macOS, setting PLATFORM=Mac"; \
		PLATFORM=Mac docker compose up --remove-orphans; \
	elif [ "$$(uname -s)" = "Linux" ]; then \
		echo "Detected Linux, setting PLATFORM=Linux"; \
		PLATFORM=Linux docker compose up --remove-orphans; \
	else \
		echo "Unknown platform, defaulting to Linux"; \
		PLATFORM=Linux docker compose up --remove-orphans; \
	fi

.PHONY: help test compose