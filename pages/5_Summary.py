import streamlit as st
from datetime import date
import calendar
import db

st.set_page_config(page_title="Monthly Summary", page_icon="🖼️", layout="wide")
db.init_db()

st.markdown("## Monthly Summary")
st.caption("Overview of all projects per month — use this for invoicing.")

# ── Month selector ────────────────────────────────────────────────────────────
_today = date.today()
_months_with_data = db.get_all_booking_months()

# Build full month list: at minimum current month ± 6
_all_months: list = list({
    *_months_with_data,
    *[(
        (_today.year if _today.month + i <= 12 else _today.year + 1),
        ((_today.month + i - 1) % 12 + 1)
    ) for i in range(-3, 4)]
})
_all_months = sorted(set(_all_months))

_month_labels = {
    (y, m): f"{calendar.month_name[m]} {y}" for y, m in _all_months
}
_default_idx = next(
    (i for i, (y, m) in enumerate(_all_months)
     if y == _today.year and m == _today.month), 0
)

_mc1, _mc2, _mc3 = st.columns([1, 3, 6])
with _mc1:
    if st.button("◀ Prev", use_container_width=True):
        st.session_state["sum_month_idx"] = max(
            0, st.session_state.get("sum_month_idx", _default_idx) - 1)
        st.rerun()
with _mc2:
    _sel_idx = st.session_state.get("sum_month_idx", _default_idx)
    _sel_idx = min(_sel_idx, len(_all_months) - 1)
    st.markdown(
        f"<h3 style='margin:0;padding-top:4px;text-align:center'>"
        f"{_month_labels[_all_months[_sel_idx]]}</h3>",
        unsafe_allow_html=True
    )
with _mc3:
    if st.button("Next ▶", use_container_width=True):
        st.session_state["sum_month_idx"] = min(
            len(_all_months) - 1,
            st.session_state.get("sum_month_idx", _default_idx) + 1)
        st.rerun()

_year, _month = _all_months[_sel_idx]

# ── Load projects for month ───────────────────────────────────────────────────
projects = db.get_projects_for_month(_year, _month)

if not projects:
    st.info(f"No bookings recorded for {calendar.month_name[_month]} {_year}.")
    st.stop()

# ── Month totals header ───────────────────────────────────────────────────────
_total_hd       = sum(p["total_handler_days"] for p in projects)
_total_internal = sum(p["internal_days"]      for p in projects)
_total_ext      = sum(p["external_days"]      for p in projects)
_total_blitz    = sum(p["blitz_days"]         for p in projects)
_n_confirmed    = sum(1 for p in projects if p["status"] == "BOOKED")
_n_preBooked    = sum(1 for p in projects if p["status"] != "BOOKED")

st.markdown(
    f"<div style='display:flex;gap:16px;flex-wrap:wrap;margin:8px 0 18px'>"
    f"<div style='background:#eef4ff;border-radius:8px;padding:10px 18px;min-width:120px'>"
    f"<div style='font-size:11px;color:#555'>Projects</div>"
    f"<div style='font-size:22px;font-weight:700;color:#2255aa'>{len(projects)}</div>"
    f"<div style='font-size:10px;color:#777'>✅ {_n_confirmed} confirmed · 🟠 {_n_preBooked} pre-booked</div>"
    f"</div>"
    f"<div style='background:#eef4ff;border-radius:8px;padding:10px 18px;min-width:120px'>"
    f"<div style='font-size:11px;color:#555'>Total handler-days</div>"
    f"<div style='font-size:22px;font-weight:700;color:#2255aa'>{_total_hd}</div>"
    f"<div style='font-size:10px;color:#777'>{_total_internal} internal · {_total_ext} sub</div>"
    f"</div>"
    f"<div style='background:#fff4e6;border-radius:8px;padding:10px 18px;min-width:120px'>"
    f"<div style='font-size:11px;color:#555'>Blitz handler-days</div>"
    f"<div style='font-size:22px;font-weight:700;color:#c05000'>{_total_blitz}</div>"
    f"<div style='font-size:10px;color:#777'>to be invoiced by Blitz</div>"
    f"</div>"
    f"</div>",
    unsafe_allow_html=True,
)

st.divider()

