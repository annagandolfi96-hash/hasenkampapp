import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET() {
  const clients = await prisma.client.findMany({ orderBy: { name: "asc" } });
  return NextResponse.json(clients);
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  const client = await prisma.client.create({ data: body });
  return NextResponse.json(client, { status: 201 });
}
