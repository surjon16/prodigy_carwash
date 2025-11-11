import logging

from datetime import datetime, date, timedelta, time
from typing import Optional, List, Union, Dict, Any
from sqlalchemy import and_, or_, cast, Date
from flask_login import login_user

from data import db  # your SQLAlchemy instance
from data.models import (
    Accounts, Customers, Staffs, Appointments, Payments, Services,
    Vehicles, Bays, Roles, Status, Notifications, Feedbacks, Loyalties,
    Schedules
)

from data.utils import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# =============================================================
# HELPERS
# =============================================================

def _parse_time(time_str: str) -> Optional[time]:
    """Convert 'HH:MM' string to datetime.time"""
    if not time_str:
        return None
    try:
        return datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        return None

def _parse_date_mmddyyyy(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    return None


def _parse_datetime_iso_or_custom(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        # ISO first
        return datetime.fromisoformat(s)
    except Exception:
        try:
            return datetime.strptime(s, "%Y-%m-%d %H:%M")
        except Exception:
            return None


# ==================================================================================
# ACCOUNTS
# ==================================================================================

def login_account(request: Dict[str, Any]) -> Optional[Accounts]:
    """
    Authenticate and log in an account.
    Returns Accounts on success, None on bad credentials.
    """
    try:
        email = request.get('email')
        pw = request.get('password')
        account = Accounts.query.filter_by(email=email).first()
        if account and account.verify_password(pw):
            login_user(account)
            return account
        return None
    except Exception as e:
        logger.exception("login_account error")
        return None


def get_accounts() -> List[Accounts]:
    """Return all accounts."""
    return Accounts.query.all()


def get_account(account_id: int) -> Optional[Accounts]:
    """Return a single account or None."""
    return Accounts.query.filter_by(id=account_id).first()


def register_account(request: Dict[str, Any]) -> Optional[Accounts]:
    """
    Create an Accounts record.
    Returns the created Accounts instance or False on failure.
    """
    try:
        birth_date = _parse_date_mmddyyyy(request.get('birth_date'))
        account = Accounts(
            first_name=request.get('first_name'),
            middle_name=request.get('middle_name'),
            last_name=request.get('last_name'),
            gender=request.get('gender'),
            phone_1=request.get('phone_1'),
            phone_2=request.get('phone_2'),
            birth_date=birth_date,
            address=request.get('address'),
            email=request.get('email'),
            role_id=int(request.get('role_id')) if request.get('role_id') is not None else None
        )
        if request.get('password'):
            account.password = request.get('password')
        db.session.add(account)
        db.session.commit()
        logger.debug("Created account id=%s", account.id)
        return account
    except Exception as e:
        db.session.rollback()
        logger.exception("register_account failed")
        return False


def upsert_account(request: Dict[str, Any]) -> Optional[Accounts]:
    """
    Create or update an Accounts record. If 'id' exists -> update and return account.
    Returns Accounts instance or False on failure.
    """
    try:
        account_id = request.get('id')
        birth_date = _parse_date_mmddyyyy(request.get('birth_date'))

        if account_id:
            account = Accounts.query.filter_by(id=account_id).first()
            if not account:
                logger.debug("upsert_account: id provided but account not found: %s", account_id)
                return None
            # update
            account.first_name = request.get('first_name', account.first_name)
            account.middle_name = request.get('middle_name', account.middle_name)
            account.last_name = request.get('last_name', account.last_name)
            account.gender = request.get('gender', account.gender)
            account.phone_1 = request.get('phone_1', account.phone_1)
            account.phone_2 = request.get('phone_2', account.phone_2)
            account.birth_date = birth_date if birth_date is not None else account.birth_date
            account.address = request.get('address', account.address)
            account.email = request.get('email', account.email)
            if request.get('role_id') is not None:
                account.role_id = int(request.get('role_id'))
            if request.get('password'):
                account.password = request.get('password')
            db.session.commit()
            logger.debug("Updated account id=%s", account.id)
            return account
        else:
            # create
            account = register_account(request)
            return account
    except Exception as e:
        db.session.rollback()
        logger.exception("upsert_account failed")
        return False


def delete_account(request: Dict[str, Any]) -> bool:
    """
    Delete an account and rely on cascade config for related rows.
    Returns True on success, False otherwise.
    """
    try:
        account = Accounts.query.filter_by(id=request.get('id')).first()
        if not account:
            logger.debug("delete_account: account not found id=%s", request.get('id'))
            return False
        db.session.delete(account)
        db.session.commit()
        logger.debug("Deleted account id=%s", request.get('id'))
        return True
    except Exception as e:
        db.session.rollback()
        logger.exception("delete_account failed")
        return False


# ==================================================================================
# CUSTOMERS
# ==================================================================================

def get_customers() -> List[Customers]:
    return Customers.query.all()


def get_customer(customer_id: int) -> Optional[Customers]:
    return Customers.query.filter_by(id=customer_id).first()


def get_registered_customers() -> List[Customers]:
    return Customers.query.filter_by(is_registered=True).all()


def create_customer(request: Dict[str, Any]) -> Optional[Customers]:
    """
    Create a customer. Accepts either 'account_id' to link an existing account
    or 'account' (dict) to create a new linked account.
    Returns the created Customer instance or False on failure.
    """
    try:
        account_id = request.get('account_id')
        if not account_id and request.get('account'):
            acct = register_account(request.get('account'))
            if not acct:
                raise ValueError("Failed to create linked account")
            account_id = acct.id

        customer = Customers(
            account_id=account_id,
            is_registered=request.get('is_registered', False),
            is_pwd=request.get('is_pwd', False),
            is_senior=request.get('is_senior', False)
        )
        db.session.add(customer)
        db.session.commit()
        logger.debug("Created customer id=%s account_id=%s", customer.id, account_id)
        return customer
    except Exception as e:
        db.session.rollback()
        logger.exception("create_customer failed")
        return False


def upsert_customer(request: Dict[str, Any]) -> Optional[Customers]:
    """
    Create or update a Customer. If request contains 'account' dict, it will
    create/update linked account before creating/updating the customer.
    Returns the Customer instance or False on failure.
    """
    try:
        cust_id = request.get('id')
        if request.get('account'):
            acct_req = request.get('account')
            acct = upsert_account(acct_req)
            if acct in (False, None):
                raise ValueError("Failed to create/update linked account")
            request['account_id'] = acct.id

        if cust_id:
            cust = Customers.query.filter_by(id=cust_id).first()
            if not cust:
                logger.debug("upsert_customer: not found id=%s", cust_id)
                return None
            cust.is_registered = request.get('is_registered', cust.is_registered)
            cust.is_pwd = request.get('is_pwd', cust.is_pwd)
            cust.is_senior = request.get('is_senior', cust.is_senior)
            if request.get('account_id'):
                cust.account_id = request.get('account_id')
            db.session.commit()
            logger.debug("Updated customer id=%s", cust.id)
            return cust
        else:
            # create
            customer = create_customer(request)
            return customer
    except Exception as e:
        db.session.rollback()
        logger.exception("upsert_customer failed")
        return False


def delete_customer(request: Dict[str, Any]) -> bool:
    try:
        cust = Customers.query.filter_by(id=request.get('id')).first()
        if not cust:
            logger.debug("delete_customer: not found id=%s", request.get('id'))
            return False
        db.session.delete(cust)
        db.session.commit()
        logger.debug("Deleted customer id=%s", request.get('id'))
        return True
    except Exception as e:
        db.session.rollback()
        logger.exception("delete_customer failed")
        return False


# ==================================================================================
# STAFFS
# ==================================================================================

def get_staffs() -> List[Staffs]:
    return Staffs.query.all()


def get_staff(staff_id: int) -> Optional[Staffs]:
    return Staffs.query.filter_by(id=staff_id).first()


def create_staff(request: Dict[str, Any]) -> Optional[Staffs]:
    """
    Create a staff. Accepts 'account_id' or 'account' dict for linked account creation.
    """
    try:
        account_id = request.get('account_id')
        if not account_id and request.get('account'):
            acct = register_account(request.get('account'))
            if not acct:
                raise ValueError("Failed to create linked account")
            account_id = acct.id

        staff = Staffs(
            account_id=account_id,
            is_front_desk=request.get('is_front_desk', False),
            is_on_shift=request.get('is_on_shift', False)
        )
        db.session.add(staff)
        db.session.commit()
        logger.debug("Created staff id=%s account_id=%s", staff.id, account_id)
        return staff
    except Exception as e:
        db.session.rollback()
        logger.exception("create_staff failed")
        return False


def upsert_staff(request: Dict[str, Any]) -> Optional[Staffs]:
    """
    Upsert staff and optionally create/update linked account.
    """
    try:
        staff_id = request.get('id')
        if request.get('account'):
            acct = upsert_account(request.get('account'))
            if acct in (False, None):
                raise ValueError("Failed to create/update linked account")
            request['account_id'] = acct.id

        if staff_id:
            staff = Staffs.query.filter_by(id=staff_id).first()
            if not staff:
                raise ValueError("Staff doesn't exist")
            staff.is_front_desk = request.get('is_front_desk', staff.is_front_desk)
            staff.is_on_shift = request.get('is_on_shift', staff.is_on_shift)
            if request.get('account_id'):
                staff.account_id = request.get('account_id')
            db.session.commit()
            logger.debug("Updated staff id=%s", staff.id)
            return staff
        else:
            return create_staff(request)
    except Exception as e:
        db.session.rollback()
        logger.exception("upsert_staff failed")
        return False


def delete_staff(request: Dict[str, Any]) -> bool:
    try:
        staff = Staffs.query.filter_by(id=request.get('id')).first()
        if not staff:
            logger.debug("delete_staff: not found id=%s", request.get('id'))
            return False
        # Many-to-many links are removed when staff is deleted by SQLAlchemy
        db.session.delete(staff)
        db.session.commit()
        logger.debug("Deleted staff id=%s", request.get('id'))
        return True
    except Exception as e:
        db.session.rollback()
        logger.exception("delete_staff failed")
        return False
    

# =============================================================
# STAFF SCHEDULES
# =============================================================

def get_schedules() -> List[Schedules]:
    """Return all staff schedules"""
    return Schedules.query.all()


def get_schedule(schedule_id: int) -> Optional[Schedules]:
    """Return a single schedule by ID"""
    return Schedules.query.filter_by(id=schedule_id).first()


def get_schedule_by_staff(staff_id: int) -> Optional[Schedules]:
    """Return the schedule for a specific staff"""
    return Schedules.query.filter_by(staff_id=staff_id).first()


def upsert_schedule(request: Dict[str, Any]) -> Union[Schedules, bool, None]:
    """
    Create or update a schedule.
    Request dict should contain:
    - staff_id (required)
    - shift_start (HH:MM string, optional)
    - shift_end (HH:MM string, optional)
    - day (optional)
    - id (optional, if updating)
    """
    try:
        sched_id = request.get('id')
        staff_id = request.get('staff_id')

        # parse time strings
        shift_start = _parse_time(request.get('shift_start')) or time(8, 0)
        shift_end = _parse_time(request.get('shift_end')) or time(17, 0)
        day = request.get('day')

        if sched_id:
            sched = Schedules.query.filter_by(id=sched_id).first()
            if not sched:
                return None
            sched.staff_id = staff_id or sched.staff_id
            sched.shift_start = shift_start
            sched.shift_end = shift_end
            sched.day = day or sched.day
            db.session.commit()
            logger.debug("Updated schedule id=%s", sched.id)
            return sched
        else:
            # Ensure one schedule per staff (unique constraint)
            existing = Schedules.query.filter_by(staff_id=staff_id).first()
            if existing:
                return None

            sched = Schedules(
                staff_id=staff_id,
                shift_start=shift_start,
                shift_end=shift_end,
                day=day
            )
            db.session.add(sched)
            db.session.commit()
            logger.debug("Created schedule id=%s", sched.id)
            return sched
    except Exception as e:
        db.session.rollback()
        logger.exception("upsert_schedule failed")
        return False


def delete_schedule(request: Dict[str, Any]) -> bool:
    """Delete a schedule by ID"""
    try:
        sched = Schedules.query.filter_by(id=request.get('id')).first()
        if not sched:
            return False
        db.session.delete(sched)
        db.session.commit()
        logger.debug("Deleted schedule id=%s", request.get('id'))
        return True
    except Exception as e:
        db.session.rollback()
        logger.exception("delete_schedule failed")
        return False

# ==================================================================================
# APPOINTMENTS
# ==================================================================================

def get_appointments() -> List[Appointments]:
    return Appointments.query.all()

def get_appointment(appointment_id: int) -> Optional[Appointments]:
    return Appointments.query.filter_by(id=appointment_id).first()

def get_current_appointments() -> List[Appointments]:
    return Appointments.query.filter(cast(Appointments.start_time, Date) == date.today(), Appointments.status_id > 1).order_by(Appointments.start_time, Appointments.status_id).all()

def get_appointment_requests() -> List[Appointments]:
    return Appointments.query.filter(Appointments.status_id == 1).order_by(Appointments.start_time).all()

def get_upcoming_appointments() -> List[Appointments]:
    return Appointments.query.filter(cast(Appointments.start_time, Date) > date.today(), Appointments.status_id > 1).order_by(Appointments.start_time, Appointments.status_id).all()

def get_appointments_by_date(start_date: Union[str, date, None]) -> List[Appointments]:
    """
    Return appointments that occur on the provided date.
    Accepts 'YYYY-MM-DD' string or date object. If None -> today.
    """
    if not start_date:
        start_date = date.today()
    elif isinstance(start_date, str):
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        except Exception:
            start_date = date.today()

    return Appointments.query.filter(cast(Appointments.start_time, Date) == start_date).order_by(Appointments.start_time).all()


def get_weekly_appointments() -> Dict[str, List[Appointments]]:
    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=7)

    appointments = Appointments.query.filter(
        Appointments.start_time >= start_of_week,
        Appointments.start_time < end_of_week
    ).all()

    week_days = { (start_of_week + timedelta(days=i)).strftime("%a"): [] for i in range(7) }
    for appt in appointments:
        if appt.start_time:
            day = appt.start_time.strftime("%a")
            week_days[day].append(appt)
    return week_days


def book_appointment(request: Dict[str, Any]) -> Union[Appointments, str, bool]:
    """
    Attempt to book an appointment into a free bay.
    Required: start_time (string "%Y-%m-%d %H:%M"), customer_id, vehicle_id, service_id
    Optional: staffs_ids (list[int] or int)
    Returns: created Appointments instance or string message or False on error.
    """
    try:
        service = Services.query.filter_by(id=request.get('service_id')).first()
        if not service:
            return "Service not found"

        start = _parse_datetime_iso_or_custom(request.get('start_time'))
        if not start:
            return "Invalid start_time"

        end = start + timedelta(minutes=service.duration)
        bays = Bays.query.all()
        for bay in bays:
            conflict = Appointments.query.filter(
                Appointments.bay_id == bay.id,
                ~((Appointments.end_time <= start) | (Appointments.start_time >= end))
            ).first()
            if not conflict:
                appt = Appointments(
                    start_time=start,
                    end_time=end,
                    customer_id=request.get('customer_id'),
                    vehicle_id=request.get('vehicle_id'),
                    service_id=request.get('service_id'),
                    bay_id=bay.id,
                    status_id=request.get('status_id', 2)
                )
                db.session.add(appt)
                db.session.flush()

                staffs_ids = request.get('staffs_ids') or request.get('staff_id')
                if staffs_ids:
                    if isinstance(staffs_ids, int):
                        staffs_ids = [staffs_ids]
                    staffs_objs = Staffs.query.filter(Staffs.id.in_(staffs_ids)).all()
                    for s in staffs_objs:
                        appt.staffs.append(s)
                db.session.commit()
                logger.debug("Booked appointment id=%s bay_id=%s", appt.id, bay.id)
                return appt
        return "No available bay at that time"
    except Exception as e:
        db.session.rollback()
        logger.exception("book_appointment failed")
        return False


def upsert_appointment(request: Dict[str, Any]) -> Union[Appointments, bool, None]:
    """
    Create or update an appointment. Returns the appointment instance or False/None on failure/not found.
    """
    try:
        appt_id = request.get('id')
        start = _parse_datetime_iso_or_custom(request.get('start_time')) if request.get('start_time') else None
        end = _parse_datetime_iso_or_custom(request.get('end_time')) if request.get('end_time') else None

        if appt_id:
            appt = Appointments.query.filter_by(id=appt_id).first()
            if not appt:
                logger.debug("upsert_appointment: not found id=%s", appt_id)
                return None
            appt.start_time = start or appt.start_time
            appt.end_time = end or appt.end_time
            appt.customer_id = request.get('customer_id', appt.customer_id)
            appt.vehicle_id = request.get('vehicle_id', appt.vehicle_id)
            appt.service_id = request.get('service_id', appt.service_id)
            appt.bay_id = request.get('bay_id', appt.bay_id)
            appt.status_id = request.get('status_id', appt.status_id)

            if 'staffs_ids' in request:
                appt.staffs = []
                staff_ids = request.get('staffs_ids')
                if isinstance(staff_ids, int):
                    staff_ids = [staff_ids]
                staffs_objs = Staffs.query.filter(Staffs.id.in_(staff_ids)).all()
                for s in staffs_objs:
                    appt.staffs.append(s)
            db.session.commit()
            logger.debug("Updated appointment id=%s", appt.id)
            return appt
        else:
            # create new
            return book_appointment(request)
    except Exception as e:
        db.session.rollback()
        logger.exception("upsert_appointment failed")
        return False


def update_appointment_status(request: Dict[str, Any]) -> bool:
    try:
        appt = Appointments.query.filter_by(id=request.get('id')).first()
        if not appt:
            return False
        appt.status_id = request.get('status_id')
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.exception("update_appointment_status failed")
        return False


def delete_appointment(request: Dict[str, Any]) -> bool:
    try:
        appt = Appointments.query.filter_by(id=request.get('id')).first()
        if not appt:
            return False
        db.session.delete(appt)
        db.session.commit()
        logger.debug("Deleted appointment id=%s", request.get('id'))
        return True
    except Exception as e:
        db.session.rollback()
        logger.exception("delete_appointment failed")
        return False


# ==================================================================================
# PAYMENTS
# ==================================================================================

def get_payments() -> List[Payments]:
    return Payments.query.all()


def get_payment(payment_id: int) -> Optional[Payments]:
    return Payments.query.filter_by(id=payment_id).first()


def upsert_payment(request: Dict[str, Any]) -> Union[Payments, bool]:
    """
    Create or update a payment. Returns Payments instance or False on error.
    """
    try:
        pay_id = request.get('id')
        if pay_id:
            pay = Payments.query.filter_by(id=pay_id).first()
            if not pay:
                return None
            pay.method = request.get('method', pay.method)
            pay.transaction_no = request.get('transaction_no', pay.transaction_no)
            pay.image_payment = request.get('image_payment', pay.image_payment)
            pay.amount = request.get('amount', pay.amount)
            pay.appointment_id = request.get('appointment_id', pay.appointment_id)
            pay.status_id = request.get('status_id', pay.status_id)
            db.session.commit()
            return pay
        else:
            pay = Payments(
                method=request.get('method'),
                transaction_no=request.get('transaction_no'),
                image_payment=request.get('image_payment'),
                amount=request.get('amount'),
                appointment_id=request.get('appointment_id'),
                status_id=request.get('status_id')
            )
            db.session.add(pay)
            db.session.commit()
            return pay
    except Exception as e:
        db.session.rollback()
        logger.exception("upsert_payment failed")
        return False


def delete_payment(request: Dict[str, Any]) -> bool:
    try:
        pay = Payments.query.filter_by(id=request.get('id')).first()
        if not pay:
            return False
        db.session.delete(pay)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.exception("delete_payment failed")
        return False


# ==================================================================================
# SERVICES
# ==================================================================================

def get_services() -> List[Services]:
    return Services.query.all()


def get_service(service_id: int) -> Optional[Services]:
    return Services.query.filter_by(id=service_id).first()


def upsert_service(request: Dict[str, Any]) -> Union[Services, bool]:
    try:
        sid = request.get('id')
        if sid:
            s = Services.query.filter_by(id=sid).first()
            if not s:
                return None
            s.name = request.get('name', s.name)
            s.description = request.get('description', s.description)
            s.price = request.get('price', s.price)
            s.duration = request.get('duration', s.duration)
            s.washers_needed = request.get('washers_needed', s.washers_needed)
            s.type = request.get('type', s.type)
            db.session.commit()
            return s
        else:
            s = Services(
                name=request.get('name'),
                description=request.get('description'),
                price=request.get('price'),
                duration=request.get('duration'),
                type=request.get('type'),
                washers_needed=request.get('washers_needed')
            )
            db.session.add(s)
            db.session.commit()
            return s
    except Exception as e:
        db.session.rollback()
        logger.exception("upsert_service failed")
        return False


def delete_service(request: Dict[str, Any]) -> bool:
    try:
        s = Services.query.filter_by(id=request.get('id')).first()
        if not s:
            return False
        db.session.delete(s)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.exception("delete_service failed")
        return False


# ==================================================================================
# VEHICLES
# ==================================================================================

def get_vehicles() -> List[Vehicles]:
    return Vehicles.query.all()


def get_vehicle(vehicle_id: int) -> Optional[Vehicles]:
    return Vehicles.query.filter_by(id=vehicle_id).first()


def get_customer_vehicles(customer_id: int) -> List[Vehicles]:
    return Vehicles.query.filter_by(customer_id=customer_id).all()


def upsert_vehicle(request: Dict[str, Any]) -> Union[Vehicles, bool]:
    try:
        vid = request.get('id')
        if vid:
            v = Vehicles.query.filter_by(id=vid).first()
            if not v:
                return None
            v.plate_number = request.get('plate_number', v.plate_number)
            v.model = request.get('model', v.model)
            v.type = request.get('type', v.type)
            v.customer_id = request.get('customer_id', v.customer_id)
            db.session.commit()
            return v
        else:
            v = Vehicles(
                plate_number=request.get('plate_number'),
                model=request.get('model'),
                type=request.get('type'),
                customer_id=request.get('customer_id')
            )
            db.session.add(v)
            db.session.commit()
            return v
    except Exception as e:
        db.session.rollback()
        logger.exception("upsert_vehicle failed")
        return False


def delete_vehicle(request: Dict[str, Any]) -> bool:
    try:
        v = Vehicles.query.filter_by(id=request.get('id')).first()
        if not v:
            return False
        db.session.delete(v)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.exception("delete_vehicle failed")
        return False


# ==================================================================================
# BAYS
# ==================================================================================

def get_bays() -> List[Bays]:
    return Bays.query.all()


def get_bay(bay_id: int) -> Optional[Bays]:
    return Bays.query.filter_by(id=bay_id).first()


def upsert_bay(request: Dict[str, Any]) -> Union[Bays, bool]:
    try:
        bid = request.get('id')
        if bid:
            b = Bays.query.filter_by(id=bid).first()
            if not b:
                return None
            b.bay = request.get('bay', b.bay)
            db.session.commit()
            return b
        else:
            b = Bays(bay=request.get('bay'))
            db.session.add(b)
            db.session.commit()
            return b
    except Exception as e:
        db.session.rollback()
        logger.exception("upsert_bay failed")
        return False


def delete_bay(request: Dict[str, Any]) -> bool:
    try:
        b = Bays.query.filter_by(id=request.get('id')).first()
        if not b:
            return False
        db.session.delete(b)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.exception("delete_bay failed")
        return False


# ==================================================================================
# ROLES
# ==================================================================================

def get_roles() -> List[Roles]:
    return Roles.query.all()


def get_role(role_id: int) -> Optional[Roles]:
    return Roles.query.filter_by(id=role_id).first()


def upsert_role(request: Dict[str, Any]) -> Union[Roles, bool]:
    try:
        rid = request.get('id')
        if rid:
            r = Roles.query.filter_by(id=rid).first()
            if not r:
                return None
            r.role = request.get('role', r.role)
            db.session.commit()
            return r
        else:
            r = Roles(role=request.get('role'))
            db.session.add(r)
            db.session.commit()
            return r
    except Exception as e:
        db.session.rollback()
        logger.exception("upsert_role failed")
        return False


def delete_role(request: Dict[str, Any]) -> bool:
    try:
        r = Roles.query.filter_by(id=request.get('id')).first()
        if not r:
            return False
        db.session.delete(r)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.exception("delete_role failed")
        return False


# ==================================================================================
# STATUS
# ==================================================================================

def get_statuses() -> List[Status]:
    return Status.query.all()


def get_status(status_id: int) -> Optional[Status]:
    return Status.query.filter_by(id=status_id).first()


def upsert_status(request: Dict[str, Any]) -> Union[Status, bool]:
    try:
        sid = request.get('id')
        if sid:
            s = Status.query.filter_by(id=sid).first()
            if not s:
                return None
            s.status = request.get('status', s.status)
            db.session.commit()
            return s
        else:
            s = Status(status=request.get('status'))
            db.session.add(s)
            db.session.commit()
            return s
    except Exception as e:
        db.session.rollback()
        logger.exception("upsert_status failed")
        return False


def delete_status(request: Dict[str, Any]) -> bool:
    try:
        s = Status.query.filter_by(id=request.get('id')).first()
        if not s:
            return False
        db.session.delete(s)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.exception("delete_status failed")
        return False


# ==================================================================================
# FEEDBACKS
# ==================================================================================

def get_feedbacks() -> List[Feedbacks]:
    return Feedbacks.query.all()


def get_feedback(feedback_id: int) -> Optional[Feedbacks]:
    return Feedbacks.query.filter_by(id=feedback_id).first()


def upsert_feedback(request: Dict[str, Any]) -> Union[Feedbacks, bool]:
    try:
        fid = request.get('id')
        if fid:
            f = Feedbacks.query.filter_by(id=fid).first()
            if not f:
                return None
            f.rating = request.get('rating', f.rating)
            f.comment = request.get('comment', f.comment)
            f.customer_id = request.get('customer_id', f.customer_id)
            f.appointment_id = request.get('appointment_id', f.appointment_id)
            db.session.commit()
            return f
        else:
            f = Feedbacks(
                rating=request.get('rating'),
                comment=request.get('comment'),
                customer_id=request.get('customer_id'),
                appointment_id=request.get('appointment_id')
            )
            db.session.add(f)
            db.session.commit()
            return f
    except Exception as e:
        db.session.rollback()
        logger.exception("upsert_feedback failed")
        return False


def delete_feedback(request: Dict[str, Any]) -> bool:
    try:
        f = Feedbacks.query.filter_by(id=request.get('id')).first()
        if not f:
            return False
        db.session.delete(f)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.exception("delete_feedback failed")
        return False


# ==================================================================================
# NOTIFICATIONS
# ==================================================================================

def send_sms(number: str, msg: str) -> bool:
    """
    Stub for SMS sending; integrate provider here.
    """
    logger.info("send_sms stub -> To: %s Msg: %s", number, msg)
    return True


def send_email(request: Dict[str, Any]) -> bool:
    """
    Stub for email sending; integrate provider here.
    """
    logger.info("send_email stub -> %s", request)
    return True


def update_notification(notification_id: int) -> bool:
    try:
        n = Notifications.query.filter_by(id=notification_id).first()
        if not n:
            return False
        n.viewed = True
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.exception("update_notification failed")
        return False


def get_account_notifications(account_id: int) -> List[Notifications]:
    return Notifications.query.filter_by(account_id=account_id).all()


def get_notification(notification_id: int) -> Optional[Notifications]:
    return Notifications.query.filter_by(id=notification_id).first()


def get_notifications() -> List[Notifications]:
    return Notifications.query.all()


def upsert_notification(request: Dict[str, Any]) -> Union[Notifications, bool]:
    try:
        nid = request.get('id')
        if nid:
            n = Notifications.query.filter_by(id=nid).first()
            if not n:
                return None
            n.content = request.get('content', n.content)
            n.notif_type = request.get('notif_type', n.notif_type)
            n.viewed = request.get('viewed', n.viewed)
            n.account_id = request.get('account_id', n.account_id)
            db.session.commit()
            return n
        else:
            n = Notifications(
                content=request.get('content'),
                notif_type=request.get('notif_type'),
                viewed=request.get('viewed', False),
                account_id=request.get('account_id')
            )
            db.session.add(n)
            db.session.commit()
            return n
    except Exception as e:
        db.session.rollback()
        logger.exception("upsert_notification failed")
        return False


def delete_notification(request: Dict[str, Any]) -> bool:
    try:
        n = Notifications.query.filter_by(id=request.get('id')).first()
        if not n:
            return False
        db.session.delete(n)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.exception("delete_notification failed")
        return False


# ==================================================================================
# LOYALTIES
# ==================================================================================

def get_loyalties() -> List[Loyalties]:
    return Loyalties.query.all()


def get_loyalty(loyalty_id: int) -> Optional[Loyalties]:
    return Loyalties.query.filter_by(id=loyalty_id).first()


def upsert_loyalty(request: Dict[str, Any]) -> Union[Loyalties, bool]:
    try:
        lid = request.get('id')
        if lid:
            l = Loyalties.query.filter_by(id=lid).first()
            if not l:
                return None
            l.points = request.get('points', l.points)
            l.note = request.get('note', l.note)
            l.customer_id = request.get('customer_id', l.customer_id)
            db.session.commit()
            return l
        else:
            l = Loyalties(
                points=request.get('points'),
                note=request.get('note'),
                customer_id=request.get('customer_id')
            )
            db.session.add(l)
            db.session.commit()
            return l
    except Exception as e:
        db.session.rollback()
        logger.exception("upsert_loyalty failed")
        return False


def delete_loyalty(request: Dict[str, Any]) -> bool:
    try:
        l = Loyalties.query.filter_by(id=request.get('id')).first()
        if not l:
            return False
        db.session.delete(l)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.exception("delete_loyalty failed")
        return False
    
# =============================================================================================

def get_available_bay_and_staff(start_time, duration, washers_needed, recursion_depth=0):
    """
    Finds an available bay and the required number of staff for a given time slot.
    Utilizes all bays first before stacking appointments, and balances staff assignments
    so that workloads are distributed fairly among on-shift washers.
    """

    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger("auto-booking")

    # # --- Skip past times ---
    # if start_time.replace(second=0, microsecond=0) < datetime.now().replace(second=0, microsecond=0):
    #     return None

    now = start_time
    end_time = start_time + duration
  
    if recursion_depth > 20:
        log.error("Recursion depth exceeded: no available slot found.")
        raise RuntimeError("No available bay or staff found after many attempts.")

    log.info(f"\nChecking slot: {start_time} → {end_time} | Depth: {recursion_depth}")

    # Step 1: Get all bays and on-shift staff
    all_bays = Bays.query.all()
    all_staff = Staffs.query.filter(Staffs.is_on_shift == True, Staffs.is_front_desk == False).all()

    log.info(f"Found {len(all_bays)} total bays, {len(all_staff)} on-shift staff")

    # Pre-compute each staff’s workload (number of appointments today)
    for staff in all_staff:
        staff.daily_appointments = sum(
            1 for a in staff.appointments if a.start_time and a.start_time.date() == now.date() and a.status.id != 5 # Cancelled
        )

    # Pre-compute each bay’s workload (number of appointments today)
    for bay in all_bays:
        bay.daily_appointments = sum(
            1 for a in bay.appointments if a.start_time and a.start_time.date() == now.date() and a.status.id != 5 # Cancelled
        )

    # Sort staff so those with fewer appointments are prioritized
    all_staff.sort(key=lambda s: s.daily_appointments)
    print(all_staff)

    # Sort bay so those with fewer appointments are prioritized
    all_bays.sort(key=lambda b: b.daily_appointments)
    print(all_bays)

    # Step 2: Iterate through all bays (to fully utilize them before stacking)
    for bay in all_bays:

        # Check if bay is busy during this time slot
        bay_busy = any(
            bay_appointment.start_time < end_time and bay_appointment.end_time > start_time and bay_appointment.status.id != 5 # Cancelled
            for bay_appointment in bay.appointments
        )
        if bay_busy:
            log.info(f"Bay '{bay.bay}' is busy during this slot.")
            continue
        else:
            log.info(f"Bay '{bay.bay}' is free.")

        # Step 3: Check staff availability based on schedule and overlaps
        available_staff = []
        for staff in all_staff:
            schedule_today = next(
                (s for s in staff.schedules if s.day.lower() == now.strftime("%A").lower()),
                None
            )
            if not schedule_today:
                continue

            # Check if staff is within shift hours
            if not (schedule_today.shift_start <= now.time() <= schedule_today.shift_end):
                continue

            # Check overlapping appointments
            overlapping = any(
                staff_appointment.start_time <= end_time and staff_appointment.end_time >= start_time and staff_appointment.status.id != 5 # Cancelled
                for staff_appointment in staff.appointments
            )
            if not overlapping:
                available_staff.append(staff)

        log.info(f"🧍Available staff for this slot: {len(available_staff)}")

        # Pick staff with lowest workloads first
        available_staff.sort(key=lambda s: s.daily_appointments)

        if len(available_staff) >= washers_needed:
            chosen_staff = available_staff[:washers_needed]
            staff_names = [f"{s.account.first_name} {s.account.last_name}" for s in chosen_staff]
            log.info(f"Found slot → Bay: {bay.bay}, Staff: {staff_names}")
            return {
                "bay": bay,
                "staff": chosen_staff,
                "start_time": start_time,
                "end_time": end_time
            }

    # Step 4: If no bay/staff combo available, try next slot
    next_bay_free = (
        Appointments.query
        .order_by(Appointments.end_time.asc())
        .filter(Appointments.end_time > now)
        .first()
    )

    if next_bay_free:
        new_start = next_bay_free.end_time + timedelta(minutes=1)
        log.info(f"All bays busy. Trying again after {next_bay_free.end_time}.")
    else:
        new_start = now + timedelta(minutes=1)
        log.info("No existing appointments found. Trying next minute.")

    new_end = new_start + duration

    return get_available_bay_and_staff(new_start, duration, washers_needed, recursion_depth + 1)


def quick_book(service_id, customer_id=None, vehicle_id=None, appointment_date=None):
    """
    Quickly books a appointment.
    Creates temporary account, customer, vehicle, and assigns bay + washers automatically.
    """
    try:
        # Service lookup
        service = Services.query.get(service_id)
        if not service:
            raise ValueError("Invalid service ID")

        duration = timedelta(minutes=service.duration)
        washers_needed = service.washers_needed

        now = datetime.now()
        
        if appointment_date:
            appointment_date = datetime.fromisoformat(appointment_date)

            # Convert appointment_date to datetime if passed as string
            if isinstance(appointment_date, str):
                now = datetime.strptime(appointment_date, "%Y-%m-%d %H:%M")
            else:
                now = appointment_date
                

        now = now.replace(second=0, microsecond=0) # truncate seconds

        # Get available slot
        slot = get_available_bay_and_staff(now, duration, washers_needed)
        if not slot:
            raise ValueError("No available bay or staff found.")

        # Customer lookup
        customer = Customers.query.get(customer_id)
        vehicle = Vehicles.query.get(vehicle_id)

        if not customer:
            
            # Create temporary customer record
            account = Accounts(
                first_name="Walk-in",
                last_name="Customer",
                email=None,
                phone_1=None,
                password_hash=None
            )
            db.session.add(account)
            db.session.flush()

            customer = Customers(account_id=account.id, is_registered=False)
            db.session.add(customer)
            db.session.flush()

        # Create temporary vehicle record
        if not vehicle:
            vehicle = Vehicles(
                model="Unknown",
                type=service.type,
                customer_id=customer.id
            )
            db.session.add(vehicle)
            db.session.flush()

        # Status handling
        status = Status.query.filter_by(status="In Queue").first()

        # Create appointment
        appointment = Appointments(
            start_time=slot["start_time"],
            end_time=slot["end_time"],
            bay_id=slot["bay"].id,
            customer_id=customer.id,
            vehicle_id=vehicle.id,
            service_id=service.id,
            status_id=status.id
        )
        appointment.staffs.extend(slot["staff"])

        db.session.add(appointment)
        db.session.commit()

        return {
            "message": "Walk-in appointment successfully booked!",
            "appointment_id": appointment.id,
            "bay": slot["bay"].bay,
            "staff": [s.account.full_name for s in slot["staff"]],
            "start_time": slot["start_time"].strftime("%Y-%m-%d %H:%M"),
            "end_time": slot["end_time"].strftime("%Y-%m-%d %H:%M"),
            "vehicle_type": vehicle.type
        }

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}


