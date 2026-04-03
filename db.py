import sqlite3
import os
from datetime import date, timedelta
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "hasenkamp.db")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS Client (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                color TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS ArtHandler (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                color TEXT NOT NULL,
                level TEXT NOT NULL,
                type TEXT NOT NULL,
                canDriveTruck INTEGER DEFAULT 0,
                canDriveCar INTEGER DEFAULT 0,
                canDriveForklift INTEGER DEFAULT 0,
                hasBadgeLouvre INTEGER DEFAULT 0,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS Truck (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                licensePlate TEXT
            );

            CREATE TABLE IF NOT EXISTS Project (
                id TEXT PRIMARY KEY,
                projectNumber TEXT NOT NULL,
                title TEXT NOT NULL,
                clientId TEXT NOT NULL,
                description TEXT,
                location TEXT,
                date TEXT NOT NULL,
                status TEXT DEFAULT 'PRE_BOOKED',
                createdBy TEXT NOT NULL,
                FOREIGN KEY (clientId) REFERENCES Client(id)
            );

            CREATE TABLE IF NOT EXISTS Booking (
                id TEXT PRIMARY KEY,
                projectId TEXT NOT NULL,
                handlerId TEXT NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY (projectId) REFERENCES Project(id) ON DELETE CASCADE,
                FOREIGN KEY (handlerId) REFERENCES ArtHandler(id)
            );

            CREATE TABLE IF NOT EXISTS TruckBooking (
                id TEXT PRIMARY KEY,
                projectId TEXT NOT NULL,
                truckId TEXT NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY (projectId) REFERENCES Project(id) ON DELETE CASCADE,
                FOREIGN KEY (truckId) REFERENCES Truck(id)
            );

            CREATE TABLE IF NOT EXISTS Unavailability (
                id TEXT PRIMARY KEY,
                handlerId TEXT NOT NULL,
                date TEXT NOT NULL,
                reason TEXT,
                FOREIGN KEY (handlerId) REFERENCES ArtHandler(id)
            );

            CREATE TABLE IF NOT EXISTS TruckUnavailability (
                id TEXT PRIMARY KEY,
                truckId TEXT NOT NULL,
                date TEXT NOT NULL,
                reason TEXT,
                FOREIGN KEY (truckId) REFERENCES Truck(id)
            );
        """)
    _seed_if_empty()


def _seed_if_empty():
    with get_conn() as conn:
        if conn.execute("SELECT COUNT(*) FROM Client").fetchone()[0] > 0:
            return

        import uuid

        clients = [
            ("client-louvre", "Louvre", "#FFD700"),
            ("client-tate", "Tate Modern", "#90EE90"),
            ("client-guggenheim", "Guggenheim", "#ADD8E6"),
            ("client-orsay", "Musée d'Orsay", "#FFB347"),
        ]
        conn.executemany("INSERT INTO Client VALUES (?,?,?)", clients)

        handlers = [
            ("h1", "Sophie Martin", "sophie.martin@hasenkamp.com", "#4A90D9", "Senior", "Internal", 1, 1, 1, 1, "Team leader"),
            ("h2", "James Thornton", "james.thornton@hasenkamp.com", "#4A90D9", "Senior", "Internal", 1, 1, 0, 1, ""),
            ("h3", "Clara Dubois", "clara.dubois@hasenkamp.com", "#27AE60", "Mid", "Internal", 0, 1, 0, 1, ""),
            ("h4", "Marcus Bauer", "marcus.bauer@hasenkamp.com", "#27AE60", "Mid", "Internal", 1, 1, 1, 0, "Louvre badge pending"),
            ("h5", "Léa Fontaine", "lea.fontaine@hasenkamp.com", "#F39C12", "Junior", "Internal", 0, 1, 0, 0, ""),
            ("h6", "Ravi Patel", "ravi.patel@freelance.com", "#9B59B6", "Senior", "Subcontractor", 1, 1, 0, 1, ""),
            ("h7", "Amelia Koch", "amelia.koch@arthandlers.eu", "#E74C3C", "Mid", "Subcontractor", 0, 1, 0, 0, ""),
            ("h8", "Yann Leclerc", "yann.leclerc@freelance.com", "#E74C3C", "Mid", "Subcontractor", 1, 1, 0, 1, ""),
            ("h9", "Nina Torres", "nina.torres@artcrew.com", "#95A5A6", "Junior", "Subcontractor", 0, 0, 0, 0, ""),
            ("h10", "Ben Walker", "ben.walker@artcrew.com", "#95A5A6", "Junior", "Subcontractor", 0, 1, 0, 0, ""),
        ]
        conn.executemany(
            "INSERT INTO ArtHandler VALUES (?,?,?,?,?,?,?,?,?,?,?)", handlers
        )

        trucks = [
            ("t1", "Van 1", "75-ART-001"),
            ("t2", "Van 2", "75-ART-002"),
            ("t3", "Truck 7.5T", "75-ART-003"),
            ("t4", "Truck 12T", "75-ART-004"),
        ]
        conn.executemany("INSERT INTO Truck VALUES (?,?,?)", trucks)

        today = date.today()
        d2 = (today + timedelta(days=2)).isoformat()
        d4 = (today + timedelta(days=4)).isoformat()
        d3 = (today + timedelta(days=3)).isoformat()

        conn.execute(
            "INSERT INTO Project VALUES (?,?,?,?,?,?,?,?,?)",
            ("p1", "HAR-2026-001", "Louvre - Egyptian Gallery Install",
             "client-louvre", "Install of 12 Egyptian artefacts in gallery B.",
             "Louvre Museum, Paris - Denon Wing", d2, "BOOKED", "AG"),
        )
        for bid, hid in [("b1a", "h1"), ("b1b", "h2"), ("b1c", "h3"), ("b1d", "h6")]:
            conn.execute("INSERT INTO Booking VALUES (?,?,?,?)", (bid, "p1", hid, d2))
        conn.execute("INSERT INTO TruckBooking VALUES (?,?,?,?)", ("tb1", "p1", "t3", d2))

        conn.execute(
            "INSERT INTO Project VALUES (?,?,?,?,?,?,?,?,?)",
            ("p2", "HAR-2026-002", "Tate Modern - Sculpture Move",
             "client-tate", "Move 3 large sculptures from storage to Turbine Hall.",
             "Tate Modern, London - Turbine Hall", d4, "PRE_BOOKED", "AG"),
        )
        for bid, hid in [("b2a", "h4"), ("b2b", "h5"), ("b2c", "h7")]:
            conn.execute("INSERT INTO Booking VALUES (?,?,?,?)", (bid, "p2", hid, d4))

        conn.execute(
            "INSERT INTO Unavailability VALUES (?,?,?,?)",
            ("u1", "h9", d3, "Annual leave"),
        )
        conn.execute(
            "INSERT INTO TruckUnavailability VALUES (?,?,?,?)",
            ("tu1", "t2", d2, "Service"),
        )


# ── Clients ──────────────────────────────────────────────────────────────────

def get_clients():
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM Client ORDER BY name").fetchall()]


def create_client(name, color):
    import uuid
    with get_conn() as conn:
        conn.execute("INSERT INTO Client VALUES (?,?,?)", (str(uuid.uuid4()), name, color))


def update_client(id, name, color):
    with get_conn() as conn:
        conn.execute("UPDATE Client SET name=?, color=? WHERE id=?", (name, color, id))


def delete_client(id):
    with get_conn() as conn:
        conn.execute("DELETE FROM Client WHERE id=?", (id,))


# ── Art Handlers ──────────────────────────────────────────────────────────────

def get_handlers():
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM ArtHandler ORDER BY type, level, name"
        ).fetchall()]


def create_handler(data: dict):
    import uuid
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO ArtHandler VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), data["name"], data["email"], data["color"],
             data["level"], data["type"], int(data["canDriveTruck"]),
             int(data["canDriveCar"]), int(data["canDriveForklift"]),
             int(data["hasBadgeLouvre"]), data.get("notes", "")),
        )


def update_handler(id, data: dict):
    with get_conn() as conn:
        conn.execute(
            """UPDATE ArtHandler SET name=?,email=?,color=?,level=?,type=?,
               canDriveTruck=?,canDriveCar=?,canDriveForklift=?,hasBadgeLouvre=?,notes=?
               WHERE id=?""",
            (data["name"], data["email"], data["color"], data["level"], data["type"],
             int(data["canDriveTruck"]), int(data["canDriveCar"]),
             int(data["canDriveForklift"]), int(data["hasBadgeLouvre"]),
             data.get("notes", ""), id),
        )


def delete_handler(id):
    with get_conn() as conn:
        conn.execute("DELETE FROM ArtHandler WHERE id=?", (id,))


# ── Trucks ────────────────────────────────────────────────────────────────────

def get_trucks():
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM Truck ORDER BY name").fetchall()]


def create_truck(name, license_plate):
    import uuid
    with get_conn() as conn:
        conn.execute("INSERT INTO Truck VALUES (?,?,?)", (str(uuid.uuid4()), name, license_plate))


def update_truck(id, name, license_plate):
    with get_conn() as conn:
        conn.execute("UPDATE Truck SET name=?,licensePlate=? WHERE id=?", (name, license_plate, id))


def delete_truck(id):
    with get_conn() as conn:
        conn.execute("DELETE FROM Truck WHERE id=?", (id,))


# ── Projects / Bookings ───────────────────────────────────────────────────────

def get_projects_in_range(start: date, days: int):
    end = start + timedelta(days=days - 1)
    with get_conn() as conn:
        projects = [dict(r) for r in conn.execute(
            "SELECT p.*, c.name as clientName, c.color as clientColor FROM Project p "
            "JOIN Client c ON c.id = p.clientId "
            "WHERE p.date >= ? AND p.date <= ? ORDER BY p.date",
            (start.isoformat(), end.isoformat()),
        ).fetchall()]

        for p in projects:
            p["bookings"] = [dict(r) for r in conn.execute(
                "SELECT b.*, h.name as handlerName, h.email as handlerEmail, "
                "h.color as handlerColor, h.level, h.hasBadgeLouvre "
                "FROM Booking b JOIN ArtHandler h ON h.id = b.handlerId "
                "WHERE b.projectId=?", (p["id"],)
            ).fetchall()]
            p["truckBookings"] = [dict(r) for r in conn.execute(
                "SELECT tb.*, t.name as truckName, t.licensePlate "
                "FROM TruckBooking tb JOIN Truck t ON t.id = tb.truckId "
                "WHERE tb.projectId=?", (p["id"],)
            ).fetchall()]
        return projects


def create_project(data: dict, handler_ids: list, truck_ids: list):
    import uuid
    pid = str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO Project VALUES (?,?,?,?,?,?,?,?,?)",
            (pid, data["projectNumber"], data["title"], data["clientId"],
             data.get("description"), data.get("location"), data["date"],
             data.get("status", "PRE_BOOKED"), data["createdBy"]),
        )
        for hid in handler_ids:
            conn.execute(
                "INSERT INTO Booking VALUES (?,?,?,?)",
                (str(uuid.uuid4()), pid, hid, data["date"]),
            )
        for tid in truck_ids:
            conn.execute(
                "INSERT INTO TruckBooking VALUES (?,?,?,?)",
                (str(uuid.uuid4()), pid, tid, data["date"]),
            )
    return pid


def confirm_project(id):
    with get_conn() as conn:
        conn.execute("UPDATE Project SET status='BOOKED' WHERE id=?", (id,))


def delete_project(id):
    with get_conn() as conn:
        conn.execute("DELETE FROM Project WHERE id=?", (id,))


# ── Unavailability ────────────────────────────────────────────────────────────

def get_unavailabilities_in_range(start: date, days: int):
    end = start + timedelta(days=days - 1)
    with get_conn() as conn:
        handler_unavail = [dict(r) for r in conn.execute(
            "SELECT * FROM Unavailability WHERE date >= ? AND date <= ?",
            (start.isoformat(), end.isoformat()),
        ).fetchall()]
        truck_unavail = [dict(r) for r in conn.execute(
            "SELECT * FROM TruckUnavailability WHERE date >= ? AND date <= ?",
            (start.isoformat(), end.isoformat()),
        ).fetchall()]
    return handler_unavail, truck_unavail


def set_handler_unavailable(handler_id, date_str, reason):
    import uuid
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM Unavailability WHERE handlerId=? AND date=?",
            (handler_id, date_str),
        )
        conn.execute(
            "INSERT INTO Unavailability VALUES (?,?,?,?)",
            (str(uuid.uuid4()), handler_id, date_str, reason),
        )


def remove_handler_unavailability(handler_id, date_str):
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM Unavailability WHERE handlerId=? AND date=?",
            (handler_id, date_str),
        )


def set_truck_unavailable(truck_id, date_str, reason):
    import uuid
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM TruckUnavailability WHERE truckId=? AND date=?",
            (truck_id, date_str),
        )
        conn.execute(
            "INSERT INTO TruckUnavailability VALUES (?,?,?,?)",
            (str(uuid.uuid4()), truck_id, date_str, reason),
        )


def remove_truck_unavailability(truck_id, date_str):
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM TruckUnavailability WHERE truckId=? AND date=?",
            (truck_id, date_str),
        )
