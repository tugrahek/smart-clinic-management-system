# Smart Clinic Appointment & Patient Flow Management System

A layered Flask prototype for hospital appointment scheduling, role-based portal access, and patient flow tracking.

This project was built as a software engineering course prototype, but it is organized to grow into a more complete hospital information system over time.

## Overview

Smart Clinic is a server-rendered full-stack web application that combines:

- a public-facing hospital landing page
- role-based authentication
- appointment management
- doctor availability management
- patient check-in and waiting room flow tracking

The project follows a layered MVC-style structure so new modules such as prescriptions, lab results, billing, and reporting can be added without rewriting the entire system.

## Main Features

- Public hospital landing page
- Role-based registration for:
  - Patient
  - Doctor
  - Secretary
- Username and password login
- Password hashing
- Doctor availability creation
- Appointment booking based on doctor schedule
- Appointment conflict prevention
- Patient check-in
- Patient flow state updates:
  - `waiting`
  - `in_exam`
  - `completed`
- Reserved UI entries for future modules with a clear not-implemented message

## Tech Stack

- **Backend:** Flask
- **Database:** PostgreSQL
- **ORM:** Flask-SQLAlchemy / SQLAlchemy
- **Frontend:** Jinja templates, HTML, CSS, small JavaScript helpers
- **Testing:** pytest

## Architecture

The application uses a layered architecture:

- **View layer**  
  HTML templates, CSS, and browser interactions

- **Controller layer**  
  Flask blueprints and route handlers

- **Service layer**  
  Business logic such as authentication, appointment validation, and patient flow transitions

- **Repository layer**  
  Database access and query coordination

- **Model layer**  
  SQLAlchemy models backed by PostgreSQL

### Request Flow

`Browser -> Controller -> Service -> Repository -> PostgreSQL -> Template Render -> Browser`

## Project Structure

```text
.
├── app.py
├── clinic/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── controllers/
│   ├── extensions.py
│   ├── models/
│   ├── repositories/
│   └── services/
├── docs/
├── schema.sql
├── static/
│   ├── css/
│   ├── images/
│   └── js/
├── templates/
├── tests/
└── requirements.txt
```

### What belongs where?

- `clinic/controllers/`  
  Handles requests, form submissions, redirects, and template selection

- `clinic/services/`  
  Holds business rules and core application logic

- `clinic/repositories/`  
  Centralizes database operations

- `clinic/models/`  
  Defines database entities such as users, patients, doctors, appointments, and availability

- `templates/`  
  Frontend HTML views rendered by Flask

- `static/`  
  CSS, JavaScript, and image assets

## Authentication and Security

- Passwords are **not stored in plain text**
- Passwords are hashed with Werkzeug security helpers
- Password checks are performed through secure hash verification
- Session cookies are configured with:
  - `HttpOnly`
  - `SameSite=Lax`
- Registration validates:
  - duplicate usernames
  - duplicate email addresses
  - password confirmation
  - required role-specific fields

## Database Design

The current schema includes:

- `users`
- `departments`
- `doctor_profiles`
- `patients`
- `doctor_availabilities`
- `appointments`
- `patient_flow`
- `medical_records`
- `prescriptions`

SQL schema file:

- [schema.sql](./schema.sql)

## Setup

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Default local database connection:

```env
DATABASE_URL=postgresql+psycopg://smart_clinic:smart_clinic@localhost:5432/smart_clinic
FLASK_SECRET_KEY=change-this-development-key
FLASK_DEBUG=1
```

### 4. Create the PostgreSQL database

```bash
createuser smart_clinic
createdb smart_clinic -O smart_clinic
psql -d smart_clinic -c "ALTER USER smart_clinic WITH PASSWORD 'smart_clinic';"
```

### 5. Initialize demo data

```bash
flask --app app init-db
```

### 6. Run the application

```bash
flask --app app run --debug --port 5001
```

## Demo Accounts

After running `init-db`, these accounts are available:

| Role | Username | Password |
|---|---|---|
| Secretary | `aylin.demir` | `clinic123` |
| Doctor | `deniz.arslan` | `clinic123` |
| Patient | `mert.kaya` | `clinic123` |

## Available Routes

### Public

- `/`
- `/login`
- `/register`

### Authenticated

- `/dashboard`
- `/appointments/`
- `/appointments/new`
- `/availability/`
- `/patient-flow/`

## Tests

Run the test suite with:

```bash
python -m pytest
```

The current tests cover:

- authentication login logic
- patient flow transitions
- time slot generation

## Current Prototype Scope

Implemented core workflows:

- register and login
- view role-based dashboards
- define doctor availability
- create appointments
- prevent doctor time conflicts
- check patients in
- update patient flow status

## Planned Future Modules

Reserved modules already visible in the UI:

- Prescription writing
- Laboratory results
- Billing and invoices
- Detailed patient registration
- Medical history
- Reports

Unimplemented actions currently return:

`This function has not been implemented yet`

## Notes

This repository is structured to support both:

- course presentation requirements
- future feature expansion with minimal restructuring