def check_or_suggest_appointment(service_id, appointment_date):
    """
    Checks if the requested appointment datetime for a given service is available.
    - If an exact slot match exists, return it as available.
    - Otherwise, return nearest suggested times.
    """

    try:

        if appointment_date:
            appointment_date = datetime.fromisoformat(appointment_date)

            # --- Parse appointment datetime ---
            if isinstance(appointment_date, str):
                appointment_date = datetime.strptime(appointment_date, "%Y-%m-%d %H:%M")

        # # --- Skip past times ---
        # if appointment_date < datetime.now():
        #     raise ValueError("Invalid appointment date")

        # --- Fetch service ---
        service = Services.query.get(service_id)
        if not service:
            raise ValueError("Invalid service ID")

        duration = timedelta(minutes=service.duration)
        washers_needed = service.washers_needed

        # --- Check exact slot availability ---
        slot = get_available_bay_and_staff(appointment_date, duration, washers_needed)
        if slot:
            if slot['start_time'] == appointment_date:
                return {
                    "available": True,
                    "message": "The selected appointment time is available!",
                    "service": service.name,
                    "slot": {
                        "start_time": slot["start_time"].strftime("%Y-%m-%d %I:%M %p"),
                        "end_time": slot["end_time"].strftime("%Y-%m-%d %I:%M %p"),
                        "schedule": f"{slot['start_time'].strftime('%a %b %d, %Y %I:%M %p')} - {slot['end_time'].strftime('%I:%M %p')}",
                        "bay": slot["bay"].bay,
                        "staff": [s.account.full_name for s in slot["staff"]],
                    }
                }                

        # --- If no exact slot, generate nearest suggestions ---
        slots = 1
        suggestions = []
        search_step = timedelta(minutes=30)   # step between search intervals
        max_attempts = 40                     # up to 40 half-hour checks (20 forward + 20 backward)
        attempts = 0
        checked_times = set()

        # %a %b %d, %Y %I:%M %p
        # append the slot returned after finding exact slot
        if slot:
            suggestions.append({
                "start_time": slot["start_time"].strftime("%Y-%m-%d %I:%M %p"),
                "end_time": slot["end_time"].strftime("%Y-%m-%d %I:%M %p"),
                "schedule": f"{slot['start_time'].strftime('%a %b %d, %Y %I:%M %p')} - {slot['end_time'].strftime('%I:%M %p')}",
                "bay": slot["bay"].bay,
                "staff": [s.account.full_name for s in slot["staff"]],
            })

        # if no slot returned, find another
        while len(suggestions) < slots and attempts < max_attempts:
            attempts += 1

            # Alternate forward and backward checking
            for direction in [1, -1]:
                delta = search_step * attempts * direction
                test_time = appointment_date + delta
                test_time = test_time.replace(second=0, microsecond=0) # truncate seconds

                # Avoid duplicates
                if test_time in checked_times:
                    continue
                checked_times.add(test_time)

                # --- Skip past times ---
                if test_time < datetime.now().replace(second=0, microsecond=0):
                    continue

                test_slot = get_available_bay_and_staff(test_time, duration, washers_needed)
                if test_slot:
                    if test_slot['start_time'] == test_time:
                        suggestions.append({
                            "start_time": test_slot["start_time"].strftime("%Y-%m-%d %I:%M %p"),
                            "end_time": test_slot["end_time"].strftime("%Y-%m-%d %I:%M %p"),
                            "schedule": f"{slot['start_time'].strftime('%a %b %d, %Y %I:%M %p')} - {slot['end_time'].strftime('%I:%M %p')}",
                            "bay": test_slot["bay"].bay,
                            "staff": [s.account.full_name for s in test_slot["staff"]],
                        })

                if len(suggestions) >= slots:
                    break

        return {
            "available": False,
            "message": "The requested time is not available.",
            "service": service.name,
            "suggestions": sorted(suggestions, key=lambda s: s["start_time"])[:slots],
        }

    except Exception as e:
        return {"error": str(e)}


