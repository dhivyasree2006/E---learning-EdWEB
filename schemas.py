from pydantic import BaseModel, EmailStr, field_validator, model_validator
import pydantic
from typing import Optional, List, Any
from datetime import datetime

# ---------------- QUESTIONS ----------------

class QuestionOption(BaseModel):
    text: str

    model_config = {"from_attributes": True}

class Question(BaseModel):
    id: Optional[int] = None
    questionText: str
    questionType: Optional[str] = "mcq"   # mcq / descriptive

    # MCQ fields
    options: Optional[List[QuestionOption]] = None
    correctOptionIndex: Optional[int] = None

    # Descriptive field
    correctAnswerText: Optional[str] = None
    difficulty: Optional[str] = "medium"

    model_config = {"from_attributes": True}


# ---------------- MODULE ----------------

class Module(BaseModel):
    id: Optional[int] = None
    title: str
    contentLink: Optional[str] = None
    documentPath: Optional[str] = None
    quiz: Optional[List[Question]] = []

    model_config = {"from_attributes": True}



# ---------------- USERS ----------------

class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: Optional[str] = "learner"

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    accessibility_enabled: Optional[bool] = False # For the enrollment context
    model_config = {"from_attributes": True}


# ---------------- COURSE ----------------

class CourseBase(BaseModel):
    id: Optional[int] = None
    _id: Optional[int] = None
    title: str
    description: str
    thumbnail: Optional[str] = None
    price: Optional[float] = 0.0
    status: Optional[str] = "Published"

    model_config = {"from_attributes": True}


class CourseCreate(CourseBase):
    modules: Optional[List[Module]] = []
    assessment: Optional[List[Question]] = []

    # ---------------- COURSE RESPONSE ----------------

class CourseResponse(CourseBase):
    id: int
    instructor_id: int
    created_at: datetime
    enrolledStudents: List[int] = pydantic.Field(default=[], validation_alias=pydantic.AliasChoices("enrolledStudents", "enrolments"))
    modules: Optional[List[Module]] = []
    assessment: Optional[List[Question]] = []
    instructor: Optional[UserResponse] = None
    progress: Optional[int] = 0

    @pydantic.field_validator("enrolledStudents", mode="before")
    @classmethod
    def map_enrolments(cls, v, info):
        # If the input is a list of Enrolment objects (from ORM), extract user_ids
        if isinstance(v, list) and v and not isinstance(v[0], int):
            try:
                # Check if it's an Enrolment object by looking for user_id attribute
                return [getattr(e, 'user_id', e) for e in v if hasattr(e, 'user_id') or isinstance(e, int)]
            except:
                return v
        return v

    model_config = {"from_attributes": True}

# ---------------- UPDATE SCHEMAS ----------------

class QuestionUpdate(BaseModel):
    id: Optional[int] = None
    questionText: str
    questionType: Optional[str] = "mcq"
    options: Optional[List[QuestionOption]] = None
    correctOptionIndex: Optional[int] = None
    correctAnswerText: Optional[str] = None
    difficulty: Optional[str] = "medium"

    model_config = {"from_attributes": True}


class ModuleUpdate(BaseModel):
    id: Optional[int] = None
    title: str
    contentLink: Optional[str] = None
    documentPath: Optional[str] = None
    quiz: Optional[List[QuestionUpdate]] = []

    model_config = {"from_attributes": True}


class CourseUpdate(CourseBase):
    modules: Optional[List[ModuleUpdate]] = []
    assessment: Optional[List[QuestionUpdate]] = []




# ---------------- TOKEN ----------------

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    user: UserResponse

    model_config = {"from_attributes": True}

class EnrolmentAccessibilityUpdate(BaseModel):
    accessibility_enabled: bool


# ---------------- QUIZ RESULT ----------------

class QuizResultBase(BaseModel):
    score: int
    total_questions: int

class QuizResultCreate(BaseModel):
    score: Optional[int] = None
    total_questions: int
    answers: Optional[List[Any]] = None

class QuizResultResponse(QuizResultBase):
    id: int
    user_id: int
    module_id: Optional[int] = None
    course_id: Optional[int] = None
    completed_at: datetime
    review: Optional[List[dict]] = None
    userAnswers: Optional[List[Any]] = None
    percentage: Optional[int] = None
    correctCount: Optional[int] = None
    model_config = {"from_attributes": True}

class AdaptiveNextRequest(BaseModel):
    answered_ids: List[int]
    last_answer: Any
    last_difficulty: str

class QuizSubmitRequest(BaseModel):
    answers: List[Any]
    is_adaptive: Optional[bool] = False
    question_ids: Optional[List[int]] = None


# ---------------- PASSWORD RESET ----------------

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


# ---------------- BADGE ----------------

class Badge(BaseModel):
    id: int
    name: str
    description: str
    icon: str
    model_config = {"from_attributes": True}


# ---------------- NOTIFICATION ----------------

class Notification(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ---------------- MESSAGE ----------------

class MessageBase(BaseModel):
    content: str
    receiver_id: int

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    sender_id: int
    is_read: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ---------------- BATCH ----------------

class BatchBase(BaseModel):
    name: str
    course_id: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class BatchCreate(BatchBase):
    pass

class Batch(BatchBase):
    id: int
    instructor_id: int
    students: List[UserResponse] = []
    created_at: datetime
    model_config = {"from_attributes": True}

class AIGenerateRequest(BaseModel):
    topic: str
    questionType: str = "mcq"   # mcq / descriptive
    difficulty: str = "medium"  # easy / medium / hard
    count: Optional[int] = 5
class CleanSpeechRequest(BaseModel):
    text: str

class CleanSpeechResponse(BaseModel):
    cleaned_text: str
    confidence: Optional[float] = None

class CertificateResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    certificate_code: str
    issued_at: datetime
    course_title: Optional[str] = None
    user_name: Optional[str] = None
    
    model_config = {"from_attributes": True}