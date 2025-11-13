
interface Account {
  id: number;
  first_name: string;
  last_name: string;
  email?: string | null;
  image_profile: string;
  phone_1?: string | null;
  address?: string | null;
}

interface Customer {
  id: number;
  account: Account;
  is_registered: boolean;
  is_pwd: boolean;
  is_senior: boolean;
}

interface Staff {
  id: number;
  is_front_desk: boolean;
  is_on_shift: boolean;
  account: Account;
}

interface Service {
  id: number;
  name: string;
  description: string;
  price: number;
  duration: number;
}

interface Vehicle {
  id: number;
  type: string;
  model: string;
  plate_number?: string | null;
  owner: Customer;
}

interface Bay {
  id: number;
  bay: string;
}

interface Status {
  id: number;
  status: string;
}

interface Appointment {
  id: number;
  start_time: string;
  end_time: string;
  customer: Customer;
  staffs: Staff[];
  service: Service;
  vehicle: Vehicle;
  bay: Bay;
  status: Status;
  payments: any[];
  feedbacks: any[];
}