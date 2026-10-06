# Polymath

Bloomberg Terminal-style analytics for prediction markets.

## Stack
- **Frontend:** Next.js 15 App Router, TypeScript, Tailwind CSS, Zustand
- **Backend:** Python FastAPI (`backend/`)
- **Deployment:** Vercel (preview + prod)
- **Data:** Polymarket Gamma API + CLOB API (public, no auth)
- **AI:** Gemini 2.5 Flash-Lite, falling back to 2.5 Flash, then Groq Llama 3.3 70B, for summarization; WoodWide AI for analysis
- **Secrets:** `.env.local`
