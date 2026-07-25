#!/usr/bin/env python3

import random
from datetime import date, timedelta

from faker import Faker

from app import app
from config import db
from models import User, Workout

fake = Faker()

with app.app_context():
    print('Clearing tables...')
    Workout.query.delete()
    User.query.delete()
    db.session.commit()

    print('Seeding users...')
    users = []
    for _ in range(3):
        user = User(username=fake.unique.user_name())
        user.password_hash = 'password123'
        users.append(user)
    db.session.add_all(users)
    db.session.commit()

    print('Seeding workouts...')
    workouts = []
    for user in users:
        for _ in range(random.randint(4, 8)):
            workout = Workout(
                title=fake.sentence(nb_words=3).rstrip('.'),
                date=date.today() - timedelta(days=random.randint(0, 60)),
                duration_minutes=random.randint(15, 90),
                notes=fake.sentence(),
                user_id=user.id,
            )
            workouts.append(workout)
    db.session.add_all(workouts)
    db.session.commit()

    print(f'Done seeding! Created {len(users)} users and {len(workouts)} workouts.')
    print('Sample login credentials for testing:')
    for u in users:
        print(f'  username={u.username}  password=password123')
