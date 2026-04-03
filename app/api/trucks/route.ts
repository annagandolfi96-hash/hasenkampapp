import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET() {
  const trucks = await prisma.truck.findMany({ orderBy: { name: "asc" } });
  return NextResponse.json(trucks);
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  const truck = await prisma.truck.create({ data: body });
  return NextResponse.json(truck, { status: 201 });
}
