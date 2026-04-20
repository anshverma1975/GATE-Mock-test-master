from controller.database import db
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")
    attempts = db.relationship("Attempt", backref="user", lazy=True)
    activities = db.relationship("Activity", backref="user", lazy=True)

class Subject(db.Model):
    __tablename__ = "subjects"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    quizzes = db.relationship("Quiz", backref="subject", lazy=True)

class Quiz(db.Model):
    __tablename__ = "quizzes"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    questions = db.relationship("Question", backref="quiz", lazy=True)
    attempts = db.relationship("Attempt", backref="quiz", lazy=True)

class Question(db.Model):
    __tablename__ = "questions"
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    option1 = db.Column(db.String(200), nullable=False)
    option2 = db.Column(db.String(200), nullable=False)
    option3 = db.Column(db.String(200), nullable=False)
    option4 = db.Column(db.String(200), nullable=False)
    correct_option = db.Column(db.Integer, nullable=False)
    marks = db.Column(db.Integer, nullable=False, default=1)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=False)

class Attempt(db.Model):
    __tablename__ = "attempts"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=False)
    score = db.Column(db.Integer)            # marks earned
    total_questions = db.Column(db.Integer)  # count of questions
    total_marks = db.Column(db.Integer)      # sum of all question marks
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    answers = db.relationship("AttemptAnswer", backref="attempt", lazy=True)
class AttemptAnswer(db.Model):
    __tablename__ = "attempt_answers"

    id = db.Column(db.Integer, primary_key=True)

    attempt_id = db.Column(db.Integer, db.ForeignKey("attempts.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)

    selected_option = db.Column(db.Integer)  

    __table_args__ = (
        db.UniqueConstraint('attempt_id', 'question_id', name='unique_attempt_question'),
    )

class Activity(db.Model):
    __tablename__ = "activities"
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)      
    message = db.Column(db.String(300), nullable=False)  
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)