def confirm_suggested_appointment(customer_id, vehicle_id, start_time):
    """
    Confirms and books one of the suggested appointment slots.
    Re-validates that the chosen slot is still available before booking.
    Then creates notifications for customer and assigned staff.
    """

    try:
        # --- Lookup customer and vehicle ---
        customer = Customers.query.get(customer_id)
        vehicle = Vehicles.query.get(vehicle_id)
        if not customer or not vehicle:
            raise ValueError("Invalid customer or vehicle ID")

        # --- Handle unregistered customer (create dummy account if needed) ---
        if not customer.is_registered and not customer.account_id:
            dummy_account = Accounts(
                first_name="Guest",
                last_name="Customer",
                email=None,
                phone_1=None,
                password_hash=None
            )
            db.session.add(dummy_account)
            db.session.flush()
            customer.account_id = dummy_account.id

        # --- Parse start_time ---
        if isinstance(start_time, str):
            start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M")

        # --- Auto-select service based on vehicle type ---
        vehicle_type = (vehicle.type or "").lower()
        if "motor" in vehicle_type or "bike" in vehicle_type:
            service = Services.query.filter(Services.name.ilike("%bike%")).first()
        else:
            service = Services.query.filter(Services.name.ilike("%car%")).first()

        if not service:
            raise ValueError(f"No matching service found for vehicle type '{vehicle_type}'")

        duration = timedelta(minutes=service.duration)
        washers_needed = service.washers_needed
        end_time = start_time + duration

        # --- Double-check availability ---
        slot = get_available_bay_and_staff(start_time, duration, washers_needed)
        if not slot:
            raise ValueError("The selected time slot is no longer available. Please pick another one.")

        # --- Confirm bay, staff, and status ---
        status = Status.query.filter_by(status="In Queue").first()
        if not status:
            status = Status(status="In Queue")
            db.session.add(status)
            db.session.flush()

        appointment = Appointments(
            start_time=slot["start_time"],
            end_time=slot["end_time"],
            bay_id=slot["bay"].id,
            customer_id=customer.id,
            vehicle_id=vehicle.id,
            service_id=service.id,
            status_id=status.id
        )
        appointment.staffs.extend(slot["staff"])

        db.session.add(appointment)
        db.session.flush()  # flush so appointment.id becomes available

        # --- Create notifications ---
        notif_message = (
            f"Your appointment for {vehicle.type or 'your vehicle'} "
            f"is confirmed on {slot['start_time'].strftime('%b %d, %Y %I:%M %p')} "
            f"at Bay {slot['bay'].bay}."
        )

        # Customer notification
        customer_notif = Notifications(
            account_id=customer.account_id,
            title="Appointment Confirmed",
            message=notif_message,
            is_read=False
        )
        db.session.add(customer_notif)

        # Staff notifications
        for staff in slot["staff"]:
            staff_notif = Notifications(
                account_id=staff.account_id,
                title="New Appointment Assigned",
                message=(
                    f"You’ve been assigned to an appointment for {vehicle.type or 'a vehicle'} "
                    f"on {slot['start_time'].strftime('%b %d, %Y %I:%M %p')} at Bay {slot['bay'].bay}."
                ),
                is_read=False
            )
            db.session.add(staff_notif)

        # --- Commit all changes ---
        db.session.commit()

        return {
            "message": "Appointment successfully confirmed and notifications sent!",
            "appointment_id": appointment.id,
            "customer_name": customer.account.full_name if customer.account else "Guest Customer",
            "bay": slot["bay"].bay,
            "staff": [s.account.full_name for s in slot["staff"]],
            "service": service.name,
            "start_time": slot["start_time"].strftime("%Y-%m-%d %H:%M"),
            "end_time": slot["end_time"].strftime("%Y-%m-%d %H:%M"),
            "vehicle_type": vehicle.type
        }

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}


