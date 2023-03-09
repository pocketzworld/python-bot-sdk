lint:
	@poetry run mypy -p highrise && poetry run flake8 src/highrise/ && poetry run isort -c src/highrise/ && poetry run black --check src/highrise/