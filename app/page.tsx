"use client";

import { useCallback, useEffect, useState } from "react";
import { addDays, format, startOfDay } from "date-fns";
import { ScheduleData, Project, Unavailability, TruckUnavailability } from "@/lib/types";
import { hexToRgba, isToday } from "@/lib/utils";
import BookingModal from "@/components/BookingModal";
import UnavailabilityModal from "@/components/UnavailabilityModal";
import OutlookInviteModal from "@/components/OutlookInviteModal";

const DAYS = 14;

type CellModal =
  | { kind: "booking"; date: string }
  | { kind: "viewProject"; project: Project }
  | { kind: "unavailHandler"; handlerId: string; handlerName: string; date: string; unavail?: Unavailability }
  | { kind: "unavailTruck"; truckId: string; truckName: string; date: string; unavail?: TruckUnavailability }
  | { kind: "outlook"; project: Project };

export default function SchedulePage() {
  const [startDate, setStartDate] = useState(startOfDay(new Date()));
  const [data, setData] = useState<ScheduleData | null>(null);
  const [modal, setModal] = useState<CellModal | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    setLoading(true);
    const res = await fetch(
      `/api/schedule?from=${startDate.toISOString()}&days=${DAYS}`
    );
    const json = await res.json();
    setData(json);
    setLoading(false);
  }, [startDate]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const dates = Array.from({ length: DAYS }, (_, i) => addDays(startDate, i));

  if (!data && loading) {
    return <div className="flex items-center justify-center h-64 text-gray-400">Loading schedule…</div>;
  }
  if (!data) return null;

  // Build lookup maps
  const projectsByDateAndHandler: Record<string, Project> = {};
  const projectsByDateAndTruck: Record<string, Project> = {};

  for (const p of data.projects) {
    const dateKey = p.date.split("T")[0];
    for (const b of p.bookings) {
      projectsByDateAndHandler[`${dateKey}_${b.handlerId}`] = p;
    }
    for (const b of p.truckBookings) {
      projectsByDateAndTruck[`${dateKey}_${b.truckId}`] = p;
    }
  }

  const unavailByDateAndHandler: Record<string, Unavailability> = {};
  for (const u of data.unavailabilities) {
    const dateKey = u.date.split("T")[0];
    unavailByDateAndHandler[`${dateKey}_${u.handlerId}`] = u;
  }

  const unavailByDateAndTruck: Record<string, TruckUnavailability> = {};
  for (const u of data.truckUnavailabilities) {
    const dateKey = u.date.split("T")[0];
    unavailByDateAndTruck[`${dateKey}_${u.truckId}`] = u;
  }

  function handleHandlerCellClick(handlerId: string, handlerName: string, dateKey: string) {
    const project = projectsByDateAndHandler[`${dateKey}_${handlerId}`];
    if (project) {
      setModal({ kind: "viewProject", project });
      return;
    }
    const unavail = unavailByDateAndHandler[`${dateKey}_${handlerId}`];
    setModal({ kind: "unavailHandler", handlerId, handlerName, date: dateKey, unavail });
  }

  function handleTruckCellClick(truckId: string, truckName: string, dateKey: string) {
    const project = projectsByDateAndTruck[`${dateKey}_${truckId}`];
    if (project) {
      setModal({ kind: "viewProject", project });
      return;
    }
    const unavail = unavailByDateAndTruck[`${dateKey}_${truckId}`];
    setModal({ kind: "unavailTruck", truckId, truckName, date: dateKey, unavail });
  }

  function handleDateHeaderClick(dateKey: string) {
    setModal({ kind: "booking", date: dateKey });
  }

  return (
    <div className="flex flex-col h-[calc(100vh-52px)]">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 bg-white border-b shadow-sm flex-shrink-0 flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setStartDate((d) => addDays(d, -DAYS))}
            className="px-3 py-1 rounded border text-sm hover:bg-gray-100"
          >
            ← Prev
          </button>
          <button
            onClick={() => setStartDate(startOfDay(new Date()))}
            className="px-3 py-1 rounded border text-sm hover:bg-gray-100"
          >
            Today
          </button>
          <button
            onClick={() => setStartDate((d) => addDays(d, DAYS))}
            className="px-3 py-1 rounded border text-sm hover:bg-gray-100"
          >
            Next →
          </button>
          <span className="text-sm text-gray-500 ml-2">
            {format(dates[0], "d MMM")} – {format(dates[dates.length - 1], "d MMM yyyy")}
          </span>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-3 text-[11px] text-gray-500 flex-wrap">
          <LegendItem color="#4A90D9" label="Senior Internal" />
          <LegendItem color="#27AE60" label="Mid Internal" />
          <LegendItem color="#F39C12" label="Junior Internal" />
          <LegendItem color="#9B59B6" label="Senior Sub" />
          <LegendItem color="#E74C3C" label="Mid Sub" />
          <LegendItem color="#95A5A6" label="Junior Sub" />
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-sm bg-gray-900 inline-block" />
            Unavailable
          </span>
          <span className="flex items-center gap-1 text-orange-600 font-bold">8</span>
          <span className="text-[11px]">= pre-booked</span>
          <span className="flex items-center gap-1 text-gray-900 font-bold">8</span>
          <span className="text-[11px]">= booked</span>
        </div>
      </div>

      {/* Grid */}
      <div className="flex-1 overflow-auto relative">
        {loading && (
          <div className="absolute inset-0 bg-white/60 flex items-center justify-center z-10 text-gray-400 text-sm">
            Refreshing…
          </div>
        )}
        <table className="border-collapse text-xs min-w-full">
          <thead className="sticky top-0 z-20 bg-gray-900 text-white">
            <tr>
              <th className="sticky left-0 z-30 bg-gray-900 w-44 min-w-44 px-3 py-2 text-left font-semibold border-r border-gray-700">
                Name
              </th>
              {dates.map((d) => {
                const dateKey = format(d, "yyyy-MM-dd");
                const today = isToday(d);
                return (
                  <th
                    key={dateKey}
                    onClick={() => handleDateHeaderClick(dateKey)}
                    className={`w-28 min-w-28 px-2 py-1.5 text-center font-medium border-r border-gray-700 cursor-pointer hover:bg-gray-700 transition-colors ${today ? "bg-blue-800" : ""}`}
                    title="Click to create a booking for this date"
                  >
                    <div className={today ? "font-bold" : ""}>{format(d, "EEE")}</div>
                    <div className="text-gray-300 text-[11px]">{format(d, "d MMM")}</div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {/* Art Handlers */}
            <tr className="bg-gray-100">
              <td
                colSpan={DAYS + 1}
                className="sticky left-0 px-3 py-1 text-[11px] font-bold text-gray-500 uppercase tracking-wider border-b border-gray-300"
              >
                Art Handlers
              </td>
            </tr>
            {data.handlers.map((handler) => (
              <tr key={handler.id} className="border-b border-gray-200 hover:bg-gray-50/80">
                {/* Handler name cell */}
                <td
                  className="sticky left-0 z-10 px-2 py-1.5 border-r border-gray-200 whitespace-nowrap"
                  style={{ backgroundColor: hexToRgba(handler.color, 0.18) }}
                >
                  <div className="flex items-center gap-1.5">
                    <span
                      className="w-2 h-2 rounded-full flex-shrink-0"
                      style={{ backgroundColor: handler.color }}
                    />
                    <span className="font-medium truncate max-w-28" title={handler.name}>{handler.name}</span>
                    <div className="flex gap-0.5 ml-auto text-[10px]">
                      {handler.canDriveTruck && <span title="Drives truck">🚛</span>}
                      {handler.canDriveForklift && <span title="Forklift">🏗</span>}
                      {handler.hasBadgeLouvre && <span title="Louvre badge">🏛</span>}
                    </div>
                  </div>
                  <div className="text-gray-400 text-[10px] pl-3.5">
                    {handler.level} · {handler.type === "Subcontractor" ? "Sub" : "Int"}
                  </div>
                </td>
                {/* Day cells */}
                {dates.map((d) => {
                  const dateKey = format(d, "yyyy-MM-dd");
                  const project = projectsByDateAndHandler[`${dateKey}_${handler.id}`];
                  const unavail = unavailByDateAndHandler[`${dateKey}_${handler.id}`];
                  const today = isToday(d);

                  return (
                    <td
                      key={dateKey}
                      className={`border-r border-b border-gray-200 text-center cursor-pointer transition-colors h-9 ${today ? "ring-1 ring-inset ring-blue-300" : ""}`}
                      style={
                        project
                          ? { backgroundColor: hexToRgba(project.client.color, 0.4) }
                          : unavail
                          ? { backgroundColor: "#111" }
                          : undefined
                      }
                      onClick={() => handleHandlerCellClick(handler.id, handler.name, dateKey)}
                      title={
                        project
                          ? `${project.client.name} — ${project.projectNumber} (${project.status})`
                          : unavail
                          ? `Unavailable: ${unavail.reason || "No reason given"}`
                          : "Click to mark unavailable or book"
                      }
                    >
                      {project && (
                        <span
                          className={`font-bold text-sm ${
                            project.status === "BOOKED" ? "text-gray-900" : "text-orange-600"
                          }`}
                        >
                          {project.bookings.length}
                        </span>
                      )}
                      {unavail && (
                        <span className="text-gray-500 text-[9px] px-0.5 leading-tight block">
                          {unavail.reason ? unavail.reason.slice(0, 6) : "N/A"}
                        </span>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}

            {/* Trucks section */}
            <tr className="bg-gray-100">
              <td
                colSpan={DAYS + 1}
                className="sticky left-0 px-3 py-1 text-[11px] font-bold text-gray-500 uppercase tracking-wider border-b border-gray-300"
              >
                Vehicles
              </td>
            </tr>
            {data.trucks.map((truck) => (
              <tr key={truck.id} className="border-b border-gray-200 hover:bg-gray-50/80">
                <td className="sticky left-0 z-10 px-2 py-1.5 border-r border-gray-200 bg-white whitespace-nowrap">
                  <div className="flex items-center gap-1.5">
                    <span className="text-sm">🚚</span>
                    <span className="font-medium">{truck.name}</span>
                  </div>
                  {truck.licensePlate && (
                    <div className="text-gray-400 text-[10px] pl-5">{truck.licensePlate}</div>
                  )}
                </td>
                {dates.map((d) => {
                  const dateKey = format(d, "yyyy-MM-dd");
                  const project = projectsByDateAndTruck[`${dateKey}_${truck.id}`];
                  const unavail = unavailByDateAndTruck[`${dateKey}_${truck.id}`];
                  const today = isToday(d);

                  return (
                    <td
                      key={dateKey}
                      className={`border-r border-b border-gray-200 text-center cursor-pointer transition-colors h-9 ${today ? "ring-1 ring-inset ring-blue-300" : ""}`}
                      style={
                        project
                          ? { backgroundColor: hexToRgba(project.client.color, 0.4) }
                          : unavail
                          ? { backgroundColor: "#111" }
                          : undefined
                      }
                      onClick={() => handleTruckCellClick(truck.id, truck.name, dateKey)}
                      title={
                        project
                          ? `${project.client.name} — ${project.projectNumber}`
                          : unavail
                          ? `Unavailable: ${unavail.reason || "No reason"}`
                          : "Click to mark unavailable"
                      }
                    >
                      {project && (
                        <span className={`font-bold text-sm ${project.status === "BOOKED" ? "text-gray-900" : "text-orange-600"}`}>
                          ✓
                        </span>
                      )}
                      {unavail && (
                        <span className="text-gray-500 text-[9px] px-0.5 leading-tight block">
                          {unavail.reason ? unavail.reason.slice(0, 6) : "N/A"}
                        </span>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modals */}
      {modal?.kind === "booking" && (
        <BookingModal
          scheduleData={data}
          selectedDate={modal.date}
          selectedProject={null}
          onClose={() => setModal(null)}
          onSaved={() => { setModal(null); fetchData(); }}
        />
      )}

      {modal?.kind === "viewProject" && (
        <ProjectDetailPanel
          project={modal.project}
          onClose={() => setModal(null)}
          onConfirm={async () => {
            await fetch(`/api/projects/${modal.project.id}`, {
              method: "PATCH",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ status: "BOOKED" }),
            });
            setModal(null);
            fetchData();
          }}
          onDelete={async () => {
            if (!confirm("Delete this booking?")) return;
            await fetch(`/api/projects/${modal.project.id}`, { method: "DELETE" });
            setModal(null);
            fetchData();
          }}
          onOutlook={() => setModal({ kind: "outlook", project: modal.project })}
        />
      )}

      {modal?.kind === "unavailHandler" && (
        <UnavailabilityModal
          entityId={modal.handlerId}
          entityName={modal.handlerName}
          entityType="handler"
          date={modal.date}
          existingId={modal.unavail?.id}
          existingReason={modal.unavail?.reason || undefined}
          onClose={() => setModal(null)}
          onSaved={() => { setModal(null); fetchData(); }}
        />
      )}

      {modal?.kind === "unavailTruck" && (
        <UnavailabilityModal
          entityId={modal.truckId}
          entityName={modal.truckName}
          entityType="truck"
          date={modal.date}
          existingId={modal.unavail?.id}
          existingReason={modal.unavail?.reason || undefined}
          onClose={() => setModal(null)}
          onSaved={() => { setModal(null); fetchData(); }}
        />
      )}

      {modal?.kind === "outlook" && (
        <OutlookInviteModal
          project={modal.project}
          onClose={() => setModal(null)}
        />
      )}
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-1">
      <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ backgroundColor: color }} />
      {label}
    </span>
  );
}

function ProjectDetailPanel({
  project,
  onClose,
  onConfirm,
  onDelete,
  onOutlook,
}: {
  project: Project;
  onClose: () => void;
  onConfirm: () => void;
  onDelete: () => void;
  onOutlook: () => void;
}) {
  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
        <div
          className="px-6 py-4 rounded-t-xl flex items-center justify-between"
          style={{
            backgroundColor: hexToRgba(project.client.color, 0.2),
            borderBottom: `3px solid ${project.client.color}`,
          }}
        >
          <div>
            <h2 className="font-bold text-lg">{project.client.name}</h2>
            <p className="text-sm text-gray-600">{project.projectNumber}</p>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                project.status === "BOOKED"
                  ? "bg-green-100 text-green-800"
                  : "bg-orange-100 text-orange-700"
              }`}
            >
              {project.status === "BOOKED" ? "Booked" : "Pre-booked"}
            </span>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-900 text-2xl leading-none ml-2">
              &times;
            </button>
          </div>
        </div>

        <div className="px-6 py-4 space-y-3 text-sm">
          <div>
            <p className="text-xs font-semibold text-gray-500 mb-0.5">Date</p>
            <p>
              {new Date(project.date).toLocaleDateString("en-GB", {
                weekday: "long",
                day: "numeric",
                month: "long",
                year: "numeric",
              })}
            </p>
          </div>
          {project.location && (
            <div>
              <p className="text-xs font-semibold text-gray-500 mb-0.5">Location</p>
              <p>{project.location}</p>
            </div>
          )}
          {project.description && (
            <div>
              <p className="text-xs font-semibold text-gray-500 mb-0.5">Description</p>
              <p className="text-gray-700">{project.description}</p>
            </div>
          )}
          <div>
            <p className="text-xs font-semibold text-gray-500 mb-1">
              Team ({project.bookings.length} handlers)
            </p>
            <ul className="space-y-0.5">
              {project.bookings.map((b) => (
                <li key={b.id} className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: b.handler.color }} />
                  <span>{b.handler.name}</span>
                  <span className="text-gray-400 text-xs">({b.handler.level})</span>
                  {b.handler.hasBadgeLouvre && <span title="Louvre badge" className="text-xs">🏛</span>}
                </li>
              ))}
            </ul>
          </div>
          {project.truckBookings.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-500 mb-1">Vehicles</p>
              <ul className="space-y-0.5">
                {project.truckBookings.map((b) => (
                  <li key={b.id}>
                    🚚 {b.truck.name}
                    {b.truck.licensePlate ? ` (${b.truck.licensePlate})` : ""}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <div className="text-xs text-gray-400">Booked by: {project.createdBy}</div>
        </div>

        <div className="px-6 py-4 border-t flex items-center gap-2 flex-wrap">
          <button
            onClick={onDelete}
            className="px-3 py-2 text-sm rounded-lg text-red-600 hover:bg-red-50 border border-red-200"
          >
            Delete
          </button>
          <button
            onClick={onOutlook}
            className="px-3 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700"
          >
            Outlook Invite
          </button>
          {project.status === "PRE_BOOKED" && (
            <button
              onClick={onConfirm}
              className="ml-auto px-4 py-2 text-sm rounded-lg bg-green-600 text-white hover:bg-green-700 font-semibold"
            >
              Confirm Booking →
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