def book_appointment_with_service(customer_id, service_id, appointment_date):
    """
    Books an appointment for an existing customer using the next available bay and staff.
    Automatically creates a temporary vehicle and queues the appointment.
    """
    try:
        logging.basicConfig(level=logging.INFO)
        log = logging.getLogger("customer-booking")

        # --- Step 1: Validate inputs ---
        customer = Customers.query.get(customer_id)
        if not customer:
            raise ValueError("Invalid customer ID")

        service = Services.query.get(service_id)
        if not service:
            raise ValueError("Invalid service ID")

        duration = timedelta(minutes=service.duration)
        washers_needed = service.washers_needed

        # --- Step 2: Determine appointment start datetime ---
        if isinstance(appointment_date, str):
            appointment_date = datetime.strptime(appointment_date, "%Y-%m-%d %H:%M")

        # --- Step 3: Find next available slot ---
        slot = get_available_bay_and_staff(appointment_date, duration, washers_needed)
        if not slot:
            raise ValueError("No available bay or staff found for this date.")
        
        # if slot.start_time != appointment_date:
            

        # --- Step 4: Create dummy vehicle (auto-tagged to customer) ---
        dummy_vehicle = Vehicles(
            model="Unknown",
            type="Motorcycle" if washers_needed == 1 else "Car",
            customer_id=customer.id
        )
        db.session.add(dummy_vehicle)
        db.session.flush()

        # --- Step 5: Determine initial appointment status ---
        status = Status.query.filter_by(status="In Queue").first()
        if not status:
            raise ValueError("Missing 'In Queue' status record in database.")

        # --- Step 6: Create appointment record ---
        appointment = Appointments(
            start_time=slot["start_time"],
            end_time=slot["end_time"],
            bay_id=slot["bay"].id,
            customer_id=customer.id,
            vehicle_id=dummy_vehicle.id,
            service_id=service.id,
            status_id=status.id
        )
        appointment.staffs.extend(slot["staff"])

        db.session.add(appointment)
        db.session.commit()

        # --- Step 7: Return structured response ---
        return {
            "message": "Appointment successfully booked for existing customer!",
            "appointment_id": appointment.id,
            "customer_name": customer.account.full_name,
            "bay": slot["bay"].bay,
            "staff": [s.account.full_name for s in slot["staff"]],
            "service": service.name,
            "start_time": slot["start_time"].strftime("%Y-%m-%d %H:%M"),
            "end_time": slot["end_time"].strftime("%Y-%m-%d %H:%M"),
            "vehicle_type": dummy_vehicle.type
        }

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}


