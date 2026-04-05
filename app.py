import streamlit as st
from datetime import date, timedelta
import db

st.set_page_config(
    page_title="Art Handler Schedule",
    page_icon="🖼️",
    layout="wide",
)

db.init_db()

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.grid-table { border-collapse: collapse; width: 100%; font-size: 11px; }
.grid-table th {
    background: #1a1a2e; color: white; padding: 4px 4px;
    border: 1px solid #333; white-space: nowrap; text-align: center;
    font-weight: 600; min-width: 58px; max-width: 58px; width: 58px;
}
.grid-table th.name-col {
    text-align: left; min-width: 150px; max-width: 150px; width: 150px;
}
.grid-table td {
    border: 1px solid #ddd; padding: 2px 3px; text-align: center;
    height: 32px; vertical-align: middle;
    min-width: 58px; max-width: 58px; width: 58px;
}
.grid-table td.name-cell {
    text-align: left; white-space: nowrap; font-weight: 500;
    min-width: 150px; max-width: 150px; width: 150px; overflow: hidden;
}
.grid-table td.section-header {
    background: #e8e8e8; font-weight: 700; font-size: 10px;
    color: #555; text-transform: uppercase; letter-spacing: 0.06em;
    text-align: left; padding: 3px 6px; min-width: unset; max-width: unset; width: auto;
}
.booked-num    { font-weight: 700; font-size: 13px; color: #1a1a1a; }
.prebooked-num { font-weight: 700; font-size: 13px; color: #e07b00; }
.unavail-text  { font-size: 9px; color: #aaa; }
.today-col     { outline: 2px solid #4A90D9; outline-offset: -2px; }
.legend { display:flex; gap:14px; flex-wrap:wrap; align-items:center;
          font-size:11px; color:#555; margin-bottom:6px; }
.ldot { width:9px;height:9px;border-radius:50%;display:inline-block;margin-right:3px; }
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


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 🖼️ Art Handler Schedule")

c1, c2, c3, c4, _ = st.columns([1, 1, 1, 4, 4])
with c1:
    if st.button("← Prev", use_container_width=True):
        st.session_state.start_date -= timedelta(days=DAYS)
        st.rerun()
with c2:
    if st.button("Today", use_container_width=True):
        st.session_state.start_date = date.today()
        st.rerun()
with c3:
    if st.button("Next →", use_container_width=True):
        st.session_state.start_date += timedelta(days=DAYS)
        st.rerun()

dates = [st.session_state.start_date + timedelta(days=i) for i in range(DAYS)]
with c4:
    st.markdown(
        f"<div style='padding-top:6px;color:#555;font-size:13px'>"
        f"{dates[0].strftime('%d %b')} – {dates[-1].strftime('%d %b %Y')}</div>",
        unsafe_allow_html=True,
    )

st.markdown("""
<div class="legend">
  <span><span class="ldot" style="background:#4A90D9"></span>Senior Internal</span>
  <span><span class="ldot" style="background:#27AE60"></span>Mid Internal</span>
  <span><span class="ldot" style="background:#F39C12"></span>Junior Internal</span>
  <span><span class="ldot" style="background:#9B59B6"></span>Senior Sub</span>
  <span><span class="ldot" style="background:#E74C3C"></span>Mid Sub</span>
  <span><span class="ldot" style="background:#95A5A6"></span>Junior Sub</span>
  <span><span class="ldot" style="background:#111;border-radius:2px"></span>Unavailable</span>
  &nbsp;<span style="color:#e07b00;font-weight:700">8</span> pre-booked &nbsp;
  <span style="color:#1a1a1a;font-weight:700">8</span> confirmed
</div>
""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
handlers     = db.get_handlers()
trucks       = db.get_trucks()
projects     = db.get_projects_in_range(st.session_state.start_date, DAYS)
handler_unavail, truck_unavail = db.get_unavailabilities_in_range(
    st.session_state.start_date, DAYS
)

proj_by_handler: dict = {}
proj_by_truck:   dict = {}
for p in projects:
    ds = p["date"]
    for b in p["bookings"]:
        proj_by_handler[(ds, b["handlerId"])] = p
    for b in p["truckBookings"]:
        proj_by_truck[(ds, b["truckId"])] = p

unavail_by_handler: dict = {}
for u in handler_unavail:
    unavail_by_handler[(u["date"], u["handlerId"])] = u

unavail_by_truck: dict = {}
for u in truck_unavail:
    unavail_by_truck[(u["date"], u["truckId"])] = u

today_str = date.today().isoformat()


# ── Grid ─────────────────────────────────────────────────────────────────────
def build_grid() -> str:
    rows = ["<table class='grid-table'><thead><tr>"]
    rows.append("<th class='name-col'>Name</th>")
    for d in dates:
        ds = d.isoformat()
        tc = " today-col" if ds == today_str else ""
        rows.append(
            f"<th class='{tc}'>{d.strftime('%a')}<br>"
            f"<span style='color:#bbb;font-size:9px'>{d.strftime('%d/%m')}</span></th>"
        )
    rows.append("</tr></thead><tbody>")

    # Art Handlers
    rows.append(f"<tr><td class='section-header' colspan='{DAYS+1}'>Art Handlers</td></tr>")
    for h in handlers:
        name_bg = hex_to_rgba(h["color"], 0.18)
        icons = ""
        if h.get("canDriveTruck"):   icons += "🚛"
        if h.get("canDriveForklift"): icons += "🏗"
        if h.get("hasBadgeLouvre"):  icons += "🏛"
        company_tag = ""
        if h.get("company") == db.BLITZ_COMPANY:
            company_tag = " <span style='font-size:9px;background:#fee;color:#c00;border-radius:2px;padding:0 2px'>B</span>"
        sub = "Sub" if h["type"] == "Subcontractor" else "Int"
        rows.append(
            f"<tr><td class='name-cell' style='background:{name_bg}'>"
            f"<span style='display:inline-block;width:7px;height:7px;border-radius:50%;"
            f"background:{h['color']};margin-right:3px;vertical-align:middle'></span>"
            f"<b>{h['name']}</b>{company_tag} {icons}<br>"
            f"<span style='font-size:9px;color:#999;padding-left:10px'>{h['level']} · {sub}</span>"
            f"</td>"
        )
        for d in dates:
            ds = d.isoformat()
            proj   = proj_by_handler.get((ds, h["id"]))
            unavail = unavail_by_handler.get((ds, h["id"]))
            tc = " today-col" if ds == today_str else ""
            if proj:
                bg = hex_to_rgba(proj["clientColor"], 0.4)
                num_cls = "booked-num" if proj["status"] == "BOOKED" else "prebooked-num"
                count = len(proj["bookings"])
                rows.append(f"<td style='background:{bg}' class='{tc}'><span class='{num_cls}'>{count}</span></td>")
            elif unavail:
                reason = (unavail.get("reason") or "N/A")[:5]
                rows.append(f"<td style='background:#111' class='{tc}'><span class='unavail-text'>{reason}</span></td>")
            else:
                rows.append(f"<td class='{tc}'></td>")
        rows.append("</tr>")

    # Vehicles
    rows.append(f"<tr><td class='section-header' colspan='{DAYS+1}'>Vehicles</td></tr>")
    for t in trucks:
        plate = f"<br><span style='font-size:9px;color:#999;padding-left:18px'>{t['licensePlate'] or ''}</span>"
        rows.append(f"<tr><td class='name-cell' style='background:#fafafa'>🚚 <b>{t['name']}</b>{plate}</td>")
        for d in dates:
            ds = d.isoformat()
            proj    = proj_by_truck.get((ds, t["id"]))
            unavail = unavail_by_truck.get((ds, t["id"]))
            tc = " today-col" if ds == today_str else ""
            if proj:
                bg = hex_to_rgba(proj["clientColor"], 0.4)
                num_cls = "booked-num" if proj["status"] == "BOOKED" else "prebooked-num"
                rows.append(f"<td style='background:{bg}' class='{tc}'><span class='{num_cls}'>✓</span></td>")
            elif unavail:
                reason = (unavail.get("reason") or "N/A")[:5]
                rows.append(f"<td style='background:#111' class='{tc}'><span class='unavail-text'>{reason}</span></td>")
            else:
                rows.append(f"<td class='{tc}'></td>")
        rows.append("</tr>")

    rows.append("</tbody></table>")
    return "".join(rows)


st.markdown(build_grid(), unsafe_allow_html=True)
st.divider()

# ── Action tabs ───────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📋 New Booking", "🚫 Mark Unavailable", "📁 View / Manage Bookings"])

# ── Tab 1: New Booking ────────────────────────────────────────────────────────
with tab1:
    clients    = db.get_clients()
    client_map = {c["name"]: c for c in clients}

    col1, col2 = st.columns(2)
    with col1:
        client_name    = st.selectbox("Client *", [c["name"] for c in clients], key="nb_client")
        project_number = st.text_input("Project Number *", placeholder="HAR-2026-XXX", key="nb_projnum")
        booking_date   = st.date_input("Date *", value=date.today(), key="nb_date")
        initials       = st.text_input("Your Initials *", max_chars=5, placeholder="AG", key="nb_initials")
    with col2:
        location    = st.text_input("Location", placeholder="Louvre Museum, Paris", key="nb_location")
        description = st.text_area("Description", placeholder="Brief description of the work…",
                                   height=108, key="nb_desc")

    handler_map = {h["name"]: h for h in handlers}
    st.markdown("**Select Art Handlers \\***")
    selected_handler_names = st.multiselect(
        "Handlers", list(handler_map.keys()), label_visibility="collapsed", key="nb_handlers"
    )

    truck_map = {t["name"]: t for t in trucks}
    st.markdown("**Assign Vehicles** (optional)")
    selected_truck_names = st.multiselect(
        "Trucks", list(truck_map.keys()), label_visibility="collapsed", key="nb_trucks"
    )

    # Split selected handlers into internal/blitz/other-sub
    selected_handlers = [handler_map[n] for n in selected_handler_names]
    blitz_handlers    = [h for h in selected_handlers if h.get("company") == db.BLITZ_COMPANY]
    own_handlers      = [h for h in selected_handlers if h.get("company") != db.BLITZ_COMPANY]

    has_blitz = len(blitz_handlers) > 0

    if has_blitz:
        st.info(
            f"⚡ **{len(blitz_handlers)} Blitz handler(s) selected:** "
            + ", ".join(h["name"] for h in blitz_handlers)
        )

    def build_booking_title():
        client = client_map.get(client_name)
        if not client or not project_number or not initials:
            return ""
        names = [h["name"].split()[0] for h in own_handlers]
        blitz_count = len(blitz_handlers)
        team_str = ", ".join(names)
        if blitz_count:
            team_str += f" + {blitz_count} Blitz"
        return f"{initials} - {client_name} - {team_str} - {project_number}"

    def do_create_booking(status: str):
        if not client_name or not project_number or not selected_handler_names or not initials:
            st.error("Please fill in client, project number, initials and select at least one handler.")
            return
        client = client_map[client_name]
        all_handler_ids = [h["id"] for h in selected_handlers]
        truck_ids       = [truck_map[n]["id"] for n in selected_truck_names]
        title           = build_booking_title()
        db.create_project(
            {
                "projectNumber": project_number,
                "title":         title,
                "clientId":      client["id"],
                "description":   description,
                "location":      location,
                "date":          booking_date.isoformat(),
                "status":        status,
                "createdBy":     initials,
            },
            all_handler_ids,
            truck_ids,
        )
        label = "Confirmed" if status == "BOOKED" else "Pre-booked"
        st.success(f"✅ {label}: {title}")
        st.rerun()

    st.markdown("")

    if has_blitz:
        # ── Blitz availability email ──────────────────────────────────────────
        bcol1, bcol2 = st.columns(2)

        with bcol1:
            if st.button("📧 Check Blitz Availability", use_container_width=True, type="secondary"):
                st.session_state["show_blitz_email"] = True

        with bcol2:
            if st.button("✅ Book the Team", use_container_width=True, type="primary"):
                do_create_booking("BOOKED")

        if st.session_state.get("show_blitz_email"):
            blitz_names = [h["name"] for h in blitz_handlers]
            date_fmt    = booking_date.strftime("%A %d %B %Y")
            subject     = f"Availability Check – {client_name} – {date_fmt} – {project_number}"
            body        = "\n".join([
                f"Dear Prabah,",
                "",
                f"I hope you're well. Could you please confirm the availability of the following "
                f"Blitz art handlers for the project below?",
                "",
                "Handlers needed:",
                *[f"  • {n}" for n in blitz_names],
                "",
                f"Project:     {project_number}",
                f"Client:      {client_name}",
                f"Date:        {date_fmt}",
                f"Location:    {location or 'TBC'}",
                f"Description: {description or '—'}",
                "",
                "Please confirm at your earliest convenience.",
                "",
                f"Best regards,",
                f"{initials}",
            ])
            mailto = (
                f"mailto:{db.PRABAH_EMAIL}"
                f"?subject={subject.replace(' ', '%20').replace('–', '%E2%80%93')}"
                f"&body={body.replace(chr(10), '%0A').replace(' ', '%20')}"
            )
            with st.expander("📧 Email to Prabah (Blitz)", expanded=True):
                st.markdown(f"**To:** `{db.PRABAH_EMAIL}`")
                st.markdown(f"**Subject:**")
                st.code(subject, language=None)
                st.markdown("**Body:**")
                st.code(body, language=None)
                st.link_button("Open in Mail app →", mailto)
                if st.button("Close", key="close_blitz_email"):
                    st.session_state["show_blitz_email"] = False
                    st.rerun()

    else:
        # No Blitz — standard pre-book / confirm buttons
        bcol1, bcol2 = st.columns(2)
        with bcol1:
            if st.button("Pre-book", use_container_width=True):
                do_create_booking("PRE_BOOKED")
        with bcol2:
            if st.button("✅ Confirm Booking", use_container_width=True, type="primary"):
                do_create_booking("BOOKED")

    title_preview = build_booking_title()
    if title_preview:
        st.caption(f"Invite title: **{title_preview}**")

# ── Tab 2: Mark Unavailable ───────────────────────────────────────────────────
with tab2:
    with st.form("unavail_form", clear_on_submit=True):
        entity_type = st.radio("Type", ["Art Handler", "Vehicle"], horizontal=True)
        if entity_type == "Art Handler":
            entity_name = st.selectbox("Handler", [h["name"] for h in handlers])
        else:
            entity_name = st.selectbox("Vehicle", [t["name"] for t in trucks])
        unavail_date = st.date_input("Date", value=date.today(), key="unavail_date")
        reason       = st.text_input("Reason", placeholder="Annual leave, Service, Training…")
        ua_col1, ua_col2 = st.columns(2)
        with ua_col1:
            mark   = st.form_submit_button("Mark Unavailable", use_container_width=True, type="primary")
        with ua_col2:
            remove = st.form_submit_button("Remove", use_container_width=True)

    if mark or remove:
        ds = unavail_date.isoformat()
        if entity_type == "Art Handler":
            h = next(h for h in handlers if h["name"] == entity_name)
            if mark:
                db.set_handler_unavailable(h["id"], ds, reason)
                st.success(f"Marked {entity_name} unavailable on {unavail_date.strftime('%d %b %Y')}")
            else:
                db.remove_handler_unavailability(h["id"], ds)
                st.success(f"Removed unavailability for {entity_name}")
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
            status_badge = "🟢 **Confirmed**" if p["status"] == "BOOKED" else "🟠 **Pre-booked**"
            with st.expander(
                f"{p['clientName']} — {p['projectNumber']} — {p['date']}  {status_badge}"
            ):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**Booked by:** {p['createdBy']}")
                    st.markdown(f"**Location:** {p['location'] or '—'}")
                    st.markdown(f"**Description:** {p['description'] or '—'}")

                    own_bookings   = [b for b in p["bookings"] if b.get("company") != db.BLITZ_COMPANY]
                    blitz_bookings = [b for b in p["bookings"] if b.get("company") == db.BLITZ_COMPANY]

                    st.markdown(f"**Team ({len(p['bookings'])} handlers):**")
                    for b in own_bookings:
                        badge = " 🏛" if b["hasBadgeLouvre"] else ""
                        st.markdown(f"- {b['handlerName']}{badge} — `{b['handlerEmail']}`")
                    for b in blitz_bookings:
                        st.markdown(f"- {b['handlerName']} *(Blitz)* — `{b['handlerEmail']}`")

                    if p["truckBookings"]:
                        st.markdown("**Vehicles:**")
                        for b in p["truckBookings"]:
                            st.markdown(f"- 🚚 {b['truckName']} {b['licensePlate'] or ''}")

                with col2:
                    if p["status"] == "PRE_BOOKED":
                        if st.button("✅ Confirm", key=f"confirm_{p['id']}", use_container_width=True):
                            db.confirm_project(p["id"])
                            st.rerun()

                    # ── Outlook invite (own handlers only) ────────────────────
                    own_emails     = "; ".join(b["handlerEmail"] for b in own_bookings)
                    blitz_names    = [b["handlerName"] for b in blitz_bookings]
                    own_names      = [b["handlerName"] for b in own_bookings]
                    first_names    = [n.split()[0] for n in own_names]
                    blitz_count    = len(blitz_bookings)

                    team_str = ", ".join(first_names)
                    if blitz_count:
                        team_str += f" + {blitz_count} Blitz"

                    invite_title = f"{p['createdBy']} - {p['clientName']} - {team_str} - {p['projectNumber']}"
                    body_lines = [
                        invite_title, "",
                        f"Client:   {p['clientName']}",
                        f"Project:  {p['projectNumber']}",
                        f"Date:     {p['date']}",
                        f"Location: {p['location'] or 'TBC'}",
                        "",
                        "Description:",
                        p["description"] or "—",
                        "",
                        "Team:",
                        *[f"  • {b['handlerName']}" for b in own_bookings],
                    ]
                    if blitz_names:
                        body_lines += [f"  • {n} (Blitz)" for n in blitz_names]
                    if p["truckBookings"]:
                        body_lines += ["", "Vehicles:"] + [f"  • {b['truckName']}" for b in p["truckBookings"]]
                    body_lines += ["", "Please bring your signed delivery note."]
                    body = "\n".join(body_lines)

                    with st.popover("📧 Outlook Invite", use_container_width=True):
                        st.caption("Recipients: your handlers only (not Blitz)")
                        st.markdown("**To:**")
                        st.code(own_emails or "—", language=None)
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
                        st.caption("⚠️ Attach the delivery note. Add manager as optional attendee.")

                    if st.button("🗑 Delete", key=f"delete_{p['id']}", use_container_width=True):
                        db.delete_project(p["id"])
                        st.rerun()
