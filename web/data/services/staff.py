from datetime import datetime
from typing import Optional
from sqlalchemy import and_
from data import db 
from data.models import  (
    Accounts, Customers, Staffs, Appointments, Payments, Services,
    Vehicles, Bays, Roles, Status, Notifications, Feedbacks, Loyalties,
    Schedules
)

class Staff:

    def get_staff_by_account_id(account_id: int) -> Optional[Staffs]:
        """Return a single staff or None."""
        return Staffs.query.filter_by(account_id=account_id).first()
    

    def get_all_staff_schedules() -> list:
        """Return all staff schedules."""

        schedules = Schedules.query.order_by(Schedules.day.asc(), Schedules.shift_start.asc()).all()
        return schedules

    def get_staff_appointments(staff_id: int) -> Optional[Appointments]:
        """Return staff appointments or None."""
        return Staffs.query.filter_by(id=staff_id).first().appointments
    
    
    def get_staffs_on_duty() -> list:
        """
        Returns a list of staff members who are currently on duty
        based on their schedule (day + shift time), sorted by shift_start.
        """

        now = datetime.now()
        current_day = now.strftime('%A')   # e.g., 'Monday'
        current_time = now.time()

        # Query all schedules for today whose time range includes the current time
        active_schedules = (
            Schedules.query
            .join(Staffs)
            .filter(
                db.func.lower(Schedules.day) == current_day.lower(),
                and_(
                    Schedules.shift_start <= current_time,
                    Schedules.shift_end >= current_time
                )
            )
            .order_by(Schedules.shift_start.asc())  # Sort by earliest shift first
            .all()
        )

        # Return structured list of staff info
        staffs_on_duty = [
            {
                "staff_id": sched.staff.id,
                "full_name": sched.staff.account.full_name,
                "shift": sched.shift,
                "is_front_desk": "Yes" if sched.staff.is_front_desk else "No",
                "is_on_shift": "Yes" if sched.staff.is_on_shift else "No",
            }
            for sched in active_schedules
        ]

        return staffs_on_duty
    
    def get_staff_schedule_matrix():
        """
        Returns a list of staff schedules in a tabular format:
        [
            {
                'staff_name': 'John Doe',
                'Monday': '08:00 AM - 05:00 PM',
                'Tuesday': '08:00 AM - 05:00 PM',
                ...
            },
            ...
        ]
        """
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        table = []

        staffs = Staffs.query.all()  # fetch all staff

        for staff in staffs:
            row = {
                'staff_id': staff.id,
                'staff_name': staff.account.full_name
            }
            for day in days_of_week:
                schedule = next((s for s in staff.schedules if s.day.lower() == day.lower()), None)
                row[day] = schedule.shift if schedule else None
            table.append(row)

        return table

    
    def get_staff_bay_appointments(staff_id: int) -> dict:
        """
        Returns a structured table (dict) showing all bays and the given staff's
        appointments (today + upcoming), arranged chronologically.
        Appointments starting at the same time are aligned in the same row.
        Blank cells indicate no booking for that bay/time.
        """
        now = datetime.now()

        # Get staff record
        staff = Staffs.query.get(staff_id)
        print(staff.account.full_name)
        if not staff:
            return {"columns": [], "rows": []}

        # Get all bays
        bays = Bays.query.all()
        bay_names = [bay.bay for bay in bays]

        # Filter staff's appointments (today and upcoming only)
        staff_appointments = [
            appt for appt in staff.appointments
            if appt.start_time and appt.start_time.day == now.day
        ]
        if not staff_appointments:
            return {"columns": bay_names, "rows": []}

        # Sort by start time
        staff_appointments.sort(key=lambda a: a.start_time)

        # Group appointments by start_time
        grouped_by_time = {}
        for appt in staff_appointments:
            key = appt.start_time.strftime("%Y-%m-%d %H:%M")
            if key not in grouped_by_time:
                grouped_by_time[key] = {}
            grouped_by_time[key][appt.bay.bay] = appt

        # Build table rows
        table_rows = []
        for time_key in sorted(grouped_by_time.keys()):
            time_group = grouped_by_time[time_key]
            row = []
            for bay in bays:
                appt = time_group.get(bay.bay)
                if appt:
                    row.append(appt)
                else:
                    row.append(None)
            table_rows.append(row)

        return {
            "columns": bay_names,  # Bay headers
            "rows": table_rows     # Chronological, aligned rows
        }


    def get_bay_appointments() -> dict:
        """
        Returns a structured table (dict) showing all bays and their appointments
        for today and upcoming dates, sorted chronologically by start_time.
        Appointments with the same start time appear on the same row.
        Blank cells are left for bays with no booking at that time.
        """
        now = datetime.now()

        bays = Bays.query.all()
        bay_names = [bay.bay for bay in bays]

        # Collect all appointments across all bays (today + upcoming)
        all_appointments = []
        for bay in bays:
            for appt in bay.appointments:
                if appt.start_time and appt.start_time.day == now.day:
                    all_appointments.append(appt)

        # Sort all appointments by start time
        all_appointments.sort(key=lambda a: a.start_time)

        # Group appointments by their exact start time
        grouped_by_time = {}
        for appt in all_appointments:
            key = appt.start_time.strftime("%Y-%m-%d %H:%M")
            if key not in grouped_by_time:
                grouped_by_time[key] = {}
            grouped_by_time[key][appt.bay.bay] = appt

        # Build table rows
        table_rows = []
        for time_key in sorted(grouped_by_time.keys()):
            time_group = grouped_by_time[time_key]
            row = []
            for bay in bays:
                appt = time_group.get(bay.bay)
                if appt:
                    row.append(appt)
                else:
                    row.append(None)
            table_rows.append(row)

        return {
            "columns": bay_names,  # Bay headers
            "rows": table_rows     # Chronological rows
        }


    def mark_staff_on_shift(staff_id: int, on_shift: bool) -> None:
        """Mark a staff member as on shift or off shift."""
        staff = Staffs.query.filter_by(id=staff_id).first()
        if staff:
            staff.is_on_shift = on_shift
            db.session.commit()

    def mark_all_staff_off_shift() -> None:
        """Mark all staff members as off shift."""
        staffs = Staffs.query.all()
        for staff in staffs:
            staff.is_on_shift = False
        db.session.commit()

    def mark_all_washers_off_shift() -> None:
        """Mark all washer staff members as off shift."""
        washers = Staffs.query.filter_by(is_front_desk=False).all()
        for washer in washers:
            washer.is_on_shift = False
        db.session.commit()

    def mark_all_front_desk_off_shift() -> None:
        """Mark all front desk staff members as off shift."""
        front_desk_staff = Staffs.query.filter_by(is_front_desk=True).all()
        for staff in front_desk_staff:
            staff.is_on_shift = False
        db.session.commit()

    def set_staff_schedule(staff_id: int, day: str, shift_start: datetime.time, shift_end: datetime.time) -> None:
        """Set or update a washer's schedule for a specific day."""
        schedule = Schedules.query.filter_by(staff_id=staff_id, day=day).first()
        if schedule:
            schedule.shift_start = shift_start
            schedule.shift_end = shift_end
        else:
            new_schedule = Schedules(
                staff_id=staff_id,
                day=day,
                shift_start=shift_start,
                shift_end=shift_end
            )
            db.session.add(new_schedule)
        db.session.commit()