# api.py
from flask import Blueprint, current_app, jsonify, request
from datetime import datetime, date
from typing import Any, Dict, List, Optional

from data.repo import *
from data.seed.populate import Populate

from data.services.appointment import Appointment

api = Blueprint('api', __name__, url_prefix='/api')

# -------------------------
# Helpers
# -------------------------

def require_token(func):
    """Decorator to enforce Bearer Token authentication."""
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header.split(" ")[1]
        if token not in get_account_tokens():
            return jsonify({"error": "Invalid or expired token"}), 403

        # Optional: attach user info to request
        request.user = token
        return func(*args, **kwargs)

    return wrapper


def check_account(request):
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing or invalid token"}), 401

    token = auth_header.split(" ")[1]
    user = decode_token(token)

    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    return jsonify({"message": "Welcome", "user": user.to_dict()})


def get_request_data() -> Dict[str, Any]:
    """Return JSON body or form data as a dict (prioritize JSON)."""
    if request.is_json:
        return request.get_json() or {}
    # request.form is an ImmutableMultiDict -> convert to plain dict
    return {k: v for k, v in request.form.items()}


def _iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    if isinstance(dt, date) and not isinstance(dt, datetime):
        return dt.isoformat()
    try:
        return dt.isoformat()
    except Exception:
        return str(dt)


# -------------------------
# Serializers for each model (based on your models.py)
# -------------------------
def serialize_account(a) -> Dict[str, Any]:
    if a is None:
        return {}
    return {
        "id": getattr(a, "id", None),
        "first_name": getattr(a, "first_name", None),
        "middle_name": getattr(a, "middle_name", None),
        "last_name": getattr(a, "last_name", None),
        "gender": getattr(a, "gender", None),
        "phone_1": getattr(a, "phone_1", None),
        "phone_2": getattr(a, "phone_2", None),
        "birth_date": _iso(getattr(a, "birth_date", None)),
        "address": getattr(a, "address", None),
        "image_profile": getattr(a, "image_profile", None),
        "email": getattr(a, "email", None),
        "is_active": getattr(a, "is_active", None),
        "role_id": getattr(a, "role_id", None),
        "login_date": _iso(getattr(a, "login_date", None)),
        "created_at": _iso(getattr(a, "created_at", None)),
        "updated_at": _iso(getattr(a, "updated_at", None)),
    }


def serialize_customer(c) -> Dict[str, Any]:
    if c is None:
        return {}
    account = getattr(c, "account", None)
    return {
        "id": getattr(c, "id", None),
        "account_id": getattr(c, "account_id", None),
        "is_registered": getattr(c, "is_registered", False),
        "is_pwd": getattr(c, "is_pwd", False),
        "is_senior": getattr(c, "is_senior", False),
        "created_at": _iso(getattr(c, "created_at", None)),
        "updated_at": _iso(getattr(c, "updated_at", None)),
        "account": serialize_account(account) if account else None
    }


def serialize_staff(s) -> Dict[str, Any]:
    if s is None:
        return {}
    account = getattr(s, "account", None)
    return {
        "id": getattr(s, "id", None),
        "account_id": getattr(s, "account_id", None),
        "is_front_desk": getattr(s, "is_front_desk", False),
        "is_on_shift": getattr(s, "is_on_shift", False),
        "created_at": _iso(getattr(s, "created_at", None)),
        "updated_at": _iso(getattr(s, "updated_at", None)),
        "account": serialize_account(account) if account else None
    }


def serialize_schedule(s) -> Dict[str, Any]:
    if s is None:
        return {}
    staff = getattr(s, "staff", None)
    return {
        "id": getattr(s, "id", None),
        "staff_id": getattr(s, "staff_id", None),
        "day": getattr(s, "day", None),
        "shift_start": getattr(s, "shift_start").isoformat() if getattr(s, "shift_start", None) else None,
        "shift_end": getattr(s, "shift_end").isoformat() if getattr(s, "shift_end", None) else None,
        "created_at": _iso(getattr(s, "created_at", None)),
        "updated_at": _iso(getattr(s, "updated_at", None)),
        "staff": {
            "id": getattr(staff, "id", None),
            "account_id": getattr(staff, "account_id", None)
        } if staff else None
    }


