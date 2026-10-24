# Lightcone

Fair "first" for a multi-planet world. Lightcone detects true ties between Earth and Mars requests (where neither side could have known about the other because of light delay) and resolves them with a verifiable fairness policy.

## Run

Backend (terminal 1):

    cd backend
    python -m venv .venv
    source .venv/bin/activate        # Windows PowerShell: .venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8000

Frontend (terminal 2):

    cd frontend
    npm install
    npm run dev

Open http://localhost:5173

## Tests

    cd backend
    python -m pytest
