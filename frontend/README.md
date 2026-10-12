# Frontend (React + Vite)

The website for the mental health chatbot: login/signup, chat with saved history, language selector,
always-visible "Get help now" button with helplines, thought of the day, breathing exercise,
log out and delete account. It talks to the FastAPI backend.

## Run locally
1. Install Node.js (LTS) from nodejs.org.
2. Start the backend first (`uvicorn app.main:app --reload` in `backend/`, port 8000).
3. In this folder:
```bash
npm install
npm run dev
```
Open http://localhost:5173

If the backend is somewhere else, copy `.env.example` to `.env` and set `VITE_API_URL`.

## Notes
- The backend must allow this site's address in `CORS_ORIGINS` (default `http://localhost:5173`).
- The login token is kept in the browser's localStorage. Fine for a demo; a production app should use httpOnly cookies.
