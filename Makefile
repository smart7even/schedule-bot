# Variables
COMPOSE_CMD = sudo docker compose

# Build and start containers
up:
	$(COMPOSE_CMD) up -d --build --force-recreate

# Stop and remove containers
down:
	$(COMPOSE_CMD) down

# Rebuild the containers without cache
rebuild:
	$(COMPOSE_CMD) build --no-cache
	$(MAKE) up

# View logs
logs:
	$(COMPOSE_CMD) logs

# Example of a custom script
custom:
	echo "Running a custom script"
	./custom_script.sh
