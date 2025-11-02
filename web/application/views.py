from flask import (
    flash, render_template, request, redirect, url_for, Blueprint
)
from flask_login import (
    login_required, login_user, logout_user, current_user
)
from marshmallow import EXCLUDE
from datetime import datetime
from functools import wraps

from application import app
from data.repo import *
from data.services.staff import Staff
from data.services.customer import Customer

# ===============================================================
# HELPERS
# ===============================================================

def humanize_ts(timestamp):
    now = datetime.today()
    delta = now - timestamp
    
    if delta.days > 365:
        years = delta.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif delta.days >= 30:
        months = delta.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif delta.days >= 1:
        days = delta.days
        return f"{days} day{'s' if days > 1 else ''} ago"
    elif delta.total_seconds() >= 3600:
        hours = delta.total_seconds() // 3600
        return f"{int(hours)} hr{'s' if hours > 1 else ''}"
    elif delta.total_seconds() >= 60:
        minutes = delta.total_seconds() // 60
        return f"{int(minutes)}m"
    else:
        return "just now"
    
app.jinja_env.filters['humanize_ts'] = humanize_ts

# ===============================================================
# CONTEXT PROCESSOR
# ===============================================================

@app.context_processor
def inject_now():
    return {'now': datetime.today()}


# ===============================================================
# ROLE-BASED ACCESS DECORATORS
# ===============================================================

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role_id != 1:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper


def staff_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role_id != 2:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper


def customer_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role_id != 3:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper


# ===============================================================
# COMMON ROUTES (LOGIN / REGISTER / HOME)
# ===============================================================

@app.route('/')
@login_required
def home():
    if current_user.role_id == 1:
        return redirect(url_for('admin_home'))
    elif current_user.role_id == 2:
        return redirect(url_for('staff_home'))
    else:
        return redirect(url_for('customer_home'))


@app.route('/login', methods=['GET', 'POST'], endpoint='login')
def login():
    if request.method == 'POST':
        user = login_account(request.form)
        if user:
            login_user(user)
            flash('Login successful.', 'success')
            return redirect(url_for('home'))
        flash('Invalid email or password.', 'danger')
    return render_template('common/login.html')


@app.route('/logout', endpoint='logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'], endpoint='register')
def register():
    if request.method == 'POST':

        if create_customer(request.form):
            flash('Registration successful. You can now log in.', 'success')
            return redirect(url_for('login'))
        # else:
        #     return render_template('common/register.html', data={'errors': errors, 'input': request.form})

    return render_template('common/register.html', data={'errors': [], 'input': []})


# ===============================================================
# ADMIN VIEWS
# ===============================================================

@app.route('/admin/home', endpoint='admin_home')
@login_required
@admin_required
def admin_home():
    data = {
        'current': get_current_appointments(),
        'requests': get_appointment_requests(),
        'upcoming': get_upcoming_appointments(),
    }
    return render_template('admin/home.html', data=data)


@app.route('/admin/customers', endpoint='admin_customers')
@login_required
@admin_required
def admin_customers():
    data = get_customers()
    return render_template('admin/customers.html', customers=data)


@app.route('/admin/customer/<int:id>', endpoint='admin_customer_details')
@login_required
@admin_required
def admin_customer_details(id):
    customer = get_customer(id)
    return render_template('admin/customer_detail.html', customer=customer)


@app.route('/admin/appointments', endpoint='admin_appointments')
@login_required
@admin_required
def admin_appointments():
    appointments = get_appointments()
    return render_template('admin/appointments.html', appointments=appointments)


@app.route('/admin/appointments/search', methods=['POST'], endpoint='admin_search_appointments')
@login_required
@admin_required
def admin_search_appointments():
    start_date = request.form.get('start_date')
    appointments = get_appointments_by_date(start_date)
    return render_template('admin/appointments.html', appointments=appointments)


@app.route('/admin/feedbacks', endpoint='admin_feedbacks')
@login_required
@admin_required
def admin_feedbacks():
    feedbacks = get_feedbacks()
    return render_template('admin/feedbacks.html', feedbacks=feedbacks)


@app.route('/admin/notifications', endpoint='admin_notifications')
@login_required
@admin_required
def admin_notifications():
    notifications = get_notifications()
    return render_template('admin/notifications.html', notifications=notifications)


@app.route('/admin/accounts', endpoint='admin_accounts')
@login_required
@admin_required
def admin_accounts():
    data = get_accounts()
    return render_template('admin/accounts.html', accounts=data)


@app.route('/admin/account/<int:id>', endpoint='admin_account_details')
@login_required
@admin_required
def admin_account_details(id):
    account = get_account(id)
    return render_template('admin/account_detail.html', account=account)


@app.route('/admin/reports', methods=['GET', 'POST'], endpoint='admin_reports')
@login_required
@admin_required
def admin_reports():
    date = request.form.get('date') if request.method == 'POST' else datetime.now().strftime('%Y-%m')
    data = {
        'date': date,
        'reports': get_monthly_reports(date)
    }
    return render_template('admin/reports.html', data=data)


@app.route('/admin/settings', endpoint='admin_settings')
@login_required
@admin_required
def admin_settings():
    data = {
        'services': get_services(),
        'roles': get_roles(),
        'bays': get_bays(),
        'status': get_statuses()
    }
    return render_template('admin/settings.html', data=data)


# ===============================================================
# STAFF VIEWS
# ===============================================================

@app.route('/staff/home', endpoint='staff_home')
@login_required
@staff_required
def staff_home():
    data = {
        'upcoming': get_upcoming_appointments(),
        'customers': get_customers(),
        'staffs': Staff.get_staffs_on_duty(),
        'services': [ data.to_json() for data in get_services() ],
        'vehicles': [ data.to_json() for data in get_vehicles() ],
        'bays': Staff.get_bay_appointments(),
    }
    return render_template('staff/home.html', data=data)


@app.route('/staff/appointments', endpoint='staff_appointments')
@login_required
@staff_required
def staff_appointments():
    data = get_staff_appointments(current_user.id)
    return render_template('staff/appointments.html', appointments=data)


@app.route('/staff/feedbacks', endpoint='staff_feedbacks')
@login_required
@staff_required
def staff_feedbacks():
    data = get_staff_feedbacks(current_user.id)
    return render_template('staff/feedbacks.html', feedbacks=data)


# ===============================================================
# CUSTOMER VIEWS
# ===============================================================

@app.route('/customer/home', endpoint='customer_home')
@login_required
@customer_required
def customer_home():
    data = {
        'appointments': get_customer_appointments(current_user.id),
        'services': get_services(),
        'notifications': get_notifications()
    }
    return render_template('customer/home.html', data=data)


@app.route('/customer/appointments', endpoint='customer_appointments')
@login_required
@customer_required
def customer_appointments():
    appointments = get_customer_appointments(current_user.id)
    return render_template('customer/appointments.html', appointments=appointments)


@app.route('/customer/feedbacks', methods=['GET', 'POST'], endpoint='customer_feedbacks')
@login_required
@customer_required
def customer_feedbacks():
    if request.method == 'POST':
        create_feedback(request.form, current_user.id)
        flash('Feedback submitted successfully.', 'success')
        return redirect(url_for('customer_feedbacks'))

    feedbacks = get_customer_feedbacks(current_user.id)
    return render_template('customer/feedbacks.html', feedbacks=feedbacks)


@app.route('/customer/profile', endpoint='customer_profile')
@login_required
@customer_required
def customer_profile():
    customer = get_customer(current_user.id)
    return render_template('customer/profile.html', customer=customer)
