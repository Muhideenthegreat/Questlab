# QuestLab

QuestLab is a Flask-based experiential learning platform that transforms theoretical lessons into practical, real-world quests. Educators create and publish quests, learners discover them and submit reflections, and the system provides feedback on submissions.

## Features

- Create and publish quests with tasks and instructions
- Browse and filter quests in a public gallery
- Submit reflections with media uploads and receive AI-generated feedback
- Track progress and submissions from a personal dashboard

## Roles

- Creator (Educator): creates and publishes quests
- Quester (Learner): discovers and completes quests
- Both: can create and complete quests
- Guest: browses public quests only

## Tech Stack

- Python 3.11+
- Flask, Flask-SQLAlchemy, Flask-Login
- SQLite (default development database)

## Setup and Run

### 1) Clone and enter the project

```bash
git clone <your-repo-url>
cd questlab
```

### 2) Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Configure environment

Create a `.env` file in `questlab/`:

```bash
FLASK_ENV=development
FLASK_CONFIG=development
SECRET_KEY=your-strong-secret-here
DATABASE_URL=sqlite:///instance/questlab.db
```

### 5) Initialize the database

Option A: Seed sample data (creates admin/Password123! and sample quests if none exist).

```bash
DATABASE_URL=sqlite:///instance/questlab.db python seed.py
```

Option B: Create an empty database schema.

```bash
python - <<'PY'
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
PY
```

### 6) Run the app

```bash
FLASK_ENV=development FLASK_CONFIG=development python run.py
```

Visit `http://127.0.0.1:5000`.

## Tests

```bash
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
venv/bin/pytest -q
```

## Project Structure

```
questlab/
  app/        # models, routes, services, templates, utils
  instance/   # db, uploads, logs (gitignored)
  tests/
  seed.py     # optional local seeding
  run.py
```

## Basic Usage

1. Register accounts for the roles you want to test (Educator, Learner, Both).
2. Create a quest from the dashboard or "Create New Quest."
3. Discover quests in the gallery and begin a quest.
4. Submit task reflections with media uploads.
5. Review feedback and track progress in the dashboard.

## Troubleshooting

- App won't start: install dependencies with `pip install -r requirements.txt`
- Import errors: ensure the virtual environment is active
- Upload errors: confirm file type and size (max 10MB)
- Database missing: initialize the schema with `db.create_all()`
- Tests fail: recreate the database schema

## Docs

- `questlab-BuildandSetupGuide.docx`
- `questlab-UserGuide.docx`
