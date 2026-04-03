import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "Hasenkamp | Art Logistics Booking",
  description: "Art handler scheduling and booking system",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-gray-50 text-gray-900 font-sans">
        <Navbar />
        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}
