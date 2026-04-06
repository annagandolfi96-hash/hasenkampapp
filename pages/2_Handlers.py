import streamlit as st
import os
from datetime import date, timedelta
import db

st.set_page_config(page_title="C · Art Handlers — Hasenkamp", layout="wide")
db.init_db()

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

LEVEL_COLORS = {
    "Internal":      {"Senior": "#4A90D9", "Mid": "#27AE60", "Junior": "#F39C12"},
    "Subcontractor": {"Senior": "#9B59B6", "Mid": "#E74C3C", "Junior": "#95A5A6"},
}
WARN_DAYS = 60  # flag Louvre badge expiry within this many days

st.markdown("## 👷 Section C — Art Handler Profiles")

handlers = db.get_handlers()
today = date.today()

# ── Group by type then level ──────────────────────────────────────────────────
GROUP_ORDER = [
    ("Internal",      "Senior"), ("Internal",      "Mid"), ("Internal",      "Junior"),
    ("Subcontractor", "Senior"), ("Subcontractor", "Mid"), ("Subcontractor", "Junior"),
]

groups: dict = {}
for h in handlers:
    groups.setdefault((h["type"], h["level"]), []).append(h)

for (htype, level) in GROUP_ORDER:
    group_list = groups.get((htype, level), [])
    if not group_list:
        continue

    color = LEVEL_COLORS[htype][level]
    company_tag = ""
    # Show company name from first item if subcontractor
    if htype == "Subcontractor":
        companies = {h.get("company","") for h in group_list if h.get("company")}
        company_tag = " · " + " / ".join(sorted(companies)) if companies else ""

    st.markdown(
        f"<div style='display:flex;align-items:center;gap:8px;"
        f"margin-top:18px;margin-bottom:6px'>"
        f"<span style='width:12px;height:12px;border-radius:50%;"
        f"background:{color};display:inline-block'></span>"
        f"<b style='font-size:14px'>{htype} — {level}{company_tag}</b></div>",
        unsafe_allow_html=True,
    )

    cols = st.columns(2)
    for i, h in enumerate(group_list):
        with cols[i % 2]:
            with st.container(border=True):
                # ── Badge / expiry warnings ───────────────────────────────
                louvre_warn = ""
                if h.get("hasBadgeLouvre") and h.get("louvre_badge_expiry"):
                    try:
                        exp = date.fromisoformat(h["louvre_badge_expiry"])
                        days_left = (exp - today).days
                        if days_left < 0:
                            louvre_warn = f"🔴 Louvre badge **EXPIRED** {exp.strftime('%d/%m/%Y')}"
                        elif days_left <= WARN_DAYS:
                            louvre_warn = f"🟠 Louvre badge expires **{exp.strftime('%d/%m/%Y')}** ({days_left}d)"
                    except Exception:
                        pass

                hc1, hc2 = st.columns([5, 1])
                with hc1:
                    st.markdown(
                        f"<div style='border-left:4px solid {h['color']};padding-left:8px'>"
                        f"<b style='font-size:14px'>{h['name']}</b>"
                        f"{' · <span style=\"color:#666;font-size:12px\">' + h.get('company','') + '</span>' if h.get('company') else ''}"
                        f"<br><span style='font-size:11px;color:#888'>{h['email']}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    if h.get("employee_id"):
                        st.caption(f"🪪 ID: `{h['employee_id']}`")
                    badges = []
                    if h["canDriveTruck"]:    badges.append("🚛 Truck")
                    if h["canDriveCar"]:      badges.append("🚗 Car")
                    if h["canDriveForklift"]: badges.append("🏗 Forklift")
                    if h["hasBadgeLouvre"]:
                        exp_str = f" (exp. {h['louvre_badge_expiry']})" if h.get("louvre_badge_expiry") else ""
                        badges.append(f"🏛 Louvre{exp_str}")
                    if badges:
                        st.caption(" · ".join(badges))
                    if louvre_warn:
                        st.warning(louvre_warn)
                    if h.get("notes"):
                        st.caption(f"📝 {h['notes']}")
                    # Emirates ID photo
                    if h.get("emirates_id_photo"):
                        photo_path = os.path.join(UPLOADS_DIR, h["emirates_id_photo"])
                        if os.path.exists(photo_path):
                            with st.expander("🪪 Emirates ID"):
                                st.image(photo_path, width=280)
                with hc2:
                    if st.button("Edit", key=f"edit_{h['id']}", use_container_width=True):
                        st.session_state["editing_handler"] = h
                        st.rerun()
                    if st.button("Del", key=f"del_{h['id']}", use_container_width=True):
                        db.delete_handler(h["id"])
                        if st.session_state.get("editing_handler", {}).get("id") == h["id"]:
                            del st.session_state["editing_handler"]
                        st.rerun()

st.divider()

# ── Add / Edit form ───────────────────────────────────────────────────────────
editing = st.session_state.get("editing_handler")
st.markdown(f"### {'✏️ Edit Handler' if editing else '➕ Add New Handler'}")

if editing:
    if st.button("← Cancel Edit"):
        del st.session_state["editing_handler"]
        st.rerun()

with st.form("handler_form", clear_on_submit=not editing):
    st.markdown("**Basic Info**")
    r1c1, r1c2, r1c3 = st.columns(3)
    with r1c1:
        name = st.text_input("Full Name *", value=editing["name"] if editing else "")
        email = st.text_input("Work Email *", value=editing["email"] if editing else "")
    with r1c2:
        htype = st.selectbox(
            "Type *", ["Internal", "Subcontractor"],
            index=["Internal","Subcontractor"].index(editing["type"]) if editing else 0,
        )
        level = st.selectbox(
            "Level *", ["Senior", "Mid", "Junior"],
            index=["Senior","Mid","Junior"].index(editing["level"]) if editing else 0,
        )
    with r1c3:
        auto_color = LEVEL_COLORS[htype][level]
        color = st.color_picker(
            "Colour (auto by level)",
            value=editing["color"] if editing else auto_color,
        )
        company = st.text_input(
            "Company",
            value=editing.get("company","") if editing else "",
            placeholder="ISS, Blitz, or leave blank",
        )

    st.markdown("**IDs & Documents**")
    r2c1, r2c2 = st.columns(2)
    with r2c1:
        employee_id = st.text_input(
            "Employee / Staff ID",
            value=editing.get("employee_id","") if editing else "",
            placeholder="HAR-0042",
        )
    with r2c2:
        emirates_uploader = st.file_uploader(
            "Emirates ID Photo (JPG/PNG)",
            type=["jpg","jpeg","png"],
            key=f"eid_upload_{editing['id'] if editing else 'new'}",
        )
        if editing and editing.get("emirates_id_photo"):
            p = os.path.join(UPLOADS_DIR, editing["emirates_id_photo"])
            if os.path.exists(p):
                st.image(p, width=160, caption="Current Emirates ID")

    st.markdown("**Skills & Licences**")
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        can_truck = st.checkbox("🚛 Drives Truck",    value=bool(editing["canDriveTruck"])    if editing else False)
        can_car   = st.checkbox("🚗 Drives Car",      value=bool(editing["canDriveCar"])      if editing else False)
    with sc2:
        can_fork  = st.checkbox("🏗 Forklift",        value=bool(editing["canDriveForklift"]) if editing else False)
    with sc3:
        louvre    = st.checkbox("🏛 Louvre Badge",    value=bool(editing["hasBadgeLouvre"])   if editing else False)

    st.markdown("**Louvre Badge Expiry**")
    lb_col1, lb_col2 = st.columns(2)
    with lb_col1:
        _default_exp = None
        if editing and editing.get("louvre_badge_expiry"):
            try:
                _default_exp = date.fromisoformat(editing["louvre_badge_expiry"])
            except Exception:
                pass
        louvre_expiry_date = st.date_input(
            "Expiry Date (leave blank if no badge / unknown)",
            value=_default_exp,
            min_value=date(2020, 1, 1),
            key="louvre_exp_input",
        )
    with lb_col2:
        clear_expiry = st.checkbox("Clear expiry date", value=False, key="clear_louvre_exp")

    notes = st.text_input(
        "Notes",
        value=editing["notes"] if editing and editing.get("notes") else "",
        placeholder="First aider, team leader, special access…",
    )

    submitted = st.form_submit_button(
        "Save Changes" if editing else "Add Handler",
        type="primary", use_container_width=True,
    )

if submitted:
    if not name or not email:
        st.error("Name and email are required.")
    else:
        # Handle Emirates ID photo upload
        eid_filename = editing.get("emirates_id_photo","") if editing else ""
        if emirates_uploader is not None:
            ext = emirates_uploader.name.rsplit(".",1)[-1].lower()
            safe_name = name.lower().replace(" ","_")
            eid_filename = f"{safe_name}_eid.{ext}"
            with open(os.path.join(UPLOADS_DIR, eid_filename), "wb") as f:
                f.write(emirates_uploader.read())

        # Handle Louvre expiry
        louvre_exp_str = ""
        if not clear_expiry and louvre_expiry_date:
            louvre_exp_str = louvre_expiry_date.isoformat()

        data = {
            "name": name, "email": email, "color": color,
            "level": level, "type": htype, "company": company,
            "canDriveTruck": can_truck, "canDriveCar": can_car,
            "canDriveForklift": can_fork, "hasBadgeLouvre": louvre,
            "notes": notes, "employee_id": employee_id,
            "louvre_badge_expiry": louvre_exp_str,
            "emirates_id_photo": eid_filename,
        }
        if editing:
            db.update_handler(editing["id"], data)
            del st.session_state["editing_handler"]
            st.success(f"Updated **{name}**")
        else:
            db.create_handler(data)
            st.success(f"Added **{name}**")
        st.rerun()
