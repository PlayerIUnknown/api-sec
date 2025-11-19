# Noir API Mapper

Tools for turning source repositories into Postman collections using OWASP Noir and Groq LLM inference.

## CLI Usage

```bash
poetry install  # or pip install -e .
noir-api-agent generate --repo https://github.com/org/project --base-url https://api.example.com --out postman.json
```

## Flask UI

```bash
export FLASK_SECRET_KEY=secret
export GROQ_API_KEY=sk-...
python -m noir_agent.webapp
```
