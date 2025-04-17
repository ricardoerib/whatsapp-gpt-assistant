FROM public.ecr.aws/lambda/python:3.11

# Copie os requisitos primeiro para aproveitar o cache em camadas do Docker
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copie o código da aplicação
COPY app/ ${LAMBDA_TASK_ROOT}/app/
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/

# Comando para executar a função Lambda
CMD [ "lambda_handler.handler" ]