def serialize_service(svc) -> Dict[str, Any]:
    if svc is None:
        return {}
    return {
        "id": getattr(svc, "id", None),
        "name": getattr(svc, "name", None),
        "description": getattr(svc, "description", None),
        "price": float(getattr(svc, "price", 0)) if getattr(svc, "price", None) is not None else None,
        "duration": getattr(svc, "duration", None),
        "washers_needed": getattr(svc, "washers_needed", None),
        "type": getattr(svc, "type", None),
        "created_at": _iso(getattr(svc, "created_at", None)),
        "updated_at": _iso(getattr(svc, "updated_at", None)),
    }


def serialize_vehicle(v) -> Dict[str, Any]:
    if v is None:
        return {}
    owner = getattr(v, "owner", None)
    return {
        "id": getattr(v, "id", None),
        "plate_number": getattr(v, "plate_number", None),
        "model": getattr(v, "model", None),
        "type": getattr(v, "type", None),
        "customer_id": getattr(v, "customer_id", None),
        "created_at": _iso(getattr(v, "created_at", None)),
        "updated_at": _iso(getattr(v, "updated_at", None)),
        "owner": serialize_customer(owner) if owner else None
    }


def serialize_bay(b) -> Dict[str, Any]:
    if b is None:
        return {}
    return {
        "id": getattr(b, "id", None),
        "bay": getattr(b, "bay", None),
        "created_at": _iso(getattr(b, "created_at", None)),
        "updated_at": _iso(getattr(b, "updated_at", None)),
    }


def serialize_role(r) -> Dict[str, Any]:
    if r is None:
        return {}
    return {
        "id": getattr(r, "id", None),
        "role": getattr(r, "role", None),
        "created_at": _iso(getattr(r, "created_at", None)),
        "updated_at": _iso(getattr(r, "updated_at", None)),
    }


def serialize_status(s) -> Dict[str, Any]:
    if s is None:
        return {}
    return {
        "id": getattr(s, "id", None),
        "status": getattr(s, "status", None),
        "created_at": _iso(getattr(s, "created_at", None)),
        "updated_at": _iso(getattr(s, "updated_at", None)),
    }


def serialize_payment(p) -> Dict[str, Any]:
    if p is None:
        return {}
    return {
        "id": getattr(p, "id", None),
        "method": getattr(p, "method", None),
        "transaction_no": getattr(p, "transaction_no", None),
        "image_payment": getattr(p, "image_payment", None),
        "amount": float(getattr(p, "amount", 0)) if getattr(p, "amount", None) is not None else None,
        "appointment_id": getattr(p, "appointment_id", None),
        "status_id": getattr(p, "status_id", None),
        "created_at": _iso(getattr(p, "created_at", None)),
        "updated_at": _iso(getattr(p, "updated_at", None)),
    }


def serialize_feedback(f) -> Dict[str, Any]:
    if f is None:
        return {}
    return {
        "id": getattr(f, "id", None),
        "rating": getattr(f, "rating", None),
        "comment": getattr(f, "comment", None),
        "customer_id": getattr(f, "customer_id", None),
        "appointment_id": getattr(f, "appointment_id", None),
        "created_at": _iso(getattr(f, "created_at", None)),
        "updated_at": _iso(getattr(f, "updated_at", None)),
    }


def serialize_notification(n) -> Dict[str, Any]:
    if n is None:
        return {}
    return {
        "id": getattr(n, "id", None),
        "content": getattr(n, "content", None),
        "notif_type": getattr(n, "notif_type", None),
        "viewed": getattr(n, "viewed", False),
        "account_id": getattr(n, "account_id", None),
        "created_at": _iso(getattr(n, "created_at", None)),
        "updated_at": _iso(getattr(n, "updated_at", None)),
    }


def serialize_loyalty(l) -> Dict[str, Any]:
    if l is None:
        return {}
    return {
        "id": getattr(l, "id", None),
        "points": getattr(l, "points", None),
        "note": getattr(l, "note", None),
        "customer_id": getattr(l, "customer_id", None),
        "created_at": _iso(getattr(l, "created_at", None)),
        "updated_at": _iso(getattr(l, "updated_at", None)),
    }


