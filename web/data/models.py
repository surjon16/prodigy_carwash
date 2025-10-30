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

    # login
    email = db.Column(db.String(100))
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
    notifications = db.relationship('Notifications', back_populates='account', cascade="all, delete-orphan", lazy='dynamic')

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

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'first_name': self.first_name,
            'middle_name': self.middle_name,
            'last_name': self.last_name,
            'gender': self.gender,
            'phone_1': self.phone_1,
            'phone_2': self.phone_2,
            'birth_date': self.birth_date.strftime('%m/%d/%Y') if self.birth_date else None,
            'email': self.email,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'address': self.address,
            'role': self.role.role if self.role else None,
            'role_id': self.role_id
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

    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True)
    account = db.relationship("Accounts", back_populates="notifications")

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

# =============================================================
# LOGIN MANAGER
# =============================================================
@login_manager.user_loader
def load_user(id):
    return Accounts.query.get(int(id))
