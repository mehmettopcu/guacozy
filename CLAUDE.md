# CLAUDE.md

Guidance for AI assistants (and humans) working in this repository.

## What Guacozy is

Guacozy is an HTML5, browser-based **RDP / VNC / SSH remote connection manager**
built on [Apache Guacamole™](https://guacamole.apache.org/) technology. Users
manage connections in a web UI and open remote desktop/terminal sessions in
browser tabs. Guacozy does **not** implement the remote protocols itself — it
relies on an external **guacd** daemon (shipped separately) to speak
RDP/VNC/SSH, and proxies the Guacamole protocol between the browser and guacd
over a WebSocket.

Official docs: https://guacozy.readthedocs.io (source under `docs/`).

## Repository layout

```
guacozy/
├── guacozy_server/          Django backend (Python 3.7, Django 2.2)
│   ├── manage.py
│   ├── requirements*.txt
│   ├── guacozy_server/       Django project (settings, routing, ASGI/WSGI)
│   │   ├── settings.py
│   │   ├── urls.py           HTTP URL routing (admin, api, accounts)
│   │   ├── routing.py        Channels/WebSocket routing
│   │   ├── asgi.py / wsgi.py
│   │   └── guacdproxy/       WebSocket consumer that proxies to guacd
│   ├── backend/             Main app: models, api, admin, rules, commands
│   └── users/               Custom User model + auth views/forms
├── frontend/                React SPA (Create React App, React 16)
│   └── src/
│       ├── Api/             axios API client (GuacozyApi.js)
│       ├── Components/      App, Sidebar, GuacViewer, Modals, ContextMenu
│       ├── Context/         React context (AppContext)
│       ├── Layout/          FlexLayout tab management
│       └── Utils/
├── docker/                  entrypoint.sh, nginx, supervisor configs (prod image)
├── docs/                    mkdocs documentation source
├── Dockerfile               Multi-stage production image (frontend + server)
├── docker-compose.yml       DEV stack (separate django + react + guacd + db)
├── docker-compose-qa.yml    QA stack (builds the production image)
└── hooks/                   DockerHub build hooks
```

## Architecture

### Two-tier app
- **Backend** (`guacozy_server/`): Django + Django REST Framework for the HTTP
  API and admin, plus **Django Channels** (ASGI) for the WebSocket tunnel.
- **Frontend** (`frontend/`): React SPA served at `/cozy/`. It calls the REST
  API and renders remote sessions using `guacamole-common-js` inside
  FlexLayout tabs.

### The connection flow (important)
1. User picks a connection in the React tree. The frontend `POST`s to
   `/api/tickets/` to obtain a **Ticket** (a short-lived UUID authorizing one
   session for one user — see `backend/models/ticket.py`).
2. The frontend opens a WebSocket to
   `/tunnelws/ticket/<uuid>/` with subprotocol `guacamole`.
3. `guacozy_server/guacdproxy/consumers.py` (`GuacamoleConsumer`, an
   `AsyncWebsocketConsumer`) validates the ticket, resolves the connection's
   Guacamole parameters + credentials, performs a handshake with **guacd**
   (via the `pyguacamole` / `guacamole` library), and then runs a bidirectional
   polling loop relaying Guacamole instructions between browser and guacd.
4. The guacd `sessionid` is stored on the ticket so reconnects and **shared**
   tickets attach to the same live session (screen sharing).

Read `guacdproxy/consumers.py` before touching anything about sessions,
reconnect, credential passthrough, or read-only/shared tickets. Note the
`allow_control` gate in `receive()` that drops mouse/key events for read-only
shared tickets, and the `4.size,1.1,1.0,1.0;` skip workaround in
`data_polling()`.

### Backend models (`backend/models/`)
- **Connection** — `PolymorphicModel` (django-polymorphic). Base class holds
  host/port/protocol/credentials; subclasses `ConnectionRdp`, `ConnectionSsh`,
  `ConnectionVnc` add protocol-specific params. `get_guacamole_parameters(user)`
  assembles the dict passed to guacd. Passwords use `EncryptedCharField`
  (django-encrypted-model-fields).
- **Folder / FolderPermission** — MPTT tree (`django-mptt`). Access is granted
  per-folder to a user or group and **inherited by descendants** (see
  `rules.py`).
- **Credentials** — `StaticCredentials` (shared), `NamedCredentials` +
  `PersonalNamedCredentials` (per-user secrets referenced by a shared
  `@name`). Blank passwords on save preserve the previously stored value.
- **Ticket** — authorization to open a session; `parent` links a shared ticket
  to its original; `control` toggles read-only; `check_validity()` self-deletes
  expired tickets.
- **GuacdServer** — a guacd endpoint (host/port). **AppSettings** — singleton
  holding the default guacd server. **TicketLog** — audit log of ticket actions.

### Permissions (`backend/rules.py`)
Uses **django-rules** (`AUTHENTICATION_BACKENDS` includes
`ObjectPermissionBackend`). Object-level predicates:
- Folder access via `has_direct_permission` / `has_inherited_permission`
  (walks MPTT ancestors; also checks **LDAP** groups when
  `AUTH_LDAP_FIND_GROUP_PERMS` is on).
- Ticket and PersonalNamedCredentials ownership checks.
API viewsets in `backend/api/views.py` layer additional queryset filtering via
`backend/api/utils.py` (`user_allowed_folders*`). Model-level CRUD perms for the
`ConnectionsAdmin` group are seeded by `manage.py initgroups`.

### REST API (`backend/api/`)
DRF `DefaultRouter` under `/api/`: `connections`, `folders`, `tickets`, `users`.
Extra routes: `connections/tree` & `folders/tree` (hierarchical, permission-
filtered), `tickets/duplicate/<uuid>/` (new independent session),
`tickets/share/<uuid>/` (share a live session with another user). Auth is
**session-based** (`SessionAuthentication`), so browser CSRF applies — the
frontend axios client sends `X-CSRFToken`.

### Frontend (`frontend/src/`)
- Entry `index.js` → `Components/App/App.js`. Global state in
  `Context/AppContext.js`; tab layout in `Layout/` (FlexLayout).
- `Api/GuacozyApi.js` — the single axios client for all `/api/` calls.
- `Components/GuacViewer/` — wraps `guacamole-common-js`, opens the
  `/tunnelws/...` WebSocket, and renders the display.
- `settings.js` — client constants (screen sizes, ticket validity options,
  settings links into `/admin/` and `/api/`).
- `setupProxy.js` — in dev, proxies `/api`, `/tunnelws` (ws), `/admin`,
  `/accounts`, `/staticfiles` to the Django server so the SPA and API share an
  origin.

## Development

Two dev servers with hot-reload; the React dev server proxies API/WS calls to
Django (see `frontend/src/setupProxy.js`).

### Local (no Docker)
```bash
# Backend — from guacozy_server/
pip install -r requirements-ldap.txt   # or requirements-base.txt (no LDAP)
python manage.py migrate
python manage.py createsuperuser
python manage.py initguacd             # optional: default guacd server ref
python manage.py initgroups            # optional: ConnectionsAdmin group perms
python manage.py runserver             # http://localhost:8000

# Frontend — from frontend/
npm install
npm run start                          # http://localhost:3000  (use THIS in browser)
```
Open the app at **http://localhost:3000/**; Django admin at
`http://localhost:8000/admin/`. Copy `guacozy_server/.env.example` to
`guacozy_server/.env` for local settings (django-environ reads it).

### Docker dev stack
```bash
docker-compose up --build              # django(:8000) + react(:3000) + guacd + postgres
docker-compose exec django python ./manage.py migrate
docker-compose exec django python ./manage.py createsuperuser
```

### Useful management commands (`backend/management/commands/`)
- `initguacd` — create the default GuacdServer reference.
- `initgroups` — seed the `ConnectionsAdmin` group's model permissions.
- `generate_encryption_key` — produce a value for `FIELD_ENCRYPTION_KEY`
  (provided by the `django-encrypted-model-fields` package, not local code).

### Tests / lint
There is effectively no automated test suite (`backend/tests.py` is a stub) and
no configured linter beyond CRA's `react-app` ESLint preset. `npm test` runs
the CRA test runner (no meaningful tests present). Verify changes by running
the stack and exercising the flow manually.

## Configuration (env vars)

Read by `guacozy_server/settings.py` via **django-environ**:
- `DEBUG`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_TIME_ZONE`
- `DJANGO_DB_URL` — e.g. `postgres://postgres@db:5432/postgres`
  (default `sqlite:///db.sqlite3`)
- `FIELD_ENCRYPTION_KEY` — **encrypts stored passwords**. Changing it makes
  existing stored passwords unreadable. Generate with
  `manage.py generate_encryption_key`.
- `CACHE_URL` — `memcache://...` in prod (shared session store across Daphne
  workers), `locmemcache://` default. Sessions use the cache backend, except in
  `DEBUG` + locmem where a file-based session store under `guacozy_server/tmp/`
  is used.
- `SUPERUSER_NAME` / `SUPERUSER_EMAIL` / `SUPERUSER_PASSWORD` — used by the
  production `entrypoint.sh` to auto-create an admin (defaults to
  `admin`/`admin`).

**LDAP** (optional): create `guacozy_server/guacozy_server/ldap_config.py`
(template: `ldap_config.py.example`). Its presence enables `LDAPBackend` and the
`AUTH_LDAP_*` settings; requires the `requirements-ldap.txt` deps.

## Production image & runtime

`Dockerfile` is multi-stage: builds the React app (`npm run build`), builds
Python wheels, then assembles a final image running **supervisord**
(`docker/supervisor-app.ini`) with:
- **Daphne** (2 ASGI workers) serving `guacozy_server.asgi:application`,
- **nginx** terminating TLS and serving static + the built SPA,
- **memcached** (unix socket) as the shared session/cache store.

`docker/entrypoint.sh` runs migrations, ensures the superuser exists, runs
`collectstatic`, `initgroups`, `initguacd`, and generates a self-signed TLS cert
if none is mounted at `/ssl/`. The image exposes ports 80 and 443. A separate
**guacd** container/service is always required. `docker-compose-qa.yml` builds
and runs this production image.

## Conventions & gotchas

- **Django 2.2 / DRF 3.10 / Channels 2.3** — old APIs; match existing patterns,
  don't assume modern Django/Channels 3+ idioms.
- Models live in a **split `backend/models/` package** (not a single
  `models.py`); re-export new models from `backend/models/__init__.py` so
  `from backend.models import X` keeps working. Admin classes mirror this under
  `backend/admin/`.
- Connections are **polymorphic** — query via `Connection` and let
  django-polymorphic return the right subclass; add protocol params on the
  subclass model + its admin.
- Passwords/secrets use `EncryptedCharField`; saving a **blank** password keeps
  the existing stored value (see `Connection.save` / `CredentialsFieldsMixin`).
- Anything session/tunnel-related is **async** (Channels). Wrap DB access with
  `database_sync_to_async` / `sync_to_async`, following `consumers.py`.
- API access is session + CSRF based; frontend requests must carry the CSRF
  token (handled centrally in `Api/GuacozyApi.js`).
- After model changes, create and commit migrations
  (`python manage.py makemigrations`). Migrations live in
  `backend/migrations/` and `users/migrations/`.
- Line endings are normalized via `.gitattributes`; keep `*.sh` and `docker/*`
  as LF.

## Git workflow

Default branch is `master` (development historically merged from a `develop`
branch). Do not push to `master` unless explicitly asked — work on the
designated feature branch, commit with clear messages, and open PRs only when
requested.
