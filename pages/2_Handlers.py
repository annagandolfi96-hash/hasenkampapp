import streamlit as st
import db

st.set_page_config(page_title="Art Handlers — Hasenkamp", layout="wide")
db.init_db()

LEVEL_COLORS = {
    "Internal": {"Senior": "#4A90D9", "Mid": "#27AE60", "Junior": "#F39C12"},
    "Subcontractor": {"Senior": "#9B59B6", "Mid": "#E74C3C", "Junior": "#95A5A6"},
}

st.markdown("## 👷 Art Handlers")

handlers = db.get_handlers()

# Group by type + level
groups = {}
for h in handlers:
    key = f"{h['type']} — {h['level']}"
    groups.setdefault(key, []).append(h)

group_order = [
    "Internal — Senior", "Internal — Mid", "Internal — Junior",
    "Subcontractor — Senior", "Subcontractor — Mid", "Subcontractor — Junior",
]

for group in group_order:
    group_handlers = groups.get(group, [])
    if not group_handlers:
        continue
    t, lvl = group.split(" — ")
    color = LEVEL_COLORS[t][lvl]
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:8px;margin-top:16px;margin-bottom:4px'>"
        f"<span style='width:12px;height:12px;border-radius:50%;background:{color};display:inline-block'></span>"
        f"<b style='font-size:14px'>{group}</b></div>",
        unsafe_allow_html=True,
    )
    cols = st.columns(2)
    for i, h in enumerate(group_handlers):
        with cols[i % 2]:
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(
                        f"<div style='border-left:4px solid {h['color']};padding-left:8px'>"
                        f"<b>{h['name']}</b><br>"
                        f"<span style='font-size:12px;color:#888'>{h['email']}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    badges = []
                    if h["canDriveTruck"]: badges.append("🚛 Truck")
                    if h["canDriveCar"]: badges.append("🚗 Car")
                    if h["canDriveForklift"]: badges.append("🏗 Forklift")
                    if h["hasBadgeLouvre"]: badges.append("🏛 Louvre")
                    if badges:
                        st.caption(" · ".join(badges))
                    if h["notes"]:
                        st.caption(f"📝 {h['notes']}")
                with c2:
                    if st.button("Edit", key=f"edit_{h['id']}"):
                        st.session_state["editing_handler"] = h
                        st.rerun()
                    if st.button("Del", key=f"del_{h['id']}"):
                        db.delete_handler(h["id"])
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
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name *", value=editing["name"] if editing else "")
        email = st.text_input("Email *", value=editing["email"] if editing else "")
        htype = st.selectbox("Type *", ["Internal", "Subcontractor"],
                             index=0 if not editing else ["Internal", "Subcontractor"].index(editing["type"]))
        level = st.selectbox("Level *", ["Senior", "Mid", "Junior"],
                             index=0 if not editing else ["Senior", "Mid", "Junior"].index(editing["level"]))
    with col2:
        auto_color = LEVEL_COLORS[htype][level]
        color = st.color_picker(
            "Colour (auto by level, override if needed)",
            value=editing["color"] if editing else auto_color,
        )
        notes = st.text_input("Notes (extra badges, etc.)",
                              value=editing["notes"] if editing and editing["notes"] else "")

    st.markdown("**Skills & Badges**")
    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        can_truck = st.checkbox("🚛 Drives Truck", value=bool(editing["canDriveTruck"]) if editing else False)
    with sc2:
        can_car = st.checkbox("🚗 Drives Car", value=bool(editing["canDriveCar"]) if editing else False)
    with sc3:
        can_fork = st.checkbox("🏗 Forklift", value=bool(editing["canDriveForklift"]) if editing else False)
    with sc4:
        louvre = st.checkbox("🏛 Louvre Badge", value=bool(editing["hasBadgeLouvre"]) if editing else False)

    submitted = st.form_submit_button(
        "Save Changes" if editing else "Add Handler", type="primary", use_container_width=True
    )

if submitted:
    if not name or not email:
        st.error("Name and email are required.")
    else:
        data = {
            "name": name, "email": email, "color": color, "level": level, "type": htype,
            "canDriveTruck": can_truck, "canDriveCar": can_car,
            "canDriveForklift": can_fork, "hasBadgeLouvre": louvre, "notes": notes,
        }
        if editing:
            db.update_handler(editing["id"], data)
            del st.session_state["editing_handler"]
            st.success(f"Updated {name}")
        else:
            db.create_handler(data)
            st.success(f"Added {name}")
        st.rerun()
