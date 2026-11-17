# University Elections Voting System

A Django-based university student election website with full CRUD
(create, read, update, delete) backed by a database.

| Page | What it does |
|------|--------------|
| Students | Register, edit and delete students |
| Election | Create/edit/delete elections; start and end voting |
| Position | Create/edit/delete positions for an election |
| Candidate | Register students as candidates; vote counts update automatically |
| Voter | Register/edit/delete voters per election |
| Ballot | Cast a ballot (one per voter, only while an election is ongoing) |

Pages are server-rendered Django templates (all extend `base.html`) using ModelForms and class-based CRUD views. Log in with the superuser below
(more users can be added at `/admin/`).

## Group Members

| # | Name | Registration No. |
|---|------|------------------|
| 1 | _Full name_ | _Reg. number_ |
| 2 | _Full name_ | _Reg. number_ |
| 3 | _Full name_ | _Reg. number_ |
| 4 | _Full name_ | _Reg. number_ |

## Run locally

```bash
python -m venv venv
venv\Scripts\activate        # Windows  (Linux/macOS: source venv/bin/activate)
pip install -r requirements.txt
python manage.py migrate
python manage.py ensure_admin
python manage.py seed_demo      # optional sample data
python manage.py runserver
```

Open http://127.0.0.1:8000/ — the Django admin is at `/admin/`.

## Superuser

- Username: `admin`
- Password: `admin123`

## Deployment

Deployed on Render using `render.yaml` / `build.sh`
(the build runs `migrate` and creates the superuser automatically).

Note: on Render's free plan the SQLite database resets on every deploy/restart, so the superuser and sample data are re-created by `build.sh`.
