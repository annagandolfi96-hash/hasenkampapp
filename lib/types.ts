export type Client = {
  id: string;
  name: string;
  color: string;
};

export type ArtHandler = {
  id: string;
  name: string;
  email: string;
  color: string;
  level: string;
  type: string;
  canDriveTruck: boolean;
  canDriveCar: boolean;
  canDriveForklift: boolean;
  hasBadgeLouvre: boolean;
  notes: string | null;
};

export type Truck = {
  id: string;
  name: string;
  licensePlate: string | null;
};

export type Project = {
  id: string;
  projectNumber: string;
  title: string;
  clientId: string;
  client: Client;
  description: string | null;
  location: string | null;
  date: string;
  status: "PRE_BOOKED" | "BOOKED";
  createdBy: string;
  bookings: { id: string; handlerId: string; handler: ArtHandler }[];
  truckBookings: { id: string; truckId: string; truck: Truck }[];
};

export type Unavailability = {
  id: string;
  handlerId: string;
  date: string;
  reason: string | null;
};

export type TruckUnavailability = {
  id: string;
  truckId: string;
  date: string;
  reason: string | null;
};

export type ScheduleData = {
  handlers: ArtHandler[];
  trucks: Truck[];
  clients: Client[];
  projects: Project[];
  unavailabilities: Unavailability[];
  truckUnavailabilities: TruckUnavailability[];
  startDate: string;
  days: number;
};
