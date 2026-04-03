"use client";

import { useEffect, useState } from "react";
import { Truck } from "@/lib/types";

const blank = (): Omit<Truck, "id"> => ({ name: "", licensePlate: "" });

export default function TrucksPage() {
  const [trucks, setTrucks] = useState<Truck[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Truck | null>(null);
  const [form, setForm] = useState(blank());
  const [saving, setSaving] = useState(false);

  async function load() {
    const res = await fetch("/api/trucks");
    setTrucks(await res.json());
  }

  useEffect(() => { load(); }, []);

  function openNew() {
    setEditing(null);
    setForm(blank());
    setShowForm(true);
  }

  function openEdit(t: Truck) {
    setEditing(t);
    setForm({ name: t.name, licensePlate: t.licensePlate });
    setShowForm(true);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    if (editing) {
      await fetch(`/api/trucks/${editing.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
    } else {
      await fetch("/api/trucks", {
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
    if (!confirm("Delete this vehicle?")) return;
    await fetch(`/api/trucks/${id}`, { method: "DELETE" });
    load();
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Vehicles</h1>
          <p className="text-gray-500 text-sm">{trucks.length} vehicles registered</p>
        </div>
        <button onClick={openNew} className="px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-semibold hover:bg-gray-700">
          + Add Vehicle
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {trucks.map((t) => (
          <div key={t.id} className="bg-white border rounded-xl p-4 flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className="text-3xl">🚚</span>
              <div>
                <p className="font-semibold">{t.name}</p>
                {t.licensePlate && <p className="text-xs text-gray-500 font-mono">{t.licensePlate}</p>}
              </div>
            </div>
            <div className="flex gap-1">
              <button onClick={() => openEdit(t)} className="px-2 py-1 text-xs rounded border hover:bg-gray-50">Edit</button>
              <button onClick={() => handleDelete(t.id)} className="px-2 py-1 text-xs rounded border border-red-200 text-red-600 hover:bg-red-50">×</button>
            </div>
          </div>
        ))}
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-2xl w-full max-w-sm">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 className="font-bold text-lg">{editing ? "Edit Vehicle" : "New Vehicle"}</h2>
              <button type="button" onClick={() => setShowForm(false)} className="text-gray-500 text-2xl leading-none">&times;</button>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Name *</label>
                <input
                  required
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="Van 1, Truck 7.5T…"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">License Plate</label>
                <input
                  className="w-full border rounded-lg px-3 py-2 text-sm font-mono"
                  value={form.licensePlate || ""}
                  onChange={(e) => setForm({ ...form, licensePlate: e.target.value })}
                  placeholder="75-ART-001"
                />
              </div>
            </div>
            <div className="px-6 py-4 border-t flex justify-end gap-2">
              <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 text-sm rounded-lg border hover:bg-gray-50">Cancel</button>
              <button type="submit" disabled={saving} className="px-4 py-2 text-sm rounded-lg bg-gray-900 text-white hover:bg-gray-700 font-semibold disabled:opacity-50">
                {saving ? "Saving…" : editing ? "Save" : "Add Vehicle"}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
