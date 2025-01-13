FROM python:3.11

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
COPY ./libs/chainlit-2.0.1-py3-none-any.whl /code/libs/chainlit-2.0.1-py3-none-any.whl

RUN ls -l

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app/ /code/

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
