import streamlit as st
import db

st.set_page_config(page_title="B · Clients — Hasenkamp", layout="wide")
db.init_db()

st.markdown("## Section B — Client Management")

clients = db.get_clients()

# ── Client cards ──────────────────────────────────────────────────────────────
if clients:
    cols = st.columns(3)
    for i, c in enumerate(clients):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:12px;margin-bottom:8px'>"
                    f"<div style='width:44px;height:44px;border-radius:10px;"
                    f"background:{c['color']};flex-shrink:0'></div>"
                    f"<div><b style='font-size:15px'>{c['name']}</b><br>"
                    f"<span style='font-size:11px;color:#888'>{c['color']}</span></div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                if c.get("contact_person"):
                    st.markdown(f"👤 **{c['contact_person']}**")
                if c.get("contact_email"):
                    st.markdown(f"✉️ `{c['contact_email']}`")
                if c.get("contact_phone"):
                    st.markdown(f"📞 {c['contact_phone']}")
                if c.get("notes"):
                    st.caption(f"📝 {c['notes']}")
                st.markdown("")
                ec1, ec2 = st.columns(2)
                with ec1:
                    if st.button("✏️ Edit", key=f"edit_{c['id']}", use_container_width=True):
                        st.session_state["editing_client"] = c
                        st.rerun()
                with ec2:
                    if st.button("🗑 Delete", key=f"del_{c['id']}", use_container_width=True):
                        db.delete_client(c["id"])
                        st.rerun()
else:
    st.info("No clients yet. Add one below.")

st.divider()

# ── Add / Edit form ───────────────────────────────────────────────────────────
editing = st.session_state.get("editing_client")
st.markdown(f"### {'✏️ Edit Client' if editing else '➕ Add New Client'}")

if editing:
    if st.button("← Cancel"):
        del st.session_state["editing_client"]
        st.rerun()

with st.form("client_form", clear_on_submit=not editing):
    fc1, fc2 = st.columns(2)
    with fc1:
        name = st.text_input(
            "Client Name *",
            value=editing["name"] if editing else "",
            placeholder="e.g. Louvre Museum",
        )
        contact_person = st.text_input(
            "Contact Person",
            value=editing.get("contact_person", "") if editing else "",
            placeholder="Jean Dupont",
        )
        contact_email = st.text_input(
            "Contact Email",
            value=editing.get("contact_email", "") if editing else "",
            placeholder="jean.dupont@louvre.fr",
        )
    with fc2:
        color = st.color_picker(
            "Schedule Colour *",
            value=editing["color"] if editing else "#FFD700",
        )
        contact_phone = st.text_input(
            "Contact Phone",
            value=editing.get("contact_phone", "") if editing else "",
            placeholder="+33 1 40 20 50 50",
        )
        notes = st.text_area(
            "Notes",
            value=editing.get("notes", "") if editing else "",
            placeholder="Billing address, access instructions, special requirements…",
            height=100,
        )

    # Live colour preview
    if name:
        st.markdown(
            f"<div style='background:{color}55;border:2px solid {color};"
            f"border-radius:8px;padding:8px 14px;font-weight:600;font-size:14px'>"
            f"<span style='display:inline-block;width:12px;height:12px;border-radius:50%;"
            f"background:{color};margin-right:8px;vertical-align:middle'></span>"
            f"{name}</div>",
            unsafe_allow_html=True,
        )

    submitted = st.form_submit_button(
        "Save Changes" if editing else "Add Client",
        type="primary", use_container_width=True,
    )

if submitted:
    if not name:
        st.error("Client name is required.")
    else:
        if editing:
            db.update_client(editing["id"], name, color,
                             contact_person, contact_email, contact_phone, notes)
            del st.session_state["editing_client"]
            st.success(f"Updated **{name}**")
        else:
            db.create_client(name, color,
                             contact_person, contact_email, contact_phone, notes)
            st.success(f"Added **{name}**")
        st.rerun()
