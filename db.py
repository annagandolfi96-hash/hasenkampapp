import sqlite3
import os
from datetime import date, timedelta
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "hasenkamp.db")

PRABAH_EMAIL = "prabah@blitz-arthandlers.com"  # update with real email
BLITZ_COMPANY = "Blitz"


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
                color TEXT NOT NULL,
                contact_person TEXT DEFAULT '',
                contact_email TEXT DEFAULT '',
                contact_phone TEXT DEFAULT '',
                notes TEXT DEFAULT ''
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
                notes TEXT,
                company TEXT DEFAULT '',
                employee_id TEXT DEFAULT '',
                louvre_badge_expiry TEXT DEFAULT '',
                emirates_id_photo TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS Truck (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                licensePlate TEXT,
                spec TEXT DEFAULT '',
                service_due TEXT DEFAULT ''
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
        # Migrations for existing databases
        for col in ["company TEXT DEFAULT ''", "notes TEXT",
                    "employee_id TEXT DEFAULT ''",
                    "louvre_badge_expiry TEXT DEFAULT ''",
                    "emirates_id_photo TEXT DEFAULT ''"]:
            try:
                conn.execute(f"ALTER TABLE ArtHandler ADD COLUMN {col}")
            except Exception:
                pass
        for col in ["spec TEXT DEFAULT ''", "service_due TEXT DEFAULT ''"]:
            try:
                conn.execute(f"ALTER TABLE Truck ADD COLUMN {col}")
            except Exception:
                pass
        for col in ["contact_person TEXT DEFAULT ''", "contact_email TEXT DEFAULT ''",
                    "contact_phone TEXT DEFAULT ''", "notes TEXT DEFAULT ''"]:
            try:
                conn.execute(f"ALTER TABLE Client ADD COLUMN {col}")
            except Exception:
                pass
    _seed_if_empty()
    _migrate_handlers()
    _migrate_trucks()
    _migrate_iss_company()


def _seed_if_empty():
    with get_conn() as conn:
        if conn.execute("SELECT COUNT(*) FROM Client").fetchone()[0] > 0:
            return

        clients = [
            ("client-louvre",      "Louvre",          "#FFD700", "", "", "", ""),
            ("client-tate",        "Tate Modern",     "#90EE90", "", "", "", ""),
            ("client-guggenheim",  "Guggenheim",      "#ADD8E6", "", "", "", ""),
            ("client-orsay",       "Musée d'Orsay",   "#FFB347", "", "", "", ""),
        ]
        conn.executemany("INSERT INTO Client VALUES (?,?,?,?,?,?,?)", clients)

        # (id, name, email, color, level, type, truck, car, forklift, louvre, notes, company, emp_id, louvre_exp, eid_photo)
        handlers = [
            ("h1",  "Sophie Martin",   "sophie.martin@hasenkamp.com",   "#4A90D9", "Senior", "Internal",      1,1,1,1, "Team leader", "", "","",""),
            ("h2",  "James Thornton",  "james.thornton@hasenkamp.com",  "#4A90D9", "Senior", "Internal",      1,1,0,1, "",            "", "","",""),
            ("h3",  "Clara Dubois",    "clara.dubois@hasenkamp.com",    "#27AE60", "Mid",    "Internal",      0,1,0,1, "",            "", "","",""),
            ("h4",  "Marcus Bauer",    "marcus.bauer@hasenkamp.com",    "#27AE60", "Mid",    "Internal",      1,1,1,0, "Louvre badge pending", "", "","",""),
            ("h5",  "Léa Fontaine",    "lea.fontaine@hasenkamp.com",    "#F39C12", "Junior", "Internal",      0,1,0,0, "",            "", "","",""),
            ("h6",  "Ravi Patel",      "ravi.patel@freelance.com",      "#9B59B6", "Senior", "Subcontractor", 1,1,0,1, "",            "ISS", "","",""),
            ("h7",  "Yann Leclerc",    "yann.leclerc@freelance.com",    "#E74C3C", "Mid",    "Subcontractor", 1,1,0,1, "",            "ISS", "","",""),
            ("h8",  "Marco Ferretti",  "marco.ferretti@blitz.com",      "#E74C3C", "Mid",    "Subcontractor", 0,1,0,0, "",            "Blitz", "","",""),
            ("h9",  "Lena Schulz",     "lena.schulz@blitz.com",         "#E74C3C", "Mid",    "Subcontractor", 0,1,0,0, "",            "Blitz", "","",""),
            ("h10", "Tom Dupont",      "tom.dupont@blitz.com",          "#95A5A6", "Junior", "Subcontractor", 0,1,0,0, "",            "Blitz", "","",""),
            ("h11", "Sara Okonkwo",    "sara.okonkwo@blitz.com",        "#95A5A6", "Junior", "Subcontractor", 0,0,0,0, "",            "Blitz", "","",""),
        ]
        conn.executemany("INSERT INTO ArtHandler VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", handlers)

        trucks = [
            ("t1", "Van 1",       "75-ART-001", "Sprinter", ""),
            ("t2", "Van 2",       "75-ART-002", "Sprinter", ""),
            ("t3", "Truck 3T",    "75-ART-003", "3 ton",    ""),
            ("t4", "Truck 10T",   "75-ART-004", "10 ton",   ""),
        ]
        conn.executemany("INSERT INTO Truck VALUES (?,?,?,?,?)", trucks)

        today = date.today()
        d2 = (today + timedelta(days=2)).isoformat()
        d4 = (today + timedelta(days=4)).isoformat()
        d3 = (today + timedelta(days=3)).isoformat()

        conn.execute("INSERT INTO Project VALUES (?,?,?,?,?,?,?,?,?)",
            ("p1","HAR-2026-001","Louvre - Egyptian Gallery Install","client-louvre",
             "Install of 12 Egyptian artefacts in gallery B.",
             "Louvre Museum, Paris - Denon Wing",d2,"BOOKED","AG"))
        for bid,hid in [("b1a","h1"),("b1b","h2"),("b1c","h3"),("b1d","h8")]:
            conn.execute("INSERT INTO Booking VALUES (?,?,?,?)",(bid,"p1",hid,d2))
        conn.execute("INSERT INTO TruckBooking VALUES (?,?,?,?)",("tb1","p1","t3",d2))

        conn.execute("INSERT INTO Project VALUES (?,?,?,?,?,?,?,?,?)",
            ("p2","HAR-2026-002","Tate Modern - Sculpture Move","client-tate",
             "Move 3 large sculptures from storage to Turbine Hall.",
             "Tate Modern, London - Turbine Hall",d4,"PRE_BOOKED","AG"))
        for bid,hid in [("b2a","h4"),("b2b","h5"),("b2c","h9")]:
            conn.execute("INSERT INTO Booking VALUES (?,?,?,?)",(bid,"p2",hid,d4))

        conn.execute("INSERT INTO Unavailability VALUES (?,?,?,?)",("u1","h10",d3,"Annual leave"))
        conn.execute("INSERT INTO TruckUnavailability VALUES (?,?,?,?)",("tu1","t2",d2,"Service"))


def _migrate_handlers():
    """Add new handlers to existing databases if they don't already exist."""
    new_handlers = [
        # Internal — Senior
        ("h12", "Antoine Morel",    "antoine.morel@hasenkamp.com",    "#4A90D9", "Senior", "Internal",      1,1,1,1, "",            ""),
        ("h13", "Nadia Rousseau",   "nadia.rousseau@hasenkamp.com",   "#4A90D9", "Senior", "Internal",      0,1,0,1, "First aider", ""),
        ("h14", "Erik Larsen",      "erik.larsen@hasenkamp.com",      "#4A90D9", "Senior", "Internal",      1,1,1,1, "",            ""),
        # Internal — Mid
        ("h15", "Camille Bernard",  "camille.bernard@hasenkamp.com",  "#27AE60", "Mid",    "Internal",      0,1,0,1, "",            ""),
        ("h16", "Julien Petit",     "julien.petit@hasenkamp.com",     "#27AE60", "Mid",    "Internal",      1,1,0,0, "",            ""),
        ("h17", "Isabelle Garnier", "isabelle.garnier@hasenkamp.com", "#27AE60", "Mid",    "Internal",      0,1,1,1, "",            ""),
        ("h18", "Lukas Hoffmann",   "lukas.hoffmann@hasenkamp.com",   "#27AE60", "Mid",    "Internal",      1,1,0,0, "",            ""),
        ("h19", "Fiona Blanc",      "fiona.blanc@hasenkamp.com",      "#27AE60", "Mid",    "Internal",      0,1,0,1, "",            ""),
        # Internal — Junior
        ("h20", "Théo Lambert",     "theo.lambert@hasenkamp.com",     "#F39C12", "Junior", "Internal",      0,1,0,0, "",            ""),
        ("h21", "Zoé Martin",       "zoe.martin@hasenkamp.com",       "#F39C12", "Junior", "Internal",      0,1,0,0, "",            ""),
        ("h22", "Hugo Renard",      "hugo.renard@hasenkamp.com",      "#F39C12", "Junior", "Internal",      0,0,0,0, "",            ""),
        ("h23", "Elisa Simon",      "elisa.simon@hasenkamp.com",      "#F39C12", "Junior", "Internal",      0,1,0,0, "",            ""),
        # Independent Subcontractors — Senior/Mid
        ("h24", "Dmitri Volkov",    "dmitri.volkov@artpro.eu",        "#9B59B6", "Senior", "Subcontractor", 1,1,1,0, "",            "ISS"),
        ("h25", "Amara Diallo",     "amara.diallo@artpro.eu",         "#9B59B6", "Senior", "Subcontractor", 0,1,0,1, "",            "ISS"),
        ("h26", "Carlos Rivera",    "carlos.rivera@artstaff.com",     "#E74C3C", "Mid",    "Subcontractor", 1,1,0,0, "",            "ISS"),
        ("h27", "Hana Novak",       "hana.novak@artstaff.com",        "#E74C3C", "Mid",    "Subcontractor", 0,1,0,0, "",            "ISS"),
        ("h28", "Stefan Braun",     "stefan.braun@artstaff.com",      "#E74C3C", "Mid",    "Subcontractor", 1,1,1,0, "",            "ISS"),
        # Blitz — additional
        ("h29", "Kevin Osei",       "kevin.osei@blitz.com",           "#E74C3C", "Mid",    "Subcontractor", 0,1,0,0, "",            "Blitz"),
        ("h30", "Miriam Adler",     "miriam.adler@blitz.com",         "#95A5A6", "Junior", "Subcontractor", 0,1,0,0, "",            "Blitz"),
        ("h31", "Patrice Nguyen",   "patrice.nguyen@blitz.com",       "#95A5A6", "Junior", "Subcontractor", 0,0,0,0, "",            "Blitz"),
    ]
    with get_conn() as conn:
        existing = {r[0] for r in conn.execute("SELECT id FROM ArtHandler").fetchall()}
        for h in new_handlers:
            if h[0] not in existing:
                # pad to 15 cols (add employee_id, louvre_badge_expiry, emirates_id_photo)
                row = h + ("", "", "") if len(h) == 12 else h
                conn.execute("INSERT INTO ArtHandler VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", row)


def _migrate_trucks():
    """Update truck specs for existing seed trucks, add spec column data."""
    spec_map = {
        "t1": "Sprinter", "t2": "Sprinter",
        "t3": "3 ton",    "t4": "10 ton",
    }
    with get_conn() as conn:
        for tid, spec in spec_map.items():
            conn.execute(
                "UPDATE Truck SET spec=? WHERE id=? AND (spec IS NULL OR spec='')",
                (spec, tid)
            )


def _migrate_iss_company():
    """Tag existing non-Blitz subcontractors as ISS if company is blank."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE ArtHandler SET company='ISS' "
            "WHERE type='Subcontractor' AND (company IS NULL OR company='')"
        )


def get_unavailable_handler_ids(date_str: str):
    with get_conn() as conn:
        unavail = {r[0] for r in conn.execute(
            "SELECT handlerId FROM Unavailability WHERE date=?", (date_str,)).fetchall()}
        booked = {r[0] for r in conn.execute(
            "SELECT handlerId FROM Booking WHERE date=?", (date_str,)).fetchall()}
    return unavail, booked


def get_unavailable_truck_ids(date_str: str):
    with get_conn() as conn:
        unavail = {r[0] for r in conn.execute(
            "SELECT truckId FROM TruckUnavailability WHERE date=?", (date_str,)).fetchall()}
        booked = {r[0] for r in conn.execute(
            "SELECT truckId FROM TruckBooking WHERE date=?", (date_str,)).fetchall()}
    return unavail, booked


# ── Clients ───────────────────────────────────────────────────────────────────

def get_clients():
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM Client ORDER BY name").fetchall()]

def create_client(name, color, contact_person="", contact_email="", contact_phone="", notes=""):
    import uuid
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO Client VALUES (?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), name, color, contact_person, contact_email, contact_phone, notes)
        )

def update_client(id, name, color, contact_person="", contact_email="", contact_phone="", notes=""):
    with get_conn() as conn:
        conn.execute(
            "UPDATE Client SET name=?,color=?,contact_person=?,contact_email=?,"
            "contact_phone=?,notes=? WHERE id=?",
            (name, color, contact_person, contact_email, contact_phone, notes, id)
        )

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
            "INSERT INTO ArtHandler VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), data["name"], data["email"], data["color"],
             data["level"], data["type"], int(data["canDriveTruck"]),
             int(data["canDriveCar"]), int(data["canDriveForklift"]),
             int(data["hasBadgeLouvre"]), data.get("notes",""), data.get("company",""),
             data.get("employee_id",""), data.get("louvre_badge_expiry",""),
             data.get("emirates_id_photo","")),
        )

def update_handler(id, data: dict):
    with get_conn() as conn:
        conn.execute(
            """UPDATE ArtHandler SET name=?,email=?,color=?,level=?,type=?,
               canDriveTruck=?,canDriveCar=?,canDriveForklift=?,hasBadgeLouvre=?,
               notes=?,company=?,employee_id=?,louvre_badge_expiry=?,emirates_id_photo=?
               WHERE id=?""",
            (data["name"], data["email"], data["color"], data["level"], data["type"],
             int(data["canDriveTruck"]), int(data["canDriveCar"]),
             int(data["canDriveForklift"]), int(data["hasBadgeLouvre"]),
             data.get("notes",""), data.get("company",""),
             data.get("employee_id",""), data.get("louvre_badge_expiry",""),
             data.get("emirates_id_photo",""), id),
        )

def delete_handler(id):
    with get_conn() as conn:
        conn.execute("DELETE FROM ArtHandler WHERE id=?", (id,))


# ── Trucks ────────────────────────────────────────────────────────────────────

def get_trucks():
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM Truck ORDER BY name").fetchall()]

def create_truck(name, license_plate, spec="", service_due=""):
    import uuid
    with get_conn() as conn:
        conn.execute("INSERT INTO Truck VALUES (?,?,?,?,?)",
                     (str(uuid.uuid4()), name, license_plate, spec, service_due))

def update_truck(id, name, license_plate, spec="", service_due=""):
    with get_conn() as conn:
        conn.execute("UPDATE Truck SET name=?,licensePlate=?,spec=?,service_due=? WHERE id=?",
                     (name, license_plate, spec, service_due, id))

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
                "h.color as handlerColor, h.level, h.hasBadgeLouvre, "
                "COALESCE(h.company,'') as company "
                "FROM Booking b JOIN ArtHandler h ON h.id = b.handlerId "
                "WHERE b.projectId=?", (p["id"],)
            ).fetchall()]
            p["truckBookings"] = [dict(r) for r in conn.execute(
                "SELECT tb.*, t.name as truckName, t.licensePlate, COALESCE(t.spec,'') as spec "
                "FROM TruckBooking tb JOIN Truck t ON t.id = tb.truckId "
                "WHERE tb.projectId=?", (p["id"],)
            ).fetchall()]
        return projects

def create_project(data: dict, handler_ids: list, truck_ids: list,
                   handler_date_pairs=None):
    """handler_date_pairs: list of (handler_id, date_str) tuples.
    Falls back to pairing each handler_id with data['date'] if not provided."""
    import uuid
    pid = str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO Project VALUES (?,?,?,?,?,?,?,?,?)",
            (pid, data["projectNumber"], data["title"], data["clientId"],
             data.get("description"), data.get("location"), data["date"],
             data.get("status","PRE_BOOKED"), data["createdBy"]),
        )
        pairs = handler_date_pairs if handler_date_pairs is not None \
                else [(hid, data["date"]) for hid in handler_ids]
        for hid, hdate in pairs:
            conn.execute("INSERT INTO Booking VALUES (?,?,?,?)",
                         (str(uuid.uuid4()), pid, hid, hdate))
        for tid in truck_ids:
            conn.execute("INSERT INTO TruckBooking VALUES (?,?,?,?)",
                         (str(uuid.uuid4()), pid, tid, data["date"]))
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
            (start.isoformat(), end.isoformat())).fetchall()]
        truck_unavail = [dict(r) for r in conn.execute(
            "SELECT * FROM TruckUnavailability WHERE date >= ? AND date <= ?",
            (start.isoformat(), end.isoformat())).fetchall()]
    return handler_unavail, truck_unavail

def set_handler_unavailable(handler_id, date_str, reason):
    import uuid
    with get_conn() as conn:
        conn.execute("DELETE FROM Unavailability WHERE handlerId=? AND date=?", (handler_id, date_str))
        conn.execute("INSERT INTO Unavailability VALUES (?,?,?,?)",
                     (str(uuid.uuid4()), handler_id, date_str, reason))

def remove_handler_unavailability(handler_id, date_str):
    with get_conn() as conn:
        conn.execute("DELETE FROM Unavailability WHERE handlerId=? AND date=?", (handler_id, date_str))

def set_truck_unavailable(truck_id, date_str, reason):
    import uuid
    with get_conn() as conn:
        conn.execute("DELETE FROM TruckUnavailability WHERE truckId=? AND date=?", (truck_id, date_str))
        conn.execute("INSERT INTO TruckUnavailability VALUES (?,?,?,?)",
                     (str(uuid.uuid4()), truck_id, date_str, reason))

def remove_truck_unavailability(truck_id, date_str):
    with get_conn() as conn:
        conn.execute("DELETE FROM TruckUnavailability WHERE truckId=? AND date=?", (truck_id, date_str))


# ── Expiry helpers (used by calendar flags) ───────────────────────────────────

def get_handlers_with_expiring_louvre(warn_days: int = 60):
    """Return handlers whose Louvre badge expires within warn_days from today."""
    today = date.today()
    cutoff = (today + timedelta(days=warn_days)).isoformat()
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT id, name, louvre_badge_expiry FROM ArtHandler "
            "WHERE hasBadgeLouvre=1 AND louvre_badge_expiry != '' "
            "AND louvre_badge_expiry <= ?", (cutoff,)
        ).fetchall()]

def get_trucks_with_upcoming_service(warn_days: int = 60):
    """Return trucks whose service is due within warn_days from today."""
    today = date.today()
    cutoff = (today + timedelta(days=warn_days)).isoformat()
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT id, name, service_due FROM Truck "
            "WHERE service_due != '' AND service_due <= ?", (cutoff,)
        ).fetchall()]


# ── Monthly invoice summary ───────────────────────────────────────────────────

def get_projects_for_month(year: int, month: int) -> list:
    """Return all projects that have at least one booking in the given month.

    Each project dict contains:
      - all Project + Client columns
      - 'days': {date_str: [booking_row, ...]} for dates within the month
      - 'all_days': same but for the full project span
      - 'total_handler_days': count of all (handler, date) pairs in the month
      - 'truck_days': list of {truckName, licensePlate, spec, date} in the month
    """
    import calendar as _cal
    last_day = _cal.monthrange(year, month)[1]
    from_date = f"{year:04d}-{month:02d}-01"
    to_date   = f"{year:04d}-{month:02d}-{last_day:02d}"

    with get_conn() as conn:
        pid_rows = conn.execute(
            "SELECT DISTINCT projectId FROM Booking WHERE date >= ? AND date <= ?",
            (from_date, to_date),
        ).fetchall()
        project_ids = [r[0] for r in pid_rows]

        results = []
        for pid in project_ids:
            row = conn.execute(
                "SELECT p.*, c.name as clientName, c.color as clientColor "
                "FROM Project p JOIN Client c ON c.id = p.clientId WHERE p.id=?",
                (pid,),
            ).fetchone()
            if not row:
                continue
            p = dict(row)

            # All bookings for this project in the selected month
            month_bookings = [dict(r) for r in conn.execute(
                "SELECT b.date, b.handlerId, h.name as handlerName, "
                "h.level, h.type, COALESCE(h.company,'') as company "
                "FROM Booking b JOIN ArtHandler h ON h.id = b.handlerId "
                "WHERE b.projectId=? AND b.date >= ? AND b.date <= ? "
                "ORDER BY b.date, h.name",
                (pid, from_date, to_date),
            ).fetchall()]

            # Group by date
            days: dict = {}
            for b in month_bookings:
                days.setdefault(b["date"], []).append(b)
            p["days"] = dict(sorted(days.items()))
            p["total_handler_days"] = len(month_bookings)

            # Internal vs subcontractor handler-days
            p["internal_days"]  = sum(1 for b in month_bookings if b["type"] == "Internal")
            p["external_days"]  = sum(1 for b in month_bookings if b["type"] != "Internal")
            p["blitz_days"]     = sum(1 for b in month_bookings if b["company"] == BLITZ_COMPANY)

            # Truck usage in the month
            p["truck_days"] = [dict(r) for r in conn.execute(
                "SELECT tb.date, t.name as truckName, t.licensePlate, "
                "COALESCE(t.spec,'') as spec "
                "FROM TruckBooking tb JOIN Truck t ON t.id = tb.truckId "
                "WHERE tb.projectId=? AND tb.date >= ? AND tb.date <= ? "
                "ORDER BY tb.date",
                (pid, from_date, to_date),
            ).fetchall()]

            results.append(p)

        results.sort(key=lambda x: (x["clientName"], x["date"]))
        return results


def get_all_booking_months() -> list:
    """Return sorted list of (year, month) tuples that have any bookings."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT substr(date,1,7) as ym FROM Booking ORDER BY ym"
        ).fetchall()
    result = []
    for r in rows:
        y, m = r[0].split("-")
        result.append((int(y), int(m)))
    return result
