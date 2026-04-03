import streamlit as st
from datetime import date, timedelta
import db

st.set_page_config(
    page_title="Hasenkamp | Art Logistics",
    page_icon="🖼️",
    layout="wide",
)

db.init_db()

# ── Shared CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.grid-table { border-collapse: collapse; width: 100%; font-size: 12px; }
.grid-table th {
    background: #1a1a2e; color: white; padding: 6px 8px;
    border: 1px solid #333; white-space: nowrap; text-align: center;
    font-weight: 600; min-width: 80px;
}
.grid-table th.name-col { text-align: left; min-width: 160px; position: sticky; left: 0; }
.grid-table td {
    border: 1px solid #ddd; padding: 4px 6px; text-align: center;
    height: 36px; vertical-align: middle;
}
.grid-table td.name-cell { text-align: left; white-space: nowrap; font-weight: 500; }
.grid-table td.section-header {
    background: #f0f0f0; font-weight: 700; font-size: 11px;
    color: #666; text-transform: uppercase; letter-spacing: 0.05em;
    text-align: left; padding: 4px 8px;
}
.grid-table .booked-num { font-weight: 700; font-size: 14px; color: #1a1a1a; }
.grid-table .prebooked-num { font-weight: 700; font-size: 14px; color: #e07b00; }
.grid-table .unavail-text { font-size: 10px; color: #aaa; }
.today-col { outline: 2px solid #4A90D9; outline-offset: -2px; }
.legend { display: flex; gap: 16px; flex-wrap: wrap; align-items: center;
          font-size: 12px; color: #555; margin-bottom: 8px; }
.legend-dot { width: 10px; height: 10px; border-radius: 50%;
              display: inline-block; margin-right: 4px; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "start_date" not in st.session_state:
    st.session_state.start_date = date.today()

DAYS = 14


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def date_range():
    return [st.session_state.start_date + timedelta(days=i) for i in range(DAYS)]


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 🖼️ Hasenkamp — Schedule")

col1, col2, col3, col4, spacer = st.columns([1, 1, 1, 3, 5])
with col1:
    if st.button("← Prev", use_container_width=True):
        st.session_state.start_date -= timedelta(days=DAYS)
        st.rerun()
with col2:
    if st.button("Today", use_container_width=True):
        st.session_state.start_date = date.today()
        st.rerun()
with col3:
    if st.button("Next →", use_container_width=True):
        st.session_state.start_date += timedelta(days=DAYS)
        st.rerun()
with col4:
    dates = date_range()
    st.markdown(
        f"<div style='padding-top:6px;color:#555;font-size:14px'>"
        f"{dates[0].strftime('%d %b')} – {dates[-1].strftime('%d %b %Y')}</div>",
        unsafe_allow_html=True,
    )

# Legend
st.markdown("""
<div class="legend">
  <span><span class="legend-dot" style="background:#4A90D9"></span>Senior Internal</span>
  <span><span class="legend-dot" style="background:#27AE60"></span>Mid Internal</span>
  <span><span class="legend-dot" style="background:#F39C12"></span>Junior Internal</span>
  <span><span class="legend-dot" style="background:#9B59B6"></span>Senior Sub</span>
  <span><span class="legend-dot" style="background:#E74C3C"></span>Mid Sub</span>
  <span><span class="legend-dot" style="background:#95A5A6"></span>Junior Sub</span>
  <span><span class="legend-dot" style="background:#111;border-radius:2px"></span>Unavailable</span>
  <span style="color:#e07b00;font-weight:700">8</span><span>= pre-booked</span>
  <span style="color:#1a1a1a;font-weight:700">8</span><span>= confirmed</span>
</div>
""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
handlers = db.get_handlers()
trucks = db.get_trucks()
projects = db.get_projects_in_range(st.session_state.start_date, DAYS)
handler_unavail, truck_unavail = db.get_unavailabilities_in_range(
    st.session_state.start_date, DAYS
)

# Build lookup maps
proj_by_handler: dict = {}  # (date_str, handler_id) -> project
proj_by_truck: dict = {}    # (date_str, truck_id) -> project
for p in projects:
    ds = p["date"]
    for b in p["bookings"]:
        proj_by_handler[(ds, b["handlerId"])] = p
    for b in p["truckBookings"]:
        proj_by_truck[(ds, b["truckId"])] = p

unavail_by_handler: dict = {}  # (date_str, handler_id) -> record
for u in handler_unavail:
    unavail_by_handler[(u["date"], u["handlerId"])] = u

unavail_by_truck: dict = {}  # (date_str, truck_id) -> record
for u in truck_unavail:
    unavail_by_truck[(u["date"], u["truckId"])] = u

today_str = date.today().isoformat()


# ── Build HTML grid ───────────────────────────────────────────────────────────
def build_grid() -> str:
    rows = ["<table class='grid-table'><thead><tr>"]
    rows.append("<th class='name-col'>Name</th>")
    for d in dates:
        ds = d.isoformat()
        today_cls = " today-col" if ds == today_str else ""
        rows.append(
            f"<th class='{today_cls}'>"
            f"{d.strftime('%a')}<br><span style='color:#aaa;font-size:10px'>{d.strftime('%d %b')}</span>"
            f"</th>"
        )
    rows.append("</tr></thead><tbody>")

    # Art Handlers section
    rows.append(f"<tr><td class='section-header' colspan='{DAYS + 1}'>Art Handlers</td></tr>")
    for h in handlers:
        name_bg = hex_to_rgba(h["color"], 0.18)
        icons = ""
        if h["canDriveTruck"]: icons += "🚛"
        if h["canDriveForklift"]: icons += "🏗"
        if h["hasBadgeLouvre"]: icons += "🏛"
        sub = "Sub" if h["type"] == "Subcontractor" else "Int"
        rows.append(
            f"<tr>"
            f"<td class='name-cell' style='background:{name_bg}'>"
            f"<span style='display:inline-block;width:8px;height:8px;border-radius:50%;"
            f"background:{h['color']};margin-right:4px'></span>"
            f"<b>{h['name']}</b> {icons}<br>"
            f"<span style='font-size:10px;color:#888;padding-left:12px'>{h['level']} · {sub}</span>"
            f"</td>"
        )
        for d in dates:
            ds = d.isoformat()
            proj = proj_by_handler.get((ds, h["id"]))
            unavail = unavail_by_handler.get((ds, h["id"]))
            today_cls = " today-col" if ds == today_str else ""
            if proj:
                bg = hex_to_rgba(proj["clientColor"], 0.4)
                num_cls = "booked-num" if proj["status"] == "BOOKED" else "prebooked-num"
                count = len(proj["bookings"])
                rows.append(
                    f"<td style='background:{bg}' class='{today_cls}'>"
                    f"<span class='{num_cls}'>{count}</span></td>"
                )
            elif unavail:
                reason = (unavail.get("reason") or "N/A")[:5]
                rows.append(
                    f"<td style='background:#111' class='{today_cls}'>"
                    f"<span class='unavail-text'>{reason}</span></td>"
                )
            else:
                rows.append(f"<td class='{today_cls}'></td>")
        rows.append("</tr>")

    # Vehicles section
    rows.append(f"<tr><td class='section-header' colspan='{DAYS + 1}'>Vehicles</td></tr>")
    for t in trucks:
        plate = f"<br><span style='font-size:10px;color:#888;padding-left:20px'>{t['licensePlate'] or ''}</span>"
        rows.append(
            f"<tr>"
            f"<td class='name-cell' style='background:#fff'>"
            f"🚚 <b>{t['name']}</b>{plate}</td>"
        )
        for d in dates:
            ds = d.isoformat()
            proj = proj_by_truck.get((ds, t["id"]))
            unavail = unavail_by_truck.get((ds, t["id"]))
            today_cls = " today-col" if ds == today_str else ""
            if proj:
                bg = hex_to_rgba(proj["clientColor"], 0.4)
                num_cls = "booked-num" if proj["status"] == "BOOKED" else "prebooked-num"
                rows.append(
                    f"<td style='background:{bg}' class='{today_cls}'>"
                    f"<span class='{num_cls}'>✓</span></td>"
                )
            elif unavail:
                reason = (unavail.get("reason") or "N/A")[:5]
                rows.append(
                    f"<td style='background:#111' class='{today_cls}'>"
                    f"<span class='unavail-text'>{reason}</span></td>"
                )
            else:
                rows.append(f"<td class='{today_cls}'></td>")
        rows.append("</tr>")

    rows.append("</tbody></table>")
    return "".join(rows)


st.markdown(build_grid(), unsafe_allow_html=True)

st.divider()

# ── Actions ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📋 New Booking", "🚫 Mark Unavailable", "📁 View / Manage Bookings"])

# ── Tab 1: New Booking ────────────────────────────────────────────────────────
with tab1:
    clients = db.get_clients()
    client_map = {c["name"]: c for c in clients}

    with st.form("new_booking_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            client_name = st.selectbox("Client *", [c["name"] for c in clients])
            project_number = st.text_input("Project Number *", placeholder="HAR-2026-XXX")
            booking_date = st.date_input("Date *", value=date.today())
            initials = st.text_input("Your Initials *", max_chars=5, placeholder="AG")
        with col2:
            location = st.text_input("Location", placeholder="Louvre Museum, Paris")
            description = st.text_area("Description", placeholder="Brief description of the work…", height=100)

        st.markdown("**Select Art Handlers \\***")
        handler_options = {h["name"]: h["id"] for h in handlers}
        selected_handler_names = st.multiselect(
            "Handlers", list(handler_options.keys()), label_visibility="collapsed"
        )

        st.markdown("**Assign Vehicles** (optional)")
        truck_options = {t["name"]: t["id"] for t in trucks}
        selected_truck_names = st.multiselect(
            "Trucks", list(truck_options.keys()), label_visibility="collapsed"
        )

        col_a, col_b = st.columns(2)
        with col_a:
            pre_book = st.form_submit_button("Pre-book", use_container_width=True)
        with col_b:
            confirm_book = st.form_submit_button(
                "✅ Confirm Booking", use_container_width=True, type="primary"
            )

    if pre_book or confirm_book:
        if not client_name or not project_number or not selected_handler_names or not initials:
            st.error("Please fill in client, project number, initials and select at least one handler.")
        else:
            client = client_map[client_name]
            handler_ids = [handler_options[n] for n in selected_handler_names]
            truck_ids = [truck_options[n] for n in selected_truck_names]
            handler_names_short = [n.split()[0] for n in selected_handler_names]
            title = f"{initials} - {client_name} - {', '.join(handler_names_short)} - {project_number}"
            status = "BOOKED" if confirm_book else "PRE_BOOKED"
            db.create_project(
                {
                    "projectNumber": project_number,
                    "title": title,
                    "clientId": client["id"],
                    "description": description,
                    "location": location,
                    "date": booking_date.isoformat(),
                    "status": status,
                    "createdBy": initials,
                },
                handler_ids,
                truck_ids,
            )
            label = "Confirmed" if confirm_book else "Pre-booked"
            st.success(f"✅ {label}: {title}")
            st.rerun()

# ── Tab 2: Mark Unavailable ───────────────────────────────────────────────────
with tab2:
    with st.form("unavail_form", clear_on_submit=True):
        entity_type = st.radio("Type", ["Art Handler", "Vehicle"], horizontal=True)
        if entity_type == "Art Handler":
            entity_name = st.selectbox("Handler", [h["name"] for h in handlers])
        else:
            entity_name = st.selectbox("Vehicle", [t["name"] for t in trucks])

        unavail_date = st.date_input("Date", value=date.today(), key="unavail_date")
        reason = st.text_input("Reason", placeholder="Annual leave, Service, Training…")

        col_a, col_b = st.columns(2)
        with col_a:
            mark = st.form_submit_button("Mark Unavailable", use_container_width=True, type="primary")
        with col_b:
            remove = st.form_submit_button("Remove Unavailability", use_container_width=True)

    if mark or remove:
        ds = unavail_date.isoformat()
        if entity_type == "Art Handler":
            h = next(h for h in handlers if h["name"] == entity_name)
            if mark:
                db.set_handler_unavailable(h["id"], ds, reason)
                st.success(f"Marked {entity_name} unavailable on {unavail_date.strftime('%d %b %Y')}")
            else:
                db.remove_handler_unavailability(h["id"], ds)
                st.success(f"Removed unavailability for {entity_name} on {unavail_date.strftime('%d %b %Y')}")
        else:
            t = next(t for t in trucks if t["name"] == entity_name)
            if mark:
                db.set_truck_unavailable(t["id"], ds, reason)
                st.success(f"Marked {entity_name} unavailable on {unavail_date.strftime('%d %b %Y')}")
            else:
                db.remove_truck_unavailability(t["id"], ds)
                st.success(f"Removed unavailability for {entity_name}")
        st.rerun()

# ── Tab 3: View / Manage Bookings ─────────────────────────────────────────────
with tab3:
    if not projects:
        st.info("No bookings in the current date range.")
    else:
        for p in projects:
            color = p["clientColor"]
            status_badge = (
                "🟢 **Confirmed**" if p["status"] == "BOOKED" else "🟠 **Pre-booked**"
            )
            with st.expander(
                f"{p['clientName']} — {p['projectNumber']} — {p['date']}  {status_badge}"
            ):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**Location:** {p['location'] or '—'}")
                    st.markdown(f"**Description:** {p['description'] or '—'}")
                    st.markdown(f"**Created by:** {p['createdBy']}")
                    st.markdown(f"**Team ({len(p['bookings'])} handlers):**")
                    for b in p["bookings"]:
                        badge = "🏛" if b["hasBadgeLouvre"] else ""
                        st.markdown(f"- {b['handlerName']} ({b['level']}) {badge} — `{b['handlerEmail']}`")
                    if p["truckBookings"]:
                        st.markdown("**Vehicles:**")
                        for b in p["truckBookings"]:
                            st.markdown(f"- 🚚 {b['truckName']} {b['licensePlate'] or ''}")

                with col2:
                    if p["status"] == "PRE_BOOKED":
                        if st.button("✅ Confirm", key=f"confirm_{p['id']}", use_container_width=True):
                            db.confirm_project(p["id"])
                            st.rerun()

                    # Outlook invite
                    emails = "; ".join(b["handlerEmail"] for b in p["bookings"])
                    handler_first_names = ", ".join(b["handlerName"].split()[0] for b in p["bookings"])
                    invite_title = f"{p['createdBy']} - {p['clientName']} - {handler_first_names} - {p['projectNumber']}"
                    body_lines = [
                        invite_title, "",
                        f"Client: {p['clientName']}",
                        f"Project: {p['projectNumber']}",
                        f"Date: {p['date']}",
                        f"Location: {p['location'] or 'TBC'}", "",
                        "Description:", p["description"] or "—", "",
                        "Team:",
                        *[f"  • {b['handlerName']} ({b['level']})" for b in p["bookings"]],
                    ]
                    if p["truckBookings"]:
                        body_lines += ["", "Vehicles:"] + [f"  • {b['truckName']}" for b in p["truckBookings"]]
                    body = "\n".join(body_lines)

                    with st.popover("📧 Outlook Invite", use_container_width=True):
                        st.markdown("**To (recipients):**")
                        st.code(emails, language=None)
                        st.markdown("**Title:**")
                        st.code(invite_title, language=None)
                        st.markdown("**Location:**")
                        st.code(p["location"] or "TBC", language=None)
                        st.markdown("**Body:**")
                        st.code(body, language=None)
                        d_str = p["date"]
                        outlook_url = (
                            f"https://outlook.office.com/calendar/deeplink/compose"
                            f"?subject={invite_title.replace(' ', '%20')}"
                            f"&startdt={d_str}T09:00:00&enddt={d_str}T17:00:00"
                            f"&location={str(p['location'] or '').replace(' ', '%20')}"
                        )
                        st.link_button("Open in Outlook →", outlook_url)
                        st.caption("⚠️ Attach the delivery note before sending. Add team manager as optional.")

                    if st.button("🗑 Delete", key=f"delete_{p['id']}", use_container_width=True):
                        db.delete_project(p["id"])
                        st.rerun()
