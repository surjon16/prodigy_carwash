from datetime import datetime
from marshmallow import Schema, fields, validates, ValidationError

# All classes declared will be used for validation

class CreateAccountSchema(Schema):
    
    first_name  = fields.Str(required=True)
    last_name   = fields.Str(required=True)
    phone_1     = fields.Str(required=True)
    email       = fields.Email(required=True)
    address     = fields.Str(required=True)
    password    = fields.Str(required=True)

    @validates('first_name')
    def validate_first_name(self, value):
        if value == '' or value is None:
            raise ValidationError('Please provide your first name.')

    @validates('last_name')
    def validate_last_name(self, value):
        if value == '' or value is None:
            raise ValidationError('Please provide your last name.')

    @validates('phone_1')
    def validate_phone_1(self, value):
        if value == '' or value is None:
            raise ValidationError('Please provide a phone number.')
        if value[:4] != '+639':
            raise ValidationError('Invalid phone number.')
        if len(value) != 13:
            raise ValidationError('Invalid phone number.')

    @validates('address')
    def validate_address(self, value):
        if value == '' or value is None:
            raise ValidationError('Please provide an address.')

    @validates('password')
    def validate_password(self, value):
        if value == '' or value is None:
            raise ValidationError('Please provide a password.')

class UpdateAccountSchema(Schema):
    
    first_name  = fields.Str(required=True)
    last_name   = fields.Str(required=True)
    phone_1     = fields.Str(required=True)
    email       = fields.Email(required=True)
    address     = fields.Str(required=True)
    role_id     = fields.Str(required=True)

    @validates('first_name')
    def validate_first_name(self, value):
        if value == '' or value is None:
            raise ValidationError('Please provide your first name.')

    @validates('last_name')
    def validate_last_name(self, value):
        if value == '' or value is None:
            raise ValidationError('Please provide your last name.')

    @validates('phone_1')
    def validate_phone_1(self, value):
        if value == '' or value is None:
            raise ValidationError('Please provide a phone number.')
        if value[:4] != '+639':
            raise ValidationError('Invalid phone number.')
        if len(value) != 13:
            raise ValidationError('Invalid phone number.')

    @validates('address')
    def validate_address(self, value):
        if value == '' or value is None:
            raise ValidationError('Please provide an address.')

    @validates('role_id')
    def validate_role_id(self, value):
        if value == '' or value is None:
            raise ValidationError('Please provide a role.')

class RegisterAccountSchema(Schema):

    first_name  = fields.Str(required=True, data_key='first_name')
    last_name   = fields.Str(required=True)
    email       = fields.Email(required=True)
    phone_1     = fields.Str(required=True)
    password    = fields.Str(required=True)

    @validates('first_name')
    def validate_first_name(self, value):
        if value == '' or value is None:
            raise ValidationError('Please provide your first name.')

    @validates('last_name')
    def validate_last_name(self, value):
        if value == '' or value is None:
            raise ValidationError('Please provide your last name.')

    @validates('phone_1')
    def validate_phone_1(self, value):
        if value == '' or value is None:
            raise ValidationError('Please provide a phone number.')
        if value[:4] != '+639':
            raise ValidationError('Invalid phone number.')
        if len(value) < 13 :
            raise ValidationError('Invalid phone number.')

    @validates('password')
    def validate_password(self, value):
        if value == '' or value is None:
            raise ValidationError('Please provide a password.')

# ============================

class CreateCustomerSchema(Schema):
    
    first_name  = fields.Str(required=True)
    last_name   = fields.Str(required=True)
    phone_1     = fields.Str(required=True)
    email       = fields.Email(required=True)
    address     = fields.Str(required=True)
    password    = fields.Str(required=True)

    @validates('first_name')
    def validate_first_name(self, value):
        if value == '' or value is None:
            raise ValidationError('Please provide your first name.')

    @validates('last_name')
    def validate_last_name(self, value):
        if value == '' or value is None:
            raise ValidationError('Please provide your last name.')

    @validates('phone_1')
    def validate_phone_1(self, value):
        if value == '' or value is None:
            raise ValidationError('Please provide a phone number.')
        if value[:4] != '+639':
            raise ValidationError('Invalid phone number.')
        if len(value) != 13:
            raise ValidationError('Invalid phone number.')

    @validates('address')
    def validate_address(self, value):
        if value == '' or value is None:
            raise ValidationError('Please provide an address.')

    @validates('password')
    def validate_password(self, value):
        if value == '' or value is None:
            raise ValidationError('Please provide a password.')

class UpdateCustomerSchema(Schema):
    
    first_name  = fields.Str(required=True)
    last_name   = fields.Str(required=True)
    phone_1     = fields.Str(required=True)
    email       = fields.Email(required=True)
    address     = fields.Str(required=True)

    @validates('first_name')
    def validate_first_name(self, value):
        if value == '' or value is None:
            raise ValidationError('Please provide your first name.')

    @validates('last_name')
    def validate_last_name(self, value):
        if value == '' or value is None:
            raise ValidationError('Please provide your last name.')

    @validates('phone_1')
    def validate_phone_1(self, value):
        if value == '' or value is None:
            raise ValidationError('Please provide a phone number.')
        if value[:4] != '+639':
            raise ValidationError('Invalid phone number.')
        if len(value) != 13:
            raise ValidationError('Invalid phone number.')

    @validates('address')
    def validate_address(self, value):
        if value == '' or value is None:
            raise ValidationError('Please provide an address.')
