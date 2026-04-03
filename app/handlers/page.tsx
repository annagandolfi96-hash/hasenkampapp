"use client";

import { useEffect, useState } from "react";
import { ArtHandler } from "@/lib/types";

const LEVEL_COLORS: Record<string, Record<string, string>> = {
  Internal: {
    Senior: "#4A90D9",
    Mid: "#27AE60",
    Junior: "#F39C12",
  },
  Subcontractor: {
    Senior: "#9B59B6",
    Mid: "#E74C3C",
    Junior: "#95A5A6",
  },
};

const blank = (): Omit<ArtHandler, "id"> => ({
  name: "",
  email: "",
  color: "#4A90D9",
  level: "Mid",
  type: "Internal",
  canDriveTruck: false,
  canDriveCar: false,
  canDriveForklift: false,
  hasBadgeLouvre: false,
  notes: "",
});

export default function HandlersPage() {
  const [handlers, setHandlers] = useState<ArtHandler[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<ArtHandler | null>(null);
  const [form, setForm] = useState(blank());
  const [saving, setSaving] = useState(false);

  async function load() {
    const res = await fetch("/api/handlers");
    setHandlers(await res.json());
  }

  useEffect(() => { load(); }, []);

  function openNew() {
    setEditing(null);
    setForm(blank());
    setShowForm(true);
  }

  function openEdit(h: ArtHandler) {
    setEditing(h);
    setForm({ ...h });
    setShowForm(true);
  }

  function autoColor(type: string, level: string) {
    return LEVEL_COLORS[type]?.[level] || "#4A90D9";
  }

  function handleTypeOrLevelChange(field: "type" | "level", value: string) {
    const next = { ...form, [field]: value };
    next.color = autoColor(field === "type" ? value : form.type, field === "level" ? value : form.level);
    setForm(next);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    if (editing) {
      await fetch(`/api/handlers/${editing.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
    } else {
      await fetch("/api/handlers", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
    }
    setSaving(false);
    setShowForm(false);
    load();
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this art handler?")) return;
    await fetch(`/api/handlers/${id}`, { method: "DELETE" });
    load();
  }

  const grouped = handlers.reduce<Record<string, ArtHandler[]>>((acc, h) => {
    const key = `${h.type} — ${h.level}`;
    if (!acc[key]) acc[key] = [];
    acc[key].push(h);
    return acc;
  }, {});

  const groupOrder = ["Internal — Senior", "Internal — Mid", "Internal — Junior", "Subcontractor — Senior", "Subcontractor — Mid", "Subcontractor — Junior"];

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Art Handlers</h1>
          <p className="text-gray-500 text-sm">{handlers.length} handlers registered</p>
        </div>
        <button
          onClick={openNew}
          className="px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-semibold hover:bg-gray-700"
        >
          + Add Handler
        </button>
      </div>

      <div className="space-y-6">
        {groupOrder.map((group) => {
          const list = grouped[group];
          if (!list?.length) return null;
          const [type, level] = group.split(" — ");
          const color = LEVEL_COLORS[type]?.[level] || "#888";
          return (
            <div key={group}>
              <div className="flex items-center gap-2 mb-2">
                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                <h2 className="text-sm font-bold text-gray-700">{group}</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {list.map((h) => (
                  <div
                    key={h.id}
                    className="bg-white border rounded-xl p-4 flex items-start justify-between gap-3"
                    style={{ borderLeftColor: h.color, borderLeftWidth: 4 }}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold">{h.name}</p>
                      <p className="text-xs text-gray-500 truncate">{h.email}</p>
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        {h.canDriveTruck && <Badge>🚛 Truck</Badge>}
                        {h.canDriveCar && <Badge>🚗 Car</Badge>}
                        {h.canDriveForklift && <Badge>🏗 Forklift</Badge>}
                        {h.hasBadgeLouvre && <Badge highlight>🏛 Louvre</Badge>}
                      </div>
                      {h.notes && <p className="text-xs text-gray-400 mt-1">{h.notes}</p>}
                    </div>
                    <div className="flex gap-1 flex-shrink-0">
                      <button
                        onClick={() => openEdit(h)}
                        className="px-2 py-1 text-xs rounded border hover:bg-gray-50"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(h.id)}
                        className="px-2 py-1 text-xs rounded border border-red-200 text-red-600 hover:bg-red-50"
                      >
                        ×
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <form
            onSubmit={handleSubmit}
            className="bg-white rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] flex flex-col"
          >
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 className="font-bold text-lg">{editing ? "Edit Art Handler" : "New Art Handler"}</h2>
              <button type="button" onClick={() => setShowForm(false)} className="text-gray-500 text-2xl leading-none">&times;</button>
            </div>
            <div className="overflow-y-auto flex-1 px-6 py-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="block text-xs font-semibold text-gray-600 mb-1">Full Name *</label>
                  <input required className="w-full border rounded-lg px-3 py-2 text-sm" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
                </div>
                <div className="col-span-2">
                  <label className="block text-xs font-semibold text-gray-600 mb-1">Email *</label>
                  <input required type="email" className="w-full border rounded-lg px-3 py-2 text-sm" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">Type *</label>
                  <select className="w-full border rounded-lg px-3 py-2 text-sm" value={form.type} onChange={(e) => handleTypeOrLevelChange("type", e.target.value)}>
                    <option>Internal</option>
                    <option>Subcontractor</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">Level *</label>
                  <select className="w-full border rounded-lg px-3 py-2 text-sm" value={form.level} onChange={(e) => handleTypeOrLevelChange("level", e.target.value)}>
                    <option>Senior</option>
                    <option>Mid</option>
                    <option>Junior</option>
                  </select>
                </div>
                <div className="col-span-2">
                  <label className="block text-xs font-semibold text-gray-600 mb-1">
                    Colour (auto-set, override if needed)
                  </label>
                  <div className="flex items-center gap-2">
                    <input type="color" className="h-9 w-16 border rounded cursor-pointer" value={form.color} onChange={(e) => setForm({ ...form, color: e.target.value })} />
                    <span className="text-xs text-gray-400">{form.color}</span>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-2">Skills &amp; Badges</label>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { key: "canDriveTruck", label: "🚛 Drives Truck" },
                    { key: "canDriveCar", label: "🚗 Drives Car" },
                    { key: "canDriveForklift", label: "🏗 Forklift" },
                    { key: "hasBadgeLouvre", label: "🏛 Louvre Badge" },
                  ].map(({ key, label }) => (
                    <label key={key} className={`flex items-center gap-2 p-2 rounded border cursor-pointer text-sm ${(form as any)[key] ? "bg-gray-900 text-white border-gray-900" : "hover:bg-gray-50"}`}>
                      <input
                        type="checkbox"
                        checked={(form as any)[key]}
                        onChange={(e) => setForm({ ...form, [key]: e.target.checked })}
                        className="sr-only"
                      />
                      {label}
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Notes (extra badges, etc.)</label>
                <input className="w-full border rounded-lg px-3 py-2 text-sm" value={form.notes || ""} onChange={(e) => setForm({ ...form, notes: e.target.value })} placeholder="e.g. Versailles badge, First Aider" />
              </div>
            </div>
            <div className="px-6 py-4 border-t flex justify-end gap-2">
              <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 text-sm rounded-lg border hover:bg-gray-50">Cancel</button>
              <button type="submit" disabled={saving} className="px-4 py-2 text-sm rounded-lg bg-gray-900 text-white hover:bg-gray-700 font-semibold disabled:opacity-50">
                {saving ? "Saving…" : editing ? "Save Changes" : "Add Handler"}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

function Badge({ children, highlight }: { children: React.ReactNode; highlight?: boolean }) {
  return (
    <span className={`text-[10px] px-1.5 py-0.5 rounded ${highlight ? "bg-yellow-100 text-yellow-800 font-semibold" : "bg-gray-100 text-gray-600"}`}>
      {children}
    </span>
  );
}
