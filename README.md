# ENS 101 Mentor Desk

A focused appointment workspace for Ensign College career mentors. It turns **ENS 101 Appointment 1a: Ensign Connect and Internship Plan** into a clear five-stage workflow and keeps every linked tool close at hand.

## What it includes

- Guided workflow: Begin, Ensign Connect, Internship Plan, Career Direction, and Complete
- Persistent appointment checklist built directly from the Appointment 1a guide
- Non-sensitive session details and locally saved working notes
- Copyable appointment summary with student and mentor next steps
- In-context links to Ensign Connect, major groups, notification preferences, alumni, Career Explorer, and international-student support
- Career Explorer AI launcher and Mentor Copilot support for questions, internship explanations, summaries, and follow-up drafts
- Built-in offline guidance, so the app is useful without an AI key
- Privacy filters, rate limiting, and local feedback storage
- Responsive desktop, tablet, and mobile layout

## Run locally

This project uses only Python's standard library—there are no packages to install.

```powershell
python app.py
```

Open [http://localhost:5050](http://localhost:5050).

## Optional AI configuration

The app does not contact an AI service by default. Copy `.env.example` to `.env`, then configure either option:

```env
# Any OpenAI-compatible endpoint, such as a local LM Studio server
LM_STUDIO_URL=http://localhost:1234/v1
MODEL_NAME=your-model-name

# Or Google Gemini
GEMINI_API_KEY=your-key
GEMINI_MODEL=gemini-2.5-flash
```

The request order is: configured OpenAI-compatible endpoint, configured Gemini, then deterministic offline guidance.

## Privacy and records

The browser saves the current draft in local storage so a refresh does not erase the appointment. The **New appointment** action clears that local draft.

Mentors should not enter student IDs, passwords, financial information, health details, immigration documents, or other protected information. Store any final record only in an institutionally approved location and follow applicable Ensign College policy.

## Project structure

- `app.py` — local server, AI routing, privacy checks, and feedback endpoint
- `static/index.html` — application structure
- `static/styles.css` — responsive visual design
- `static/app.js` — workflow, local persistence, resources, notes, and Copilot UI
- `.env.example` — optional AI and server configuration

## Key settings

```env
PORT=5050
HOST=0.0.0.0
RATE_LIMIT_PER_MIN=50
```

## Source

Adapted from the [Gemini Coaching Agent Starter](https://github.com/robbagley-afk/gemini-coaching-agent-starter). The ENS 101 workflow and interface are purpose-built for this project.
