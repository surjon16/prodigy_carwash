import logging, random

from datetime import datetime, date, timedelta, time
from typing import Optional, List, Union, Dict, Any
from sqlalchemy import and_, or_, cast, Date
from flask_login import login_user
from collections import defaultdict

from data import db  # your SQLAlchemy instance
from data.models import (
    Accounts, Customers, Staffs, Appointments, Payments, Services,
    Vehicles, Bays, Roles, Status, Notifications, Feedbacks, Loyalties,
    Schedules
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def get_least_score(scores: dict):
    """
    Returns the key (variable name) with the least score.
    If multiple have the same least score, returns the first one.
    
    Example:
        scores = {"a": 10, "b": 5, "c": 5, "d": 8}
        -> returns "b"
    """
    # Check if dictionary is empty
    if not scores:
        return None

    # Get the first key with the minimum value
    min_key = min(scores, key=lambda k: (scores[k], list(scores.keys()).index(k)))
    return min_key