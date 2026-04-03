import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function PUT(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const body = await req.json();
  const handler = await prisma.artHandler.update({ where: { id }, data: body });
  return NextResponse.json(handler);
}

export async function DELETE(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  await prisma.artHandler.delete({ where: { id } });
  return NextResponse.json({ ok: true });
}
