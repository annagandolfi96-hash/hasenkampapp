import streamlit as st
import os
from datetime import date
import db

st.set_page_config(page_title="C · Art Handlers — Hasenkamp", layout="wide")
db.init_db()

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

LEVEL_COLORS = {
    "Internal":      {"Senior": "#4A90D9", "Mid": "#27AE60", "Junior": "#F39C12"},
    "Subcontractor": {"Senior": "#9B59B6", "Mid": "#E74C3C", "Junior": "#95A5A6"},
}
WARN_DAYS = 60

st.markdown("## Section C — Art Handler Profiles")

handlers = db.get_handlers()
today = date.today()

# ── Inline edit helper ────────────────────────────────────────────────────────
def _inline_edit_form(h):
    """Render the edit form inline inside the handler's container."""
    hid = h["id"]
    with st.form(f"edit_form_{hid}", border=False):
        st.markdown("**Basic Info**")
        f1, f2, f3 = st.columns(3)
        with f1:
            name  = st.text_input("Full Name *", value=h["name"])
            email = st.text_input("Work Email *", value=h["email"])
        with f2:
            htype = st.selectbox("Type *", ["Internal", "Subcontractor"],
                                 index=["Internal","Subcontractor"].index(h["type"]))
            level = st.selectbox("Level *", ["Senior", "Mid", "Junior"],
                                 index=["Senior","Mid","Junior"].index(h["level"]))
        with f3:
            color   = st.color_picker("Colour", value=h["color"])
            company = st.text_input("Company", value=h.get("company") or "",
                                    placeholder="ISS, Blitz, or leave blank")

        st.markdown("**Louvre Badge & IDs**")
        b1, b2, b3 = st.columns(3)
        with b1:
            louvre = st.checkbox("🏛L Has Louvre Badge", value=bool(h["hasBadgeLouvre"]))
            _def_exp = None
            if h.get("louvre_badge_expiry") or "":
                try:
                    _def_exp = date.fromisoformat(h["louvre_badge_expiry"])
                except Exception:
                    pass
            louvre_exp = st.date_input("Louvre Expiry", value=_def_exp,
                                       min_value=date(2020, 1, 1),
                                       key=f"lexp_{hid}")
            clear_exp  = st.checkbox("Clear expiry", value=False, key=f"clrexp_{hid}")
        with b2:
            employee_id = st.text_input("Employee / Staff ID",
                                        value=h.get("employee_id") or "",
                                        placeholder="HAR-0042")
        with b3:
            eid_upload = st.file_uploader("Emirates ID Photo (JPG/PNG)",
                                          type=["jpg","jpeg","png"],
                                          key=f"eid_{hid}")
            if h.get("emirates_id_photo") or "":
                p = os.path.join(UPLOADS_DIR, h.get("emirates_id_photo",""))
                if os.path.exists(p):
                    st.image(p, width=140, caption="Current")

        st.markdown("**Skills & Licences**")
        s1, s2, s3 = st.columns(3)
        with s1:
            can_truck = st.checkbox("🚛 Truck",    value=bool(h["canDriveTruck"]))
            can_car   = st.checkbox("🚗 Car",      value=bool(h["canDriveCar"]))
        with s2:
            can_fork  = st.checkbox("🏗 Forklift", value=bool(h["canDriveForklift"]))
        with s3:
            notes = st.text_input("Notes", value=h.get("notes") or "")

        sv_col, cx_col = st.columns(2)
        with sv_col:
            do_save   = st.form_submit_button("💾 Save Changes", type="primary",
                                              use_container_width=True)
        with cx_col:
            do_cancel = st.form_submit_button("Cancel", use_container_width=True)

    # ── Handle submission ─────────────────────────────────────────────────────
    if do_save:
        if not name or not email:
            st.error("Name and email are required.")
        else:
            eid_filename = h.get("emirates_id_photo") or ""
            if eid_upload is not None:
                ext = eid_upload.name.rsplit(".", 1)[-1].lower()
                eid_filename = f"{name.lower().replace(' ','_')}_eid.{ext}"
                with open(os.path.join(UPLOADS_DIR, eid_filename), "wb") as f:
                    f.write(eid_upload.read())
            louvre_exp_str = "" if clear_exp else (louvre_exp.isoformat() if louvre_exp else "")
            db.update_handler(hid, {
                "name": name, "email": email, "color": color,
                "level": level, "type": htype, "company": company,
                "canDriveTruck": can_truck, "canDriveCar": can_car,
                "canDriveForklift": can_fork, "hasBadgeLouvre": louvre,
                "notes": notes, "employee_id": employee_id,
                "louvre_badge_expiry": louvre_exp_str,
                "emirates_id_photo": eid_filename,
            })
            del st.session_state["editing_id"]
            st.success(f"Updated **{name}**")
            st.rerun()

    if do_cancel:
        del st.session_state["editing_id"]
        st.rerun()


