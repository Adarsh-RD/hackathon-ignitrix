# returnX AI

**An always-on AI tax & job assistant built for India's gig workforce.**

returnX AI helps gig delivery partners (Swiggy, Zomato, Rapido, Zepto, Blinkit, Dunzo, etc.) make smarter real-time decisions — parse payment SMS messages to track income, estimate taxes, and use AI to pick the most profitable delivery job from live notifications.

The app runs **100% in the browser**. No server. No signup. No data leaves the device except the API call to Groq.

![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)
![Groq](https://img.shields.io/badge/Groq_API-FF6600?style=flat-square)
![Llama 3.3](https://img.shields.io/badge/Llama_3.3_70B-0467DF?style=flat-square&logo=meta&logoColor=white)

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Solution](#solution)
- [Features](#features)
- [Smart Job Picker](#smart-job-picker)
- [Multi-Agent Pipeline](#multi-agent-pipeline)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Tax Logic](#tax-logic)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Sample Test Data](#sample-test-data)
- [Privacy and Security](#privacy-and-security)
- [Roadmap](#roadmap)
- [Team](#team)

---

## Problem Statement

India has over 15 million gig workers across platforms like Swiggy, Zomato, Rapido, Ola, and Uber. Most of them:

- Receive 50–100+ payment SMS messages per month with no organized record
- Have no awareness of TDS (Tax Deducted at Source) obligations
- Lose money choosing the wrong delivery job without knowing real profit per km
- Cannot afford professional CA services (₹5,000–15,000/year for basic filing)

This leads to missed deductions, surprise tax notices, and poor delivery job selection.

---

## Solution

returnX AI is a two-in-one tool for gig workers:

1. **Tax Assistant** — Paste payment SMS messages. AI extracts income, tracks it over time, and shows real-time TDS + Section 44AD tax estimates.
2. **Smart Job Picker** — Paste delivery app notifications or simulate live orders. AI compares profitability (pay, fuel cost, distance, traffic) and recommends the best job in real time.

---

## Features

| Feature | Description |
|---|---|
| 🤖 **3-Agent AI Pipeline** | SmsParser → TaxAdvisor → Insights agents run sequentially via Groq (client-side, no backend) |
| 📊 **Income Dashboard** | Income table with platform, amount, date — plus running totals |
| 💰 **Tax Estimates** | Real-time TDS (1%) and Section 44AD (6%) shown as top-level summary cards |
| 💡 **AI Insights** | InsightsAgent generates 3 actionable financial tips based on your income data |
| ⚡ **Smart Job Picker** | AI compares multiple delivery job offers and picks the highest ₹/hour option |
| 🗺️ **Live Delivery Map** | Google Maps embed showing your delivery zone, updated with each comparison |
| 🚦 **Traffic Analysis** | Zone-based congestion heuristics — shows traffic level, delay, and how it affects net profit |
| 📱 **Paste or Simulate** | Paste real app notifications OR simulate live push notifications in demo mode |
| 📈 **Income Chart** | Bar chart showing income breakdown by platform (Chart.js) |
| 💾 **Persistent Storage** | All data stored in localStorage — survives page refreshes |
| 🔒 **Privacy First** | Zero backend, zero analytics — data never leaves the browser |
| 📱 **Mobile Responsive** | Collapses to single-column layout below 900px |

---

## Smart Job Picker

The Smart Job Picker is a real-time AI engine that helps riders choose the best delivery job available.

### How it works

```
App Notifications (text)
        │
        ▼
  AI Notification Parser
  (Groq: Llama 3.3 70B)
        │
        ▼
  Extracted Job Offers
  [platform, pay, distance, type]
        │
        ▼
  Job Comparison Engine
  (Groq: profitability analysis)
        │
        ▼
  ┌─────────────────────────────────────────┐
  │  Traffic Analysis  │  3 Analysis Cards  │
  │  (zone heuristics) │  (side by side)    │
  ├─────────────────────────────────────────┤
  │  AI Winner Card (Best Pick + confidence)│
  ├─────────────────────────────────────────┤
  │  Live Delivery Zone Map                 │
  └─────────────────────────────────────────┘
```

### Metrics computed per job

| Metric | Formula |
|---|---|
| Fuel Cost | Distance × ₹4/km (average two-wheeler) |
| Net Profit | Pay − Fuel Cost |
| Time (with traffic) | Base time + traffic delay |
| ₹/Hour | (Net Profit / Time) × 60 |
| ₹/KM | Net Profit / Distance |
| Score | Weighted composite of ₹/hour, ₹/km, distance |

### Input Modes

- **Paste Notifications** — Copy notification text directly from your phone's notification shade. AI auto-extracts platform, pay, distance, and delivery type.
- **Simulate Live** — Demo mode that generates realistic push notifications from Swiggy, Zomato, Zepto, Blinkit, Rapido, Dunzo — appearing one by one as they would on a real device.

---

## Multi-Agent Pipeline

The "Add & Analyse" button triggers a 3-agent pipeline that runs **entirely client-side** via the Groq API:

```
User SMS Text
      │
      ▼
┌─────────────────────────────────┐
│  Agent 1: SmsParserAgent        │
│  • Extracts income transactions │
│  • Platform, amount, date       │
│  • Returns income[]             │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│  Agent 2: TaxAdvisorAgent       │
│  • Computes TDS (1%)            │
│  • Computes Sec 44AD (6%)       │
│  • Identifies tax slab          │
│  • Provides 1 tax-saving tip    │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│  Agent 3: InsightsAgent         │
│  • Platform breakdown analysis  │
│  • 3 actionable financial tips  │
│  • Colour-coded insight cards   │
└─────────────────────────────────┘
```

Each agent is a separate Groq API call with a dedicated system prompt, running sequentially with state passed between them. The stepper UI shows live progress.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        USER'S BROWSER                            │
│                                                                  │
│  ┌────────────────┐         ┌──────────────────────────────────┐ │
│  │  Paste Panel   │         │          Dashboard               │ │
│  │                │         │                                  │ │
│  │  • API Key     │         │  ┌────────┬─────────┬─────────┐  │ │
│  │  • SMS Input   │────────▶│  │ Income │   TDS   │  44AD   │  │ │
│  │  • Add Button  │         │  └────────┴─────────┴─────────┘  │ │
│  │  • Agent Steps │         │                                  │ │
│  │  • Activity Log│         │  Smart Job Picker                │ │
│  └────────────────┘         │  ┌──────────────────────────────┐│ │
│                             │  │ Paste / Simulate Notifs      ││ │
│                             │  │ ──────────────────────────── ││ │
│                             │  │ Traffic Analysis             ││ │
│                             │  │ [Card] [Card] [Card]         ││ │
│                             │  │ Live Map                     ││ │
│                             │  └──────────────────────────────┘│ │
│                             │                                  │ │
│                             │  Income Table  │  Income Chart   │ │
│                             │  AI Insights                     │ │
│                             └──────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                      localStorage                          │  │
│  │  returnx_income  │  returnx_log  │  returnx_insights       │  │
│  └──────────────────────────────────┬─────────────────────────┘  │
└─────────────────────────────────────┼──────────────────────────── ┘
                                      │ HTTPS
                                      ▼
                           ┌──────────────────────┐
                           │    Groq Cloud API     │
                           │    Llama 3.3 70B      │
                           │  (3 sequential calls) │
                           └──────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| Structure | HTML5 | Semantic markup, no build step |
| Styling | Vanilla CSS3 | CSS Grid + Flexbox, zero dependencies |
| Logic | Vanilla JavaScript (ES6+) | Async/await, IIFE module pattern, no framework |
| Charts | Chart.js 4.4 | Lightweight, beautiful bar charts |
| Maps | Google Maps Embed API | Live delivery zone visualization |
| AI Model | Llama 3.3 70B Versatile | Best open-source model for structured extraction |
| AI Infrastructure | Groq API | ~500 tokens/sec; free tier; JSON mode |
| Persistence | localStorage API | Client-side; no backend required |
| Typography | Google Fonts (Inter) | Modern UI typeface |
| Icons | Material Icons Round | Consistent Google icon system |

---

## Tax Logic

### Summary Cards (always visible at the top)

| Card | Formula | Description |
|---|---|---|
| **Total Income** | Sum of all parsed income | Running total across all sessions |
| **TDS Estimated (1%)** | Total Income × 0.01 | Tax deducted at source by platforms under Sec 194-O |
| **Sec 44AD Taxable (6%)** | Total Income × 0.06 | Presumptive taxation — only 6% of digital receipts is taxable profit |

### Relevant Indian Tax Provisions

- **Section 194-O**: E-commerce operators (Swiggy, Zomato, Ola, etc.) deduct 1% TDS on payments exceeding ₹5 lakh/year to gig workers.
- **Section 44AD / 44ADA**: Gig workers can opt for presumptive taxation. For digital/UPI receipts, only 6% of gross receipts is treated as taxable profit — the remaining 94% is treated as business expenditure by default.

---

## Project Structure

```
returnX AI/
├── index.html          # Full app layout: paste panel + dashboard + job picker
├── style.css           # Design tokens, Grid layout, all component styles
├── app.js              # Core: state management, rendering, localStorage, pipeline
├── agents.js           # 3-agent pipeline (SmsParser, TaxAdvisor, Insights) via Groq
├── groq.js             # Groq API helper (used by job picker)
├── job-picker.js       # Smart Job Picker: parse/simulate/compare delivery jobs
├── README.md           # Documentation
└── backend/            # Python Flask backend (optional, not required for frontend)
    ├── app.py
    └── agents/
        ├── base_agent.py
        ├── job_advisor.py
        └── knowledge_base.py
```

| File | Responsibility |
|---|---|
| `index.html` | Semantic layout: 2-panel app (paste + dashboard), Job Picker, charts, map |
| `style.css` | Full design system: tokens, Grid, cards, tabs, charts, responsive breakpoints |
| `app.js` | State management, dashboard rendering, 3-agent pipeline trigger, localStorage |
| `agents.js` | Client-side multi-agent orchestrator — calls Groq directly, no server needed |
| `groq.js` | Shared Groq API helper for SMS parsing |
| `job-picker.js` | Job notification parser, simulate mode, comparison renderer, traffic analysis |

---

## Getting Started

### Prerequisites

- Any modern web browser (Chrome, Firefox, Edge, Safari)
- A free Groq API key → [console.groq.com/keys](https://console.groq.com/keys)

### Installation

```bash
git clone https://github.com/KLE-Tech-Ignitrix/team-18.git
cd team-18
```

### Running Locally

```bash
# Option 1: Python
python -m http.server 8080

# Option 2: Node.js
npx http-server -p 8080

# Option 3: Open index.html directly in the browser
```

> **Note:** The frontend works standalone with no backend. The `backend/` folder is an optional Python Flask server for extended API features.

### Usage

#### Income Tracking
1. Open the app in your browser
2. Paste your Groq API key in the **API Key** field
3. Paste SMS payment messages in the textarea
4. Click **Add & Analyse**
5. Watch the 3 agents run (Parser → Tax Advisor → Insights)
6. View income table, TDS + 44AD estimates, and AI insights in the dashboard

#### Smart Job Picker
1. Click **Compare & Suggest Best Job** in the Smart Job Picker section
2. **Paste mode** — paste notification text copied from your phone; AI extracts jobs
3. **Simulate mode** — click "Simulate Incoming Notifications" for a live demo
4. Click **Compare & Suggest Best Job** to get the AI winner with confidence score
5. View traffic analysis and the live delivery zone map

---

## Sample Test Data

### SMS Income Messages

```
Swiggy has transferred ₹1,243 to your account on 10-Apr
Zomato Foods credited ₹876 to your bank on 12-Apr
Rapido ride payment ₹540 credited on 15-Apr
Ola driver payout ₹2,100 credited on 18-Apr
Uber trip earnings ₹1,650 deposited on 20-Apr
```

### Job Picker Notifications

```
🍔 Swiggy: New order! ₹45 for 3.2 km delivery. Pickup from Meghana Foods, deliver to Koramangala.

⚡ Zepto: Delivery request! Earn ₹35. Distance: 1.5 km. Grocery order from Zepto Dark Store.

🍕 Zomato: Order available! ₹62 payout, 4.1 km. Food pickup from Paradise Biryani.
```

---

## Privacy and Security

- **No backend required** — the entire app runs client-side
- **No database** — all data stored in the browser's localStorage
- **No tracking** — zero analytics, cookies, or fingerprinting
- **Direct API calls** — text is sent browser → Groq API over HTTPS only
- **One-click clear** — the trash icon removes all stored data instantly
- **API key isolation** — key stored in localStorage, sent only to `api.groq.com`

---

## Roadmap

- [ ] Receipt photo scanning (OCR for fuel bills, service receipts)
- [ ] Monthly / quarterly income trend charts
- [ ] Auto-generate ITR-4 draft for tax filing
- [ ] Bank statement CSV/PDF import
- [ ] Multi-language support (Hindi, Kannada, Tamil, Telugu)
- [ ] PWA with offline access and home screen installation
- [ ] Real-time map routing for delivery zone comparison

---

## Team

**Team 18 — KLE Tech Ignitrix**

---

## License

This project is developed for the KLE Tech Ignitrix hackathon.
