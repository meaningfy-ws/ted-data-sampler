SHELL=/bin/bash -o pipefail
BUILD_PRINT = \e[1;34mSTEP:
END_BUILD_PRINT = \e[0m

CURRENT_UID := $(shell id -u)
export CURRENT_UID
# These are constants used for make targets so we can start prod and staging services on the same machine
ENV_FILE := .env

# include .env files if they exist
-include .env


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