# ── Group ordering ────────────────────────────────────────────────────────────
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
    if htype == "Subcontractor":
        companies = {h.get("company","") for h in group_list if h.get("company")}
        company_tag = " · " + " / ".join(sorted(companies)) if companies else ""
    else:
        company_tag = ""

    st.markdown(
        f"<div style='display:flex;align-items:center;gap:8px;"
        f"margin-top:18px;margin-bottom:4px'>"
        f"<span style='width:11px;height:11px;border-radius:50%;"
        f"background:{color};display:inline-block'></span>"
        f"<b style='font-size:13px'>{htype} — {level}{company_tag}</b></div>",
        unsafe_allow_html=True,
    )

    for h in group_list:
        editing_this = (st.session_state.get("editing_id") == h["id"])

        with st.container(border=True):
            if editing_this:
                # ── Inline edit form ──────────────────────────────────────
                st.markdown(
                    f"<div style='border-left:4px solid {h['color']};padding-left:8px;"
                    f"margin-bottom:8px'><b>{h['name']}</b>"
                    f" <span style='color:#888;font-size:12px'>— editing</span></div>",
                    unsafe_allow_html=True,
                )
                _inline_edit_form(h)

            else:
                # ── Read view ─────────────────────────────────────────────
                louvre_warn = ""
                if h.get("hasBadgeLouvre") and (h.get("louvre_badge_expiry") or ""):
                    try:
                        exp = date.fromisoformat(h["louvre_badge_expiry"])
                        days_left = (exp - today).days
                        if days_left < 0:
                            louvre_warn = f"🔴 Louvre badge **EXPIRED** {exp.strftime('%d/%m/%Y')}"
                        elif days_left <= WARN_DAYS:
                            louvre_warn = (f"🟠 Louvre badge expires "
                                           f"**{exp.strftime('%d/%m/%Y')}** ({days_left}d)")
                    except Exception:
                        pass

                rc1, rc2 = st.columns([8, 1])
                with rc1:
                    company_str = (f" · <span style='color:#666;font-size:12px'>"
                                   f"{h.get('company','')}</span>"
                                   if h.get("company") else "")
                    st.markdown(
                        f"<div style='border-left:4px solid {h['color']};padding-left:8px'>"
                        f"<b style='font-size:14px'>{h['name']}</b>{company_str}<br>"
                        f"<span style='font-size:11px;color:#888'>{h['email']}</span>"
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
                        exp_str = (f" (exp. {h['louvre_badge_expiry']})"
                                   if (h.get("louvre_badge_expiry") or "") else "")
                        badges.append(f"🏛L Louvre{exp_str}")
                    if badges:
                        st.caption(" · ".join(badges))
                    if louvre_warn:
                        st.warning(louvre_warn)
                    if h.get("notes"):
                        st.caption(f"📝 {h['notes']}")
                    if h.get("emirates_id_photo") or "":
                        photo_path = os.path.join(UPLOADS_DIR, h.get("emirates_id_photo",""))
                        if os.path.exists(photo_path):
                            with st.expander("🪪 Emirates ID"):
                                st.image(photo_path, width=280)

                with rc2:
                    if st.button("Edit", key=f"btn_edit_{h['id']}", use_container_width=True):
                        st.session_state["editing_id"] = h["id"]
                        # Clear any previous editing_handler state
                        st.session_state.pop("editing_handler", None)
                        st.rerun()
                    if st.button("Del", key=f"btn_del_{h['id']}", use_container_width=True):
                        db.delete_handler(h["id"])
                        st.session_state.pop("editing_id", None)
                        st.rerun()

st.divider()

# ── Add New Handler ───────────────────────────────────────────────────────────
st.markdown("### ➕ Add New Handler")

with st.form("new_handler_form", clear_on_submit=True):
    st.markdown("**Basic Info**")
    n1, n2, n3 = st.columns(3)
    with n1:
        new_name  = st.text_input("Full Name *", placeholder="Sophie Martin")
        new_email = st.text_input("Work Email *", placeholder="sophie@hasenkamp.com")
    with n2:
        new_type  = st.selectbox("Type *", ["Internal", "Subcontractor"])
        new_level = st.selectbox("Level *", ["Senior", "Mid", "Junior"])
    with n3:
        new_color   = st.color_picker("Colour",
                                       value=LEVEL_COLORS[new_type][new_level])
        new_company = st.text_input("Company", placeholder="ISS, Blitz, or leave blank")

    st.markdown("**Louvre Badge & IDs**")
    nb1, nb2, nb3 = st.columns(3)
    with nb1:
        new_louvre = st.checkbox("🏛L Has Louvre Badge")
        new_louvre_exp = st.date_input("Louvre Expiry", value=None,
                                        min_value=date(2020, 1, 1),
                                        key="new_lexp")
    with nb2:
        new_emp_id = st.text_input("Employee / Staff ID", placeholder="HAR-0042")
    with nb3:
        new_eid_upload = st.file_uploader("Emirates ID Photo",
                                           type=["jpg","jpeg","png"],
                                           key="new_eid")

    st.markdown("**Skills & Licences**")
    ns1, ns2 = st.columns(2)
    with ns1:
        new_truck = st.checkbox("🚛 Drives Truck")
        new_car   = st.checkbox("🚗 Drives Car")
    with ns2:
        new_fork  = st.checkbox("🏗 Forklift")
    new_notes = st.text_input("Notes", placeholder="First aider, team leader…")

    add_btn = st.form_submit_button("Add Handler", type="primary",
                                    use_container_width=True)

if add_btn:
    if not new_name or not new_email:
        st.error("Name and email are required.")
    else:
        eid_filename = ""
        if new_eid_upload is not None:
            ext = new_eid_upload.name.rsplit(".", 1)[-1].lower()
            eid_filename = f"{new_name.lower().replace(' ','_')}_eid.{ext}"
            with open(os.path.join(UPLOADS_DIR, eid_filename), "wb") as f:
                f.write(new_eid_upload.read())
        louvre_exp_str = new_louvre_exp.isoformat() if new_louvre_exp else ""
        db.create_handler({
            "name": new_name, "email": new_email, "color": new_color,
            "level": new_level, "type": new_type, "company": new_company,
            "canDriveTruck": new_truck, "canDriveCar": new_car,
            "canDriveForklift": new_fork, "hasBadgeLouvre": new_louvre,
            "notes": new_notes, "employee_id": new_emp_id,
            "louvre_badge_expiry": louvre_exp_str,
            "emirates_id_photo": eid_filename,
        })
        st.success(f"Added **{new_name}**")
        st.rerun()
