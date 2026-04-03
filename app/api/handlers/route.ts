import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET() {
  const handlers = await prisma.artHandler.findMany({
    orderBy: [{ type: "asc" }, { level: "asc" }, { name: "asc" }],
  });
  return NextResponse.json(handlers);
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  const handler = await prisma.artHandler.create({ data: body });
  return NextResponse.json(handler, { status: 201 });
}
