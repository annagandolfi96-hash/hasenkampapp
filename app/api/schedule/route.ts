import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { startOfDay, endOfDay, addDays } from "date-fns";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const from = searchParams.get("from");
  const days = parseInt(searchParams.get("days") || "7");

  const startDate = from ? new Date(from) : startOfDay(new Date());
  const endDate = endOfDay(addDays(startDate, days - 1));

  const [handlers, trucks, clients, projects, unavailabilities, truckUnavailabilities] = await Promise.all([
    prisma.artHandler.findMany({ orderBy: [{ type: "asc" }, { level: "desc" }, { name: "asc" }] }),
    prisma.truck.findMany({ orderBy: { name: "asc" } }),
    prisma.client.findMany({ orderBy: { name: "asc" } }),
    prisma.project.findMany({
      where: { date: { gte: startDate, lte: endDate } },
      include: {
        client: true,
        bookings: { include: { handler: true } },
        truckBookings: { include: { truck: true } },
      },
    }),
    prisma.unavailability.findMany({
      where: { date: { gte: startDate, lte: endDate } },
    }),
    prisma.truckUnavailability.findMany({
      where: { date: { gte: startDate, lte: endDate } },
    }),
  ]);

  return NextResponse.json({
    handlers,
    trucks,
    clients,
    projects,
    unavailabilities,
    truckUnavailabilities,
    startDate: startDate.toISOString(),
    days,
  });
}
