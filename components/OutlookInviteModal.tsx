"use client";

import { Project } from "@/lib/types";
import { useState } from "react";

type Props = {
  project: Project;
  onClose: () => void;
};

export default function OutlookInviteModal({ project, onClose }: Props) {
  const [copied, setCopied] = useState<string | null>(null);

  const handlerEmails = project.bookings.map((b) => b.handler.email).join("; ");
  const inviteTitle = `${project.createdBy} - ${project.client.name} - ${project.bookings.map((b) => b.handler.name.split(" ")[0]).join(", ")} - ${project.projectNumber}`;
  const body = [
    inviteTitle,
    "",
    `Client: ${project.client.name}`,
    `Project: ${project.projectNumber}`,
    `Date: ${new Date(project.date).toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long", year: "numeric" })}`,
    `Location: ${project.location || "TBC"}`,
    "",
    "Description:",
    project.description || "—",
    "",
    "Team:",
    ...project.bookings.map((b) => `  • ${b.handler.name} (${b.handler.level} ${b.handler.type})`),
    ...(project.truckBookings.length > 0
      ? ["", "Vehicles:", ...project.truckBookings.map((b) => `  • ${b.truck.name}${b.truck.licensePlate ? ` (${b.truck.licensePlate})` : ""}`)]
      : []),
    "",
    "Please bring your signed delivery note.",
  ].join("\n");

  function copy(text: string, key: string) {
    navigator.clipboard.writeText(text);
    setCopied(key);
    setTimeout(() => setCopied(null), 2000);
  }

  const dateStr = new Date(project.date).toISOString().split("T")[0];
  const outlookDeepLink = `https://outlook.office.com/calendar/deeplink/compose?subject=${encodeURIComponent(inviteTitle)}&body=${encodeURIComponent(body)}&location=${encodeURIComponent(project.location || "")}&startdt=${dateStr}T09:00:00&enddt=${dateStr}T17:00:00`;

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="font-bold text-lg">Outlook Invite</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-900 text-2xl leading-none">&times;</button>
        </div>

        <div className="overflow-y-auto flex-1 px-6 py-4 space-y-4">
          <p className="text-sm text-gray-500">
            Copy the fields below into your Outlook calendar invite, or click the button to open Outlook directly.
          </p>

          <Field label="To (Art Handlers)" value={handlerEmails} onCopy={() => copy(handlerEmails, "emails")} copied={copied === "emails"} />
          <Field label="Meeting Title" value={inviteTitle} onCopy={() => copy(inviteTitle, "title")} copied={copied === "title"} />
          <Field label="Location" value={project.location || "TBC"} onCopy={() => copy(project.location || "TBC", "location")} copied={copied === "location"} />
          <Field
            label="Body / Description"
            value={body}
            onCopy={() => copy(body, "body")}
            copied={copied === "body"}
            multiline
          />

          <div className="bg-amber-50 rounded-lg p-3 text-xs text-amber-800">
            <strong>Reminder:</strong> Attach the delivery note to the invite before sending. Add the team manager as optional attendee.
          </div>
        </div>

        <div className="px-6 py-4 border-t flex items-center justify-between">
          <button onClick={onClose} className="px-4 py-2 text-sm rounded-lg border hover:bg-gray-50">
            Close
          </button>
          <a
            href={outlookDeepLink}
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 font-semibold"
          >
            Open in Outlook →
          </a>
        </div>
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onCopy,
  copied,
  multiline,
}: {
  label: string;
  value: string;
  onCopy: () => void;
  copied: boolean;
  multiline?: boolean;
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <label className="text-xs font-semibold text-gray-600">{label}</label>
        <button
          onClick={onCopy}
          className={`text-xs px-2 py-0.5 rounded transition-colors ${
            copied ? "bg-green-100 text-green-700" : "bg-gray-100 hover:bg-gray-200 text-gray-600"
          }`}
        >
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
      {multiline ? (
        <pre className="text-xs bg-gray-50 border rounded-lg p-3 whitespace-pre-wrap font-sans text-gray-800 max-h-40 overflow-y-auto">
          {value}
        </pre>
      ) : (
        <div className="text-sm bg-gray-50 border rounded-lg px-3 py-2 text-gray-800 break-all">
          {value}
        </div>
      )}
    </div>
  );
}
