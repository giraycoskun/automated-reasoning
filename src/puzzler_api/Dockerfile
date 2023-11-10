FROM python:3.11.2

RUN mkdir /app 

COPY /src /app/src

COPY pyproject.toml /app 

WORKDIR /app

ENV PYTHONPATH=${PYTHONPATH}:${PWD} 

RUN pip install poetry

RUN poetry config virtualenvs.create false

RUN poetry install --without dev,test,docs

EXPOSE 80

# CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "80"]
CMD ["python", "src/main.py"]