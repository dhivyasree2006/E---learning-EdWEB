from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Table, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from database import Base

# Association tables
user_badges = Table(
    "user_badges",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("badge_id", Integer, ForeignKey("badges.id"), primary_key=True),
    Column("earned_at", DateTime, default=datetime.utcnow)
)

batch_students = Table(
    "batch_students",
    Base.metadata,
    Column("batch_id", Integer, ForeignKey("batches.id"), primary_key=True),
    Column("student_id", Integer, ForeignKey("users.id"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default="learner")
    created_at = Column(DateTime, default=datetime.utcnow)
    reset_otp = Column(String, nullable=True)
    otp_expiry = Column(DateTime, nullable=True)

    courses = relationship("Course", back_populates="instructor")
    enrolments = relationship("Enrolment", back_populates="user")
    quiz_results = relationship("QuizResult", back_populates="user")
    badges = relationship("Badge", secondary=user_badges, back_populates="users")
    notifications = relationship("Notification", back_populates="user")

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    thumbnail = Column(String, nullable=True)
    price = Column(Float, default=0.0)
    status = Column(String, default="Published")
    instructor_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    instructor = relationship("User", back_populates="courses")
    modules = relationship("Module", back_populates="course", cascade="all, delete-orphan")
    assessment = relationship("Question", back_populates="course", cascade="all, delete-orphan")
    enrolments = relationship("Enrolment", back_populates="course", cascade="all, delete-orphan")
    batches = relationship("Batch", back_populates="course", cascade="all, delete-orphan")

class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    contentLink = Column(String, nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"))

    course = relationship("Course", back_populates="modules")
    quiz = relationship("Question", back_populates="module", cascade="all, delete-orphan")
    results = relationship("QuizResult", back_populates="module", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    questionText = Column(String)
    questionType = Column(String, default="mcq") # 'mcq' or 'descriptive'
    correctOptionIndex = Column(Integer, nullable=True) # For MCQ
    correctAnswerText = Column(String, nullable=True) # For Descriptive
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=True) # Optional for assessment
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True) # For final assessment
    difficulty = Column(String, default="medium") # 'easy', 'medium', 'hard'
    
    module = relationship("Module", back_populates="quiz")
    course = relationship("Course", back_populates="assessment")
    options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan")

class QuestionOption(Base):
    __tablename__ = "question_options"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String)
    question_id = Column(Integer, ForeignKey("questions.id"))

    question = relationship("Question", back_populates="options")

class Enrolment(Base):
    __tablename__ = "enrolments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    accessibility_enabled = Column(Boolean, default=False)

    user = relationship("User", back_populates="enrolments")
    course = relationship("Course", back_populates="enrolments")

class QuizResult(Base):
    __tablename__ = "quiz_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    score = Column(Integer)
    total_questions = Column(Integer)
    answers = Column(JSON, nullable=True)
    question_ids = Column(JSON, nullable=True) # To track specific questions in order
    completed_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="quiz_results")
    module = relationship("Module", back_populates="results")
    course = relationship("Course")

class Badge(Base):
    __tablename__ = "badges"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    icon = Column(String)
    
    users = relationship("User", secondary=user_badges, back_populates="badges")

class Batch(Base):
    __tablename__ = "batches"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    course_id = Column(Integer, ForeignKey("courses.id"))
    instructor_id = Column(Integer, ForeignKey("users.id"))
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="batches")
    instructor = relationship("User")
    students = relationship("User", secondary=batch_students)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    message = Column(String)
    type = Column(String) 
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    content = Column(String)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])

class Certificate(Base):
    __tablename__ = "certificates"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    certificate_code = Column(String, unique=True)
    issued_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    course = relationship("Course")

