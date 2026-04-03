"use client";

import { useEffect, useState } from "react";
import { Client } from "@/lib/types";

const blank = (): Omit<Client, "id"> => ({ name: "", color: "#FFD700" });

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Client | null>(null);
  const [form, setForm] = useState(blank());
  const [saving, setSaving] = useState(false);

  async function load() {
    const res = await fetch("/api/clients");
    setClients(await res.json());
  }

  useEffect(() => { load(); }, []);

  function openNew() {
    setEditing(null);
    setForm(blank());
    setShowForm(true);
  }

  function openEdit(c: Client) {
    setEditing(c);
    setForm({ name: c.name, color: c.color });
    setShowForm(true);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    if (editing) {
      await fetch(`/api/clients/${editing.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
    } else {
      await fetch("/api/clients", {
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
    if (!confirm("Delete this client? This will not delete existing bookings.")) return;
    await fetch(`/api/clients/${id}`, { method: "DELETE" });
    load();
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Clients</h1>
          <p className="text-gray-500 text-sm">{clients.length} clients · Each client has a unique colour on the schedule</p>
        </div>
        <button onClick={openNew} className="px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-semibold hover:bg-gray-700">
          + Add Client
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {clients.map((c) => (
          <div
            key={c.id}
            className="bg-white border rounded-xl p-4 flex items-center justify-between gap-3"
            style={{ borderLeftColor: c.color, borderLeftWidth: 4 }}
          >
            <div className="flex items-center gap-3">
              <div
                className="w-10 h-10 rounded-lg flex-shrink-0"
                style={{ backgroundColor: c.color }}
              />
              <div>
                <p className="font-semibold">{c.name}</p>
                <p className="text-xs text-gray-400">{c.color}</p>
              </div>
            </div>
            <div className="flex gap-1">
              <button onClick={() => openEdit(c)} className="px-2 py-1 text-xs rounded border hover:bg-gray-50">Edit</button>
              <button onClick={() => handleDelete(c.id)} className="px-2 py-1 text-xs rounded border border-red-200 text-red-600 hover:bg-red-50">×</button>
            </div>
          </div>
        ))}
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-2xl w-full max-w-sm">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 className="font-bold text-lg">{editing ? "Edit Client" : "New Client"}</h2>
              <button type="button" onClick={() => setShowForm(false)} className="text-gray-500 text-2xl leading-none">&times;</button>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Client Name *</label>
                <input
                  required
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="e.g. Louvre, Tate Modern"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Schedule Colour *</label>
                <div className="flex items-center gap-3">
                  <input
                    type="color"
                    className="h-12 w-20 border rounded cursor-pointer"
                    value={form.color}
                    onChange={(e) => setForm({ ...form, color: e.target.value })}
                  />
                  <div
                    className="flex-1 h-12 rounded-lg border text-sm flex items-center px-3 font-semibold"
                    style={{ backgroundColor: form.color + "66" }}
                  >
                    {form.name || "Preview"}
                  </div>
                </div>
              </div>
            </div>
            <div className="px-6 py-4 border-t flex justify-end gap-2">
              <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 text-sm rounded-lg border hover:bg-gray-50">Cancel</button>
              <button type="submit" disabled={saving} className="px-4 py-2 text-sm rounded-lg bg-gray-900 text-white hover:bg-gray-700 font-semibold disabled:opacity-50">
                {saving ? "Saving…" : editing ? "Save" : "Add Client"}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
