
from typing import List
from data.models import Customers

class Customer:

    def get_registered_customers() -> List[Customers]:
        return Customers.query.filter_by(is_registered=True).all()
