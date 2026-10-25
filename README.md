# Prep App

A practice site for graduate trainee aptitude tests. It gives candidates timed practice in numerical, verbal and critical reasoning, then shows their scores and explains every answer.

**Live app:** https://prep-app-tuqf.onrender.com
## What it does

- **Full practice test:** 60 questions in 60 minutes, drawn from three sections: numerical, verbal and critical reasoning.
- **Section tests:** 10 questions in 10 minutes for one section, for quick practice.
- **Fresh questions first:** the app remembers which questions a user has already seen and picks unseen ones before repeating any.
- **Results and review:** an overall score, a score per section, and a review screen showing missed and skipped questions with explanations.
- **Accounts:** register and log in. Each user has a limited number of free tests.
- **Admin routes:** reset a user's attempts or seen questions.

## How it's built

- **Backend:** Python with FastAPI
- **Database:** SQLAlchemy, with SQLite locally and PostgreSQL in production
- **Authentication:** passwords are hashed with Argon2, and logged-in users receive a JWT token
- **Front end:** plain HTML, CSS and JavaScript, with no framework
- **Hosting:** Render, with a managed Postgres database

## Design decisions

- **The server owns the clock.** A test's deadline is calculated and stored on the server when the test starts. The browser only displays a countdown, so changing the device clock gains nothing.
- **Answers stay on the server.** Questions are sent to the browser without their correct answers or explanations. Results are only available after submitting.
- **Ownership checks.** Every attempt belongs to a user, and users can only submit or view their own attempts.
- **Simple deployment config.** The database address comes from a `DATABASE_URL` environment variable, so the same code runs on a laptop and on Render.

## Run it locally

```
git clone <this-repo-url>
cd <repo-folder>
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open http://127.0.0.1:8000. With no `DATABASE_URL` set, the app uses a local SQLite file. API docs are at `/docs`.

## Status

Early stage and still improving. Planned next:

- Automated tests with pytest
- Database migrations with Alembic
- Email verification at sign-up

## Feedback

Found a wrong answer or a bug? Use the feedback link inside the app.
