import sys

sys.path.append("../")

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Table, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.base import Base


class UserProblem(Base):
    __tablename__ = "user_problems"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False)
    user = relationship("User", back_populates="problem_associations")
    problem = relationship("Problem", back_populates="user_associations")


class Problem(Base):
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True, index=True)
    contest_id = Column(Integer, unique=False, nullable=False)
    index = Column(String(2), unique=False, nullable=False)
    name = Column(String(100), nullable=True)
    rating = Column(Integer, unique=False, nullable=True)
    tags = Column(JSON)
    user_associations = relationship("UserProblem", back_populates="problem", cascade="all, delete-orphan")
    @property
    def solved_by_users(self):
        return [assoc.user for assoc in self.user_associations]


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    codeforces_handle = Column(String(50), unique=False, index=True)
    problem_associations = relationship("UserProblem", back_populates="user", cascade="all, delete-orphan")
    @property
    def solved_problems(self):
        return [assoc.problem for assoc in self.problem_associations]


class Conversation(Base):
    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=True)

    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True)

    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    conversation = relationship("Conversation", back_populates="messages")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False, index=True)
    reason = Column(Text, nullable=True)
    score = Column(Float, nullable=False, default=0.0)
    completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
