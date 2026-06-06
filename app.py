import os
import sqlite3
from datetime import datetime
from flask import Flask, g, request, jsonify, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "wander.db")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-secret-key")


def get_db():
    db = getattr(g, "db", None)
    if db is None:
        db = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        db.row_factory = sqlite3.Row
        g.db = db
    return db


@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def dict_from_row(row):
    return dict(row) if row else None


def init_db():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            is_admin INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS destinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            destination_name TEXT NOT NULL UNIQUE,
            added_by_admin INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS explored_destinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            destination_id INTEGER NOT NULL,
            budget INTEGER NOT NULL,
            days INTEGER NOT NULL,
            travelers INTEGER NOT NULL,
            explored_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(destination_id) REFERENCES destinations(id)
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS recommendation_places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            destination_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            place_name TEXT NOT NULL,
            description TEXT,
            rating REAL,
            budget_tier TEXT,
            image_url TEXT,
            google_maps_link TEXT,
            added_by_admin INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(destination_id) REFERENCES destinations(id)
        )
        """
    )
    db.commit()


def seed_data():
    db = get_db()
    row = db.execute("SELECT COUNT(1) AS cnt FROM users").fetchone()
    if row["cnt"] == 0:
        users = [
            {"name": "Administrator", "email": "admin", "password": generate_password_hash("admin123"), "is_admin": 1},
            {"name": "Diya Kathiria", "email": "diya.kathiria125624@marwadiuniversity.ac.in", "password": generate_password_hash("password123"), "is_admin": 0},
            {"name": "Krish Kathiria", "email": "krishkathiria46@gmail.com", "password": generate_password_hash("password123"), "is_admin": 0},
        ]
        for user in users:
            db.execute(
                "INSERT INTO users (name, email, password, is_admin) VALUES (?, ?, ?, ?)",
                (user["name"], user["email"], user["password"], user["is_admin"]),
            )

    row = db.execute("SELECT COUNT(1) AS cnt FROM destinations").fetchone()
    if row["cnt"] == 0:
        default_destinations = [
            "Agra", "Ahmedabad", "Aizawl", "Ajmer", "Alappuzha", "Almora", "Amarnath", "Amritsar",
            "Andaman and Nicobar Islands", "Araku Valley", "Auli", "Aurangabad", "Ayodhya", "Badami",
            "Bangalore", "Baroda", "Bhopal", "Bhubaneswar", "Bhuj", "Bikaner", "Bodh Gaya", "Chandigarh",
            "Chennai", "Cherrapunji", "Chikkamagaluru", "Chittorgarh", "Coorg", "Darjeeling", "Dehradun",
            "Delhi", "Deoghar", "Dhanaulti", "Dharamshala", "Diu", "Dwarka", "Fatehpur Sikri", "Gandhinagar",
            "Gangtok", "Girinagar", "Goa", "Gokarna", "Gulmarg", "Gurugram", "Gwalior", "Hampi", "Haridwar",
            "Havelock Island", "Hyderabad", "Imphal", "Indore", "Jabalpur", "Jaipur", "Jaisalmer", "Jammu",
            "Jamnagar", "Jodhpur", "Junagadh", "Kanyakumari", "Kargil", "Kavaratti", "Kaziranga", "Kedarnath",
            "Khajuraho", "Kochi", "Kolkata", "Konark", "Kullu", "Kumbhalgarh", "Kutch", "Leh Ladakh",
            "Lonavala", "Lucknow", "Madurai", "Mahabaleshwar", "Mahabalipuram", "Manali", "Manikaran",
            "Mount Abu", "Mumbai", "Munnar", "Mussoorie", "Mysore", "Nagpur", "Nainital", "Nashik", "Ooty",
            "Pachmarhi", "Pahalgam", "Palitana", "Patna", "Pondicherry", "Pune", "Puri", "Rameshwaram",
            "Ranchi", "Ranthambore", "Rishikesh", "Saputara", "Sarnath", "Shillong", "Shimla", "Somnath",
            "Spiti Valley", "Srinagar", "Sundarbans", "Surat", "Tawang", "Thanjavur", "Tirupati", "Udaipur",
            "Ujjain", "Vapi", "Varanasi", "Varkala", "Vijayawada", "Visakhapatnam", "Vrindavan", "Wayanad"
        ]
        for name in default_destinations:
            db.execute(
                "INSERT INTO destinations (destination_name, added_by_admin) VALUES (?, 1)",
                (name,),
            )

    row = db.execute("SELECT COUNT(1) AS cnt FROM recommendation_places").fetchone()
    if row["cnt"] == 0:
        default_places = [
            {"destination": "Goa", "category": "restaurants", "place_name": "Curlies Beach Shack", "description": "Famous beachside shack offering fresh seafood, Goan curries, and stunning ocean views.", "rating": 4.4, "budget_tier": "Medium", "image_url": "https://images.unsplash.com/photo-1590050752117-238cb0fb12b1?auto=format&fit=crop&w=600&q=80", "google_maps_link": ""},
            {"destination": "Goa", "category": "restaurants", "place_name": "Gunpowder", "description": "Acclaimed restaurant serving rich, spicy South Indian coastal cuisine in a beautiful garden setting.", "rating": 4.6, "budget_tier": "Medium", "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80", "google_maps_link": ""},
            {"destination": "Goa", "category": "restaurants", "place_name": "Thalassa", "description": "Greek tavern perched on a hilltop in Siolim, offering legendary sunset views and Mediterranean platters.", "rating": 4.5, "budget_tier": "High", "image_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=600&q=80", "google_maps_link": ""},
            {"destination": "Goa", "category": "restaurants", "place_name": "The Black Sheep Bistro", "description": "Contemporary fine dining in Panaji focusing on global street food flavors with farm-to-table local ingredients.", "rating": 4.7, "budget_tier": "High", "image_url": "https://images.unsplash.com/photo-1552566626-52f8b828add9?auto=format&fit=crop&w=600&q=80", "google_maps_link": ""},
            {"destination": "Goa", "category": "hotels", "place_name": "Taj Exotica Resort & Spa", "description": "Luxury Mediterranean-style oasis perched directly on the calm white sands of Benaulim Beach.", "rating": 4.8, "budget_tier": "High", "image_url": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=600&q=80", "google_maps_link": ""},
            {"destination": "Goa", "category": "hotels", "place_name": "W Goa", "description": "Vibrant beachside luxury resort situated on Vagator beach featuring modern interior design and pool party lounges.", "rating": 4.7, "budget_tier": "High", "image_url": "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=600&q=80", "google_maps_link": ""},
            {"destination": "Goa", "category": "hotels", "place_name": "Alila Diwa Goa", "description": "A premium eco-friendly resort in South Goa, surrounded by lush, sprawling green rice plantations.", "rating": 4.6, "budget_tier": "Medium", "image_url": "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=600&q=80", "google_maps_link": ""},
            {"destination": "Goa", "category": "hotels", "place_name": "Cidade de Goa", "description": "A breathtaking beachfront structural hotel designed by Charles Correa reflecting historic Portuguese hamlets.", "rating": 4.4, "budget_tier": "Medium", "image_url": "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=600&q=80", "google_maps_link": ""},
            {"destination": "Goa", "category": "attractions", "place_name": "Aguada Fort", "description": "Historic 17th-century Portuguese lighthouse and coastal fortress looking out over the Arabian Sea.", "rating": 4.5, "budget_tier": "Low", "image_url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=600&q=80", "google_maps_link": ""},
            {"destination": "Goa", "category": "attractions", "place_name": "Baga Beach", "description": "One of the most lively coastal paths in North Goa, ideal for sunset views, water sports, and nightlife lanes.", "rating": 4.3, "budget_tier": "Low", "image_url": "https://images.unsplash.com/photo-1519046904884-53103b34b206?auto=format&fit=crop&w=600&q=80", "google_maps_link": ""},
            {"destination": "Goa", "category": "attractions", "place_name": "Dudhsagar Falls", "description": "A magnificent four-tiered majestic waterfall cascading through the Western Ghats mountain forests.", "rating": 4.7, "budget_tier": "Low", "image_url": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=600&q=80", "google_maps_link": ""},
            {"destination": "Goa", "category": "attractions", "place_name": "Basilica of Bom Jesus", "description": "UNESCO World Heritage site holding the sacred mortal remains of St. Francis Xavier in Old Goa.", "rating": 4.6, "budget_tier": "Low", "image_url": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?auto=format&fit=crop&w=600&q=80", "google_maps_link": ""},
            {"destination": "Agra", "category": "restaurants", "place_name": "Peshawri", "description": "Award-winning restaurant offering legendary North-West frontier tandoori cuisine and kebabs.", "rating": 4.8, "budget_tier": "High", "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80", "google_maps_link": ""},
            {"destination": "Agra", "category": "restaurants", "place_name": "Sinchian Rogue Bistro", "description": "Top rooftop culinary views paired with elegant regional street food platters and local curries.", "rating": 4.3, "budget_tier": "Medium", "image_url": "https://images.unsplash.com/photo-1590050752117-238cb0fb12b1?auto=format&fit=crop&w=600&q=80", "google_maps_link": ""},
            {"destination": "Agra", "category": "restaurants", "place_name": "Dasaprakash", "description": "Highly rated establishment renowned for its incredibly delicious and authentic South Indian vegetarian thalis.", "rating": 4.4, "budget_tier": "Low", "image_url": "https://images.unsplash.com/photo-1610192244261-3f33de3f55e4?auto=format&fit=crop&w=600&q=80", "google_maps_link": ""},
            {"destination": "Agra", "category": "restaurants", "place_name": "Joney's Place", "description": "A charming, historic traveler hotspot serving quick, hot, and delicious creamy lassis.", "rating": 4.5, "budget_tier": "Low", "image_url": "https://images.unsplash.com/photo-1565299624946-b28f40a0638b?auto=format&fit=crop&w=600&q=80", "google_maps_link": ""},
            {"destination": "Agra", "category": "hotels", "place_name": "The Oberoi Amarvilas", "description": "Unmatched ultra-luxury resort situated just 600 meters from the majestic Taj Mahal complex.", "rating": 4.9, "budget_tier": "High", "image_url": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=600&q=80", "google_maps_link": ""},
            {"destination": "Agra", "category": "hotels", "place_name": "ITC Mughal Agra", "description": "Luxury sprawling property blending royal Mughal architecture with state-of-the-art modern amenities.", "rating": 4.6, "budget_tier": "High", "image_url": "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=600&q=80", "google_maps_link": ""},
            {"destination": "Agra", "category": "hotels", "place_name": "Radisson Hotel Agra", "description": "Comfortable urban stay with an incredible rooftop pool overlooking city monuments.", "rating": 4.3, "budget_tier": "Medium", "image_url": "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=600&q=80", "google_maps_link": ""},
            {"destination": "Agra", "category": "hotels", "place_name": "Trident Agra", "description": "Beautiful low-rise structure featuring red stone layouts and classic manicured courtyards.", "rating": 4.5, "budget_tier": "Medium", "image_url": "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=600&q=80", "google_maps_link": ""},
            {"destination": "Agra", "category": "attractions", "place_name": "The Taj Mahal", "description": "World-famous ivory-white marble mausoleum and globally iconic architectural wonder.", "rating": 5.0, "budget_tier": "Low", "image_url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=600&q=80", "google_maps_link": ""},
            {"destination": "Agra", "category": "attractions", "place_name": "Agra Fort", "description": "Grand imperial walled city structure showcasing beautiful palaces and historical royal courts.", "rating": 4.7, "budget_tier": "Low", "image_url": "https://images.unsplash.com/photo-1614082242765-7c98ca0f3df7?auto=format&fit=crop&w=600&q=80", "google_maps_link": ""},
            {"destination": "Agra", "category": "attractions", "place_name": "Fatehpur Sikri", "description": "The legendary red sandstone ghost city founded by Emperor Akbar in the late 16th century.", "rating": 4.6, "budget_tier": "Low", "image_url": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?auto=format&fit=crop&w=600&q=80", "google_maps_link": ""},
            {"destination": "Agra", "category": "attractions", "place_name": "Mehtab Bagh", "description": "The moonlight garden square perfectly aligned across the Yamuna river offering views of the Taj.", "rating": 4.4, "budget_tier": "Low", "image_url": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=600&q=80", "google_maps_link": ""}
        ]

        destination_rows = db.execute("SELECT id, destination_name FROM destinations").fetchall()
        destination_map = {row["destination_name"]: row["id"] for row in destination_rows}

        for place in default_places:
            destination_id = destination_map.get(place["destination"])
            if not destination_id:
                continue
            db.execute(
                "INSERT INTO recommendation_places (destination_id, category, place_name, description, rating, budget_tier, image_url, google_maps_link, added_by_admin) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)",
                (
                    destination_id,
                    place["category"],
                    place["place_name"],
                    place["description"],
                    place["rating"],
                    place["budget_tier"],
                    place["image_url"],
                    place["google_maps_link"],
                ),
            )
    db.commit()


def query_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    row = get_db().execute("SELECT id, name, email, is_admin FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict_from_row(row)


@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "A3_planner.html")


@app.route("/api/session")
def session_info():
    user = query_current_user()
    if user:
        return jsonify({"user": user})
    return jsonify({"user": None})


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not name or not email or not password:
        return jsonify({"error": "name, email and password are required."}), 400
    if email == "admin":
        return jsonify({"error": "admin is reserved."}), 400
    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        return jsonify({"error": "Email already registered."}), 409
    db.execute(
        "INSERT INTO users (name, email, password, is_admin) VALUES (?, ?, ?, 0)",
        (name, email, generate_password_hash(password)),
    )
    db.commit()
    return jsonify({"success": True})


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    db = get_db()
    user = db.execute("SELECT id, name, email, password, is_admin FROM users WHERE email = ?", (email,)).fetchone()
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid credentials."}), 401
    session["user_id"] = user["id"]
    session["is_admin"] = int(user["is_admin"])
    return jsonify({"user": {"id": user["id"], "name": user["name"], "email": user["email"], "is_admin": bool(user["is_admin"])}})


@app.route("/api/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    session.pop("is_admin", None)
    return jsonify({"success": True})


@app.route("/api/destinations")
def api_destinations():
    rows = get_db().execute("SELECT id, destination_name FROM destinations ORDER BY destination_name").fetchall()
    destinations = [{"id": row["id"], "destination_name": row["destination_name"]} for row in rows]
    return jsonify({"destinations": destinations})


@app.route("/api/recommendations")
def api_recommendations():
    destination_id = request.args.get("destination_id")
    category = request.args.get("category")
    if not destination_id:
        return jsonify({"error": "destination_id is required."}), 400
    query = "SELECT * FROM recommendation_places WHERE destination_id = ?"
    params = [destination_id]
    if category:
        query += " AND category = ?"
        params.append(category)
    rows = get_db().execute(query, params).fetchall()
    recommendations = [
        {
            "id": row["id"],
            "name": row["place_name"],
            "desc": row["description"],
            "rating": str(row["rating"]),
            "budgetTier": row["budget_tier"],
            "img": row["image_url"],
            "mapsLink": row["google_maps_link"],
            "category": row["category"],
        }
        for row in rows
    ]
    return jsonify({"recommendations": recommendations})


@app.route("/api/explore", methods=["POST"])
def api_explore():
    user = query_current_user()
    if not user:
        return jsonify({"error": "Authentication required."}), 401
    data = request.get_json() or {}
    destination_id = data.get("destination_id")
    budget = data.get("budget")
    days = data.get("days")
    travelers = data.get("travelers")
    if not destination_id or budget is None or days is None or travelers is None:
        return jsonify({"error": "destination_id, budget, days, and travelers are required."}), 400
    get_db().execute(
        "INSERT INTO explored_destinations (user_id, destination_id, budget, days, travelers) VALUES (?, ?, ?, ?, ?)",
        (user["id"], destination_id, budget, days, travelers),
    )
    get_db().commit()
    return jsonify({"success": True})


def require_admin():
    user = query_current_user()
    if not user or not user.get("is_admin"):
        return None
    return user


@app.route("/api/admin/users")
def api_admin_users():
    if not require_admin():
        return jsonify({"error": "Admin access required."}), 403
    rows = get_db().execute("SELECT id, name, email, created_at FROM users ORDER BY created_at DESC").fetchall()
    users = [dict_from_row(row) for row in rows]
    return jsonify({"users": users})


@app.route("/api/admin/destinations", methods=["GET", "POST"])
def api_admin_destinations():
    if not require_admin():
        return jsonify({"error": "Admin access required."}), 403
    db = get_db()
    if request.method == "GET":
        rows = db.execute("SELECT id, destination_name FROM destinations ORDER BY destination_name").fetchall()
        destinations = [dict_from_row(row) for row in rows]
        return jsonify({"destinations": destinations})
    data = request.get_json() or {}
    destination_name = (data.get("destination_name") or "").strip()
    if not destination_name:
        return jsonify({"error": "destination_name is required."}), 400
    try:
        db.execute(
            "INSERT INTO destinations (destination_name, added_by_admin) VALUES (?, 1)",
            (destination_name,),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Destination already exists."}), 409
    return jsonify({"success": True})


@app.route("/api/admin/destinations/<int:destination_id>", methods=["PUT", "DELETE"])
def api_admin_destination_detail(destination_id):
    if not require_admin():
        return jsonify({"error": "Admin access required."}), 403
    db = get_db()
    if request.method == "PUT":
        data = request.get_json() or {}
        destination_name = (data.get("destination_name") or "").strip()
        if not destination_name:
            return jsonify({"error": "destination_name is required."}), 400
        try:
            db.execute(
                "UPDATE destinations SET destination_name = ? WHERE id = ?",
                (destination_name, destination_id),
            )
            db.commit()
            return jsonify({"success": True})
        except sqlite3.IntegrityError:
            return jsonify({"error": "Destination name already exists."}), 409
    if request.method == "DELETE":
        db.execute("DELETE FROM recommendation_places WHERE destination_id = ?", (destination_id,))
        db.execute("DELETE FROM destinations WHERE id = ?", (destination_id,))
        db.commit()
        return jsonify({"success": True})


@app.route("/api/admin/places", methods=["GET", "POST"])
def api_admin_places():
    if not require_admin():
        return jsonify({"error": "Admin access required."}), 403
    db = get_db()
    if request.method == "GET":
        destination_filter = request.args.get("destination_id")
        query = "SELECT p.*, d.destination_name FROM recommendation_places p JOIN destinations d ON p.destination_id = d.id"
        params = []
        if destination_filter:
            query += " WHERE p.destination_id = ?"
            params.append(destination_filter)
        query += " ORDER BY p.created_at DESC"
        rows = db.execute(query, params).fetchall()
        places = []
        for row in rows:
            places.append(
                {
                    "id": row["id"],
                    "destination_id": row["destination_id"],
                    "destination_name": row["destination_name"],
                    "category": row["category"],
                    "place_name": row["place_name"],
                    "description": row["description"],
                    "rating": str(row["rating"]),
                    "budget_tier": row["budget_tier"],
                    "image_url": row["image_url"],
                    "google_maps_link": row["google_maps_link"],
                }
            )
        return jsonify({"places": places})
    data = request.get_json() or {}
    destination_id = data.get("destination_id")
    category = (data.get("category") or "").strip()
    place_name = (data.get("place_name") or "").strip()
    description = (data.get("description") or "").strip()
    rating = data.get("rating")
    budget_tier = (data.get("budget_tier") or "").strip()
    image_url = (data.get("image_url") or "").strip()
    google_maps_link = (data.get("google_maps_link") or "").strip()
    if not destination_id or not category or not place_name or not rating:
        return jsonify({"error": "destination_id, category, place_name and rating are required."}), 400
    db.execute(
        "INSERT INTO recommendation_places (destination_id, category, place_name, description, rating, budget_tier, image_url, google_maps_link, added_by_admin) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)",
        (destination_id, category, place_name, description, rating, budget_tier, image_url, google_maps_link),
    )
    db.commit()
    return jsonify({"success": True})


@app.route("/api/admin/places/<int:place_id>", methods=["PUT", "DELETE"])
def api_admin_place_detail(place_id):
    if not require_admin():
        return jsonify({"error": "Admin access required."}), 403
    db = get_db()
    if request.method == "PUT":
        data = request.get_json() or {}
        destination_id = data.get("destination_id")
        category = (data.get("category") or "").strip()
        place_name = (data.get("place_name") or "").strip()
        description = (data.get("description") or "").strip()
        rating = data.get("rating")
        budget_tier = (data.get("budget_tier") or "").strip()
        image_url = (data.get("image_url") or "").strip()
        google_maps_link = (data.get("google_maps_link") or "").strip()
        if not destination_id or not category or not place_name or not rating:
            return jsonify({"error": "destination_id, category, place_name and rating are required."}), 400
        db.execute(
            "UPDATE recommendation_places SET destination_id = ?, category = ?, place_name = ?, description = ?, rating = ?, budget_tier = ?, image_url = ?, google_maps_link = ? WHERE id = ?",
            (destination_id, category, place_name, description, rating, budget_tier, image_url, google_maps_link, place_id),
        )
        db.commit()
        return jsonify({"success": True})
    if request.method == "DELETE":
        db.execute("DELETE FROM recommendation_places WHERE id = ?", (place_id,))
        db.commit()
        return jsonify({"success": True})


if __name__ == "__main__":
    with app.app_context():
        init_db()
        seed_data()
    app.run(debug=True)
