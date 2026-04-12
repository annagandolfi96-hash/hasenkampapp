import streamlit as st
import streamlit.components.v1 as components
from datetime import date, timedelta
from itertools import groupby
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
.legend { display:flex; gap:12px; flex-wrap:wrap; align-items:center;
          font-size:11px; color:#555; margin-bottom:6px; }
.ldot { width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:3px; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "start_date" not in st.session_state:
    # Start from the 1st of the current month
    st.session_state.start_date = date.today().replace(day=1)

# Show 3 full months from the start date
import calendar as _cal
def _months_of_days(start: date, n_months: int) -> int:
    """Total days spanning n_months calendar months from start."""
    d = start
    total = 0
    for _ in range(n_months):
        days_in_month = _cal.monthrange(d.year, d.month)[1]
        total += days_in_month
        # advance to next month
        if d.month == 12:
            d = d.replace(year=d.year + 1, month=1, day=1)
        else:
            d = d.replace(month=d.month + 1, day=1)
    return total

DAYS = _months_of_days(st.session_state.start_date, 3)


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def hex_to_opaque_tint(hex_color: str, alpha: float = 0.15) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r2 = int(255 * (1 - alpha) + r * alpha)
    g2 = int(255 * (1 - alpha) + g * alpha)
    b2 = int(255 * (1 - alpha) + b * alpha)
    return f"rgb({r2},{g2},{b2})"


def hex_to_circle_emoji(hex_color: str) -> str:
    """Map a hex colour to the nearest coloured-circle emoji."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    mx, mn = max(r, g, b), min(r, g, b)
    if mx - mn < 40:
        return "⚫" if mx < 100 else ("⚪" if mx > 200 else "⚫")
    if r >= g and r >= b:
        return "🟠" if g > 120 else "🔴"
    if g >= r and g >= b:
        return "🟢"
    if b >= r and b >= g:
        return "🔵"
    if r >= b and g >= b:
        return "🟡"
    return "🟣"


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## Art Handler Schedule")

# Month jump — pick any month to start the 3-month scrollable view
_hcol1, _hcol2 = st.columns([2, 8])
with _hcol1:
    _jump = st.date_input(
        "Start month",
        value=st.session_state.start_date,
        key="month_jump",
        label_visibility="collapsed",
        help="Pick a date to jump to that month",
    )
    _jump_first = _jump.replace(day=1)
    if _jump_first != st.session_state.start_date:
        st.session_state.start_date = _jump_first
        st.rerun()

dates = [st.session_state.start_date + timedelta(days=i) for i in range(DAYS)]
with _hcol2:
    st.markdown(
        f"<div style='padding-top:6px;color:#555;font-size:13px'>"
        f"Showing {dates[0].strftime('%B %Y')} → {dates[-1].strftime('%B %Y')}"
        f" &nbsp;·&nbsp; scroll the grid horizontally to move between months</div>",
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
clients      = db.get_clients()
client_map   = {c["name"]: c for c in clients}
handler_map  = {h["id"]: h for h in handlers}

# Pre-compute expiry sets for calendar flags
_louvre_expiry = {r["id"]: r["louvre_badge_expiry"]
                  for r in db.get_handlers_with_expiring_louvre(60)}
_service_due   = {r["id"]: r["service_due"]
                  for r in db.get_trucks_with_upcoming_service(60)}
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

# Selected cells from query params — format: "h1:2026-04-15,h3:2026-04-16"
_sel_cells: set = set(st.query_params.get("sel", "").split(",")) - {""}


# ── Grid ─────────────────────────────────────────────────────────────────────
def _handler_rows(h_list, rows):
    for h in h_list:
        name_bg = hex_to_opaque_tint(h["color"], 0.18)
        icons = ""
        if h.get("canDriveTruck"):    icons += "🚛"
        if h.get("canDriveForklift"): icons += "🏗"
        if h.get("hasBadgeLouvre"):   icons += "🏛L"
        company = h.get("company") or ""
        sub_label = company if company else ""
        # Louvre badge expiry flag
        louvre_flag = ""
        if h["id"] in _louvre_expiry:
            try:
                from datetime import date as _d
                exp = _d.fromisoformat(_louvre_expiry[h["id"]])
                louvre_flag = (f"<br><span style='font-size:7px;color:#c00;padding-left:8px'>"
                               f"⚠ Louvre exp. {exp.strftime('%d/%m/%Y')}</span>")
            except Exception:
                pass
        rows.append(
            f"<tr><td class='name-cell' style='background:{name_bg}'>"
            f"<span style='display:inline-block;width:6px;height:6px;border-radius:50%;"
            f"background:{h['color']};margin-right:2px;vertical-align:middle'></span>"
            f"<b style='font-size:12px;color:#111'>{h['name']}</b>"
            f"{(' ' + icons) if icons else ''}<br>"
            f"<span style='font-size:7px;color:#999;padding-left:8px'>"
            f"{h['level']}{(' · ' + sub_label) if sub_label else ''}</span>"
            f"{louvre_flag}"
            f"</td>"
        )
        for d in dates:
            ds = d.isoformat()
            proj    = proj_by_handler.get((ds, h["id"]))
            unavail = unavail_by_handler.get((ds, h["id"]))
            tc = " today-col" if ds == today_str else ""
            if proj:
                bg = hex_to_rgba(proj["clientColor"], 0.4)
                num_cls = "booked-num" if proj["status"] == "BOOKED" else "prebooked-num"
                count = len(proj["bookings"])
                rows.append(f"<td style='background:{bg}' class='{tc}'><span class='{num_cls}'>{count}</span></td>")
            elif unavail:
                reason = (unavail.get("reason") or "")[:4]
                rows.append(f"<td style='background:#111' class='{tc}'><span class='unavail-text'>{reason}</span></td>")
            else:
                cell_key = f"{h['id']}:{ds}"
                tc_cls   = tc  # already has leading space or is ""
                if cell_key in _sel_cells:
                    # Already selected → click deselects
                    new_sel = ",".join(sorted(_sel_cells - {cell_key}))
                    rows.append(f"<td class='selected-cell{tc_cls}'>"
                                f"<a class='cell-link' data-sel='{new_sel}' href='#' title='Deselect'>✓</a></td>")
                else:
                    # Not selected → click selects
                    new_sel = ",".join(sorted(_sel_cells | {cell_key}))
                    h_name  = h["name"]
                    rows.append(f"<td class='clickable{tc_cls}'>"
                                f"<a class='cell-link' data-sel='{new_sel}' href='#' title='Select {h_name}'>+</a></td>")
        rows.append("</tr>")


def build_grid() -> str:
    internal_h = [h for h in handlers if h["type"] == "Internal"]
    iss_h      = [h for h in handlers if h.get("company") == "ISS"]
    blitz_h    = [h for h in handlers if h.get("company") == db.BLITZ_COMPANY]

    # Group dates by month for the top header row
    month_groups = [
        (month, list(ds_group))
        for month, ds_group in groupby(dates, key=lambda d: d.strftime("%B %Y"))
    ]

    rows = ["<div class='grid-wrap'><table class='grid-table'><thead>"]

    # ── Row 1: Month headers ──────────────────────────────────────────────────
    rows.append("<tr>")
    rows.append("<th class='name-col month-col' rowspan='2'>Name</th>")
    for month_name, month_dates in month_groups:
        rows.append(
            f"<th class='month-col' colspan='{len(month_dates)}'>{month_name}</th>"
        )
    rows.append("</tr>")

    # ── Row 2: Day headers ────────────────────────────────────────────────────
    rows.append("<tr>")
    for d in dates:
        ds = d.isoformat()
        tc = " today-col" if ds == today_str else ""
        rows.append(
            f"<th class='{tc}'>{d.strftime('%a')}<br>"
            f"<span style='color:#bbb;font-size:7px'>{d.strftime('%d')}</span></th>"
        )
    rows.append("</tr>")
    rows.append("</thead><tbody>")

    # Art Handlers — internal only
    rows.append(f"<tr><td class='section-header' colspan='{DAYS+1}'>Art Handlers</td></tr>")
    _handler_rows(internal_h, rows)

    # Vehicles
    rows.append(f"<tr><td class='section-header' colspan='{DAYS+1}'>Vehicles</td></tr>")
    for t in trucks:
        spec_str = t.get("spec") or ""
        plate_str = t.get("licensePlate") or ""
        sub_info = " · ".join(filter(None, [spec_str, plate_str]))
        sub_line = f"<br><span style='font-size:7px;color:#999;padding-left:10px'>{sub_info}</span>" if sub_info else ""
        svc_flag = ""
        if t["id"] in _service_due:
            try:
                from datetime import date as _d
                svc = _d.fromisoformat(_service_due[t["id"]])
                svc_flag = (f"<br><span style='font-size:7px;color:#c00;padding-left:10px'>"
                            f"⚠ Service {svc.strftime('%d/%m/%Y')}</span>")
            except Exception:
                pass
        rows.append(
            f"<tr><td class='name-cell' style='background:#f5f5f5'>"
            f"🚚 <b style='font-size:12px;color:#111'>{t['name']}</b>{sub_line}{svc_flag}</td>"
        )
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
                reason = (unavail.get("reason") or "")[:4]
                rows.append(f"<td style='background:#111' class='{tc}'><span class='unavail-text'>{reason}</span></td>")
            else:
                rows.append(f"<td class='{tc}'></td>")
        rows.append("</tr>")

    # ISS subcontractors — at the bottom
    if iss_h:
        rows.append(
            f"<tr><td class='section-header' colspan='{DAYS+1}' "
            f"style='background:#f0f4ff;color:#336'>ISS Subcontractors</td></tr>"
        )
        _handler_rows(iss_h, rows)

    # Blitz subcontractors — at the bottom
    if blitz_h:
        rows.append(
            f"<tr><td class='section-header' colspan='{DAYS+1}' "
            f"style='background:#fff0f0;color:#c00'>⚡ Blitz Subcontractors</td></tr>"
        )
        _handler_rows(blitz_h, rows)

    rows.append("</tbody></table></div>")
    return "".join(rows)


def build_grid_page() -> str:
    """Wrap the grid table in a full HTML page with embedded CSS + JS.
    Rendered via st.components.v1.html so JavaScript actually executes."""
    grid_css = """
body { margin:0; padding:0; overflow:hidden; background:transparent; }
.grid-wrap {
    overflow: auto;
    height: 100vh;
    border: 1px solid #ccc;
    border-radius: 4px;
}
.grid-table { border-collapse: collapse; font-size: 9px; }
.grid-table th {
    position: sticky; top: 0; z-index: 2;
    background: #1a1a2e; color: white;
    padding: 2px 2px; border: 1px solid #333;
    white-space: nowrap; text-align: center;
    font-weight: 600; width: 38px; min-width: 38px; max-width: 38px;
}
.grid-table thead tr:nth-child(2) th { top: 20px; }
.grid-table th.name-col {
    position: sticky; left: 0; top: 0; z-index: 4;
    text-align: left; width: 130px; min-width: 130px; max-width: 130px;
}
.grid-table thead tr:nth-child(2) th.name-col { top: 20px; }
.grid-table th.month-col {
    font-size: 10px; font-weight: 700; letter-spacing: .04em;
    background: #12122a; border-bottom: 1px solid #444;
}
.grid-table td {
    border: 1px solid #e0e0e0; padding: 1px 2px; text-align: center;
    height: 22px; vertical-align: middle;
    width: 38px; min-width: 38px; max-width: 38px;
}
.grid-table td.name-cell {
    position: sticky; left: 0; z-index: 1;
    text-align: left; white-space: nowrap;
    font-weight: 500; overflow: hidden;
    width: 130px; min-width: 130px; max-width: 130px;
    padding: 1px 4px;
}
.grid-table td.section-header {
    position: sticky; left: 0; z-index: 1;
    background: #e8e8e8; font-weight: 700; font-size: 9px;
    color: #555; text-transform: uppercase; letter-spacing: 0.06em;
    text-align: left; padding: 2px 4px;
    width: auto; max-width: unset; min-width: unset;
}
.grid-table tr td.section-header ~ td { background: #f0f0f0; }
.booked-num    { font-weight: 700; font-size: 10px; color: #1a1a1a; }
.prebooked-num { font-weight: 700; font-size: 10px; color: #e07b00; }
.unavail-text  { font-size: 7px; color: #aaa; }
.today-col     { outline: 2px solid #4A90D9; outline-offset: -2px; }
.grid-table td.clickable, .grid-table td.selected-cell { padding: 0; cursor: pointer; }
.grid-table td.clickable a, .grid-table td.selected-cell a {
    display: flex; align-items: center; justify-content: center;
    width: 100%; height: 22px; text-decoration: none; font-size: 11px; font-weight: 600;
}
.grid-table td.clickable a { color: transparent; }
.grid-table td.clickable a:hover { color: #4A90D9; background: rgba(74,144,217,0.13); }
.grid-table td.selected-cell { background: rgba(74,144,217,0.22); }
.grid-table td.selected-cell a { color: #2266cc; }
.grid-table td.selected-cell a:hover { background: rgba(74,144,217,0.32); }
"""
    js = """
document.addEventListener('click', function(e) {
    e.preventDefault();
    var a = e.target.closest('a.cell-link');
    if (!a) return;
    var sel = a.getAttribute('data-sel');
    var search = sel ? ('?sel=' + sel) : '';
    try { window.top.location.search = search; } catch(err) {
        try { window.parent.location.search = search; } catch(e2) {}
    }
});
"""
    return (
        "<!DOCTYPE html><html><head>"
        f"<style>{grid_css}</style>"
        "</head><body>"
        f"{build_grid()}"
        f"<script>{js}</script>"
        "</body></html>"
    )


# Compute a reasonable iframe height based on row count
_n_rows = len(handlers) + len(trucks) + 6   # +6 for section headers
_grid_h = min(max(_n_rows * 24 + 50, 300), 720)
components.html(build_grid_page(), height=_grid_h, scrolling=False)

# ── Multi-cell selection summary bar ─────────────────────────────────────────
if _sel_cells:
    # Parse & validate selected cells
    _parsed_sel: list = []
    for _ck in sorted(_sel_cells):
        parts = _ck.split(":")
        if len(parts) == 2 and parts[0] in handler_map:
            _parsed_sel.append((handler_map[parts[0]], parts[1]))

    if _parsed_sel:
        # Compact summary shown below the grid
        _names_str = ", ".join(
            f"**{h['name']}** ({ds})" for h, ds in _parsed_sel
        )
        st.markdown(
            f"<div style='background:#eef4ff;border:2px solid #4A90D9;"
            f"border-radius:8px;padding:10px 16px;margin:6px 0'>"
            f"<b style='font-size:13px;color:#2255aa'>"
            f"🗂 {len(_parsed_sel)} cell{'s' if len(_parsed_sel)>1 else ''} selected</b>"
            f"<br><span style='font-size:11px;color:#444'>{_names_str}</span></div>",
            unsafe_allow_html=True,
        )

        _sb1, _sb2, _sb3 = st.columns([2, 2, 6])
        with _sb1:
            _do_next = st.button("Next →", type="primary", use_container_width=True,
                                 key="qb_next")
        with _sb2:
            _do_clear = st.button("✕ Clear selection", use_container_width=True,
                                  key="qb_clear")
        if _do_clear:
            st.query_params.clear()
            st.session_state.pop("qb_show_form", None)
            st.rerun()
        if _do_next:
            st.session_state["qb_show_form"] = True
            st.rerun()

        # ── Booking form (expands when Next is clicked) ───────────────────
        if st.session_state.get("qb_show_form"):
            st.markdown("---")
            st.markdown("#### Confirm Booking")

            # Check current availability for each selected cell
            _blocked_cells = []
            for _h, _ds in _parsed_sel:
                _u, _b = db.get_unavailable_handler_ids(_ds)
                if _h["id"] in (_u | _b):
                    _blocked_cells.append((_h, _ds))
            _free_cells = [(_h, _ds) for _h, _ds in _parsed_sel
                           if (_h, _ds) not in _blocked_cells]

            if _blocked_cells:
                st.warning(
                    "The following slots are no longer available and will be skipped: "
                    + ", ".join(f"{h['name']} ({ds})" for h, ds in _blocked_cells)
                )
            if not _free_cells:
                st.error("All selected slots are now unavailable.")
                if st.button("← Back", key="qb_back_all_blocked"):
                    st.session_state.pop("qb_show_form", None)
                    st.rerun()
            else:
                # Group by handler → show each handler's dates as a compact range summary
                from collections import defaultdict as _dd
                _by_handler: dict = _dd(list)
                for _fh, _fds in _free_cells:
                    _by_handler[_fh["id"]].append(_fds)
                _summary_parts = []
                for _hid, _dlist in sorted(_by_handler.items(),
                                           key=lambda x: handler_map[x[0]]["name"]):
                    _hname  = handler_map[_hid]["name"]
                    _sorted = sorted(_dlist)
                    # Collapse consecutive dates into ranges
                    _ranges, _rstart, _rprev = [], _sorted[0], _sorted[0]
                    for _dd_s in _sorted[1:]:
                        _prev_d = date.fromisoformat(_rprev)
                        _cur_d  = date.fromisoformat(_dd_s)
                        if (_cur_d - _prev_d).days == 1:
                            _rprev = _dd_s
                        else:
                            _ranges.append((_rstart, _rprev))
                            _rstart = _rprev = _dd_s
                    _ranges.append((_rstart, _rprev))
                    _range_strs = [
                        _r[0][5:] if _r[0] == _r[1] else f"{_r[0][5:]} → {_r[1][5:]}"
                        for _r in _ranges
                    ]
                    _summary_parts.append(f"**{_hname}**: {', '.join(_range_strs)}")

                st.markdown(
                    "<div style='background:#f6f8ff;border:1px solid #c0d0f0;"
                    "border-radius:6px;padding:8px 12px;margin-bottom:8px'>"
                    "<b style='color:#2255aa'>Slots to book:</b><br>"
                    + "<br>".join(
                        f"<span style='font-size:12px'>· {p}</span>"
                        for p in _summary_parts
                    )
                    + "</div>",
                    unsafe_allow_html=True,
                )
                # Earliest date used as project date
                _proj_date = min(ds for _, ds in _free_cells)

                with st.form("multi_book_form"):
                    mf1, mf2, mf3 = st.columns(3)
                    with mf1:
                        _cc = {c["name"]: c["color"] for c in clients}
                        def _mfmt(n): return f"{hex_to_circle_emoji(_cc.get(n,'#888'))} {n}"
                        mf_client  = st.selectbox("Client *",
                                                  [c["name"] for c in clients],
                                                  format_func=_mfmt)
                        mf_projnum = st.text_input("Project Number *",
                                                   placeholder="HAR-2026-XXX")
                    with mf2:
                        mf_initials = st.text_input("Your Initials *", max_chars=5,
                                                    placeholder="AG")
                        mf_location = st.text_input("Location",
                                                    placeholder="Louvre Museum, Paris")
                    with mf3:
                        mf_desc = st.text_area("Description", height=88,
                                               placeholder="Brief description…")

                    mb1, mb2, mb3 = st.columns(3)
                    with mb1:
                        do_prebook = st.form_submit_button("Pre-book",
                                                           use_container_width=True)
                    with mb2:
                        do_confirm = st.form_submit_button("✅ Confirm Booking",
                                                           type="primary",
                                                           use_container_width=True)
                    with mb3:
                        do_cancel  = st.form_submit_button("Cancel",
                                                           use_container_width=True)

                if do_cancel:
                    st.session_state.pop("qb_show_form", None)
                    st.rerun()

                if do_prebook or do_confirm:
                    if not mf_client or not mf_projnum or not mf_initials:
                        st.error("Client, project number and initials are required.")
                    else:
                        _status = "BOOKED" if do_confirm else "PRE_BOOKED"
                        _first_names = [h["name"].split()[0] for h, _ in _free_cells]
                        _team_str = ", ".join(dict.fromkeys(_first_names))  # deduplicated
                        _title = f"{mf_initials} - {mf_client} - {_team_str} - {mf_projnum}"
                        _pairs = [(_h["id"], _ds) for _h, _ds in _free_cells]
                        db.create_project(
                            {"projectNumber": mf_projnum, "title": _title,
                             "clientId": client_map[mf_client]["id"],
                             "description": mf_desc, "location": mf_location,
                             "date": _proj_date, "status": _status,
                             "createdBy": mf_initials},
                            [], [],
                            handler_date_pairs=_pairs,
                        )
                        st.success(
                            f"{'Confirmed' if do_confirm else 'Pre-booked'}: "
                            f"**{_title}** ({len(_free_cells)} slot(s))"
                        )
                        st.query_params.clear()
                        st.session_state.pop("qb_show_form", None)
                        st.rerun()

st.divider()

# ── Action tabs ───────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📋 New Booking", "🚫 Mark Unavailable", "📁 View / Manage Bookings"])

# ── Tab 1: New Booking ────────────────────────────────────────────────────────
with tab1:
    # ── Project metadata ──────────────────────────────────────────────────────
    meta_c1, meta_c2 = st.columns(2)
    with meta_c1:
        _client_color_map = {c["name"]: c["color"] for c in clients}
        def _fmt_client(name):
            return f"{hex_to_circle_emoji(_client_color_map.get(name, '#888'))} {name}"

        _cur_client = st.session_state.get("nb_client") or (clients[0]["name"] if clients else None)
        _dot = ""
        if _cur_client and _cur_client in client_map:
            _col = client_map[_cur_client]["color"]
            _dot = (f"<span style='display:inline-block;width:10px;height:10px;"
                    f"border-radius:50%;background:{_col};vertical-align:middle;"
                    f"margin-right:4px'></span>")
        st.markdown(f"{_dot}**Client \\***", unsafe_allow_html=True)
        client_name = st.selectbox(
            "Client", [c["name"] for c in clients],
            format_func=_fmt_client,
            key="nb_client", label_visibility="collapsed",
        )
        project_number = st.text_input("Project Number *", placeholder="HAR-2026-XXX", key="nb_projnum")
        initials = st.text_input("Your Initials *", max_chars=5, placeholder="AG", key="nb_initials")
    with meta_c2:
        location    = st.text_input("Location", placeholder="Louvre Museum, Paris", key="nb_location")
        description = st.text_area("Description", placeholder="Brief description of the work…",
                                   height=108, key="nb_desc")

    st.markdown("---")

    # ── Booking schedule (multi-date-range lines) ─────────────────────────────
    st.markdown("**Booking Schedule**")
    st.caption("Add one or more date ranges, each with their own team. All ranges form a single project.")

    if "nb_booking_lines" not in st.session_state:
        st.session_state.nb_booking_lines = []

    _lines = st.session_state.nb_booking_lines

    # Show existing lines
    if _lines:
        for _li, _line in enumerate(_lines):
            _h_names = [handler_map[_hid]["name"] for _hid in _line["handler_ids"]
                        if _hid in handler_map]
            _dfrom, _dto = _line["date_from"], _line["date_to"]
            _d_label = _dfrom if _dfrom == _dto else f"{_dfrom} → {_dto}"
            _lc1, _lc2 = st.columns([11, 1])
            with _lc1:
                st.markdown(
                    f"<div style='background:#f0f4ff;border:1px solid #b8ccf0;"
                    f"border-radius:6px;padding:6px 12px;margin-bottom:4px'>"
                    f"<b style='color:#2255aa'>{_d_label}</b> &nbsp;·&nbsp; "
                    f"{len(_line['handler_ids'])} handler(s): "
                    f"<span style='color:#444'>{', '.join(_h_names)}</span></div>",
                    unsafe_allow_html=True,
                )
            with _lc2:
                if st.button("✕", key=f"nb_del_{_li}", help="Remove this line"):
                    st.session_state.nb_booking_lines.pop(_li)
                    st.rerun()
    else:
        st.caption("_No date ranges added yet._")

    # ── Add-line expander ─────────────────────────────────────────────────────
    internal_h = [h for h in handlers if h["type"] == "Internal"]
    iss_h      = [h for h in handlers if h.get("company") == "ISS"]
    blitz_h    = [h for h in handlers if h.get("company") == db.BLITZ_COMPANY]
    all_for_select = internal_h + iss_h + blitz_h

    def _make_label(h):
        icons = ""
        if h.get("hasBadgeLouvre"):   icons += "🏛L"
        if h.get("canDriveTruck"):    icons += "🚛"
        if h.get("canDriveForklift"): icons += "🏗"
        company = h.get("company") or ""
        company_tag = f" · {company}" if company else ""
        icon_tag = (" · " + icons) if icons else ""
        return f"{h['name']}  [{h['level']}{company_tag}{icon_tag}]"

    _all_h_labels   = [_make_label(h) for h in all_for_select]
    _all_h_label_map = {_make_label(h): h["id"] for h in all_for_select}

    with st.expander("➕ Add date range", expanded=(len(_lines) == 0)):
        _ac1, _ac2, _ac3 = st.columns([2, 2, 5])
        with _ac1:
            _add_from = st.date_input("From *", value=date.today(), key="nb_add_from")
        with _ac2:
            _add_to   = st.date_input("To *",   value=date.today(), key="nb_add_to")
        with _ac3:
            st.markdown("**Handlers \\***")
            _add_sel = st.multiselect(
                "Handlers", options=_all_h_labels,
                key="nb_add_handlers", label_visibility="collapsed",
            )
        if st.button("Add to schedule →", key="nb_add_line", type="primary"):
            if _add_to < _add_from:
                st.error("'To' date must be on or after 'From' date.")
            elif not _add_sel:
                st.error("Select at least one handler.")
            else:
                st.session_state.nb_booking_lines.append({
                    "date_from":   _add_from.isoformat(),
                    "date_to":     _add_to.isoformat(),
                    "handler_ids": [_all_h_label_map[_l] for _l in _add_sel
                                    if _l in _all_h_label_map],
                })
                # Reset multiselect for next addition
                st.session_state.pop("nb_add_handlers", None)
                st.rerun()

    # ── Truck selection (whole-project) ───────────────────────────────────────
    st.markdown("**Assign Vehicles** (optional)")
    _truck_ref_date = _lines[0]["date_from"] if _lines else date.today().isoformat()
    t_unavail_ids, t_booked_ids = db.get_unavailable_truck_ids(_truck_ref_date)
    t_blocked_ids = t_unavail_ids | t_booked_ids

    truck_cols = st.columns(min(len(trucks), 4)) if trucks else st.columns(1)
    selected_truck_ids = []
    for _ti, _t in enumerate(trucks):
        with truck_cols[_ti % 4]:
            _t_blocked = _t["id"] in t_blocked_ids
            _t_label   = ("⛔ Unavailable" if _t["id"] in t_unavail_ids
                          else ("⛔ Booked" if _t["id"] in t_booked_ids else ""))
            _t_spec_h  = (f'<br><span style="font-size:10px;color:#777">'
                          f'{_t.get("spec") or ""}</span>') if _t.get("spec") else ""
            _t_label_h = (f'<br><span style="font-size:10px;color:#c00">'
                          f'{_t_label}</span>') if _t_label else ""
            _t_bg = '#f5f5f5' if _t_blocked else 'white'
            _t_nc = '#aaa'    if _t_blocked else '#111'
            st.markdown(
                f"<div style='background:{_t_bg};border:1px solid #e0e0e0;"
                f"border-radius:6px;padding:6px 8px;margin-bottom:2px'>"
                f"<span style='font-size:12px;font-weight:600;color:{_t_nc}'>"
                f"🚚 {_t['name']}</span>{_t_spec_h}{_t_label_h}</div>",
                unsafe_allow_html=True,
            )
            if st.checkbox("Select", key=f"tsel_{_truck_ref_date}_{_t['id']}",
                           disabled=_t_blocked, label_visibility="collapsed"):
                selected_truck_ids.append(_t["id"])

    # ── Blitz info ────────────────────────────────────────────────────────────
    _blitz_hids_in_lines: set = set()
    for _ln in _lines:
        for _hid in _ln["handler_ids"]:
            if _hid in handler_map and handler_map[_hid].get("company") == db.BLITZ_COMPANY:
                _blitz_hids_in_lines.add(_hid)
    _has_blitz = len(_blitz_hids_in_lines) > 0
    if _has_blitz:
        _blitz_names_str = ", ".join(handler_map[_hid]["name"] for _hid in _blitz_hids_in_lines)
        st.info(f"⚡ **{len(_blitz_hids_in_lines)} Blitz handler(s) in schedule:** {_blitz_names_str}")

    # ── Build title preview ───────────────────────────────────────────────────
    def _build_nb_title():
        if not client_name or not project_number or not initials or not _lines:
            return ""
        _all_hids = list(dict.fromkeys(
            _hid for _ln in _lines for _hid in _ln["handler_ids"]
        ))
        _own_names  = [handler_map[_hid]["name"].split()[0] for _hid in _all_hids
                       if _hid in handler_map
                       and handler_map[_hid].get("company") != db.BLITZ_COMPANY]
        _team_str   = ", ".join(_own_names[:4])
        if len(_own_names) > 4:
            _team_str += f" +{len(_own_names) - 4}"
        if _has_blitz:
            _team_str += f" + {len(_blitz_hids_in_lines)} Blitz"
        return f"{initials} - {client_name} - {_team_str} - {project_number}"

    _title_prev = _build_nb_title()
    if _title_prev:
        st.caption(f"Invite title: **{_title_prev}**")

    # ── Submit ────────────────────────────────────────────────────────────────
    def do_create_booking(status: str):
        if not client_name or not project_number or not initials:
            st.error("Please fill in Client, Project Number and Initials.")
            return
        if not _lines:
            st.error("Add at least one date range to the Booking Schedule.")
            return
        # Expand each line into individual (handler_id, date) pairs
        _pairs: list = []
        for _ln in _lines:
            _d_cur = date.fromisoformat(_ln["date_from"])
            _d_end = date.fromisoformat(_ln["date_to"])
            while _d_cur <= _d_end:
                for _hid in _ln["handler_ids"]:
                    _pairs.append((_hid, _d_cur.isoformat()))
                _d_cur += timedelta(days=1)
        _proj_date = min(_ds for _, _ds in _pairs)
        _title = _build_nb_title() or f"{initials} - {client_name} - {project_number}"
        db.create_project(
            {"projectNumber": project_number, "title": _title,
             "clientId":      client_map[client_name]["id"],
             "description":   description, "location": location,
             "date":          _proj_date,  "status":   status,
             "createdBy":     initials},
            [], selected_truck_ids,
            handler_date_pairs=_pairs,
        )
        st.success(f"{'Confirmed' if status == 'BOOKED' else 'Pre-booked'}: **{_title}**"
                   f" ({len(_pairs)} handler-day slot(s))")
        st.session_state.nb_booking_lines = []
        st.rerun()

    st.markdown("")
    if _has_blitz:
        _bcol1, _bcol2, _bcol3 = st.columns(3)
        with _bcol1:
            if st.button("📧 Check Blitz Availability", use_container_width=True, type="secondary"):
                st.session_state["show_blitz_email"] = True
        with _bcol2:
            if st.button("Pre-book Schedule", use_container_width=True):
                do_create_booking("PRE_BOOKED")
        with _bcol3:
            if st.button("✅ Confirm Schedule", use_container_width=True, type="primary"):
                do_create_booking("BOOKED")

        if st.session_state.get("show_blitz_email"):
            _blitz_names = [handler_map[_hid]["name"] for _hid in _blitz_hids_in_lines]
            _date_lines  = []
            for _ln in _lines:
                _d1 = date.fromisoformat(_ln["date_from"]).strftime("%d %B %Y")
                _d2 = date.fromisoformat(_ln["date_to"]).strftime("%d %B %Y")
                _ln_blitz = [handler_map[_hid]["name"] for _hid in _ln["handler_ids"]
                             if _hid in _blitz_hids_in_lines]
                if _ln_blitz:
                    _range_str = _d1 if _d1 == _d2 else f"{_d1} – {_d2}"
                    _date_lines.append(f"  {_range_str}: {', '.join(_ln_blitz)}")
            subject = f"Availability Check – {client_name} – {project_number}"
            body = "\n".join([
                "Dear Prabah,", "",
                "I hope you're well. Could you please confirm the availability of the "
                "following Blitz art handlers for the dates listed below?", "",
                "Project details:",
                f"  Project:     {project_number}",
                f"  Client:      {client_name}",
                f"  Location:    {location or 'TBC'}",
                f"  Description: {description or '—'}", "",
                "Dates and handlers needed:",
                *_date_lines, "",
                "Please confirm at your earliest convenience.", "",
                "Best regards,", initials,
            ])
            mailto = (
                f"mailto:{db.PRABAH_EMAIL}"
                f"?subject={subject.replace(' ', '%20').replace('–', '%E2%80%93')}"
                f"&body={body.replace(chr(10), '%0A').replace(' ', '%20')}"
            )
            with st.expander("📧 Email to Prabah (Blitz)", expanded=True):
                st.markdown(f"**To:** `{db.PRABAH_EMAIL}`")
                st.markdown("**Subject:**")
                st.code(subject, language=None)
                st.markdown("**Body:**")
                st.code(body, language=None)
                st.link_button("Open in Mail app →", mailto)
                if st.button("Close", key="close_blitz_email"):
                    st.session_state["show_blitz_email"] = False
                    st.rerun()
    else:
        _bcol1, _bcol2 = st.columns(2)
        with _bcol1:
            if st.button("Pre-book Schedule", use_container_width=True):
                do_create_booking("PRE_BOOKED")
        with _bcol2:
            if st.button("✅ Confirm Schedule", use_container_width=True, type="primary"):
                do_create_booking("BOOKED")

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
                            spec = f" ({b['spec']})" if b.get("spec") else ""
                            st.markdown(f"- 🚚 {b['truckName']}{spec} {b['licensePlate'] or ''}")

                with col2:
                    if p["status"] == "PRE_BOOKED":
                        if st.button("✅ Confirm", key=f"confirm_{p['id']}", use_container_width=True):
                            db.confirm_project(p["id"])
                            st.rerun()

                    # ── Outlook invite (own handlers only) ────────────────────
                    own_emails  = "; ".join(b["handlerEmail"] for b in own_bookings)
                    blitz_names = [b["handlerName"] for b in blitz_bookings]
                    own_names   = [b["handlerName"] for b in own_bookings]
                    first_names = [n.split()[0] for n in own_names]
                    blitz_count = len(blitz_bookings)

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
                        body_lines += ["", "Vehicles:"] + [
                            f"  • {b['truckName']}{' (' + b['spec'] + ')' if b.get('spec') else ''}"
                            for b in p["truckBookings"]
                        ]
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