def serialize_appointment(a) -> Dict[str, Any]:
    if a is None:
        return {}
    # many-to-many staffs
    staffs = getattr(a, "staffs", []) or []
    return {
        "id": getattr(a, "id", None),
        "start_time": _iso(getattr(a, "start_time", None)),
        "end_time": _iso(getattr(a, "end_time", None)),
        "bay_id": getattr(a, "bay_id", None),
        "customer_id": getattr(a, "customer_id", None),
        "vehicle_id": getattr(a, "vehicle_id", None),
        "service_id": getattr(a, "service_id", None),
        "status_id": getattr(a, "status_id", None),
        "created_at": _iso(getattr(a, "created_at", None)),
        "updated_at": _iso(getattr(a, "updated_at", None)),
        "bay": serialize_bay(getattr(a, "bay", None)),
        "customer": serialize_customer(getattr(a, "customer", None)),
        "vehicle": serialize_vehicle(getattr(a, "vehicle", None)),
        "service": serialize_service(getattr(a, "service", None)),
        "status": serialize_status(getattr(a, "status", None)),
        "payments": [serialize_payment(p) for p in (getattr(a, "payments", []) or [])],
        "feedbacks": [serialize_feedback(f) for f in (getattr(a, "feedbacks", []) or [])],
        "staffs": [serialize_staff(s) for s in staffs]
    }


# ----------------------------
# Endpoints per entity (CRUD)
# ----------------------------

# LOGIN
@api.route('/login', methods=['POST'])
def api_login():
    data = get_request_data()
    try:
        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password are required'}), 400

        account = authenticate_account(email, password)
        if not account:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

        return jsonify({'success': True, 'data': serialize_account(account)})
    except Exception as e:
        current_app.logger.exception("api_login error")
        return jsonify({'success': False, 'error': str(e)}), 500

