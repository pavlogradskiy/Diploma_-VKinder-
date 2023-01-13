import sqlalchemy as sq
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import date

Base = declarative_base()
engine = sq.create_engine('postgresql://oks:@localhost:5432/vk_users_db', client_encoding='utf8')
Session = sessionmaker(bind=engine)


class FoundUsers(Base):
    __tablename__ = 'found_users'

    vk_id = sq.Column(sq.Integer, primary_key=True)
    name = sq.Column(sq.String, nullable=False)
    url = sq.Column(sq.String, unique=True, nullable=False)
    photos = sq.Column(sq.String, nullable=False)
    bot_users = relationship(
        'BotUsers',
        secondary='bot_users_to_found_users',
        back_populates='found_users'
    )


bot_users_to_found_users = sq.Table(
    'bot_users_to_found_users', Base.metadata,
    sq.Column('bot_user', sq.Integer, sq.ForeignKey('bot_users.user_id')),
    sq.Column('found_user', sq.Integer, sq.ForeignKey('found_users.vk_id')),
    sq.PrimaryKeyConstraint('bot_user', 'found_user')
)


class BotUsers(Base):
    __tablename__ = 'bot_users'

    id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, unique=True)
    last_date = sq.Column(sq.DATE)
    found_users = relationship(
        FoundUsers,
        secondary='bot_users_to_found_users',
        back_populates='bot_users'
    )


def add_user_session(session, sender_id):
    user = session.query(BotUsers).filter_by(user_id=sender_id).first()
    if user:
        user.last_date = date.today()
    else:
        new_user = BotUsers(user_id=sender_id, last_date=date.today())
        session.add(new_user)


def add_found_user(session, sender_id, found_user: dict):
    new_user = session.query(FoundUsers).filter_by(vk_id=found_user['id']).first()
    bot_user = session.query(BotUsers).filter(BotUsers.user_id == sender_id).one()
    if new_user:
        for user in bot_user.found_users:
            if new_user.vk_id == user.vk_id:
                return
    else:
        new_user = FoundUsers(
            vk_id=found_user['id'],
            name=found_user['name'],
            url=found_user['url'],
            photos=found_user['photos']
        )
        session.add(new_user)
    bot_user.found_users.append(new_user)