# Medical Translation Module

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Create .env

```
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

## Run the Backend

```bash
uvicorn backend.main:app --reload
```

Open:

```
http://127.0.0.1:8000/docs
```

Use the `/translate` endpoint to translate English medical summaries into Hindi or Telugu.