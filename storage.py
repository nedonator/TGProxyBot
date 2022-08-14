import queue
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, \
    PrimaryKeyConstraint, Enum, MetaData
from sqlalchemy.orm import declarative_base, relationship, Session

engine = create_engine("sqlite:///data.db?check_same_thread=false")
metadata = MetaData()
metadata.drop_all(engine)
session = Session(bind=engine)
Base = declarative_base()


class State(Enum):
    IDLE = 'IDLE'
    CHOOSE_RECEIVER = 'CHOOSE_RECEIVER'
    MAKE_MESSAGE = 'MAKE_MESSAGE'
    SET_DELAY = 'SET_DELAY'


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer())
    username = Column(String(200), nullable=False)
    name = Column(String(200), nullable=False)
    state = relationship('UserState', backref='user', uselist=False)

    __table_args__ = (
       PrimaryKeyConstraint('id'),
    )

    def __str__(self):
        return f'@{self.username} {self.name}'


class UserState(Base):
    __tablename__ = 'states'
    id = Column(ForeignKey('users.id'))
    state = Column(Enum('IDLE', 'CHOOSE_RECEIVER', 'MAKE_MESSAGE', 'SET_DELAY', name='State'), nullable=False)
    message = relationship('Message', backref='state', uselist=False)

    __table_args__ = (
        PrimaryKeyConstraint('id'),
    )


class Message(Base):
    __tablename__ = 'messages'
    id = Column(ForeignKey('states.id'))
    to_user_id = Column(String(200), nullable=True)
    body = Column(String(2000), nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint('id'),
    )


class SentMessage(Base):
    __tablename__ = 'sent_messages'
    message_id = Column(Integer())
    time = Column(DateTime(), nullable=False)
    from_user_id = Column(ForeignKey('users.id'))
    to_user_id = Column(ForeignKey('users.id'))
    body = Column(String(2000), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('message_id'),
    )


Base.metadata.create_all(engine)


users_by_id = {}
users_by_username = {}
message_queue = queue.PriorityQueue()


def load_data_from_db():
    users = session.query(User).all()
    for user in users:
        users_by_id[user.id] = user
        users_by_username[user.username] = user


load_data_from_db()


def create_user(user_id: int, username: str, name: str):
    user = User(id=user_id, username=username, name=name)
    message = Message(id=user_id, to_user_id=None, body=None)
    state = UserState(id=user_id, state=State.IDLE, message=message)
    users_by_id[user_id] = user
    users_by_username[username] = user
    session.add_all([user, state, message])
    session.commit()
    return user


def change_state(user: User, state: State, message_to_user_id: Optional[int]=None, message_body: Optional[str]=None):
    user.state.state = state
    user.state.message.to_user_id = message_to_user_id
    user.state.message.body = message_body
    session.add_all([user.state, user.state.message])
    session.commit()


def send_message(user: User, time: int):
    message = user.state.message
    sent_message = SentMessage(time=time, from_user_id=user.id, to_user_id=message.to_user_id, body=message.body)
    message_queue.put((time, sent_message))
