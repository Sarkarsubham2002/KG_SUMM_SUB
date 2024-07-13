# kg-summarizer
Knowledge graph summarization using LLMs with a FastAPI interface

## Create Environment
```bash
python -m venv venv
venv\Scripts\activate # on Unix/Mac: source venv/bin/activate
pip install -r .\requirements.txt
```

## Start FastAPI/Uvicorn Server
```bash
uvicorn main:app --reload # Using local library: ./venv/bin/uvicorn main:app --reload
```

## Local Development
This service requires a valid OpenAI API key and organization ID to be passed as
environment variables. See the [`sample.env` file](./sample.env) for a template.

For webapps developed against a local deployment of this service, the `PYTHON_ENV` env variable must be set to `dev`. This setting enables browsers to interact with the local server by ensuring responses to preflight CORS requests include the `Access-Control-Allow-Private-Network: true` header, facilitating access within private networks. See the [Chrome blog post](https://developer.chrome.com/blog/private-network-access-preflight) for more details. **To avoid CSRF attacks, this variable shouldn't be set to `dev` in production**.

## Server Update Steps
1) Push changes and make new release on github
    - Make sure release version matches FastAPI docs version in kg_summarizer/server.py and setup.py
2) Update Helm chart
    - Update values.yaml with new release version
    - cd translator-devops/helm/kg-summarizer
    - helm -n translator-dev upgrade -f values-populated.yaml kg-summarizer .


## Redis server
Start server: redis-server --dbfilename aragorn_cache.rdb --dir /home/joeyr/data/kg_summarizer

## API Location
https://kg-summarizer.apps.renci.org/docs

## Todo
- Redis database indices changed???
- This example is interesting because Cisplatin is shown to treat multiple subclasses of mucin-producing carcinoma. Can GPT summarize this well? Don't have example indices anymore 
- Add pyunit tests
    - Aragorn and strider have unit tests
- Add abstract summary preprocess flag to server
- Create database dataclass and sort keys as initialization
