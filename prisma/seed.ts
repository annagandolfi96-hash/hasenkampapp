import { PrismaClient } from "@prisma/client";
import { PrismaLibSql } from "@prisma/adapter-libsql";
import { addDays, startOfDay } from "date-fns";

const adapter = new PrismaLibSql({ url: "file:./dev.db" });
const prisma = new PrismaClient({ adapter } as any);

async function main() {
  // Clients
  const louvre = await prisma.client.upsert({
    where: { id: "client-louvre" },
    update: {},
    create: { id: "client-louvre", name: "Louvre", color: "#FFD700" },
  });
  const tate = await prisma.client.upsert({
    where: { id: "client-tate" },
    update: {},
    create: { id: "client-tate", name: "Tate Modern", color: "#90EE90" },
  });
  const guggenheim = await prisma.client.upsert({
    where: { id: "client-guggenheim" },
    update: {},
    create: { id: "client-guggenheim", name: "Guggenheim", color: "#ADD8E6" },
  });
  const orsay = await prisma.client.upsert({
    where: { id: "client-orsay" },
    update: {},
    create: { id: "client-orsay", name: "Musée d'Orsay", color: "#FFB347" },
  });

  console.log("Clients seeded:", louvre.name, tate.name, guggenheim.name, orsay.name);

  // Art Handlers
  const handlers = [
    {
      id: "handler-1",
      name: "Sophie Martin",
      email: "sophie.martin@hasenkamp.com",
      color: "#4A90D9", // Senior Internal - blue
      level: "Senior",
      type: "Internal",
      canDriveTruck: true,
      canDriveCar: true,
      canDriveForklift: true,
      hasBadgeLouvre: true,
      notes: "Team leader",
    },
    {
      id: "handler-2",
      name: "James Thornton",
      email: "james.thornton@hasenkamp.com",
      color: "#4A90D9",
      level: "Senior",
      type: "Internal",
      canDriveTruck: true,
      canDriveCar: true,
      canDriveForklift: false,
      hasBadgeLouvre: true,
      notes: "",
    },
    {
      id: "handler-3",
      name: "Clara Dubois",
      email: "clara.dubois@hasenkamp.com",
      color: "#27AE60", // Mid Internal - green
      level: "Mid",
      type: "Internal",
      canDriveTruck: false,
      canDriveCar: true,
      canDriveForklift: false,
      hasBadgeLouvre: true,
      notes: "",
    },
    {
      id: "handler-4",
      name: "Marcus Bauer",
      email: "marcus.bauer@hasenkamp.com",
      color: "#27AE60",
      level: "Mid",
      type: "Internal",
      canDriveTruck: true,
      canDriveCar: true,
      canDriveForklift: true,
      hasBadgeLouvre: false,
      notes: "Louvre badge pending",
    },
    {
      id: "handler-5",
      name: "Léa Fontaine",
      email: "lea.fontaine@hasenkamp.com",
      color: "#F39C12", // Junior Internal - orange
      level: "Junior",
      type: "Internal",
      canDriveTruck: false,
      canDriveCar: true,
      canDriveForklift: false,
      hasBadgeLouvre: false,
      notes: "",
    },
    {
      id: "handler-6",
      name: "Ravi Patel",
      email: "ravi.patel@freelance.com",
      color: "#9B59B6", // Senior Sub - purple
      level: "Senior",
      type: "Subcontractor",
      canDriveTruck: true,
      canDriveCar: true,
      canDriveForklift: false,
      hasBadgeLouvre: true,
      notes: "",
    },
    {
      id: "handler-7",
      name: "Amelia Koch",
      email: "amelia.koch@arthandlers.eu",
      color: "#E74C3C", // Mid Sub - red
      level: "Mid",
      type: "Subcontractor",
      canDriveTruck: false,
      canDriveCar: true,
      canDriveForklift: false,
      hasBadgeLouvre: false,
      notes: "",
    },
    {
      id: "handler-8",
      name: "Yann Leclerc",
      email: "yann.leclerc@freelance.com",
      color: "#E74C3C",
      level: "Mid",
      type: "Subcontractor",
      canDriveTruck: true,
      canDriveCar: true,
      canDriveForklift: false,
      hasBadgeLouvre: true,
      notes: "",
    },
    {
      id: "handler-9",
      name: "Nina Torres",
      email: "nina.torres@artcrew.com",
      color: "#95A5A6", // Junior Sub - gray
      level: "Junior",
      type: "Subcontractor",
      canDriveTruck: false,
      canDriveCar: false,
      canDriveForklift: false,
      hasBadgeLouvre: false,
      notes: "",
    },
    {
      id: "handler-10",
      name: "Ben Walker",
      email: "ben.walker@artcrew.com",
      color: "#95A5A6",
      level: "Junior",
      type: "Subcontractor",
      canDriveTruck: false,
      canDriveCar: true,
      canDriveForklift: false,
      hasBadgeLouvre: false,
      notes: "",
    },
  ];

  for (const h of handlers) {
    await prisma.artHandler.upsert({
      where: { id: h.id },
      update: {},
      create: h,
    });
  }
  console.log("Art handlers seeded:", handlers.length);

  // Trucks
  const trucks = [
    { id: "truck-1", name: "Van 1", licensePlate: "75-ART-001" },
    { id: "truck-2", name: "Van 2", licensePlate: "75-ART-002" },
    { id: "truck-3", name: "Truck 7.5T", licensePlate: "75-ART-003" },
    { id: "truck-4", name: "Truck 12T", licensePlate: "75-ART-004" },
  ];

  for (const t of trucks) {
    await prisma.truck.upsert({
      where: { id: t.id },
      update: {},
      create: t,
    });
  }
  console.log("Trucks seeded:", trucks.length);

  // Sample projects for demo (next 7 days from today)
  const today = startOfDay(new Date());
  const day2 = addDays(today, 2);
  const day4 = addDays(today, 4);

  const project1 = await prisma.project.upsert({
    where: { id: "project-1" },
    update: {},
    create: {
      id: "project-1",
      projectNumber: "HAR-2026-001",
      title: "Louvre - Egyptian Gallery Install",
      clientId: louvre.id,
      description: "Install of 12 Egyptian artefacts in gallery B. Handle with extreme care.",
      location: "Louvre Museum, Paris - Denon Wing",
      date: day2,
      status: "BOOKED",
      createdBy: "AG",
    },
  });

  await prisma.booking.upsert({
    where: { id: "booking-1a" },
    update: {},
    create: { id: "booking-1a", projectId: project1.id, handlerId: "handler-1", date: day2 },
  });
  await prisma.booking.upsert({
    where: { id: "booking-1b" },
    update: {},
    create: { id: "booking-1b", projectId: project1.id, handlerId: "handler-2", date: day2 },
  });
  await prisma.booking.upsert({
    where: { id: "booking-1c" },
    update: {},
    create: { id: "booking-1c", projectId: project1.id, handlerId: "handler-3", date: day2 },
  });
  await prisma.booking.upsert({
    where: { id: "booking-1d" },
    update: {},
    create: { id: "booking-1d", projectId: project1.id, handlerId: "handler-6", date: day2 },
  });
  await prisma.truckBooking.upsert({
    where: { id: "tbooking-1a" },
    update: {},
    create: { id: "tbooking-1a", projectId: project1.id, truckId: "truck-3", date: day2 },
  });

  const project2 = await prisma.project.upsert({
    where: { id: "project-2" },
    update: {},
    create: {
      id: "project-2",
      projectNumber: "HAR-2026-002",
      title: "Tate Modern - Sculpture Move",
      clientId: tate.id,
      description: "Move 3 large sculptures from storage to Turbine Hall.",
      location: "Tate Modern, London - Turbine Hall",
      date: day4,
      status: "PRE_BOOKED",
      createdBy: "AG",
    },
  });

  await prisma.booking.upsert({
    where: { id: "booking-2a" },
    update: {},
    create: { id: "booking-2a", projectId: project2.id, handlerId: "handler-4", date: day4 },
  });
  await prisma.booking.upsert({
    where: { id: "booking-2b" },
    update: {},
    create: { id: "booking-2b", projectId: project2.id, handlerId: "handler-5", date: day4 },
  });
  await prisma.booking.upsert({
    where: { id: "booking-2c" },
    update: {},
    create: { id: "booking-2c", projectId: project2.id, handlerId: "handler-7", date: day4 },
  });

  // Unavailabilities
  const day3 = addDays(today, 3);
  await prisma.unavailability.upsert({
    where: { id: "unavail-1" },
    update: {},
    create: {
      id: "unavail-1",
      handlerId: "handler-9",
      date: day3,
      reason: "Annual leave",
    },
  });
  await prisma.truckUnavailability.upsert({
    where: { id: "tunavail-1" },
    update: {},
    create: {
      id: "tunavail-1",
      truckId: "truck-2",
      date: day2,
      reason: "Service",
    },
  });

  console.log("Sample projects and bookings seeded.");
}

main()
  .then(() => prisma.$disconnect())
  .catch(async (e) => {
    console.error(e);
    await prisma.$disconnect();
    process.exit(1);
  });
