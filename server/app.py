from functools import wraps

from flask import request, session
from flask_restful import Resource
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Workout
from schemas import UserSchema, public_user_schema, login_schema, workout_schema, workouts_schema


def login_required(func):
    """Blocks access to a resource method unless a user is logged in (session cookie present)."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('user_id'):
            return {'errors': ['Unauthorized. Please log in.']}, 401
        return func(*args, **kwargs)
    return wrapper


def flatten_errors(messages):
    """Converts Marshmallow's {field: [msg, ...]} error dict into a flat list of
    'field: message' strings, matching the frontend's expected {errors: [...]} shape."""
    flattened = []
    for field, msgs in messages.items():
        for msg in msgs:
            flattened.append(f'{field}: {msg}' if field != '_schema' else msg)
    return flattened


# ---------------------- Auth ----------------------

class Signup(Resource):
    def post(self):
        data = request.get_json()
        try:
            validated = UserSchema().load(data)
        except ValidationError as err:
            return {'errors': flatten_errors(err.messages)}, 400

        if validated['password'] != validated['password_confirmation']:
            return {'errors': ['Password and password confirmation do not match.']}, 400

        try:
            user = User(username=validated['username'])
            user.password_hash = validated['password']
            db.session.add(user)
            db.session.commit()
        except ValueError as err:
            db.session.rollback()
            return {'errors': [str(err)]}, 400
        except IntegrityError:
            db.session.rollback()
            return {'errors': ['Username is already taken.']}, 422

        session['user_id'] = user.id
        return public_user_schema.dump(user), 201


class Login(Resource):
    def post(self):
        data = request.get_json()
        try:
            validated = login_schema.load(data)
        except ValidationError as err:
            return {'errors': flatten_errors(err.messages)}, 400

        user = User.query.filter_by(username=validated['username']).first()
        if user and user.authenticate(validated['password']):
            session['user_id'] = user.id
            return public_user_schema.dump(user), 200

        return {'errors': ['Invalid username or password.']}, 401


class Logout(Resource):
    def delete(self):
        session['user_id'] = None
        return {}, 204


class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            user = db.session.get(User, user_id)
            if user:
                return public_user_schema.dump(user), 200
        return {'errors': ['Not logged in.']}, 401


# ---------------------- Workouts (protected, user-owned) ----------------------

class Workouts(Resource):
    method_decorators = [login_required]

    def get(self):
        # Pagination: /workouts?page=1&per_page=10
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        pagination = (
            Workout.query
            .filter_by(user_id=session['user_id'])
            .order_by(Workout.date.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

        return {
            'workouts': workouts_schema.dump(pagination.items),
            'total': pagination.total,
            'page': pagination.page,
            'pages': pagination.pages,
            'per_page': pagination.per_page,
        }, 200

    def post(self):
        data = request.get_json()
        try:
            validated = workout_schema.load(data)
        except ValidationError as err:
            return {'errors': flatten_errors(err.messages)}, 400

        try:
            workout = Workout(
                title=validated['title'],
                date=validated['date'],
                duration_minutes=validated['duration_minutes'],
                notes=validated.get('notes'),
                user_id=session['user_id'],
            )
            db.session.add(workout)
            db.session.commit()
        except ValueError as err:
            db.session.rollback()
            return {'errors': [str(err)]}, 400

        return workout_schema.dump(workout), 201


class WorkoutByID(Resource):
    method_decorators = [login_required]

    def _get_owned_workout(self, id):
        """Only returns the workout if it exists AND belongs to the logged-in user."""
        return Workout.query.filter_by(id=id, user_id=session['user_id']).first()

    def get(self, id):
        workout = self._get_owned_workout(id)
        if not workout:
            return {'errors': ['Workout not found.']}, 404
        return workout_schema.dump(workout), 200

    def patch(self, id):
        workout = self._get_owned_workout(id)
        if not workout:
            return {'errors': ['Workout not found.']}, 404

        data = request.get_json()
        try:
            validated = workout_schema.load(data, partial=True)
        except ValidationError as err:
            return {'errors': flatten_errors(err.messages)}, 400

        try:
            for key, value in validated.items():
                setattr(workout, key, value)
            db.session.commit()
        except ValueError as err:
            db.session.rollback()
            return {'errors': [str(err)]}, 400

        return workout_schema.dump(workout), 200

    def delete(self, id):
        workout = self._get_owned_workout(id)
        if not workout:
            return {'errors': ['Workout not found.']}, 404

        db.session.delete(workout)
        db.session.commit()
        return {}, 204


api.add_resource(Signup, '/signup')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(CheckSession, '/check_session')
api.add_resource(Workouts, '/workouts')
api.add_resource(WorkoutByID, '/workouts/<int:id>')


if __name__ == '__main__':
    app.run(port=5555, debug=True)
