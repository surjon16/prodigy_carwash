from datetime import time
from data import db, login_manager
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# =============================================================
# ASSOCIATION TABLES
# =============================================================
washers = db.Table(
    'washers',
    db.Column('staff_id', db.Integer, db.ForeignKey('staffs.id'), primary_key=True),
    db.Column('appointment_id', db.Integer, db.ForeignKey('appointments.id'), primary_key=True)
)

# =============================================================
# ACCOUNTS
# =============================================================
class Accounts(UserMixin, db.Model):
    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    middle_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    gender = db.Column(db.String(10))
    phone_1 = db.Column(db.String(15))
    phone_2 = db.Column(db.String(15))
    birth_date = db.Column(db.DateTime)
    address = db.Column(db.String(100))
    image_profile = db.Column(db.String(128), default="img/no-photo.jpg")
    token = db.Column(db.String(500), nullable=True)

    # login
    email = db.Column(db.String(100), unique=True, nullable=True)
    password_hash = db.Column(db.String(128))

    # additional_conditions
    is_active = db.Column(db.Boolean, default=True)

    # timestamps
    login_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # relationships
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=True)
    customer = db.relationship('Customers', uselist=False, back_populates='account', cascade="all, delete-orphan")
    staff = db.relationship('Staffs', uselist=False, back_populates='account', cascade="all, delete-orphan")
    sent = db.relationship('Notifications', back_populates='sender', cascade="all, delete-orphan", lazy='dynamic', foreign_keys='Notifications.sender_id')
    inbox = db.relationship('Notifications', back_populates='recipient', cascade="all, delete-orphan", lazy='dynamic', foreign_keys='Notifications.recipient_id')

    # Password management
    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute.')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @hybrid_property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def to_json(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'middle_name': self.middle_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'gender': self.gender,
            'phone_1': self.phone_1,
            'phone_2': self.phone_2,
            'birth_date': self.birth_date.strftime('%Y-%m-%d') if self.birth_date else None,
            'email': self.email,
            'address': self.address,
            'image_profile': self.image_profile,
            'is_active': self.is_active,
            'role': self.role.role if self.role else None,
            'role_id': self.role_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# =============================================================
