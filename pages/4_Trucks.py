import streamlit as st
import db

st.set_page_config(page_title="Vehicles — Hasenkamp", layout="wide")
db.init_db()

st.markdown("## 🚚 Vehicles")

trucks = db.get_trucks()

cols = st.columns(3)
for i, t in enumerate(trucks):
    with cols[i % 3]:
        with st.container(border=True):
            st.markdown(f"### 🚚 {t['name']}")
            if t["licensePlate"]:
                st.code(t["licensePlate"], language=None)
            tc1, tc2 = st.columns(2)
            with tc1:
                if st.button("Edit", key=f"edit_{t['id']}", use_container_width=True):
                    st.session_state["editing_truck"] = t
                    st.rerun()
            with tc2:
                if st.button("Delete", key=f"del_{t['id']}", use_container_width=True):
                    db.delete_truck(t["id"])
                    st.rerun()

st.divider()

editing = st.session_state.get("editing_truck")
st.markdown(f"### {'✏️ Edit Vehicle' if editing else '➕ Add New Vehicle'}")

if editing:
    if st.button("← Cancel Edit"):
        del st.session_state["editing_truck"]
        st.rerun()

with st.form("truck_form", clear_on_submit=not editing):
    name = st.text_input("Name *", value=editing["name"] if editing else "",
                         placeholder="Van 1, Truck 7.5T…")
    plate = st.text_input("License Plate", value=editing["licensePlate"] if editing and editing["licensePlate"] else "",
                          placeholder="75-ART-001")
    submitted = st.form_submit_button(
        "Save" if editing else "Add Vehicle", type="primary", use_container_width=True
    )

if submitted:
    if not name:
        st.error("Vehicle name is required.")
    else:
        if editing:
            db.update_truck(editing["id"], name, plate)
            del st.session_state["editing_truck"]
            st.success(f"Updated {name}")
        else:
            db.create_truck(name, plate)
            st.success(f"Added {name}")
        st.rerun()
