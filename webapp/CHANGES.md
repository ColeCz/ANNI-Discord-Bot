
# Change Log – July 23, 2025


### ✅ Initial Setup and Fixes

- **Configured Django environment:**
  - Activated Python virtual environment (`venv`)
  - Installed dependencies via `requirements.txt`
  - Ensured `.env` file is correctly placed and referenced using `python-decouple`
  - Stubbed out backend database config to allow frontend development without PostgreSQL/Docker

---

### ✅ Routing and Views Setup

- Updated `form_site/settings.py` to:
  - Add `'forms'` to `INSTALLED_APPS`
  - Configure `STATICFILES_DIRS` and `TEMPLATES` directories for consistent styling and layout

- Created and registered view functions in `forms/views.py`:
  - `home_view`
  - `form_view`
  - `about_view`

- Defined app-level URL routes in `forms/urls.py` with proper `name=` attributes:
  - `/` → Home
  - `/form/` → Form
  - `/about/` → About

- Hooked app URLs into the main project via `form_site/urls.py`

---

### ✅ Template & Static Files

- Set up project-wide base layout:
  - Created `forms/templates/forms/base.html` to serve as the shared layout template
  - All pages (`home.html`, `form.html`, `about.html`) now extend `base.html`

- Added and tested global CSS:
  - Moved `styles.css` into `forms/static/`
  - Linked stylesheet in `base.html` using `{% static %}` tag

---

### ✅ Page Stubs

Created minimal templates as starting points:
- `home.html` — Default landing page
- `form.html` — Placeholder for form logic to be built later
- `about.html` — Informational page stub

Each page currently contains test headers and extends the shared base template.

---

### ✅ Testing

- Successfully ran development server (`python manage.py runserver`)
- Confirmed all pages load without error
- Verified that navigation links work and are correctly routed
