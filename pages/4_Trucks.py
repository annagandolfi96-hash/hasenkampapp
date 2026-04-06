import streamlit as st
from datetime import date
import db

st.set_page_config(page_title="D · Vehicles — Hasenkamp", layout="wide")
db.init_db()

WARN_DAYS = 60  # flag service due within this many days

st.markdown("## 🚚 Section D — Vehicles")

trucks = db.get_trucks()
today = date.today()

# ── Vehicle cards ─────────────────────────────────────────────────────────────
if trucks:
    cols = st.columns(3)
    for i, t in enumerate(trucks):
        with cols[i % 3]:
            with st.container(border=True):
                spec_label = f" · {t['spec']}" if t.get("spec") else ""
                st.markdown(f"### 🚚 {t['name']}{spec_label}")

                if t.get("licensePlate"):
                    st.code(t["licensePlate"], language=None)

                # Service due warning
                if t.get("service_due"):
                    try:
                        svc = date.fromisoformat(t["service_due"])
                        days_left = (svc - today).days
                        if days_left < 0:
                            st.error(f"🔴 Service **OVERDUE** — was due {svc.strftime('%d/%m/%Y')}")
                        elif days_left <= WARN_DAYS:
                            st.warning(f"🟠 Service due **{svc.strftime('%d/%m/%Y')}** ({days_left} days)")
                        else:
                            st.caption(f"🔧 Next service: {svc.strftime('%d/%m/%Y')}")
                    except Exception:
                        st.caption(f"🔧 Service due: {t['service_due']}")

                st.markdown("")
                tc1, tc2 = st.columns(2)
                with tc1:
                    if st.button("✏️ Edit", key=f"edit_{t['id']}", use_container_width=True):
                        st.session_state["editing_truck"] = t
                        st.rerun()
                with tc2:
                    if st.button("🗑 Delete", key=f"del_{t['id']}", use_container_width=True):
                        db.delete_truck(t["id"])
                        st.rerun()
else:
    st.info("No vehicles yet. Add one below.")

st.divider()

# ── Add / Edit form ───────────────────────────────────────────────────────────
editing = st.session_state.get("editing_truck")
st.markdown(f"### {'✏️ Edit Vehicle' if editing else '➕ Add New Vehicle'}")

if editing:
    if st.button("← Cancel"):
        del st.session_state["editing_truck"]
        st.rerun()

with st.form("truck_form", clear_on_submit=not editing):
    fc1, fc2 = st.columns(2)
    with fc1:
        name = st.text_input(
            "Vehicle Name *",
            value=editing["name"] if editing else "",
            placeholder="Van 1, Truck 10T…",
        )
        plate = st.text_input(
            "License Plate",
            value=editing.get("licensePlate","") if editing else "",
            placeholder="75-ART-001",
        )
    with fc2:
        spec = st.text_input(
            "Spec / Type",
            value=editing.get("spec","") if editing else "",
            placeholder="Sprinter, 3 ton, 10 ton…",
        )
        _default_svc = None
        if editing and editing.get("service_due"):
            try:
                _default_svc = date.fromisoformat(editing["service_due"])
            except Exception:
                pass
        service_due = st.date_input(
            "Next Service Due",
            value=_default_svc,
            min_value=date(2020, 1, 1),
            key="svc_due_input",
        )
        clear_svc = st.checkbox("Clear service date", value=False, key="clear_svc")

    submitted = st.form_submit_button(
        "Save Changes" if editing else "Add Vehicle",
        type="primary", use_container_width=True,
    )

if submitted:
    if not name:
        st.error("Vehicle name is required.")
    else:
        svc_str = "" if clear_svc else (service_due.isoformat() if service_due else "")
        if editing:
            db.update_truck(editing["id"], name, plate, spec, svc_str)
            del st.session_state["editing_truck"]
            st.success(f"Updated **{name}**")
        else:
            db.create_truck(name, plate, spec, svc_str)
            st.success(f"Added **{name}**")
        st.rerun()
