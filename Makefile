.PHONY: setup run test lint clean

setup:
	python -m venv .venv
	.venv\Scripts\pip install -r requirements.txt

run:
	python src/run.py "$(QUERY)"

test:
	python -m pytest tests/ -v --cov=src

lint:
	python -m pylint src/ --disable=C0111,R0913,R0914

clean:
	del /Q reports\*.md reports\*.json logs\*.json 2>nul || exit 0
	rmdir /S /Q __pycache__ .pytest_cache 2>nul || exit 0