# CUSTOMERS
# =============================================================
class Customers(UserMixin, db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # flags
    is_registered = db.Column(db.Boolean, default=False)
    is_pwd = db.Column(db.Boolean, default=False)
    is_senior = db.Column(db.Boolean, default=False)

    # parent
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), unique=True, nullable=False)

    # relationships
    account = db.relationship('Accounts', back_populates='customer')
    vehicles = db.relationship('Vehicles', back_populates='owner', cascade="all, delete-orphan")
    feedbacks = db.relationship('Feedbacks', back_populates='customer', cascade="all, delete-orphan")
    appointments = db.relationship('Appointments', back_populates='customer', cascade="all, delete-orphan")
    loyalties = db.relationship('Loyalties', back_populates='customer', cascade="all, delete-orphan")

    def to_json(self):
        return {
            'id': self.id,
            'is_registered': self.is_registered,
            'is_pwd': self.is_pwd,
            'is_senior': self.is_senior,
            'account': self.account.to_json() if self.account else None,
            'vehicles': [v.to_json() for v in self.vehicles],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
# =============================================================
# STAFFS
# =============================================================
class Staffs(UserMixin, db.Model):
    __tablename__ = 'staffs'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # flags
    is_front_desk = db.Column(db.Boolean, default=False)
    is_on_shift = db.Column(db.Boolean, default=False)

    # parent
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), unique=True, nullable=False)

    # relationships
    account = db.relationship('Accounts', back_populates='staff')
    appointments = db.relationship('Appointments', secondary=washers, back_populates='staffs', lazy='subquery')
    schedules = db.relationship('Schedules', back_populates='staff', cascade="all, delete-orphan")
    
    @hybrid_method
    def shift(self, day):
        return next((s.shift for s in self.schedules if s.day.lower() == day.lower()), None)

    def to_json(self):
        return {
            'id': self.id,
            'is_front_desk': self.is_front_desk,
            'is_on_shift': self.is_on_shift,
            'account': self.account.to_json() if self.account else None,
            'schedules': [s.to_json() for s in self.schedules],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# =============================================================
# STAFF SCHEDULES
# =============================================================
class Schedules(UserMixin, db.Model):
    __tablename__ = 'schedules'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # shift schedule
    shift_start = db.Column(db.Time, default=time(8, 0))    # 8:00 AM
    shift_end   = db.Column(db.Time, default=time(17, 0))   # 5:00 PM
    day         = db.Column(db.String(10))

    # parent
    staff_id = db.Column(db.Integer, db.ForeignKey('staffs.id'), nullable=False)

    # relationships
    staff = db.relationship('Staffs', back_populates='schedules')

    @hybrid_property
    def shift(self):
        return f'{self.shift_start.strftime("%I:%M %p") } - {self.shift_end.strftime("%I:%M %p") }'

    def to_json(self):
        return {
            'id': self.id,
            'day': self.day,
            'shift_start': self.shift_start.strftime('%H:%M') if self.shift_start else None,
            'shift_end': self.shift_end.strftime('%H:%M') if self.shift_end else None,
            'shift': self.shift,
            'staff_id': self.staff_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
# =============================================================
# APPOINTMENTS
# =============================================================
class Appointments(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)

    # Foreign keys
    bay_id = db.Column(db.Integer, db.ForeignKey("bays.id"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    status_id = db.Column(db.Integer, db.ForeignKey('status.id'), nullable=False)

    # relationships
    customer = db.relationship('Customers', back_populates='appointments')
    staffs = db.relationship('Staffs', secondary=washers, back_populates='appointments')
    feedbacks = db.relationship('Feedbacks', back_populates='appointment', cascade="all, delete-orphan")
    payments = db.relationship('Payments', back_populates='appointment', cascade="all, delete-orphan")
    status = db.relationship('Status', back_populates='appointments')
    service = db.relationship('Services', back_populates='appointments')
    bay = db.relationship('Bays', back_populates='appointments')
    vehicle = db.relationship('Vehicles', back_populates='appointments')

    def to_json(self):
        return {
            'id': self.id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'bay': self.bay.to_json() if self.bay else None,
            'customer': self.customer.account.to_json() if self.customer and self.customer.account else None,
            'vehicle': self.vehicle.to_json() if self.vehicle else None,
            'service': self.service.to_json() if self.service else None,
            'status': self.status.to_json() if self.status else None,
            'staffs': [s.account.to_json() for s in self.staffs],
            'payments': [p.to_json() for p in self.payments],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
# =============================================================
# PAYMENTS
# =============================================================
class Payments(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    method = db.Column(db.Enum('xendit', 'gcash', 'cash', name='payment_method'))
    transaction_no = db.Column(db.String(20), nullable=True)
    image_payment = db.Column(db.String(128), default="img/txn/no-photo.jpg")
    amount = db.Column(db.Numeric(10, 2), nullable=False)

    # timestamps
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Foreign key
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    status_id = db.Column(db.Integer, db.ForeignKey('status.id'), nullable=False)

    # relationships
    appointment = db.relationship('Appointments', back_populates='payments')
    status = db.relationship('Status', back_populates='payments')

    def to_json(self):
        return {
            'id': self.id,
            'method': self.method,
            'transaction_no': self.transaction_no,
            'image_payment': self.image_payment,
            'amount': float(self.amount),
            'status': self.status.to_json() if self.status else None,
            'appointment_id': self.appointment_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
# =============================================================
# SERVICES
# =============================================================
class Services(db.Model):
    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Numeric, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    washers_needed = db.Column(db.Integer, default=1)
    type = db.Column(db.String(50), nullable=True)

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    appointments = db.relationship('Appointments', back_populates='service', cascade="all, delete-orphan")

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price),
            'duration': self.duration,
            'washers_needed': self.washers_needed,
            'type': self.type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
# =============================================================
# VEHICLES
# =============================================================
class Vehicles(db.Model):
    __tablename__ = 'vehicles'

    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(20), unique=True, nullable=True)
    model = db.Column(db.String(100), nullable=True)
    type = db.Column(db.String(50), nullable=True)

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)

    owner = db.relationship("Customers", back_populates="vehicles")
    appointments = db.relationship("Appointments", back_populates="vehicle", cascade="all, delete-orphan")

    def to_json(self):
        return {
            'id': self.id,
            'plate_number': self.plate_number,
            'model': self.model,
            'type': self.type,
            'customer_id': self.customer_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
# =============================================================
# BAYS
# =============================================================
class Bays(db.Model):
    __tablename__ = 'bays'

    id = db.Column(db.Integer, primary_key=True)
    bay = db.Column(db.String(20))

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    appointments = db.relationship("Appointments", back_populates="bay", cascade="all, delete-orphan")

    def to_json(self):
        return {
            'id': self.id,
            'bay': self.bay,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
# =============================================================
# ROLES
# =============================================================
class Roles(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20))

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    accounts = db.relationship('Accounts', backref='role', lazy='dynamic')

    def to_json(self):
        return {
            'id': self.id,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
# =============================================================
# STATUS
# =============================================================
class Status(db.Model):
    __tablename__ = 'status'

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    appointments = db.relationship('Appointments', back_populates='status', lazy='dynamic')
    payments = db.relationship('Payments', back_populates='status', lazy='dynamic')

    def to_json(self):
        return {
            'id': self.id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
# =============================================================
# NOTIFICATIONS
# =============================================================
class Notifications(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    notif_type = db.Column(db.String(20))
    viewed = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    recipient_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True)
    recipient = db.relationship("Accounts", back_populates="inbox", foreign_keys=[recipient_id])

    sender_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True)
    sender = db.relationship("Accounts", back_populates="sent", foreign_keys=[sender_id])

    def to_json(self):
        return {
            'id': self.id,
            'content': self.content,
            'notif_type': self.notif_type,
            'viewed': self.viewed,
            'recipient_id': self.recipient_id,
            'recipient': self.recipient.to_json() if self.recipient else None,
            'sender_id': self.sender_id,
            'sender': self.sender.to_json() if self.sender else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
# =============================================================
# FEEDBACKS
# =============================================================
class Feedbacks(db.Model):
    __tablename__ = 'feedbacks'

    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)

    customer = db.relationship("Customers", back_populates="feedbacks")
    appointment = db.relationship("Appointments", back_populates="feedbacks")

    def to_json(self):
        return {
            'id': self.id,
            'rating': self.rating,
            'comment': self.comment,
            'customer_id': self.customer_id,
            'appointment_id': self.appointment_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
# =============================================================
# LOYALTIES
# =============================================================
class Loyalties(db.Model):
    __tablename__ = 'loyalties'

    id = db.Column(db.Integer, primary_key=True)
    points = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    customer = db.relationship("Customers", back_populates="loyalties")

    def to_json(self):
        return {
            'id': self.id,
            'points': self.points,
            'note': self.note,
            'customer_id': self.customer_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
# =============================================================
# LOGIN MANAGER
# =============================================================
@login_manager.user_loader
def load_user(id):
    return Accounts.query.get(int(id))
