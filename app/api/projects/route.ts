import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET() {
  const projects = await prisma.project.findMany({
    include: {
      client: true,
      bookings: { include: { handler: true } },
      truckBookings: { include: { truck: true } },
    },
    orderBy: { date: "asc" },
  });
  return NextResponse.json(projects);
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  const { handlerIds, truckIds, date, ...projectData } = body;

  const project = await prisma.project.create({
    data: {
      ...projectData,
      date: new Date(date),
      bookings: {
        create: handlerIds.map((hid: string) => ({
          handlerId: hid,
          date: new Date(date),
        })),
      },
      truckBookings: truckIds
        ? {
            create: truckIds.map((tid: string) => ({
              truckId: tid,
              date: new Date(date),
            })),
          }
        : undefined,
    },
    include: {
      client: true,
      bookings: { include: { handler: true } },
      truckBookings: { include: { truck: true } },
    },
  });

  return NextResponse.json(project, { status: 201 });
}