def book_existing_customer(customer_id, vehicle_id, appointment_date):
    """
    Books an appointment for an existing customer.
    If customer is not registered, creates a temporary dummy account.
    Automatically selects service based on vehicle type and finds next available slot.
    """

    try:
        # Lookup customer and vehicle
        customer = Customers.query.get(customer_id)
        vehicle = Vehicles.query.get(vehicle_id)

        if not customer or not vehicle:
            raise ValueError("Invalid customer or vehicle ID")

        # If customer is not registered, create a dummy account
        if not customer.is_registered:
            dummy_account = Accounts(
                first_name="Guest",
                last_name="Customer",
                email=None,
                phone_1=None,
                password_hash=None
            )
            db.session.add(dummy_account)
            db.session.flush()
            customer.account_id = dummy_account.id

        # Determine service based on vehicle type
        vehicle_type = (vehicle.type or "").lower()
        if "motor" in vehicle_type or "bike" in vehicle_type:
            service = Services.query.filter(Services.name.ilike("%bike%")).first()
        else:
            service = Services.query.filter(Services.name.ilike("%car%")).first()

        if not service:
            raise ValueError(f"No matching service found for vehicle type '{vehicle_type}'")

        duration = timedelta(minutes=service.duration)
        washers_needed = service.washers_needed

        # Convert appointment_date to datetime if needed
        if isinstance(appointment_date, str):
            appointment_date = datetime.strptime(appointment_date, "%Y-%m-%d %H:%M")

        # Find available bay and staff (start from appointment_date)
        slot = get_available_bay_and_staff(appointment_date, duration, washers_needed)
        if not slot:
            raise ValueError("No available bay or staff found for this time.")

        # Get 'In Queue' or default status
        status = Status.query.filter_by(status="In Queue").first()
        if not status:
            status = Status(status="In Queue")
            db.session.add(status)
            db.session.flush()

        # Create appointment
        appointment = Appointments(
            start_time=slot["start_time"],
            end_time=slot["end_time"],
            bay_id=slot["bay"].id,
            customer_id=customer.id,
            vehicle_id=vehicle.id,
            service_id=service.id,
            status_id=status.id
        )
        appointment.staffs.extend(slot["staff"])

        db.session.add(appointment)
        db.session.commit()

        return {
            "message": f"Appointment booked successfully for customer ID {customer_id}",
            "appointment_id": appointment.id,
            "customer_name": customer.account.full_name if customer.account else "Guest Customer",
            "bay": slot["bay"].bay,
            "staff": [s.account.full_name for s in slot["staff"]],
            "service": service.name,
            "start_time": slot["start_time"].strftime("%Y-%m-%d %H:%M"),
            "end_time": slot["end_time"].strftime("%Y-%m-%d %H:%M"),
            "vehicle_type": vehicle.type
        }

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}


