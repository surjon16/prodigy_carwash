
from typing import Optional
from data.models import  (
    Accounts, Customers, Staffs, Appointments, Payments, Services,
    Vehicles, Bays, Roles, Status, Notifications, Feedbacks, Loyalties,
    Schedules
)

class Staff:

    def get_staff_appointments(staff_id: int) -> Optional[Appointments]:
        """Return a single account or None."""
        return Staffs.query.filter_by(id=staff_id).first().appointments