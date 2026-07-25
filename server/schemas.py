from marshmallow import Schema, fields, validate


class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True, validate=validate.Length(min=1))
    # Password fields are write-only: accepted on load (signup), never included on dump.
    password = fields.Str(required=True, load_only=True, validate=validate.Length(min=6))
    password_confirmation = fields.Str(required=True, load_only=True)


class LoginSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)


class WorkoutSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=1))
    date = fields.Date(required=True)
    duration_minutes = fields.Int(
        required=True, validate=validate.Range(min=1, error='duration_minutes must be at least 1.')
    )
    notes = fields.Str(required=False, allow_none=True)
    user_id = fields.Int(dump_only=True)


# Schema used to serialize a logged-in user without ever exposing password fields.
public_user_schema = UserSchema(exclude=('password', 'password_confirmation'))

login_schema = LoginSchema()

workout_schema = WorkoutSchema()
workouts_schema = WorkoutSchema(many=True)