def suggest_appointments_for_customer(customer_id, vehicle_id, appointment_date):
    """
    Suggests up to 5 available appointment slots for an existing customer.
    If the customer is not registered, creates a dummy account.
    Auto-selects service based on vehicle type and finds the nearest available slots
    starting from the given appointment_date.
    """

    try:
        # Validate inputs
        customer = Customers.query.get(customer_id)
        vehicle = Vehicles.query.get(vehicle_id)
        if not customer or not vehicle:
            raise ValueError("Invalid customer or vehicle ID")

        # If customer is not registered, create a dummy account
        if not customer.is_registered:
            dummy_account = Accounts(
                first_name="Guest",
                last_name="Customer",
                email=None,
                phone_1=None,
                password_hash=None
            )
            db.session.add(dummy_account)
            db.session.flush()
            customer.account_id = dummy_account.id

        # Determine service based on vehicle type
        vehicle_type = (vehicle.type or "").lower()
        if "motor" in vehicle_type or "bike" in vehicle_type:
            service = Services.query.filter(Services.name.ilike("%bike%")).first()
        else:
            service = Services.query.filter(Services.name.ilike("%car%")).first()

        if not service:
            raise ValueError(f"No matching service found for vehicle type '{vehicle_type}'")

        # Convert appointment_date to datetime if passed as string
        if isinstance(appointment_date, str):
            appointment_date = datetime.strptime(appointment_date, "%Y-%m-%d %H:%M")

        duration = timedelta(minutes=service.duration)
        washers_needed = service.washers_needed

        # Prepare suggestion list
        suggestions = []
        check_time = appointment_date

        # Loop to find 5 valid available slots
        while len(suggestions) < 5:
            slot = get_available_bay_and_staff(check_time, duration, washers_needed)
            if not slot:
                break

            # Avoid duplicate times if recursion returns same slot
            if any(s["start_time"] == slot["start_time"] for s in suggestions):
                check_time += timedelta(minutes=service.duration)
                continue

            suggestions.append({
                "bay": slot["bay"].bay,
                "staff": [s.account.full_name for s in slot["staff"]],
                "start_time": slot["start_time"].strftime("%Y-%m-%d %H:%M"),
                "end_time": slot["end_time"].strftime("%Y-%m-%d %H:%M"),
                "vehicle_type": vehicle.type,
                "service": service.name
            })

            # Move forward to the next possible slot (end of this one + 1 min)
            check_time = slot["end_time"] + timedelta(minutes=1)

        if not suggestions:
            return {"message": "No available slots found near the given date."}

        return {
            "customer_name": customer.account.full_name if customer.account else "Guest Customer",
            "vehicle_type": vehicle.type,
            "service": service.name,
            "suggestions": suggestions
        }

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}
    
    from datetime import datetime

