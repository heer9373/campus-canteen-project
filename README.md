# Campus Canteen Dynamic Smart-Menu & Analytics Engine (Python Edition)

Full implementation of the SRS using **FastAPI + SQLite (raw SQL)**. No Node.js,
no npm, no separate frontend server — everything runs from one Python process.

## Stack
- **Backend**: FastAPI, SQLite (`sqlite3` stdlib, raw SQL — no ORM), native WebSockets, JWT (`python-jose`), bcrypt
- **Frontend**: Plain HTML/CSS/JavaScript, served directly by FastAPI, connects via native browser WebSocket

## Requirement → Code Map

| Requirement | Where it's implemented |
|---|---|
| FR-1 Auth (JWT, HMAC-SHA256, 24h) | `app/routers/auth.py`, `app/auth.py` |
| FR-2 Slot allocation & capping (15-min, cap 30) | `app/utils/slots.py`, `app/routers/slots.py` |
| FR-3 Auto out-of-stock, live broadcast | `app/routers/menu.py` (`menu:updated` WS event) |
| FR-4 Dynamic discount (20% / final 60 min) | `app/utils/pricing.py` |
| FR-5 Kitchen Display System | `app/routers/orders.py` (`/kds`, status transitions), `app/static/kitchen.js` |
| FR-6 Real-time "order ready" push | `order:ready` WS event sent to a single user, `app/static/app.js` toast |
| NFR-1 Performance/concurrency | SQLite WAL mode, async FastAPI request handling |
| NFR-2 Password hashing (bcrypt, 10 rounds) | `app/auth.py` |
| NFR-3 Availability / daily backup | Background asyncio task in `app/main.py` (checks for 23:59 daily) |

## Setup

### 1. Install Python dependencies
```bash
cd canteen-py
pip install -r requirements.txt
```
If you're on Windows and see a `pip` warning about scripts not being on PATH, that's fine — just use `python -m pip install -r requirements.txt` instead.

### 2. (Optional) Edit `.env`
Change `JWT_SECRET` before deploying anywhere beyond your own laptop. You can also tweak slot size, discount %, and closing time here.

### 3. Seed a starter menu (recommended)
This populates the canteen with ~19 realistic cafe items (coffee, sandwiches, burgers, desserts, etc.), each with a real food photo, so the app looks alive immediately instead of showing an empty menu:
```bash
python seed.py
```
Safe to re-run — it skips items that already exist. Skip this step if you'd rather add items manually as Admin.

### 4. Run the server
```bash
uvicorn app.main:app --reload --port 8000
```
You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 5. Open the app
Go to **http://localhost:8000** in your browser. That's it — one process serves both the API and the frontend.

Register three accounts to try each role:
- **Student** — browse menu, pick a slot, place orders, see live "Ready" notifications
- **Kitchen Staff** — view the KDS board grouped by slot, advance order status
- **Admin** — add/edit menu items, adjust stock (triggers auto out-of-stock), view analytics


## Adding food photos
The app does **not** depend on any online photo service. Photos live inside the project:

1. Save photos into `app/static/img/food/`, named after the menu item
   (e.g. `cappuccino.jpg`, `veg-burger.jpg`). The full list of expected filenames is in
   `app/static/img/food/README.txt`.
2. Run `python seed.py` again. Items with a photo use it; items without one show a clean emoji tile.
3. Optional: `app/static/img/hero.jpg` becomes the landing-page hero photo.

Admins can also set a custom photo (any URL, or `/static/img/food/file.jpg`) when adding a menu item.
Free photo sources: unsplash.com, pexels.com, pixabay.com. Check each license before publishing publicly.

## Notes
- Database is a single SQLite file (`canteen.db`), created automatically on first run, in the project root.
- Real-time updates (FR-3, FR-6) use the browser's native `WebSocket` API talking to FastAPI's built-in WebSocket support — no external real-time library needed.
- Order status machine is enforced server-side: `Received → Preparing → Ready → Completed`, no skipping or reversing.
- All SQL is raw and visible in the router files — useful for showing query logic directly in a report/demo.
- Food photos are pulled live from [LoremFlickr](https://loremflickr.com) by keyword (e.g. `loremflickr.com/480/360/samosa,food`) — no API key needed, no images stored in the repo. Requires an internet connection to load images; if you're offline, the menu will still work but photos won't render.
- Admin can set a custom `image_url` per item when adding it; if left blank, one is auto-generated from the item's name.

## What makes this a strong portfolio project
- Full CRUD + auth + role-based access control (student / kitchen / admin)
- Real-time features via native WebSockets (no polling)
- Atomic transactions for concurrent-safe slot booking and stock management
- A genuine business rule engine (time-based dynamic discounting)
- Clean separation of concerns: routers, schemas, utils, raw SQL data layer
- A visually polished, image-rich frontend — not just a bare CRUD UI
- Fully testable via the auto-generated Swagger docs at `/docs`

## Interactive API docs
FastAPI auto-generates interactive API documentation. With the server running, visit:
- **http://localhost:8000/docs** (Swagger UI)
- **http://localhost:8000/redoc** (ReDoc)

Both let you try every endpoint directly in the browser — handy for demoing the SRS requirements without writing any curl commands.
