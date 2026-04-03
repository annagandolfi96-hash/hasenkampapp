"use client";

import { useState } from "react";

type Props = {
  entityId: string;
  entityName: string;
  entityType: "handler" | "truck";
  date: string;
  existingId?: string;
  existingReason?: string;
  onClose: () => void;
  onSaved: () => void;
};

export default function UnavailabilityModal({
  entityId,
  entityName,
  entityType,
  date,
  existingId,
  existingReason,
  onClose,
  onSaved,
}: Props) {
  const [reason, setReason] = useState(existingReason || "");
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    await fetch("/api/unavailability", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type: entityType, entityId, date, reason }),
    });
    setSaving(false);
    onSaved();
  }

  async function handleRemove() {
    if (!existingId) return;
    setSaving(true);
    await fetch(`/api/unavailability?type=${entityType}&id=${existingId}`, { method: "DELETE" });
    setSaving(false);
    onSaved();
  }

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-sm">
        <div className="flex items-center justify-between px-5 py-4 border-b">
          <h2 className="font-bold text-base">
            {existingId ? "Edit Unavailability" : "Mark Unavailable"}
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-900 text-2xl leading-none">&times;</button>
        </div>
        <div className="px-5 py-4 space-y-3">
          <p className="text-sm text-gray-600">
            <span className="font-semibold">{entityName}</span> — {new Date(date).toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long" })}
          </p>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Reason</label>
            <input
              className="w-full border rounded-lg px-3 py-2 text-sm"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Annual leave, Service, Training…"
            />
          </div>
        </div>
        <div className="px-5 py-4 border-t flex justify-between">
          {existingId && (
            <button
              onClick={handleRemove}
              disabled={saving}
              className="px-3 py-2 text-sm rounded-lg text-red-600 hover:bg-red-50 border border-red-200"
            >
              Remove
            </button>
          )}
          <div className="flex gap-2 ml-auto">
            <button onClick={onClose} className="px-3 py-2 text-sm rounded-lg border hover:bg-gray-50">
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-2 text-sm rounded-lg bg-gray-900 text-white hover:bg-gray-700 disabled:opacity-50"
            >
              {saving ? "Saving…" : existingId ? "Update" : "Mark Unavailable"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
