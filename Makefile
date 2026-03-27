SHELL=/bin/bash -o pipefail
BUILD_PRINT = \e[1;34mSTEP:
END_BUILD_PRINT = \e[0m

CURRENT_UID := $(shell id -u)
export CURRENT_UID
# These are constants used for make targets so we can start prod and staging services on the same machine
ENV_FILE := .env

# include .env files if they exist
-include .env

install: install-poetry
	@ echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Installing MSSDK requirements$(END_BUILD_PRINT)"
	@ poetry install --all-groups
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) MSSDK requirements are installed$(END_BUILD_PRINT)"

lock:
	@ echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Locking MSSDK dependencies$(END_BUILD_PRINT)"
	@ poetry lock
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) MSSDK dependencies are locked$(END_BUILD_PRINT)"
install-poetry:
	@ echo -e "$(BUILD_PRINT)$(ICON_PROGRESS) Installing Poetry for MSSDK$(END_BUILD_PRINT)"
	@ pip install "poetry==2.0.1"
	@ echo -e "$(BUILD_PRINT)$(ICON_DONE) Poetry for MSSDK is installed$(END_BUILD_PRINT)"

build-externals:
	@ echo -e "$(BUILD_PRINT)Creating the necessary volumes, networks and folders and setting the special rights"
	@ docker network create proxy-net || true
	@ docker network create common-ext-${ENVIRONMENT} || true

start-traefik: build-externals
	@ echo -e "$(BUILD_PRINT)Starting the Traefik services $(END_BUILD_PRINT)"
	@ docker-compose -p common --file ./infra/traefik/docker-compose.yml --env-file ${ENV_FILE} up -d

stop-traefik:
	@ echo -e "$(BUILD_PRINT)Stopping the Traefik services $(END_BUILD_PRINT)"
	@ docker-compose -p common --file ./infra/traefik/docker-compose.yml --env-file ${ENV_FILE} down


start-jupyter:
	@ echo -e "$(BUILD_PRINT)Starting the jupyter services $(END_BUILD_PRINT)"
	@ docker-compose -p common --file ./infra/jupyter_notebook/docker-compose.yml --env-file ${ENV_FILE} up -d

stop-jupyter:
	@ echo -e "$(BUILD_PRINT)Stopping the jupyter services $(END_BUILD_PRINT)"
	@ docker-compose -p common --file ./infra/jupyter_notebook/docker-compose.yml --env-file ${ENV_FILE} down

sample-data-eforms:
	@ echo -e "$(BUILD_PRINT)Running data-sampler-cli $(END_BUILD_PRINT)"
	poetry run data-sampler-cli -o $(OUTPUT_FOLDER) -n eforms

sample-data-eforms-nohup:
	@ echo -e "$(BUILD_PRINT)Running data-sampler-cli in background $(END_BUILD_PRINT)"
	@ nohup poetry run data-sampler-cli -o $(OUTPUT_FOLDER) -n eforms > /dev/null 2>&1 &
	@ echo -e "$(BUILD_PRINT)Job started in background. Check logs in $(OUTPUT_FOLDER) $(END_BUILD_PRINT)"

load-notices-from-folder:
	@ echo -e "$(BUILD_PRINT)Running load-notices-cli $(END_BUILD_PRINT)"
	poetry run load-notices-cli -i $(NOTICES_INPUT_FOLDER) $(if $(NOTICES_LOG_FOLDER),-o $(NOTICES_LOG_FOLDER),)

load-notices-from-folder-nohup:
	@ echo -e "$(BUILD_PRINT)Running load-notices-cli in background $(END_BUILD_PRINT)"
	@ nohup poetry run load-notices-cli -i $(NOTICES_INPUT_FOLDER) $(if $(NOTICES_LOG_FOLDER),-o $(NOTICES_LOG_FOLDER),) > /dev/null 2>&1 &

download-notices:
	@ echo -e "$(BUILD_PRINT)Running download-notices-cli $(END_BUILD_PRINT)"
	poetry run download-notices-cli -o $(NOTICES_DOWNLOAD_FOLDER) -r $(YEAR_MONTH_RANGE)

download-notices-nohup:
	@ echo -e "$(BUILD_PRINT)Running download-notices-cli in background $(END_BUILD_PRINT)"
	@ nohup poetry run download-notices-cli -o $(NOTICES_DOWNLOAD_FOLDER) -r $(YEAR_MONTH_RANGE) > /dev/null 2>&1 &
