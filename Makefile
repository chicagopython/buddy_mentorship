.PHONY: start
start:
	docker-compose up -d

.PHONY: start-build
start-build:
	docker-compose up --build -d

.PHONY: stop
stop:
	docker-compose down

.PHONY: test
test:
	docker-compose exec web pytest

.PHONY: migrate
migrate:
	docker-compose exec web python manage.py migrate

.PHONY: superuser
superuser:
	docker-compose exec web python manage.py createsuperuser
