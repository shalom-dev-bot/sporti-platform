.PHONY: install run migrate format lint test

install:
	pip install -r requirements/dev.txt
	pre-commit install

run:
	python manage.py runserver

migrate:
	python manage.py makemigrations
	python manage.py migrate

format:
	black .
	isort .

lint:
	flake8 .

test:
	pytest
