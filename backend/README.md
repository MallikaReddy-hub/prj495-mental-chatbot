# Backend (FastAPI)

Handles login, saved conversations, helplines, thought of the day, the crisis check and the output guard.
Replies come from the fine-tuned model server (English/Spanish) or Gemini (other languages and fallback).

## Run locally
```bash
cd backend
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                  # then fill in the values
uvicorn app.main:app --reload
```
Interactive docs: http://localhost:8000/docs

## Test
```bash
pip install pytest
pytest -q
```

## Endpoints
| Method | Path | Notes |
|---|---|---|
| POST | /auth/signup, /auth/login | return a JWT token |
| GET | /me | current user; DELETE /me deletes the account and all data |
| POST | /chat | `{message, language, conversation_id?}`; crisis check, model call, output guard, save |
| GET | /conversations, /conversations/{id} | saved chats; DELETE /conversations/{id} |
| GET | /helplines?country=IN&lang=hi | helpline list |
| GET | /quote | thought of the day |
| GET | /health | liveness check |

## Before release
- Verify the numbers in `app/data/helplines.json`.
- Extend the phrase lists in `app/safety.py` and have native speakers review the Telugu, Tamil and Kannada additions.
- Use a hosted Postgres `DATABASE_URL`; a free host's local disk is wiped on restart.
- Set a long random `JWT_SECRET`.
