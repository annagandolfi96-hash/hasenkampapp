import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function PUT(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const body = await req.json();
  const truck = await prisma.truck.update({ where: { id }, data: body });
  return NextResponse.json(truck);
}

export async function DELETE(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  await prisma.truck.delete({ where: { id } });
  return NextResponse.json({ ok: true });
}