# ACCOUNTS
@api.route('/account/get/<int:id>', methods=['GET'])
def api_get_account(id):
    try:
        a = get_account(id)
        if not a:
            return jsonify({'success': False, 'message': 'Account not found'}), 404
        return jsonify({'success': True, 'data': serialize_account(a)})
    except Exception as e:
        current_app.logger.exception("api_get_account error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/account/get/all', methods=['GET'])
def api_get_all_accounts():
    try:
        items = get_accounts()
        return jsonify({'success': True, 'data': [serialize_account(x) for x in items]})
    except Exception as e:
        current_app.logger.exception("api_get_all_accounts error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/account/upsert', methods=['POST'])
def api_upsert_account():
    data = get_request_data()
    try:
        # Create vs Update : support id == -1 or missing -> create
        if str(data.get('id', '-1')) in ('-1', '', None):
            created = register_account(data)
            if created in (False, None):
                return jsonify({'success': False, 'message': 'Failed to create account'}), 400
            return jsonify({'success': True, 'data': serialize_account(created)})
        else:
            updated = upsert_account(data)  # allow upsert to return the updated account
            if updated in (False, None):
                return jsonify({'success': False, 'message': 'Failed to update account'}), 400
            # if upsert_account returns account object:
            try:
                return jsonify({'success': True, 'data': serialize_account(updated)})
            except Exception:
                return jsonify({'success': True})
    except Exception as e:
        current_app.logger.exception("api_upsert_account error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/account/delete', methods=['POST'])
def api_delete_account():
    data = get_request_data()
    try:
        ok = delete_account({"id": data.get('id')}) if callable(delete_account) else delete_account(data.get('id'))
        if ok:
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Delete failed or not found'}), 400
    except Exception as e:
        current_app.logger.exception("api_delete_account error")
        return jsonify({'success': False, 'error': str(e)}), 500


# CUSTOMERS
@api.route('/customer/get/<int:id>', methods=['GET'])
def api_get_customer(id):
    try:
        c = get_customer(id)
        if not c:
            return jsonify({'success': False, 'message': 'Customer not found'}), 404
        return jsonify({'success': True, 'data': serialize_customer(c)})
    except Exception as e:
        current_app.logger.exception("api_get_customer error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/customer/get/all', methods=['GET'])
def api_get_all_customers():
    try:
        items = get_customers()
        return jsonify({'success': True, 'data': [serialize_customer(x) for x in items]})
    except Exception as e:
        current_app.logger.exception("api_get_all_customers error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/customer/upsert', methods=['POST'])
def api_upsert_customer():
    data = get_request_data()
    try:
        if str(data.get('id', '-1')) in ('-1', '', None):
            created = create_customer(data)
            if created in (False, None):
                return jsonify({'success': False, 'message': 'Failed to create customer'}), 400
            return jsonify({'success': True, 'data': serialize_customer(created)})
        else:
            updated = upsert_customer(data)
            if updated in (False, None):
                return jsonify({'success': False, 'message': 'Failed to update customer'}), 400
            return jsonify({'success': True, 'data': serialize_customer(updated)})
    except Exception as e:
        current_app.logger.exception("api_upsert_customer error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/customer/delete', methods=['POST'])
def api_delete_customer():
    data = get_request_data()
    try:
        ok = delete_customer({"id": data.get('id')}) if callable(delete_customer) else delete_customer(data.get('id'))
        if ok:
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Delete failed or not found'}), 400
    except Exception as e:
        current_app.logger.exception("api_delete_customer error")
        return jsonify({'success': False, 'error': str(e)}), 500


# STAFFS
@api.route('/staff/get/<int:id>', methods=['GET'])
def api_get_staff(id):
    try:
        s = get_staff(id)
        if not s:
            return jsonify({'success': False, 'message': 'Staff not found'}), 404
        return jsonify({'success': True, 'data': serialize_staff(s)})
    except Exception as e:
        current_app.logger.exception("api_get_staff error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/staff/get/all', methods=['GET'])
def api_get_all_staffs():
    try:
        items = get_staffs()
        return jsonify({'success': True, 'data': [serialize_staff(x) for x in items]})
    except Exception as e:
        current_app.logger.exception("api_get_all_staffs error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/staff/upsert', methods=['POST'])
def api_upsert_staff():
    data = get_request_data()
    try:
        if str(data.get('id', '-1')) in ('-1', '', None):
            created = create_staff(data)
            if created in (False, None):
                return jsonify({'success': False, 'message': 'Failed to create staff'}), 400
            return jsonify({'success': True, 'data': serialize_staff(created)})
        else:
            updated = upsert_staff(data)
            if updated in (False, None):
                return jsonify({'success': False, 'message': 'Failed to update staff'}), 400
            return jsonify({'success': True, 'data': serialize_staff(updated)})
    except Exception as e:
        current_app.logger.exception("api_upsert_staff error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/staff/delete', methods=['POST'])
def api_delete_staff():
    data = get_request_data()
    try:
        ok = delete_staff({"id": data.get('id')}) if callable(delete_staff) else delete_staff(data.get('id'))
        if ok:
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Delete failed or not found'}), 400
    except Exception as e:
        current_app.logger.exception("api_delete_staff error")
        return jsonify({'success': False, 'error': str(e)}), 500

# STAFF SCHEDULES
@api.route('/schedule/get/all', methods=['GET'])
def api_get_all_schedules():
    try:
        items = get_schedules()
        return jsonify({'success': True, 'data': [serialize_schedule(x) for x in items]})
    except Exception as e:
        current_app.logger.exception("api_get_all_schedules error")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/schedule/get/<int:id>', methods=['GET'])
def api_get_schedule(id):
    try:
        s = get_schedule(id)
        if not s:
            return jsonify({'success': False, 'message': 'Schedule not found'}), 404
        return jsonify({'success': True, 'data': serialize_schedule(s)})
    except Exception as e:
        current_app.logger.exception("api_get_schedule error")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/schedule/upsert', methods=['POST'])
def api_upsert_schedule():
    data = get_request_data()
    try:
        obj = upsert_schedule(data)
        if obj in (False, None):
            return jsonify({'success': False, 'message': 'Upsert failed'}), 400
        return jsonify({'success': True, 'data': serialize_schedule(obj)})
    except Exception as e:
        current_app.logger.exception("api_upsert_schedule error")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/schedule/delete', methods=['POST'])
def api_delete_schedule():
    data = get_request_data()
    try:
        ok = delete_schedule({"id": data.get('id')}) if callable(delete_schedule) else delete_schedule(data.get('id'))
        if ok:
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Delete failed or not found'}), 400
    except Exception as e:
        current_app.logger.exception("api_delete_schedule error")
        return jsonify({'success': False, 'error': str(e)}), 500

# VEHICLES
@api.route('/vehicle/get/<int:id>', methods=['GET'])
def api_get_vehicle(id):
    try:
        v = get_vehicle(id)
        if not v:
            return jsonify({'success': False, 'message': 'Vehicle not found'}), 404
        return jsonify({'success': True, 'data': serialize_vehicle(v)})
    except Exception as e:
        current_app.logger.exception("api_get_vehicle error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/vehicle/get/all', methods=['GET'])
def api_get_all_vehicles():
    try:
        items = get_vehicles()
        return jsonify({'success': True, 'data': [serialize_vehicle(x) for x in items]})
    except Exception as e:
        current_app.logger.exception("api_get_all_vehicles error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/vehicle/upsert', methods=['POST'])
def api_upsert_vehicle():
    data = get_request_data()
    try:
        if str(data.get('id', '-1')) in ('-1', '', None):
            created = upsert_vehicle(data)  # upsertVehicle can return object
            if created in (False, None):
                return jsonify({'success': False, 'message': 'Failed to create vehicle'}), 400
            return jsonify({'success': True, 'data': serialize_vehicle(created)})
        else:
            updated = upsert_vehicle(data)
            if updated in (False, None):
                return jsonify({'success': False, 'message': 'Failed to update vehicle'}), 400
            return jsonify({'success': True, 'data': serialize_vehicle(updated)})
    except Exception as e:
        current_app.logger.exception("api_upsert_vehicle error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/vehicle/delete', methods=['POST'])
def api_delete_vehicle():
    data = get_request_data()
    try:
        ok = delete_vehicle({"id": data.get('id')}) if callable(delete_vehicle) else delete_vehicle(data.get('id'))
        if ok:
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Delete failed or not found'}), 400
    except Exception as e:
        current_app.logger.exception("api_delete_vehicle error")
        return jsonify({'success': False, 'error': str(e)}), 500


# SERVICES
@api.route('/service/get/<int:id>', methods=['GET'])
def api_get_service(id):
    try:
        s = get_service(id)
        if not s:
            return jsonify({'success': False, 'message': 'Service not found'}), 404
        return jsonify({'success': True, 'data': serialize_service(s)})
    except Exception as e:
        current_app.logger.exception("api_get_service error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/service/get/all', methods=['GET'])
def api_get_all_services():
    try:
        items = get_services()
        return jsonify({'success': True, 'data': [serialize_service(x) for x in items]})
    except Exception as e:
        current_app.logger.exception("api_get_all_services error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/service/upsert', methods=['POST'])
def api_upsert_service():
    data = get_request_data()
    try:
        # We allow upsert_service to create or update depending on id presence
        obj = upsert_service(data)
        if obj in (False, None):
            return jsonify({'success': False, 'message': 'Upsert failed'}), 400
        return jsonify({'success': True, 'data': serialize_service(obj)})
    except Exception as e:
        current_app.logger.exception("api_upsert_service error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/service/delete', methods=['POST'])
def api_delete_service():
    data = get_request_data()
    try:
        ok = delete_service({"id": data.get('id')}) if callable(delete_service) else delete_service(data.get('id'))
        if ok:
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Delete failed or not found'}), 400
    except Exception as e:
        current_app.logger.exception("api_delete_service error")
        return jsonify({'success': False, 'error': str(e)}), 500


# BAYS
@api.route('/bay/get/<int:id>', methods=['GET'])
def api_get_bay(id):
    try:
        b = get_bay(id)
        if not b:
            return jsonify({'success': False, 'message': 'Bay not found'}), 404
        return jsonify({'success': True, 'data': serialize_bay(b)})
    except Exception as e:
        current_app.logger.exception("api_get_bay error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/bay/get/all', methods=['GET'])
def api_get_all_bays():
    try:
        items = get_bays()
        return jsonify({'success': True, 'data': [serialize_bay(x) for x in items]})
    except Exception as e:
        current_app.logger.exception("api_get_all_bays error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/bay/upsert', methods=['POST'])
def api_upsert_bay():
    data = get_request_data()
    try:
        obj = upsert_bay(data)
        if obj in (False, None):
            return jsonify({'success': False, 'message': 'Upsert failed'}), 400
        return jsonify({'success': True, 'data': serialize_bay(obj)})
    except Exception as e:
        current_app.logger.exception("api_upsert_bay error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/bay/delete', methods=['POST'])
def api_delete_bay():
    data = get_request_data()
    try:
        ok = delete_bay({"id": data.get('id')}) if callable(delete_bay) else delete_bay(data.get('id'))
        if ok:
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Delete failed or not found'}), 400
    except Exception as e:
        current_app.logger.exception("api_delete_bay error")
        return jsonify({'success': False, 'error': str(e)}), 500


# APPOINTMENTS
@api.route('/appointment/get/<int:id>', methods=['GET'])
def api_get_appointment(id):
    try:
        a = get_appointment(id)
        if not a:
            return jsonify({'success': False, 'message': 'Appointment not found'}), 404
        return jsonify({'success': True, 'data': serialize_appointment(a)})
    except Exception as e:
        current_app.logger.exception("api_get_appointment error")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/appointment/set/status', methods=['POST'])
def api_set_appointment_status():
    data = get_request_data()
    try:
        appointment_id  = data.get('appointment_id')
        status_id       = data.get('status_id')
        obj = Appointment.set_appointment_status(appointment_id, status_id)
        if obj in (False, None):
            return jsonify({'success': False, 'message': 'Upsert failed'}), 400
        return jsonify({'success': True, 'data': serialize_appointment(obj)})
    except Exception as e:
        current_app.logger.exception("api_set_appointment_status error")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/appointment/get/all', methods=['GET'])
def api_get_all_appointments():
    try:
        items = get_appointments()
        return jsonify({'success': True, 'data': [serialize_appointment(x) for x in items]})
    except Exception as e:
        current_app.logger.exception("api_get_all_appointments error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/appointment/upsert', methods=['POST'])
def api_upsert_appointment():
    data = get_request_data()
    try:
        obj = upsert_appointment(data)
        if obj in (False, None):
            return jsonify({'success': False, 'message': 'Upsert failed'}), 400
        return jsonify({'success': True, 'data': serialize_appointment(obj) if hasattr(obj, '__dict__') else None})
    except Exception as e:
        current_app.logger.exception("api_upsert_appointment error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/appointment/book', methods=['POST'])
def api_book_appointment():
    data = get_request_data()
    try:
        res = book_appointment(data)
        # book_appointment can return appointment object, False, or text message
        if isinstance(res, str):
            return jsonify({'success': False, 'message': res}), 400
        if res in (False, None):
            return jsonify({'success': False, 'message': 'Booking failed'}), 400
        return jsonify({'success': True, 'data': serialize_appointment(res)})
    except Exception as e:
        current_app.logger.exception("api_book_appointment error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/appointment/delete', methods=['POST'])
def api_delete_appointment():
    data = get_request_data()
    try:
        ok = delete_appointment({"id": data.get('id')}) if callable(delete_appointment) else delete_appointment(data.get('id'))
        if ok:
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Delete failed or not found'}), 400
    except Exception as e:
        current_app.logger.exception("api_delete_appointment error")
        return jsonify({'success': False, 'error': str(e)}), 500


# PAYMENTS
@api.route('/payment/get/<int:id>', methods=['GET'])
def api_get_payment(id):
    try:
        p = get_payment(id)
        if not p:
            return jsonify({'success': False, 'message': 'Payment not found'}), 404
        return jsonify({'success': True, 'data': serialize_payment(p)})
    except Exception as e:
        current_app.logger.exception("api_get_payment error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/payment/get/all', methods=['GET'])
def api_get_all_payments():
    try:
        items = get_payments()
        return jsonify({'success': True, 'data': [serialize_payment(x) for x in items]})
    except Exception as e:
        current_app.logger.exception("api_get_all_payments error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/payment/upsert', methods=['POST'])
def api_upsert_payment():
    data = get_request_data()
    try:
        obj = upsert_payment(data)
        if obj in (False, None):
            return jsonify({'success': False, 'message': 'Upsert failed'}), 400
        return jsonify({'success': True, 'data': serialize_payment(obj)})
    except Exception as e:
        current_app.logger.exception("api_upsert_payment error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/payment/delete', methods=['POST'])
def api_delete_payment():
    data = get_request_data()
    try:
        ok = delete_payment({"id": data.get('id')}) if callable(delete_payment) else delete_payment(data.get('id'))
        if ok:
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Delete failed or not found'}), 400
    except Exception as e:
        current_app.logger.exception("api_delete_payment error")
        return jsonify({'success': False, 'error': str(e)}), 500


# FEEDBACKS
@api.route('/feedback/get/<int:id>', methods=['GET'])
def api_get_feedback(id):
    try:
        f = get_feedback(id)
        if not f:
            return jsonify({'success': False, 'message': 'Feedback not found'}), 404
        return jsonify({'success': True, 'data': serialize_feedback(f)})
    except Exception as e:
        current_app.logger.exception("api_get_feedback error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/feedback/get/all', methods=['GET'])
def api_get_all_feedbacks():
    try:
        items = get_feedbacks()
        return jsonify({'success': True, 'data': [serialize_feedback(x) for x in items]})
    except Exception as e:
        current_app.logger.exception("api_get_all_feedbacks error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/feedback/upsert', methods=['POST'])
def api_upsert_feedback():
    data = get_request_data()
    try:
        obj = upsert_feedback(data)
        if obj in (False, None):
            return jsonify({'success': False, 'message': 'Upsert failed'}), 400
        return jsonify({'success': True, 'data': serialize_feedback(obj)})
    except Exception as e:
        current_app.logger.exception("api_upsert_feedback error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/feedback/delete', methods=['POST'])
def api_delete_feedback():
    data = get_request_data()
    try:
        ok = delete_feedback({"id": data.get('id')}) if callable(delete_feedback) else delete_feedback(data.get('id'))
        if ok:
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Delete failed or not found'}), 400
    except Exception as e:
        current_app.logger.exception("api_delete_feedback error")
        return jsonify({'success': False, 'error': str(e)}), 500


# NOTIFICATIONS
@api.route('/notifications/get/all', methods=['GET'])
def api_get_all_notifications():
    try:
        items = get_all_notifications()
        return jsonify({'success': True, 'data': [serialize_notification(x) for x in items]})
    except Exception as e:
        current_app.logger.exception("api_get_all_notifications error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/notifications/account/get/<int:id>', methods=['GET'])
def api_get_account_notifications(id):
    try:
        items = get_account_notifications(id)
        return jsonify({'success': True, 'data': [serialize_notification(x) for x in items]})
    except Exception as e:
        current_app.logger.exception("api_get_account_notifications error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/notifications/get/<int:id>', methods=['GET'])
def api_get_notification(id):
    try:
        n = get_notification(id)
        if not n:
            return jsonify({'success': False, 'message': 'Notification not found'}), 404
        return jsonify({'success': True, 'data': serialize_notification(n)})
    except Exception as e:
        current_app.logger.exception("api_get_notification error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/notifications/update/<int:id>', methods=['GET', 'POST'])
def api_update_notification(id):
    try:
        ok = update_notification(id)
        if ok:
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Update failed'}), 400
    except Exception as e:
        current_app.logger.exception("api_update_notification error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/notifications/sms/send', methods=['POST'])
def api_send_sms():
    data = get_request_data()
    try:
        # Expecting JSON: { "number": "...", "msg": "..." }
        number = data.get('number')
        msg = data.get('msg')
        if not number or not msg:
            return jsonify({'success': False, 'message': 'number and msg required'}), 400
        ok = send_sms(number, msg)
        return jsonify({'success': ok})
    except Exception as e:
        current_app.logger.exception("api_send_sms error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/notifications/email/send', methods=['POST'])
def api_send_email():
    data = get_request_data()
    try:
        ok = send_email(data)
        return jsonify({'success': ok})
    except Exception as e:
        current_app.logger.exception("api_send_email error")
        return jsonify({'success': False, 'error': str(e)}), 500


# ROLES
@api.route('/role/get/<int:id>', methods=['GET'])
def api_get_role(id):
    try:
        r = get_role(id)
        if not r:
            return jsonify({'success': False, 'message': 'Role not found'}), 404
        return jsonify({'success': True, 'data': serialize_role(r)})
    except Exception as e:
        current_app.logger.exception("api_get_role error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/role/get/all', methods=['GET'])
def api_get_all_roles():
    try:
        items = get_roles()
        return jsonify({'success': True, 'data': [serialize_role(x) for x in items]})
    except Exception as e:
        current_app.logger.exception("api_get_all_roles error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/role/upsert', methods=['POST'])
def api_upsert_role():
    data = get_request_data()
    try:
        obj = upsert_role(data)
        if obj in (False, None):
            return jsonify({'success': False, 'message': 'Upsert failed'}), 400
        return jsonify({'success': True, 'data': serialize_role(obj)})
    except Exception as e:
        current_app.logger.exception("api_upsert_role error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/role/delete', methods=['POST'])
def api_delete_role():
    data = get_request_data()
    try:
        ok = delete_role({"id": data.get('id')}) if callable(delete_role) else delete_role(data.get('id'))
        if ok:
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Delete failed or not found'}), 400
    except Exception as e:
        current_app.logger.exception("api_delete_role error")
        return jsonify({'success': False, 'error': str(e)}), 500


# STATUS
@api.route('/status/get/<int:id>', methods=['GET'])
def api_get_status(id):
    try:
        s = get_status(id)
        if not s:
            return jsonify({'success': False, 'message': 'Status not found'}), 404
        return jsonify({'success': True, 'data': serialize_status(s)})
    except Exception as e:
        current_app.logger.exception("api_get_status error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/status/get/all', methods=['GET'])
def api_get_all_status():
    try:
        items = get_all_statuses()
        return jsonify({'success': True, 'data': [serialize_status(x) for x in items]})
    except Exception as e:
        current_app.logger.exception("api_get_all_status error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/status/upsert', methods=['POST'])
def api_upsert_status():
    data = get_request_data()
    try:
        obj = upsert_status(data)
        if obj in (False, None):
            return jsonify({'success': False, 'message': 'Upsert failed'}), 400
        return jsonify({'success': True, 'data': serialize_status(obj)})
    except Exception as e:
        current_app.logger.exception("api_upsert_status error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/status/delete', methods=['POST'])
def api_delete_status():
    data = get_request_data()
    try:
        ok = delete_status({"id": data.get('id')}) if callable(delete_status) else delete_status(data.get('id'))
        if ok:
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Delete failed or not found'}), 400
    except Exception as e:
        current_app.logger.exception("api_delete_status error")
        return jsonify({'success': False, 'error': str(e)}), 500


# LOYALTIES
@api.route('/loyalty/get/<int:id>', methods=['GET'])
def api_get_loyalty(id):
    try:
        l = get_loyalty(id)
        if not l:
            return jsonify({'success': False, 'message': 'Loyalty not found'}), 404
        return jsonify({'success': True, 'data': serialize_loyalty(l)})
    except Exception as e:
        current_app.logger.exception("api_get_loyalty error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/loyalty/get/all', methods=['GET'])
def api_get_all_loyalties():
    try:
        items = get_loyalties()
        return jsonify({'success': True, 'data': [serialize_loyalty(x) for x in items]})
    except Exception as e:
        current_app.logger.exception("api_get_all_loyalties error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/loyalty/upsert', methods=['POST'])
def api_upsert_loyalty():
    data = get_request_data()
    try:
        obj = upsert_loyalty(data)
        if obj in (False, None):
            return jsonify({'success': False, 'message': 'Upsert failed'}), 400
        return jsonify({'success': True, 'data': serialize_loyalty(obj)})
    except Exception as e:
        current_app.logger.exception("api_upsert_loyalty error")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/loyalty/delete', methods=['POST'])
def api_delete_loyalty():
    data = get_request_data()
    try:
        ok = delete_loyalty({"id": data.get('id')}) if callable(delete_loyalty) else delete_loyalty(data.get('id'))
        if ok:
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Delete failed or not found'}), 400
    except Exception as e:
        current_app.logger.exception("api_delete_loyalty error")
        return jsonify({'success': False, 'error': str(e)}), 500


# FACTORY / POPULATE
@api.route('/populate', methods=['GET'])
def api_populate():
    try:
        # If you implemented a populate_seed_data() or populate() in crud.py, call it
        Populate.populate()
        return jsonify({'success': True, 'message': 'Populated'})
    except Exception as e:
        current_app.logger.exception("api_populate error")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/quick_book', methods=['POST'])
def api_quick_book():
    data = get_request_data()
    try:
        # Extract data from request
        vehicle_id = data.get('vehicle_id')
        service_id = data.get('service_id')
        customer_id = data.get('customer_id')
        appointment_date = data.get('appointment_date')
        appointment_id = data.get('appointment_id')

        if 'quick_book' in globals() and callable(quick_book):
            response = quick_book(service_id, customer_id, vehicle_id, appointment_date, appointment_id)
            return jsonify({'success': True, 'message': response})
        return jsonify({'success': False, 'message': 'No quick_book function found'}), 500
    except Exception as e:
        current_app.logger.exception("api_quick_book error")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/check_or_suggest_appointment', methods=['POST'])
def api_check_or_suggest_appointment():
    data = get_request_data()
    try:
        # Extract data from request
        service_id = data.get('service_id')
        appointment_date = data.get('appointment_date')

        if 'check_or_suggest_appointment' in globals() and callable(check_or_suggest_appointment):
            response = check_or_suggest_appointment(service_id, appointment_date)
            return jsonify({'success': True, 'message': response})
        return jsonify({'success': False, 'message': 'No check_or_suggest_appointment function found'}), 500
    except Exception as e:
        current_app.logger.exception("api_check_or_suggest_appointment error")
        return jsonify({'success': False, 'error': str(e)}), 500
