# GitHub: last steps (run on your machine)

Use this after the app runs, tests pass, and screenshots are in `assets/screenshots/`.

## 0) Must-check before any commit (no code edits required if already correct)

- `.env` is not in the repo (only `.env.example`). Real API keys never go in git.
- `.venv/` stays untracked (already in `.gitignore`).
- Run tests once: `pytest -q`
- Optional: `streamlit run src/talk_to_data/app.py` and smoke-test upload + Q&A.

There is no separate “must change these files after GitHub” rule — only verify you did not add secrets or junk. If organisers ask for a specific link or branch name later, update README or submission form only as they say.

## 1) Create the empty repo on GitHub

- GitHub.com → New repository → choose name → create.
- Prefer private until organisers say public.
- Do not add README, .gitignore, or license on GitHub if you already have them locally (avoids merge mess).

## 2) First-time git in this folder (copy-paste)

Run from the project root (folder that contains `README.md`):

```bash
cd /Users/naman/Desktop/natwestSubmission

git init
git branch -M main
git add .
git status
```

Check `git status`: you should not see `.env` or `.venv/`. If `.env` appears, stop and fix before committing.

Sign-off commit (DCO-style; use the email GitHub expects):

```bash
git commit -s -m "Initial hackathon submission: Talk to Data (grounded PDF/CSV)"
```

Connect remote (replace `YOUR_USER` and `YOUR_REPO`):

```bash
git remote add origin git@github.com:YOUR_USER/YOUR_REPO.git
```

HTTPS alternative:

```bash
git remote add origin https://github.com/YOUR_USER/YOUR_REPO.git
```

Push:

```bash
git push -u origin main
```

If GitHub shows “repository not empty”, you added files on GitHub — either use a fresh empty repo or follow GitHub’s “push an existing repository” doc with pull/merge.

## 3) Single email (organiser rule)

Use one email for GitHub account, `git config user.email`, and hackathon communication.

Set locally for this repo only:

```bash
git config user.name "Your Name"
git config user.email "your-one-email@example.com"
```

## 4) After push

- Submit the GitHub URL in the hackathon portal if required.
- Keep commits signed-off if rules require DCO (`git commit -s`).

This file is documentation only; it does not run commands for you.
