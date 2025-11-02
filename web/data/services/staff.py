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

    def get_staff_appointments(staff_id: int) -> Optional[Appointments]:
        """Return a single account or None."""
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
