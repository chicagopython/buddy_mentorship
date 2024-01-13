.PHONY: start

.env:
	cp sample.env .env

build:
	docker-compose build

start: .env
	docker-compose up -d

up: start

.PHONY: start-build
start-build:
	docker-compose up --build -d

shell:
	docker-compose exec web bash

.PHONY: stop
stop:
	docker-compose down

down: stop

.PHONY: test
test:
	docker-compose exec web pytest

.PHONY: migrate
migrate:
	docker-compose exec web python manage.py migrate

.PHONY: superuser
superuser:
	docker-compose exec web python manage.py createsuperuser
