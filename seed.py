"""
seed.py
Populates the canteen with a realistic starter menu so the app looks
alive on first run — useful for demos, screenshots, and portfolio use.

Run with:  python seed.py
Safe to re-run: existing items are refreshed rather than duplicated.

Images: each item gets a keyword-based photo URL plus an emoji fallback.
If the image service is unreachable (offline demo, blocked network), the
frontend renders a styled emoji tile instead of a broken image icon.
"""

import re
import sys
from pathlib import Path

from app.database import get_connection, init_db

PHOTO_DIR = Path(__file__).parent / "app" / "static" / "img" / "food"
PHOTO_EXTS = (".jpg", ".jpeg", ".png", ".webp")


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def local_photo_for(name: str):
    """Returns /static/img/food/<slug>.<ext> if the file exists, else None."""
    slug = slugify(name)
    for ext in PHOTO_EXTS:
        if (PHOTO_DIR / f"{slug}{ext}").exists():
            return f"/static/img/food/{slug}{ext}"
    return None

# (name, description, price, is_perishable, stock, image_keyword, emoji)
MENU_ITEMS = [
    # --- Beverages ---
    ("Cold Coffee",         "Chilled coffee blended with milk and ice cream",       60, False, 40, "iced-coffee",    "🧋"),
    ("Cappuccino",          "Freshly brewed espresso topped with steamed milk",     50, False, 40, "cappuccino",     "☕"),
    ("Masala Chai",         "Classic Indian spiced tea, brewed strong",             20, True,  60, "chai-tea",       "🍵"),
    ("Fresh Lime Soda",     "Sweet and tangy lime soda, served chilled",            35, True,  30, "lemonade",       "🥤"),
    ("Iced Tea",            "Refreshing peach iced tea over ice",                   45, True,  30, "iced-tea",       "🧊"),
    ("Chocolate Milkshake", "Thick chocolate shake topped with whipped cream",      70, False, 25, "milkshake",      "🥛"),

    # --- Snacks & Fast Food ---
    ("Veg Sandwich",        "Grilled sandwich with fresh vegetables and chutney",   50, True,  30, "sandwich",       "🥪"),
    ("Grilled Cheese",      "Melted cheese between crispy golden bread",            55, True,  25, "grilled-cheese", "🧀"),
    ("Samosa",              "Crispy fried pastry with spiced potato filling",       15, True,  50, "samosa",         "🥟"),
    ("French Fries",        "Crispy golden fries served with ketchup",              45, True,  40, "french-fries",   "🍟"),
    ("Veg Burger",          "Crispy veg patty burger with lettuce and mayo",        65, True,  25, "burger",         "🍔"),
    ("Chicken Burger",      "Grilled chicken patty with cheese and special sauce",  90, True,  20, "chicken-burger", "🍔"),
    ("Spring Rolls",        "Crispy vegetable spring rolls with sweet chili sauce", 55, True,  20, "spring-rolls",   "🥠"),
    ("Veg Pasta",           "Creamy white sauce pasta with mixed vegetables",       80, True,  20, "pasta",          "🍝"),
    ("Hakka Noodles",       "Stir-fried noodles tossed with vegetables and soy",    75, True,  20, "noodles",        "🍜"),
    ("Margherita Pizza",    "Classic cheese and tomato pizza slice",                60, True,  25, "pizza",          "🍕"),

    # --- Desserts ---
    ("Chocolate Brownie",   "Rich, fudgy brownie served warm",                      45, True,  20, "brownie",        "🍫"),
    ("Blueberry Muffin",    "Soft muffin loaded with blueberries",                  40, True,  20, "muffin",         "🧁"),
    ("Glazed Donut",        "Classic sugar-glazed donut",                           35, True,  25, "donut",          "🍩"),
]


def seed():
    init_db()
    conn = get_connection()

    # `emoji` was added after the first release, so older databases won't have
    # the column. Add it on the fly rather than forcing a full DB reset.
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(menu_items)").fetchall()]
    if "emoji" not in cols:
        conn.execute("ALTER TABLE menu_items ADD COLUMN emoji TEXT")
        conn.commit()

    inserted = 0
    updated = 0
    for idx, (name, description, price, perishable, stock, keyword, emoji) in enumerate(MENU_ITEMS):
        # `lock` keeps the same photo for an item across reloads instead of
        # reshuffling the image on every page refresh.
        # Photos are served from inside the project (no external service, works
        # offline). With no local photo the card shows a designed emoji tile.
        image_url = local_photo_for(name)
        if image_url is None and "--remote-photos" in sys.argv:
            # Opt-in only: third-party placeholder photos. Needs internet and the
            # service being reachable from your network, so not the default.
            image_url = f"https://loremflickr.com/480/360/{keyword}?lock={idx + 101}"
        existing = conn.execute("SELECT id FROM menu_items WHERE name = ?", (name,)).fetchone()

        if existing:
            conn.execute(
                "UPDATE menu_items SET emoji = ?, image_url = ?, description = ? WHERE id = ?",
                (emoji, image_url, description, existing["id"]),
            )
            updated += 1
            continue

        conn.execute(
            """
            INSERT INTO menu_items
                (name, description, price, is_perishable, stock_count, is_out_of_stock, image_url, emoji)
            VALUES (?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (name, description, price, int(perishable), stock, image_url, emoji),
        )
        inserted += 1

    conn.commit()
    conn.close()
    with_photo = sum(1 for n, *_ in MENU_ITEMS if local_photo_for(n))
    print(f"Seed complete: {inserted} new items added, {updated} existing items refreshed.")
    print(f"Photos found in app/static/img/food/: {with_photo} of {len(MENU_ITEMS)} items "
          f"(the rest show an emoji tile).")


if __name__ == "__main__":
    seed()
