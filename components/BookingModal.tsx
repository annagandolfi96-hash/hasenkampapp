"use client";

import { useState } from "react";
import { ArtHandler, Client, Project, ScheduleData, Truck } from "@/lib/types";

type Props = {
  scheduleData: ScheduleData;
  selectedDate: string | null;
  selectedProject: Project | null;
  onClose: () => void;
  onSaved: () => void;
};

export default function BookingModal({ scheduleData, selectedDate, selectedProject, onClose, onSaved }: Props) {
  const isEdit = !!selectedProject;

  const [clientId, setClientId] = useState(selectedProject?.clientId || "");
  const [projectNumber, setProjectNumber] = useState(selectedProject?.projectNumber || "");
  const [description, setDescription] = useState(selectedProject?.description || "");
  const [location, setLocation] = useState(selectedProject?.location || "");
  const [createdBy, setCreatedBy] = useState(selectedProject?.createdBy || "");
  const [date, setDate] = useState(
    selectedProject?.date
      ? selectedProject.date.split("T")[0]
      : selectedDate || new Date().toISOString().split("T")[0]
  );
  const [selectedHandlerIds, setSelectedHandlerIds] = useState<string[]>(
    selectedProject?.bookings.map((b) => b.handlerId) || []
  );
  const [selectedTruckIds, setSelectedTruckIds] = useState<string[]>(
    selectedProject?.truckBookings.map((b) => b.truckId) || []
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const client = scheduleData.clients.find((c) => c.id === clientId);
  const title = client
    ? `${createdBy} - ${client.name} - ${selectedHandlerIds.length} handlers - ${projectNumber}`
    : "";

  function toggleHandler(id: string) {
    setSelectedHandlerIds((prev) =>
      prev.includes(id) ? prev.filter((h) => h !== id) : [...prev, id]
    );
  }

  function toggleTruck(id: string) {
    setSelectedTruckIds((prev) =>
      prev.includes(id) ? prev.filter((t) => t !== id) : [...prev, id]
    );
  }

  async function handleSave(status: "PRE_BOOKED" | "BOOKED") {
    if (!clientId || !projectNumber || !date || selectedHandlerIds.length === 0) {
      setError("Please fill in client, project number, date and select at least one handler.");
      return;
    }
    setSaving(true);
    setError("");

    try {
      if (isEdit) {
        await fetch(`/api/projects/${selectedProject!.id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status }),
        });
      } else {
        await fetch("/api/projects", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            clientId,
            projectNumber,
            title,
            description,
            location,
            createdBy,
            date,
            status,
            handlerIds: selectedHandlerIds,
            truckIds: selectedTruckIds,
          }),
        });
      }
      onSaved();
    } catch {
      setError("Failed to save. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  const levelOrder = ["Senior", "Mid", "Junior"];
  const groupedHandlers = scheduleData.handlers.reduce<Record<string, ArtHandler[]>>((acc, h) => {
    const key = `${h.type} - ${h.level}`;
    if (!acc[key]) acc[key] = [];
    acc[key].push(h);
    return acc;
  }, {});

  const sortedGroups = Object.entries(groupedHandlers).sort(([a], [b]) => {
    const [aType, aLevel] = a.split(" - ");
    const [bType, bLevel] = b.split(" - ");
    if (aType !== bType) return aType === "Internal" ? -1 : 1;
    return levelOrder.indexOf(aLevel) - levelOrder.indexOf(bLevel);
  });

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-bold">
            {isEdit ? `Edit Booking — ${selectedProject!.projectNumber}` : "New Booking"}
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-900 text-2xl leading-none">&times;</button>
        </div>

        <div className="overflow-y-auto flex-1 px-6 py-4 space-y-5">
          {error && <p className="text-red-600 text-sm bg-red-50 rounded p-2">{error}</p>}

          {!isEdit && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">Client *</label>
                  <select
                    className="w-full border rounded-lg px-3 py-2 text-sm"
                    value={clientId}
                    onChange={(e) => setClientId(e.target.value)}
                  >
                    <option value="">Select client…</option>
                    {scheduleData.clients.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">Project Number *</label>
                  <input
                    className="w-full border rounded-lg px-3 py-2 text-sm"
                    value={projectNumber}
                    onChange={(e) => setProjectNumber(e.target.value)}
                    placeholder="HAR-2026-XXX"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">Date *</label>
                  <input
                    type="date"
                    className="w-full border rounded-lg px-3 py-2 text-sm"
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">Your Initials *</label>
                  <input
                    className="w-full border rounded-lg px-3 py-2 text-sm"
                    value={createdBy}
                    onChange={(e) => setCreatedBy(e.target.value)}
                    placeholder="AG"
                    maxLength={5}
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Location</label>
                <input
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="Louvre Museum, Paris - Denon Wing"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Project Description</label>
                <textarea
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Brief description of what needs to be done…"
                />
              </div>

              {title && (
                <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-600">
                  <span className="font-semibold">Invite title preview: </span>
                  <span className="font-mono">{title}</span>
                </div>
              )}
            </>
          )}

          {isEdit && (
            <div className="bg-gray-50 rounded-lg p-3 text-sm space-y-1">
              <p><span className="font-semibold">Status:</span>{" "}
                <span className={selectedProject!.status === "BOOKED" ? "text-green-700 font-bold" : "text-orange-600 font-bold"}>
                  {selectedProject!.status === "BOOKED" ? "Booked" : "Pre-booked"}
                </span>
              </p>
              <p><span className="font-semibold">Client:</span> {selectedProject!.client.name}</p>
              <p><span className="font-semibold">Location:</span> {selectedProject!.location || "—"}</p>
              <p><span className="font-semibold">Description:</span> {selectedProject!.description || "—"}</p>
              <p className="font-semibold mt-2">Team:</p>
              <ul className="list-disc list-inside text-xs text-gray-700">
                {selectedProject!.bookings.map((b) => (
                  <li key={b.id}>{b.handler.name} ({b.handler.level} {b.handler.type})</li>
                ))}
              </ul>
              {selectedProject!.truckBookings.length > 0 && (
                <>
                  <p className="font-semibold mt-2">Vehicles:</p>
                  <ul className="list-disc list-inside text-xs text-gray-700">
                    {selectedProject!.truckBookings.map((b) => (
                      <li key={b.id}>{b.truck.name} {b.truck.licensePlate ? `(${b.truck.licensePlate})` : ""}</li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          )}

          {!isEdit && (
            <>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-2">
                  Select Art Handlers * ({selectedHandlerIds.length} selected)
                </label>
                <div className="space-y-3 max-h-64 overflow-y-auto border rounded-lg p-3">
                  {sortedGroups.map(([group, handlers]) => (
                    <div key={group}>
                      <p className="text-xs font-bold text-gray-500 uppercase mb-1">{group}</p>
                      <div className="grid grid-cols-2 gap-1">
                        {handlers.map((h) => (
                          <label
                            key={h.id}
                            className={`flex items-center gap-2 p-2 rounded cursor-pointer text-xs transition-colors ${
                              selectedHandlerIds.includes(h.id)
                                ? "bg-gray-800 text-white"
                                : "bg-gray-100 hover:bg-gray-200"
                            }`}
                          >
                            <input
                              type="checkbox"
                              checked={selectedHandlerIds.includes(h.id)}
                              onChange={() => toggleHandler(h.id)}
                              className="sr-only"
                            />
                            <span
                              className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                              style={{ backgroundColor: h.color }}
                            />
                            <span className="truncate">{h.name}</span>
                            {h.hasBadgeLouvre && <span title="Louvre badge" className="ml-auto">🏛</span>}
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-2">
                  Assign Trucks (optional)
                </label>
                <div className="flex flex-wrap gap-2">
                  {scheduleData.trucks.map((t) => (
                    <label
                      key={t.id}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs cursor-pointer transition-colors ${
                        selectedTruckIds.includes(t.id)
                          ? "bg-gray-800 text-white"
                          : "bg-gray-100 hover:bg-gray-200"
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedTruckIds.includes(t.id)}
                        onChange={() => toggleTruck(t.id)}
                        className="sr-only"
                      />
                      {t.name}
                    </label>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>

        <div className="px-6 py-4 border-t flex items-center justify-between gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm rounded-lg border hover:bg-gray-50"
          >
            Cancel
          </button>
          <div className="flex gap-2">
            {isEdit && selectedProject!.status === "PRE_BOOKED" && (
              <button
                onClick={() => handleSave("BOOKED")}
                disabled={saving}
                className="px-4 py-2 text-sm rounded-lg bg-green-600 text-white hover:bg-green-700 font-semibold disabled:opacity-50"
              >
                {saving ? "Saving…" : "Confirm Booking"}
              </button>
            )}
            {!isEdit && (
              <>
                <button
                  onClick={() => handleSave("PRE_BOOKED")}
                  disabled={saving}
                  className="px-4 py-2 text-sm rounded-lg bg-orange-500 text-white hover:bg-orange-600 font-semibold disabled:opacity-50"
                >
                  {saving ? "Saving…" : "Pre-book"}
                </button>
                <button
                  onClick={() => handleSave("BOOKED")}
                  disabled={saving}
                  className="px-4 py-2 text-sm rounded-lg bg-gray-900 text-white hover:bg-gray-700 font-semibold disabled:opacity-50"
                >
                  {saving ? "Saving…" : "Confirm Booking"}
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
