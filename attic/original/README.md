# 🌾 GramSahayak AI — Rural Entrepreneurship & Business Feasibility Platform

An AI-powered advisory and financial feasibility platform designed specifically for rural and micro-entrepreneurs across India. Built for SIH 2026.

---

## 🌟 Key Platform Modules

1. **Animated Landing Page**: High-impact, responsive hero section showcasing platform mission, key metrics, and features.
2. **Multilingual Support (i18n & Bhashini)**: Full UI localization across major Indian regional languages (Hindi, Tamil, Telugu, Kannada, Bengali, Marathi, Gujarati, etc.).
3. **Authentication**: Firebase authentication with Email/Password, Google, Facebook, plus an **Instant Demo Access** mode for 1-click evaluation without API keys.
4. **Feasibility Assessment Engine**: Multi-step wizard evaluating business concepts across Financial, Market, Operational, and Experience dimensions with instant viability scoring (0-100).
5. **Interactive Feasibility Dashboard**: Real-time radar charts, break-even timeline projections, SWOT breakdown, and tailored suggestions.
6. **Financial Planning & Runway**: Dynamic capital allocation sliders, cash runway calculator, Capex vs Opex breakdown.
7. **Government Schemes & EMI Calculator**: Curated directory of schemes (PM SVANidhi, MUDRA Shishu/Kishore, PMEGP, Stand-Up India, PMFME, Lakhpati Didi) with interactive EMI and subsidy calculators.
8. **Cash Flow & Burn Rate**: 12-month interactive inflows/outflows forecast, peak cash month detection, and emergency reserve planning.
9. **Credit & Debt Monitoring**: CIBIL credit health score tracker, loan debt-to-income ratio analysis, and credit score improvement tips.
10. **AI Voice & Chat Advisor**: Multilingual conversational assistant capable of answering questions on schemes, loans, profitability, and operational guidance.

---

## 🏗️ Tech Stack

- **Frontend**: React 19, Vite 8, Tailwind CSS v4, Framer Motion, Lucide React, Recharts, i18next, Leaflet
- **Backend**: FastAPI, Uvicorn, Pydantic v2, Python 3.14
- **Language Intelligence**: Bhashini API integration + AI Engine
- **Auth**: Firebase Auth with instant guest fallback

---

## 🚀 Running the Project

### Option A: Already Running
Both the frontend and backend are currently running in the background:
- **Frontend App**: [http://localhost:5173](http://localhost:5173)
- **FastAPI Backend**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Option B: Starting Manually

#### 1. Start the FastAPI Backend
```bash
cd backend
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

#### 2. Start the Frontend Dev Server
In a second terminal:
```bash
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your web browser. Click **"⚡ Instant Demo Access"** on the login page to immediately explore the entire platform!
