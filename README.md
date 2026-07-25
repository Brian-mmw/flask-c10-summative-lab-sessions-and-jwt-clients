# Workout Tracker API (Session Auth)

## Description
A secure Flask REST API backend for a personal productivity app. Users can sign up,
log in, and manage their own private workout log. Authentication is session-based
(signed cookies) using Flask's built-in session with Flask-Bcrypt for password hashing.
Users can only view, create, update, or delete their **own** workouts — all resource
routes enforce ownership.

## Tech Stack
Flask, Flask-RESTful, Flask-SQLAlchemy, Flask-Migrate, Flask-Bcrypt, Marshmallow, Faker, SQLite

## Installation

```bash
git clone <your-repo-url>
cd <repo-name>
pipenv install
pipenv shell
```

Set up and migrate the database:

```bash
cd server
export FLASK_APP=app.py
flask db init
flask db migrate -m "create users and workouts tables"
flask db upgrade head
```

Seed the database with example users and workouts:

```bash
python seed.py
```

This prints sample login credentials (all seeded users share the password `password123`)
for testing.

## Running the App

```bash
cd server
flask run --port 5555
```

The server runs at `http://localhost:5555`.

### Connecting the provided frontend
This backend expects to be used with the **session-based** version of the provided
client app (`flask-c10-summative-lab-sessions-and-jwt-clients` repo). Because sessions
rely on a browser cookie, make sure:
- The frontend sends requests with `credentials: 'include'`.
- If frontend and backend run on different ports during local dev, either use the
  frontend's dev-server proxy (recommended, avoids CORS/cookie issues entirely) or
  configure CORS + `SameSite`/`Secure` cookie settings appropriately.

## Endpoints

### Auth

| Method | Route | Description |
|---|---|---|
| POST | `/signup` | Register a new user. Body: `{ "username": "string", "password": "string (min 6 chars)", "password_confirmation": "string" }`. Logs the user in (sets session cookie) and returns the created user. |
| POST | `/login` | Log in. Body: `{ "username": "string", "password": "string" }`. Sets session cookie on success. |
| DELETE | `/logout` | Clears the session cookie. |
| GET | `/check_session` | Returns the currently logged-in user (200) or `401` if no active session. |

All error responses use the shape `{ "errors": ["message 1", "message 2"] }` — a flat
array of strings, matching what the provided `client-with-sessions` frontend expects
(`err.errors.map(...)`).

### Workouts (all require an active session — `401` otherwise)

| Method | Route | Description |
|---|---|---|
| GET | `/workouts?page=1&per_page=10` | Paginated list of the **logged-in user's own** workouts. Returns `{ workouts, total, page, pages, per_page }`. |
| POST | `/workouts` | Create a workout for the logged-in user. Body: `{ "title": "string", "date": "YYYY-MM-DD", "duration_minutes": int, "notes": "string" }`. |
| GET | `/workouts/<id>` | Get a single workout — only if it belongs to the logged-in user, otherwise `404`. |
| PATCH | `/workouts/<id>` | Update a workout — only if it belongs to the logged-in user. Accepts any subset of the fields above. |
| DELETE | `/workouts/<id>` | Delete a workout — only if it belongs to the logged-in user. |

## Validations

**Table Constraints**
- `users.username` is unique
- `workouts.duration_minutes` must be > 0 (CHECK constraint)

**Model Validations**
- `User.username` cannot be empty
- `Workout.title` cannot be empty
- `Workout.duration_minutes` must be positive

**Schema Validations (Marshmallow)**
- `UserSchema.password` — minimum 6 characters, write-only (never serialized back)
- `UserSchema.password_confirmation` — required at signup; backend rejects the request if it doesn't match `password`
- `WorkoutSchema.duration_minutes` — required, minimum 1

## Security Notes
- Passwords are never stored in plain text — `Flask-Bcrypt` hashes them before saving,
  and the `password_hash` property raises an error if anything tries to read it back.
- Every `/workouts` route filters by `user_id=session['user_id']`, so a user can never
  see, edit, or delete another user's data — even by guessing IDs.
- `app.secret_key` is used to cryptographically sign session cookies; set the
  `SECRET_KEY` environment variable in production rather than relying on the dev default.
