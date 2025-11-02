import logging, random

from datetime import time
from collections import defaultdict

from data import db  # your SQLAlchemy instance
from data.models import (
    Accounts, Customers, Staffs, Appointments, Payments, Services,
    Vehicles, Bays, Roles, Status, Notifications, Feedbacks, Loyalties,
    Schedules
)

from data.utils import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class Populate:

    def populate():
        db.drop_all()
        db.create_all()

        # =============================================================
        # ROLES
        # =============================================================
        roles = ['admin', 'staff', 'customer']
        for r in roles:
            db.session.add(Roles(role=r))
        db.session.commit()

        # =============================================================
        # STATUS
        # =============================================================
        statuses = [
            'Pending', 'In Queue', 'Now Serving', 'Completed', 'Cancelled',
            'Vacant', 'Reserved', 'Full', 'Paid', 'Unpaid', 'Refunded'
        ]
        for s in statuses:
            db.session.add(Status(status=s))
        db.session.commit()

        # =============================================================
        # BAYS
        # =============================================================
        for i in range(1, 6):
            db.session.add(Bays(bay=f'Bay #{i}'))
        db.session.commit()

        # =============================================================
        # SERVICES
        # ============================================================= 
        services = [
            ('Small Bike',          '', 200, 45, 1, 'Motorcycle'),
            ('Big Bike',            '', 300, 45, 1, 'Motorcycle'),
            ('Interior',            '', 150, 45, 2, 'Sedan'),
            ('Exterior',            '', 250, 45, 2, 'Sedan'),
            ('Interior + Exterior', '', 300, 90, 2, 'Sedan'),
            ('Interior',            '', 300, 45, 2, 'SUV'),
            ('Exterior',            '', 250, 45, 2, 'SUV'),
            ('Interior + Exterior', '', 400, 90, 2, 'SUV'),
            ('Interior',            '', 350, 45, 2, 'Van'),
            ('Exterior',            '', 250, 45, 2, 'Van'),
            ('Interior + Exterior', '', 500, 90, 2, 'Van')
        ]
        for name, desc, price, duration, washers, vehicle_type in services:
            db.session.add(Services(
                name=name, 
                description=desc, 
                price=price, 
                duration=duration, 
                washers_needed=washers, 
                type=vehicle_type))
        db.session.commit()

        # =============================================================
        # ADMIN ACCOUNT
        # =============================================================
        admin = Accounts(
            first_name='System', last_name='Administrator', email='admin@gmail.com',
            password='admin1234', role_id=1, address='CDO', phone_1='+639000000001'
        )
        db.session.add(admin)
        db.session.commit()

        # =============================================================
        # STAFF ACCOUNTS
        # =============================================================
        staff_accounts = []
        for i in range(1, 8):
            acc = Accounts(
                first_name='Staff',
                last_name=f'{i:02d}',
                email=f'staff{i:02d}@gmail.com',
                password='admin1234',
                role_id=2,
                address='CDO',
                phone_1=f'+63900000000{i}'
            )
            db.session.add(acc)
            db.session.flush()
            staff_accounts.append(acc)

            staff = Staffs(
                account_id=acc.id,
                is_front_desk=(i == 1),
                is_on_shift=True
            )
            db.session.add(staff)
        db.session.commit()

        washers = Staffs.query.filter_by(is_front_desk=False).all()
        front_desk = Staffs.query.filter_by(is_front_desk=True).first()

        # =============================================================
        # STAFF SCHEDULES
        # =============================================================
        all_staff = Staffs.query.all()
        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

        # Define shift blocks
        shifts = [
            ('Day', time(8, 0), time(16, 0)),
            ('Evening', time(16, 0), time(23, 59)),
            ('Night', time(0, 0), time(8, 0))
        ]

        db.session.query(Schedules).delete()  # clear existing schedules

        # Track which staff got which shift count
        staff_shift_count = defaultdict(lambda: {'Day':0, 'Evening':0, 'Night':0})

        for day_name in day_names:
            # Sort staff by least assigned shifts for fairness
            staff_sorted = sorted(all_staff, key=lambda s: sum(staff_shift_count[s.id].values()))
            
            for i, staff in enumerate(staff_sorted):
                shift_index = i % len(shifts)
                shift_name, start_time, end_time = shifts[shift_index]

                schedule = Schedules(
                    staff_id=staff.id,
                    day=day_name,
                    shift_start=start_time,
                    shift_end=end_time
                )
                db.session.add(schedule)

                # Update shift count
                staff_shift_count[staff.id][shift_name] += 1

        db.session.commit()

        # =============================================================
        # CUSTOMER ACCOUNTS
        # =============================================================
        customer_profiles = [
            {'fname': 'Juan', 'lname': 'Dela Cruz', 'email': 'senior@gmail.com', 'is_senior': True},
            {'fname': 'Pedro', 'lname': 'Magbanua', 'email': 'pwd@gmail.com', 'is_pwd': True},
            {'fname': 'Maria', 'lname': 'Guest', 'email': 'guest@gmail.com', 'is_registered': False}
        ]

        customers = []
        for profile in customer_profiles:
            acc = Accounts(
                first_name=profile['fname'],
                last_name=profile['lname'],
                email=profile['email'],
                password='admin1234',
                role_id=3,
                address='CDO',
                phone_1='+639123456789'
            )
            db.session.add(acc)
            db.session.flush()
            cust = Customers(
                account_id=acc.id,
                is_registered=profile.get('is_registered', True),
                is_pwd=profile.get('is_pwd', False),
                is_senior=profile.get('is_senior', False)
            )
            db.session.add(cust)
            customers.append(cust)
        db.session.commit()

        # =============================================================
        # VEHICLES (each customer has 2)
        # =============================================================
        vehicles = []
        for cust in customers:
            bike_size = random.choice([0, 1])
            car_size = random.choice([0, 2])
            small_vehicle = Vehicles(
                plate_number=f'{cust.id}SMB{random.randint(100,999)}',
                model=['Yamaha Mio', 'Kawasaki Ninja'][bike_size],
                type=['Small Bike', 'Big Bike'][bike_size],
                customer_id=cust.id
            )
            car_vehicle = Vehicles(
                plate_number=f'{cust.id}CAR{random.randint(100,999)}',
                model=['Toyota Vios', 'Mitsubishi Montero', 'Hyundai Starex'][car_size],
                type=['Sedan', 'SUV', 'Van'][car_size],
                customer_id=cust.id
            )
            db.session.add_all([small_vehicle, car_vehicle])
            vehicles.extend([small_vehicle, car_vehicle])
        db.session.commit()

        # =============================================================
        # APPOINTMENTS, PAYMENTS, FEEDBACKS, NOTIFICATIONS, LOYALTIES
        # =============================================================
        # bays = Bays.query.all()
        # services = Services.query.all()

        # for cust in customers:
        #     total_loyalty_points = 0

        #     for v in cust.vehicles:
        #         for j in range(2):  # 2 appointments per vehicle
        #             start = datetime.now() + timedelta(days=random.randint(0, 7))
        #             end = start + timedelta(minutes=45)

        #             service = random.choice(services)
        #             status = random.choice([
        #                         'Pending', 'In Queue', 'Now Serving', 'Completed', 'Cancelled'
        #                     ])
        #             status = Status.query.filter_by(status=status).first()
        #             bay = random.choice(bays)

        #             appointment = Appointments(
        #                 start_time=start,
        #                 end_time=end,
        #                 customer_id=cust.id,
        #                 vehicle_id=v.id,
        #                 service_id=service.id,
        #                 bay_id=bay.id,
        #                 status_id=status.id
        #             )

        #             # Assign staff
        #             if 'Bike' in v.type:
        #                 appointment.staffs = [random.choice(washers)]
        #             else:
        #                 appointment.staffs = random.sample(washers, 2)

        #             db.session.add(appointment)
        #             db.session.flush()

        #             # Payment
        #             payment_status = random.choice([
        #                                 'Pending', 'Paid', 'Unpaid', 'Cancelled', 'Refunded'
        #                             ])
        #             payment_status = Status.query.filter_by(status=payment_status).first()
                    
        #             pay = Payments(
        #                 method=random.choice(['gcash', 'cash', 'xendit']),
        #                 transaction_no=f"TXN{random.randint(10000,99999)}",
        #                 amount=service.price,
        #                 appointment_id=appointment.id,
        #                 status_id=payment_status.id
        #             )
        #             db.session.add(pay)

        #             # Feedback
        #             feedback = Feedbacks(
        #                 rating=random.randint(3, 5),
        #                 comment=random.choice([
        #                     "Great service!",
        #                     "Will come back again.",
        #                     "Satisfied customer.",
        #                     "Could be faster but clean."
        #                 ]),
        #                 customer_id=cust.id,
        #                 appointment_id=appointment.id
        #             )
        #             db.session.add(feedback)

        #             # Notification
        #             notif = Notifications(
        #                 content=f"Your appointment on {start.strftime('%Y-%m-%d')} is now {status.status}.",
        #                 notif_type='status_update',
        #                 account_id=cust.account_id
        #             )
        #             db.session.add(notif)

        #             # Loyalty points for completed appointments
        #             if status.status == "Completed":
        #                 earned = 10
        #                 total_loyalty_points += earned
        #                 loyalty = Loyalties(
        #                     customer_id=cust.id,
        #                     points=earned,
        #                     note=f"Earned {earned} points for completed service: {service.name}"
        #                 )
        #                 db.session.add(loyalty)

        #     db.session.commit()

        #     # Optional summary notification for loyalty
        #     if total_loyalty_points > 0:
        #         notif = Notifications(
        #             content=f"You’ve earned a total of {total_loyalty_points} loyalty points!",
        #             notif_type='loyalty_reward',
        #             account_id=cust.account_id
        #         )
        #         db.session.add(notif)
        #         db.session.commit()

        print("Database successfully seeded!")
        return True

