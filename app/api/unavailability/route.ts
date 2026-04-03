import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const { type, entityId, date, reason } = body;

  if (type === "truck") {
    const record = await prisma.truckUnavailability.create({
      data: { truckId: entityId, date: new Date(date), reason },
    });
    return NextResponse.json(record, { status: 201 });
  } else {
    const record = await prisma.unavailability.create({
      data: { handlerId: entityId, date: new Date(date), reason },
    });
    return NextResponse.json(record, { status: 201 });
  }
}

export async function DELETE(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const type = searchParams.get("type");
  const id = searchParams.get("id");
  if (!id) return NextResponse.json({ error: "Missing id" }, { status: 400 });

  if (type === "truck") {
    await prisma.truckUnavailability.delete({ where: { id } });
  } else {
    await prisma.unavailability.delete({ where: { id } });
  }
  return NextResponse.json({ ok: true });
}
