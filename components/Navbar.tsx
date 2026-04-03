"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Schedule" },
  { href: "/handlers", label: "Art Handlers" },
  { href: "/clients", label: "Clients" },
  { href: "/trucks", label: "Trucks" },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="bg-gray-900 text-white px-6 py-3 flex items-center gap-8 shadow-md">
      <div className="flex items-center gap-2 mr-4">
        <span className="text-lg font-bold tracking-tight">HASENKAMP</span>
        <span className="text-xs text-gray-400 hidden sm:block">Art Logistics</span>
      </div>
      <div className="flex gap-1">
        {links.map((l) => (
          <Link
            key={l.href}
            href={l.href}
            className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
              pathname === l.href
                ? "bg-white text-gray-900"
                : "text-gray-300 hover:text-white hover:bg-gray-700"
            }`}
          >
            {l.label}
          </Link>
        ))}
      </div>
    </nav>
  );
}
