from datetime import datetime
from typing import Optional
from sqlalchemy import and_
from data import db 
from data.models import  (
    Accounts, Customers, Staffs, Appointments, Payments, Services,
    Vehicles, Bays, Roles, Status, Notifications, Feedbacks, Loyalties,
    Schedules
)

class Appointment:

    def get_appointment_by_id(appointment_id: int) -> Optional[Appointments]:
        """Return a single appointment or None."""
        return Appointments.query.filter_by(id=appointment_id).first()
    
    def set_appointment_status(appointment_id: int, status_id: int) -> None:
        """Update the status of an appointment."""
        try:
            appointment = Appointments.query.filter_by(id=appointment_id).first()
            if not appointment:                
                return None
            appointment.status_id = status_id
            db.session.commit()
            return appointment
        except Exception as e:
            db.session.rollback()
            return False
        
    def add_payment(appointment_id: int, amount: float) -> None:
        """Update the status of an appointment."""
        try:
            appointment = Appointments.query.filter_by(id=appointment_id).first()
            if not appointment:                
                return None
            if amount > 0:
                appointment.payments.extend(Payments(amount=amount))
                db.session.commit()
            return appointment
        except Exception as e:
            db.session.rollback()
            return False
        