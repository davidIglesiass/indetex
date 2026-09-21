# Feature: fullstack-backend

## Objective
`indetex` is a Flask app that only renders static theme templates (no forms
wired, no DB, no auth). User asked to implement the full stack so the
functionality the templates promise (login/registro, product CRUD, carrito,
favoritos, contacto, comentarios de blog) actually works.

## Why
Confirmed via grep: zero `{% for %}` / `{% if %}` in any template, all
forms have empty/missing `action`, wishlist button only fires a client-side
SweetAlert with no persistence, `app.py` has 13 routes that all just call
`render_template()`.

## Scope
Add a real backend: SQLite via SQLAlchemy, session-based auth with hashed
passwords, product CRUD backed by the DB, a persisted cart and wishlist per
user, a contact form that stores messages, and blog comments that persist
and render.

## Constraints
- No new deps beyond Flask + Flask-SQLAlchemy + Werkzeug's existing
  `generate_password_hash` (already a Flask dependency). No Flask-Login —
  session dict is enough for this app's size.
- Don't touch the theme HTML/CSS beyond what's needed to add Jinja loops,
  form actions, and CSRF-free POST handlers.
- SQLite file-based DB (no external service) — keeps Docker setup unchanged.
- Route names/URLs in app.py stay the same where templates already link to
  them (avoid breaking existing `url_for` usage... there is none — templates
  use static hrefs, so link updates are needed anyway to point at real ids).

## TDD mode
Disabled — no test runner configured for this project (no requirements.txt
entry, no test files existed before this feature). Verification is
functional: build the Docker image, hit each route with curl/browser, check
DB state after each action.

## Tasks

- [x] T1: Data layer — `database.py` (sqlite3, not an ORM — see Route
      declaration) with `user`, `product`, `cart_item`, `wishlist_item`,
      `contact_message`, `comment` tables in `schema.sql`, `init_app`
      wired into `app.py`, seeded with the theme's 16 existing product
      images/names/prices. Commit `198c834`.
- [x] T2: Auth — `/registro`, `/login`, `/logout`, `werkzeug.security`
      password hashing, `session['user_id']`/`session['is_admin']`,
      `login_required`/`admin_required` decorators guarding `/AdminPro`,
      `/crearProducto`, `/EditarProducto/<id>`, `/EliminarProducto/<id>`,
      cart and wishlist routes. `login.html`/`registro.html` wired to real
      POST endpoints (also fixed registro's duplicate `name="nombre"`
      field). Commits `c395788`, `5827c7e`.
- [x] T3: Product CRUD — create/edit/delete backed by the DB,
      `adminProduct.html` and `baseProducto.html` (shared by home + catalog)
      converted to `{% for product in products %}` loops,
      `product-detail.html` driven by `/DetallePro/<int:product_id>`.
      Commits `c395788`, `5827c7e`.
- [x] T4: Cart — `/carrito/agregar/<id>` (POST), `/carrito/eliminar/<id>`
      (POST), `shoping-cart.html` renders real rows + server-computed
      total. Commits `c395788`, `5827c7e`.
- [x] T5: Wishlist — `/favoritos/agregar/<id>`, `/favoritos/eliminar/<id>`,
      `favoritos.html` renders the logged-in user's real rows. Commits
      `c395788`, `5827c7e`.
- [x] T6: Contact — `/contactanos` POST stores the message and flashes a
      confirmation. Commits `c395788`, `5827c7e`.
- [x] T7: Blog comments — `/BlogDetail/comentar` POST persists and renders
      under the post. Commits `c395788`, `5827c7e`.

## Authorized scope
Full stack per user's explicit choice ("Todo el stack") after being asked
to scope down. odd/tasks + Engram mirror created per ODD before first write.

## Route declaration
All tasks: **direct inline** (single developer, one coherent `app.py` +
`models.py` — splitting across delegated writers risks merge conflicts in
the same two files). Mapping already done inline via earlier grep/read
exploration in this session (>4 files read: app.py, login.html, registro.html,
crearProducto.html, editarProducto.html, adminProduct.html, product.html,
product-detail.html, favoritos.html, shoping-cart.html, contact.html,
blog-detail.html) — mapping trigger already satisfied before this file was
created.

## Acceptance criteria — all verified via curl against the built Docker image
- [x] `docker build` succeeds; every route returns 200 (public pages,
      `/DetallePro/1`, and `/AdminPro`, `/crearProducto`,
      `/EditarProducto/1`, `/ShopingCart`, `/Favoritos` with an admin
      session cookie).
- [x] Register → login → session persists → `/AdminPro` while logged out
      redirects to `/login` (302); logged in as a non-admin it also
      redirects to `/login`.
- [x] Creating a product via `/crearProducto` (id 17) showed up in both
      `/producto` and `/AdminPro`; editing it updated the catalog; deleting
      it removed it from both (verified by grep count before/after).
- [x] Add-to-cart persisted across requests — `/ShopingCart` showed the
      correct product name/price after a POST from a separate curl call,
      total computed server-side.
- [x] Add-to-wishlist persisted — `/Favoritos` showed the added product
      after a separate request.
- [x] Contact POST returned 302 (stored + flashed).
- [x] Blog comment POST returned 302 and the comment body appeared on the
      next `/BlogDetail` GET.

## Progress
- Branch: `feature/fullstack-backend` (was on `master`, branched before
  first write).
- Engram mirror: **pending** — no memory-write tool available in this
  session's toolset; local task file is authoritative until reconciled.
- Commits: `1e9301a` (Docker/gitignore chore), `198c834` (T1 data layer),
  `c395788` (T2-T7 backend routes), `5827c7e` (T2-T7 template wiring).

## Known simplifications (not bugs, deliberately out of scope)
- Wishlist add is a GET link (`agregarFavorito`), not a POST — the theme's
  heart icons are plain `<a>` tags; rewriting every card into a `<form>`
  wasn't worth it for a demo app. Noted with a `ponytail:` comment in
  `app.py`.
- Admin-created products always land in the `women` isotope category —
  the create/edit form only exposes talla/color pickers, not a category
  select.
- Size/color selects in product-detail and crear/editarProducto are
  decorative — the `Product` model doesn't track variants.
- Coupon field on the cart page and the isotope filter/sort UI (price
  range, color, tags) remain client-side decorative, as they were before.

## Next step
None — all 7 tasks done and verified. User may want a real admin seed
account (currently promoting a user to admin requires a manual UPDATE on
the sqlite row) or variant/category support if the product model needs to
grow.
