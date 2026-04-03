import streamlit as st
import db

st.set_page_config(page_title="Clients — Hasenkamp", layout="wide")
db.init_db()

st.markdown("## 🏛️ Clients")

clients = db.get_clients()

cols = st.columns(3)
for i, c in enumerate(clients):
    with cols[i % 3]:
        with st.container(border=True):
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:12px'>"
                f"<div style='width:40px;height:40px;border-radius:8px;background:{c['color']};flex-shrink:0'></div>"
                f"<div><b>{c['name']}</b><br><span style='font-size:11px;color:#888'>{c['color']}</span></div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.markdown("")
            ec1, ec2 = st.columns(2)
            with ec1:
                if st.button("Edit", key=f"edit_{c['id']}", use_container_width=True):
                    st.session_state["editing_client"] = c
                    st.rerun()
            with ec2:
                if st.button("Delete", key=f"del_{c['id']}", use_container_width=True):
                    db.delete_client(c["id"])
                    st.rerun()

st.divider()

editing = st.session_state.get("editing_client")
st.markdown(f"### {'✏️ Edit Client' if editing else '➕ Add New Client'}")

if editing:
    if st.button("← Cancel Edit"):
        del st.session_state["editing_client"]
        st.rerun()

with st.form("client_form", clear_on_submit=not editing):
    name = st.text_input("Client Name *", value=editing["name"] if editing else "")
    color = st.color_picker(
        "Schedule Colour *",
        value=editing["color"] if editing else "#FFD700",
    )
    if name:
        st.markdown(
            f"<div style='background:{color}55;border-radius:8px;padding:8px 12px;"
            f"font-weight:600;font-size:14px'>{name}</div>",
            unsafe_allow_html=True,
        )
    submitted = st.form_submit_button(
        "Save" if editing else "Add Client", type="primary", use_container_width=True
    )

if submitted:
    if not name:
        st.error("Client name is required.")
    else:
        if editing:
            db.update_client(editing["id"], name, color)
            del st.session_state["editing_client"]
            st.success(f"Updated {name}")
        else:
            db.create_client(name, color)
            st.success(f"Added {name}")
        st.rerun()
