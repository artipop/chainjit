# chainjit (change it)

## Build custom chainlit
https://github.com/Chainlit/chainlit/blob/main/.github/CONTRIBUTING.md
poetry self add poetry-plugin-ignore-build-script && poetry build --ignore-build-script

Then
pip install chainlit-2.0.1-py3-none-any.whl

## For RAG
pip install langchain langchain-community chromadb tiktoken openai langchain-openai

And Google packages ([drive](https://developers.google.com/drive/api/quickstart/python) and [docs](https://developers.google.com/docs/api/quickstart/python))
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

## Postgresql
https://github.com/Chainlit/chainlit-datalayer

pip install asyncpg

```shell
git clone git@github.com:Chainlit/chainlit-datalayer.git
cd chainlit-datalayer
cp .env.example .env
docker compose up -d
npx prisma migrate deploy
```
