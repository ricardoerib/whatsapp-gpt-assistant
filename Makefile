.PHONY: help install run test lint format clean docker-build docker-run docker-stop

help:
	@echo "Comandos disponíveis:"
	@echo "  make install    - Instala as dependências"
	@echo "  make run        - Inicia a aplicação"
	@echo "  make test       - Executa os testes"
	@echo "  make lint       - Executa verificação de código"
	@echo "  make format     - Formata o código"
	@echo "  make clean      - Remove arquivos temporários"
	@echo "  make docker-build  - Constrói a imagem Docker"
	@echo "  make docker-run    - Executa o contêiner Docker"
	@echo "  make docker-stop   - Para o contêiner Docker"

install:
	pip install -r requirements.txt

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest

test-cov:
	pytest --cov=app --cov-report=html

lint:
	isort app tests
	black app tests
	mypy app

format:
	isort app tests
	black app tests

clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	rm -rf temp/*

docker-build:
	docker build -t whatsapp-gpt-assistant .

docker-run:
	docker run -d --name whatsapp-gpt-container -p 8000:8000 --env-file .env whatsapp-gpt-assistant

docker-stop:
	docker stop whatsapp-gpt-container
	docker rm whatsapp-gpt-container