# ── Per-project cards ─────────────────────────────────────────────────────────
for p in projects:
    _status_badge = (
        "<span style='background:#d4edda;color:#155724;border-radius:4px;"
        "padding:2px 8px;font-size:11px;font-weight:600'>✅ CONFIRMED</span>"
        if p["status"] == "BOOKED" else
        "<span style='background:#fff3cd;color:#856404;border-radius:4px;"
        "padding:2px 8px;font-size:11px;font-weight:600'>🟠 PRE-BOOKED</span>"
    )
    _p_color   = p["clientColor"]
    _p_client  = p["clientName"]
    _p_projnum = p["projectNumber"]
    _p_loc     = p.get("location") or ""
    _p_desc    = p.get("description") or ""
    _loc_html  = f"<br><span style='font-size:11px;color:#555'>📍 {_p_loc}</span>" if _p_loc else ""
    _desc_html = f"<br><span style='font-size:11px;color:#666'>{_p_desc}</span>" if _p_desc else ""
    _dot       = (f"<span style='display:inline-block;width:12px;height:12px;"
                  f"border-radius:50%;background:{_p_color};"
                  f"vertical-align:middle;margin-right:6px'></span>")
    st.markdown(
        f"<div style='background:{_p_color}18;border-left:4px solid {_p_color};"
        f"border-radius:0 8px 8px 0;padding:10px 16px;margin-bottom:4px'>"
        f"{_dot}<b style='font-size:15px'>{_p_client}</b>"
        f"&nbsp;&nbsp;<code style='font-size:12px'>{_p_projnum}</code>"
        f"&nbsp;&nbsp;{_status_badge}"
        f"{_loc_html}{_desc_html}"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Date breakdown table
    _rows_html = ""
    for _ds, _bookings in p["days"].items():
        try:
            _d = date.fromisoformat(_ds)
            _d_label = _d.strftime("%a %d %b")
        except Exception:
            _d_label = _ds
        _internal = [b for b in _bookings if b["type"] == "Internal"]
        _iss      = [b for b in _bookings if b["company"] == "ISS"]
        _blitz    = [b for b in _bookings if b["company"] == db.BLITZ_COMPANY]

        def _names(blist):
            return ", ".join(b["handlerName"] for b in blist) if blist else "—"

        _bg = "#f9f9f9" if _ds == list(p["days"].keys())[0] or True else "white"
        _has_blitz = len(_blitz) > 0
        _blitz_tag = (
            f"&nbsp;<span style='background:#ffeaea;color:#c00;border-radius:3px;"
            f"padding:1px 5px;font-size:10px'>⚡{len(_blitz)} Blitz</span>"
            if _has_blitz else ""
        )
        _rows_html += (
            f"<tr style='border-bottom:1px solid #eee'>"
            f"<td style='padding:4px 10px;white-space:nowrap;font-weight:600;color:#333'>{_d_label}</td>"
            f"<td style='padding:4px 10px;text-align:center;font-weight:700;font-size:15px'>{len(_bookings)}</td>"
            f"<td style='padding:4px 10px;font-size:11px;color:#222'>{_names(_internal)}</td>"
            f"<td style='padding:4px 10px;font-size:11px;color:#555'>{_names(_iss)}</td>"
            f"<td style='padding:4px 10px;font-size:11px;color:#c00'>{_names(_blitz)}{_blitz_tag}</td>"
            f"</tr>"
        )

    # Truck rows
    _truck_by_date: dict = {}
    for tb in p["truck_days"]:
        _truck_by_date.setdefault(tb["date"], []).append(tb["truckName"])
    _truck_summary = "; ".join(
        f"{date.fromisoformat(d).strftime('%d %b')}: {', '.join(ts)}"
        for d, ts in sorted(_truck_by_date.items())
    ) if _truck_by_date else "None"

    st.markdown(
        f"<div style='margin:0 0 4px 4px'>"
        f"<table style='width:100%;border-collapse:collapse;font-size:12px'>"
        f"<thead><tr style='background:#f0f0f0;font-size:11px;color:#555'>"
        f"<th style='padding:4px 10px;text-align:left'>Date</th>"
        f"<th style='padding:4px 10px;text-align:center'>Count</th>"
        f"<th style='padding:4px 10px;text-align:left'>Internal</th>"
        f"<th style='padding:4px 10px;text-align:left'>ISS</th>"
        f"<th style='padding:4px 10px;text-align:left'>Blitz ⚡</th>"
        f"</tr></thead>"
        f"<tbody>{_rows_html}</tbody>"
        f"</table>"
        f"<div style='display:flex;gap:16px;padding:6px 10px;background:#fafafa;"
        f"border-top:2px solid #ddd;font-size:11px'>"
        f"<span><b>Total handler-days:</b> {p['total_handler_days']}</span>"
        f"<span style='color:#2255aa'><b>Internal:</b> {p['internal_days']}</span>"
        f"<span style='color:#555'><b>ISS:</b> {p['external_days'] - p['blitz_days']}</span>"
        f"<span style='color:#c00'><b>Blitz:</b> {p['blitz_days']}</span>"
        f"<span style='color:#555;margin-left:auto'>🚚 Vehicles: {_truck_summary}</span>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Confirm button for pre-booked projects
    _pc1, _pc2 = st.columns([1, 9])
    with _pc1:
        if p["status"] == "PRE_BOOKED":
            if st.button("✅ Confirm", key=f"sum_confirm_{p['id']}", use_container_width=True):
                db.confirm_project(p["id"])
                st.rerun()
        else:
            if st.button("🗑 Delete", key=f"sum_del_{p['id']}", use_container_width=True,
                         type="secondary", help="Delete this project permanently"):
                if st.session_state.get(f"del_confirm_{p['id']}"):
                    db.delete_project(p["id"])
                    st.rerun()
                else:
                    st.session_state[f"del_confirm_{p['id']}"] = True
                    st.warning("Click Delete again to confirm.")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

st.divider()

# ── CSV export ────────────────────────────────────────────────────────────────
import csv, io

def _build_csv():
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Project Number", "Client", "Status", "Date",
                "Handler Count", "Internal", "ISS", "Blitz",
                "Handler Names", "Location", "Description"])
    for p in projects:
        for _ds, _bookings in p["days"].items():
            _internal = [b for b in _bookings if b["type"] == "Internal"]
            _iss      = [b for b in _bookings if b["company"] == "ISS"]
            _blitz    = [b for b in _bookings if b["company"] == db.BLITZ_COMPANY]
            w.writerow([
                p["projectNumber"], p["clientName"], p["status"], _ds,
                len(_bookings), len(_internal), len(_iss), len(_blitz),
                "; ".join(b["handlerName"] for b in _bookings),
                p.get("location", ""), p.get("description", ""),
            ])
    return buf.getvalue().encode()

_month_str = f"{calendar.month_name[_month]}_{_year}"
st.download_button(
    label=f"⬇ Export {_month_str} to CSV",
    data=_build_csv(),
    file_name=f"hasenkamp_summary_{_month_str}.csv",
    mime="text/csv",
)
