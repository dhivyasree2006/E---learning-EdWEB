import models, database, auth, schemas, random
from datetime import timedelta, datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os, shutil, csv
from io import StringIO
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel  # Import BaseModel
import rag  # Import the RAG engine
from dotenv import load_dotenv

# Load environment variables at the very beginning
load_dotenv(override=True)

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="EdWeb API (SQLAlchemy)")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- RAG Integration ---
@app.on_event("startup")
def startup_event():
    # Only index content if not already indexed (lazy/persisted)
    if rag.is_indexed():
        print("RAG Index found on disk. Skipping startup indexing.")
        return

    print("Building initial RAG Index...")
    db = database.SessionLocal()
    try:
        courses = db.query(models.Course).filter(models.Course.status == "Published").all()
        # Transform to list of dicts for RAG
        courses_data = []
        for c in courses:
            c_dict = {
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "modules": [{"id": m.id, "title": m.title, "contentLink": m.contentLink} for m in c.modules]
            }
            courses_data.append(c_dict)
        
        # Build Index
        rag.index_content(courses_data)
        print("RAG Index built and persisted successfully.")
    except Exception as e:
        print(f"Failed to build RAG index: {e}")
    finally:
        db.close()

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    user_query = request.message
    
    # 1. Retrieve Context
    context_chunks = rag.retrieve(user_query)
    
    # 2. Generate Response
    response_text = rag.generate_response(user_query, context_chunks)
    
    return {"response": response_text}

@app.post("/api/ai/clean-speech", response_model=schemas.CleanSpeechResponse)
async def clean_speech_endpoint(request: schemas.CleanSpeechRequest):
    """
    Intelligently reconstructs fragmented/impaired speech using Groq.
    Part of the Accessibility Voice Mode feature.
    """
    try:
        cleaned = rag.clean_speech(request.text)
        return {"cleaned_text": cleaned, "confidence": None}
    except Exception as e:
        print(f"Clean Speech Endpoint Error: {e}")
        # Always return something safe for accessibility users
        return {"cleaned_text": request.text, "confidence": None}

@app.post("/api/ai/generate-questions")
async def ai_generate_questions(request: schemas.AIGenerateRequest, current_user: dict = Depends(auth.get_current_user)):
    if current_user["role"] != "instructor":
        raise HTTPException(status_code=403, detail="Only instructors can generate questions")
    
    questions = rag.generate_questions(request.topic, request.questionType, request.count)
    return {"questions": questions}


# Global Exception Handler
@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        import traceback
        with open("backend_errors_global.log", "a") as f:
            f.write(f"\nUnhandled Error: {request.method} {request.url}\n")
            f.write(traceback.format_exc())
            print(traceback.format_exc()) # Print to console too
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "error": str(e)}
        )


# Ensure upload directory exists
UPLOAD_DIR = "uploads/documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
def read_root():
    return {"message": "EdWeb API (SQLAlchemy) is running"}

@app.post("/auth/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(
        name=user.name,
        email=user.email,
        password=hashed_password,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/auth/login", response_model=schemas.Token)
def login(user_data: schemas.UserLogin, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == user_data.username).first()
    
    if not user or not auth.verify_password(user_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={
            "sub": user.email, 
            "role": user.role,
            "id": user.id
        }, 
        expires_delta=access_token_expires
    )
    
    # We return the user object as well for the frontend
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "role": user.role,
        "user": user
    }

@app.post("/auth/forgot-password")
def forgot_password(request: schemas.ForgotPasswordRequest, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user:
        # For security, don't reveal if user doesn't exist, but frontend logic here says 
        # "If an account exists with this email, you will receive a reset link."
        # However, it returns success: true.
        return {"message": "If an account exists, an OTP has been sent"}
    
    # Generate 6-digit OTP
    otp = f"{random.randint(100000, 999999)}"
    user.reset_otp = otp
    user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
    db.commit()
    
    # In a real app, send email. Here, we print it to the console.
    print(f"\n[RESET OTP] Email: {user.email}, OTP: {otp}\n")
    
    return {"message": "OTP sent to email"}

@app.post("/auth/verify-otp")
def verify_otp(request: schemas.VerifyOtpRequest, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user or user.reset_otp != request.otp or (user.otp_expiry and user.otp_expiry < datetime.utcnow()):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    return {"message": "OTP verified"}

@app.post("/auth/reset-password")
def reset_password(request: schemas.ResetPasswordRequest, db: Session = Depends(database.get_db)):
    # Frontend passes 'token' as the OTP in verifyOtp then 'token' again in resetPassword
    # Looking at AuthContext.jsx: 
    # verifyOtp sends {email, otp}
    # resetPassword sends {token, new_password} where 'token' is likely the OTP or email.
    # In ForgotPasswordPage.jsx, it doesn't even use verifyOtp yet? 
    # Actually, let's assume 'token' in ResetPasswordRequest is the OTP.
    
    user = db.query(models.User).filter(models.User.reset_otp == request.token).first()
    if not user or (user.otp_expiry and user.otp_expiry < datetime.utcnow()):
        raise HTTPException(status_code=400, detail="Invalid token or expired OTP")
    
    user.password = auth.get_password_hash(request.new_password)
    user.reset_otp = None # Clear OTP after use
    user.otp_expiry = None
    db.commit()
    
    return {"message": "Password reset successfully"}

@app.get("/courses", response_model=List[dict])
def get_all_courses(q: Optional[str] = None, db: Session = Depends(database.get_db)):
    # Only return published courses for the general explore feed
    query = db.query(models.Course).filter(models.Course.status == "Published")
    
    if q:
        query = query.filter(
            or_(
                models.Course.title.ilike(f"%{q}%"),
                models.Course.description.ilike(f"%{q}%")
            )
        )
    
    courses = query.all()
    
    result = []
    for c in courses:
        result.append({
            "id": c.id,
            "_id": c.id,
            "title": c.title,
            "description": c.description,
            "thumbnail": c.thumbnail,
            "price": c.price,
            "status": c.status,
            "instructor_id": c.instructor_id,
            "enrolledStudents": [e.user_id for e in c.enrolments],
            "progress": 0,
            "instructor": schemas.UserResponse.from_orm(c.instructor) if c.instructor else None
        })
    return result

@app.get("/courses/my-courses", response_model=List[dict])
def get_my_courses(
    status: Optional[str] = None, 
    q: Optional[str] = None,
    current_user: dict = Depends(auth.get_current_user), 
    db: Session = Depends(database.get_db)
):
    user_id = current_user["id"]
    if current_user["role"] == "instructor":
        query = db.query(models.Course).filter(models.Course.instructor_id == user_id)
    else:
        # Get courses the user is enrolled in
        enrolments = db.query(models.Enrolment).filter(models.Enrolment.user_id == user_id).all()
        course_ids = [e.course_id for e in enrolments]
        
        # Learners should ONLY see 'Published' courses in their learning list
        query = db.query(models.Course).filter(
            models.Course.id.in_(course_ids),
            models.Course.status == "Published"
        )
    
    if status and status != 'All':
        query = query.filter(models.Course.status == status)
    
    if q:
        query = query.filter(
            or_(
                models.Course.title.ilike(f"%{q}%"),
                models.Course.description.ilike(f"%{q}%")
            )
        )

    courses = query.all()
    
    result = []
    for c in courses:
        progress = 0
        if current_user["role"] == "learner":
            total_modules = len(c.modules)
            if total_modules > 0:
                completed_modules = db.query(models.QuizResult.module_id).filter(
                    models.QuizResult.user_id == user_id,
                    models.QuizResult.module_id.in_([m.id for m in c.modules])
                ).distinct().count()
                progress = int((completed_modules / total_modules) * 100)
                
        result.append({
            "id": c.id,
            "_id": c.id,
            "title": c.title,
            "description": c.description,
            "thumbnail": c.thumbnail,
            "price": c.price,
            "status": c.status,
            "instructor_id": c.instructor_id,
            "enrolledStudents": [e.user_id for e in c.enrolments],
            "progress": progress,
            "instructor": schemas.UserResponse.from_orm(c.instructor) if c.instructor else None
        })
    return result

@app.post("/courses", response_model=dict)
def create_course(course: schemas.CourseCreate, current_user: dict = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user["role"] != "instructor":
        raise HTTPException(status_code=403, detail="Only instructors can create courses")
    
    new_course = models.Course(
        title=course.title,
        description=course.description,
        thumbnail=course.thumbnail,
        price=course.price,
        status=course.status,
        instructor_id=current_user["id"]
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    
    # Create modules if provided
    for mod_data in course.modules:
        new_module = models.Module(
            title=mod_data.title,
            contentLink=mod_data.contentLink,
            course_id=new_course.id
        )
        db.add(new_module)
        db.commit()
        db.refresh(new_module)
        
        for q_data in mod_data.quiz:
            new_q = models.Question(
                questionText=q_data.questionText,
                questionType=q_data.questionType or "mcq",
                correctOptionIndex=q_data.correctOptionIndex,
                correctAnswerText=q_data.correctAnswerText,
                difficulty=q_data.difficulty or "medium",
                module_id=new_module.id
            )
            db.add(new_q)
            db.commit()
            db.refresh(new_q)
            
            if q_data.options:
                for opt_data in q_data.options:
                    new_opt = models.QuestionOption(
                        text=opt_data.text,
                        question_id=new_q.id
                    )
                    db.add(new_opt)
    
    # Create course-level assessment questions if provided
    for q_data in course.assessment:
        new_q = models.Question(
            questionText=q_data.questionText,
            questionType=q_data.questionType or "mcq",
            correctOptionIndex=q_data.correctOptionIndex,
            correctAnswerText=q_data.correctAnswerText,
            difficulty=q_data.difficulty or "medium",
            course_id=new_course.id
        )
        db.add(new_q)
        db.commit()
        db.refresh(new_q)
        
        if q_data.options:
            for opt_data in q_data.options:
                new_opt = models.QuestionOption(
                    text=opt_data.text,
                    question_id=new_q.id
                )
                db.add(new_opt)
    
    # Notify all learners about the new course
    learners = db.query(models.User).filter(models.User.role == "learner").all()
    for learner in learners:
        notif = models.Notification(
            user_id=learner.id,
            title="New Course Available",
            message=f"A new course '{new_course.title}' has been published. Check it out!",
            type="course_launch",
            is_read=False,
            created_at=datetime.utcnow()
        )
        db.add(notif)

    db.commit()
    return {**schemas.CourseResponse.from_orm(new_course).dict(), "_id": new_course.id}

@app.put("/courses/{course_id}/status")
def update_course_status(course_id: int, status_update: dict, current_user: dict = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if course.instructor_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    course.status = status_update.get("status", "Draft")
    db.commit()

    # If status is Published, notify all learners
    if course.status == "Published":
        learners = db.query(models.User).filter(models.User.role == "learner").all()
        for learner in learners:
            notification = models.Notification(
                user_id=learner.id,
                title="New Course Launched!",
                message=f"Instructor {current_user['name']} has launched a new course: {course.title}",
                type="course_launch"
            )
            db.add(notification)
        db.commit()

    return {"message": "Status updated", "status": course.status}

@app.put("/courses/{course_id}", response_model=dict)
def update_course(course_id: int, course_update: schemas.CourseUpdate, current_user: dict = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user["role"] != "instructor":
        raise HTTPException(status_code=403, detail="Only instructors can update courses")
    
    db_course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if db_course.instructor_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update Course Metadata
    db_course.title = course_update.title
    db_course.description = course_update.description
    db_course.thumbnail = course_update.thumbnail
    db_course.price = course_update.price
    db_course.status = course_update.status
    
    # Handle Modules
    incoming_module_ids = [m.id for m in course_update.modules if m.id is not None]
    
    # Delete modules not in update
    db.query(models.Module).filter(
        models.Module.course_id == course_id,
        ~models.Module.id.in_(incoming_module_ids)
    ).delete(synchronize_session=False)
    
    for mod_data in course_update.modules:
        if mod_data.id:
            db_module = db.query(models.Module).filter(models.Module.id == mod_data.id).first()
            if db_module:
                db_module.title = mod_data.title
                db_module.contentLink = mod_data.contentLink
        else:
            db_module = models.Module(
                title=mod_data.title,
                contentLink=mod_data.contentLink,
                course_id=course_id
            )
            db.add(db_module)
            db.flush()
            
        # Handle Quiz for this module
        incoming_q_ids = [q.id for q in mod_data.quiz if q.id is not None]
        db.query(models.Question).filter(
            models.Question.module_id == db_module.id,
            ~models.Question.id.in_(incoming_q_ids)
        ).delete(synchronize_session=False)
        
        for q_data in mod_data.quiz:
            if q_data.id:
                db_q = db.query(models.Question).filter(models.Question.id == q_data.id).first()
                if db_q:
                    db_q.questionText = q_data.questionText
                    db_q.correctOptionIndex = q_data.correctOptionIndex
            else:
                db_q = models.Question(
                    questionText=q_data.questionText,
                    correctOptionIndex=q_data.correctOptionIndex,
                    module_id=db_module.id
                )
                db.add(db_q)
                db.flush()
            
            # Recreate options for simplicity
            db.query(models.QuestionOption).filter(models.QuestionOption.question_id == db_q.id).delete()
            for opt_data in q_data.options:
                db.add(models.QuestionOption(text=opt_data.text, question_id=db_q.id))

    # Handle Course-Level Assessment
    incoming_ass_ids = [q.id for q in course_update.assessment if q.id is not None]
    db.query(models.Question).filter(
        models.Question.course_id == course_id,
        ~models.Question.id.in_(incoming_ass_ids)
    ).delete(synchronize_session=False)

    for q_data in course_update.assessment:
        if q_data.id:
            db_q = db.query(models.Question).filter(models.Question.id == q_data.id).first()
            if db_q:
                db_q.questionText = q_data.questionText
                db_q.questionType = q_data.questionType or "mcq"
                db_q.correctOptionIndex = q_data.correctOptionIndex
                db_q.correctAnswerText = q_data.correctAnswerText
                db_q.difficulty = q_data.difficulty or "medium"
        else:
            db_q = models.Question(
                questionText=q_data.questionText,
                questionType=q_data.questionType or "mcq",
                correctOptionIndex=q_data.correctOptionIndex,
                correctAnswerText=q_data.correctAnswerText,
                difficulty=q_data.difficulty or "medium",
                course_id=course_id
            )
            db.add(db_q)
            db.flush()

        # Recreate options
        db.query(models.QuestionOption).filter(models.QuestionOption.question_id == db_q.id).delete()
        if q_data.options:
            for opt_data in q_data.options:
                db.add(models.QuestionOption(text=opt_data.text, question_id=db_q.id))

    db.commit()
    return {"message": "Course updated successfully"}

@app.delete("/courses/{course_id}")
def delete_course(course_id: int, current_user: dict = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user["role"] != "instructor":
        raise HTTPException(status_code=403, detail="Only instructors can delete courses")
        
    db_course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    if db_course.instructor_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Deletion is handled by cascades in models.py
    db.delete(db_course)
    db.commit()
    return {"message": "Course deleted successfully"}

import traceback

@app.get("/courses/my-learners", response_model=List[dict])
def get_my_learners(current_user: dict = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    try:
        if current_user["role"] != "instructor":
            raise HTTPException(status_code=403, detail="Only instructors can access learner reports")
        
        instructor_id = current_user["id"]
        
        # Courses owned by this instructor
        my_courses = db.query(models.Course).filter(models.Course.instructor_id == instructor_id).all()
        my_course_ids = [c.id for c in my_courses]
        
        # Find all enrollments for these courses
        relevant_enrolments = db.query(models.Enrolment).filter(models.Enrolment.course_id.in_(my_course_ids)).all()
        
        # Group by student and calculate progress
        student_map = {}
        for e in relevant_enrolments:
            student = e.user
            course = e.course
            
            if not student or not course:
                continue
                
            # Get total modules in this course to calculate progress for this specific course/student pair
            total_modules = len(course.modules)
            course_progress = 0
            if total_modules > 0:
                completed_modules = db.query(models.QuizResult.module_id).filter(
                    models.QuizResult.user_id == student.id,
                    models.QuizResult.module_id.in_([m.id for m in course.modules])
                ).distinct().count()
                course_progress = int((completed_modules / total_modules) * 100)

            # Create student entry if it doesn't exist
            if student.id not in student_map:
                student_map[student.id] = {
                    "id": student.id,
                    "name": student.name or "User",
                    "email": student.email,
                    "courses": [],
                    "progress_total": 0,
                    "course_count": 0,
                    "badges": [],
                    "status": "Active",
                    "accessibility_enabled": e.accessibility_enabled,
                    "enrolment_id": e.id,
                    "lastActive": student.created_at.strftime("%Y-%m-%d") if student.created_at else "Recently",
                    "avatar": student.name[0].upper() if (student.name and len(student.name) > 0) else "U"
                }
            
            student_data = student_map[student.id]
            student_data["courses"].append(course.title)
            student_data["progress_total"] += course_progress
            student_data["course_count"] += 1
            if course_progress == 100 and "Legend" not in student_data["badges"]:
                student_data["badges"].append("Legend")

        # Finalize progress (average)
        result = []
        for s_id, data in student_map.items():
            progress_total = data.get("progress_total", 0)
            course_count = data.get("course_count", 0)
            data["progress"] = int(progress_total / course_count) if course_count > 0 else 0
            if not data["badges"]:
                data["badges"] = ["Newbie"]
            # Remove intermediate fields
            data.pop("progress_total", None)
            data.pop("course_count", None)
            result.append(data)
        
        return result
    except Exception as e:
        print("ERROR in get_my_learners:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/courses/{course_id}")
def get_course(course_id: int, current_user_opt: Optional[dict] = Depends(auth.get_current_user_optional), db: Session = Depends(database.get_db)):
    try:
        course = db.query(models.Course).filter(models.Course.id == course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # Security: If not published and user is not the instructor, deny access
        if course.status != "Published":
            is_instructor = current_user_opt and current_user_opt.get("role") == "instructor" and course.instructor_id == current_user_opt.get("id")
            if not is_instructor:
                raise HTTPException(status_code=403, detail="This course is currently not available (Draft/Archived)")
        
        # Batch Timing Check for Learners
        if current_user_opt and current_user_opt.get("role") == "learner":
            user_id = current_user_opt.get("id")
            # Find if user is in any batch for this specific course
            batch = db.query(models.Batch).join(models.Batch.students).filter(
                models.Batch.course_id == course_id,
                models.User.id == user_id
            ).first()
            
            if batch and (batch.start_time or batch.end_time):
                now = datetime.utcnow()
                if batch.start_time and now < batch.start_time:
                    raise HTTPException(
                        status_code=403, 
                        detail=f"Your batch access starts at {batch.start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC"
                    )
                if batch.end_time and now > batch.end_time:
                    raise HTTPException(
                        status_code=403, 
                        detail=f"Your batch access ended at {batch.end_time.strftime('%Y-%m-%d %H:%M:%S')} UTC"
                    )
        
        return {
            "id": course.id,
            "_id": course.id,
            "title": course.title,
            "description": course.description,
            "thumbnail": course.thumbnail,
            "price": course.price,
            "status": course.status,
            "instructor_id": course.instructor_id,
            "enrolledStudents": [e.user_id for e in course.enrolments],
            "instructor": {
                "id": course.instructor.id if course.instructor else None,
                "name": course.instructor.name if course.instructor else "Unknown",
                "email": course.instructor.email if course.instructor else ""
            },
                "modules": [
                    {
                        "id": m.id,
                        "title": m.title,
                        "contentLink": m.contentLink,
                        "quiz": [
                            {
                                "id": q.id,
                                "questionText": q.questionText,
                                "questionType": q.questionType,
                                "options": [{"text": o.text} for o in q.options]
                                # Removed correctOptionIndex for learner security
                            } for q in m.quiz
                        ]
                    } for m in course.modules
                ],
                "assessment": [
                    {
                        "id": q.id,
                        "questionText": q.questionText,
                        "questionType": q.questionType,
                        "options": [{"text": o.text} for o in q.options],
                        # Only instructor sees answers and difficulty in course view
                        **({
                            "correctOptionIndex": q.correctOptionIndex,
                            "correctAnswerText": q.correctAnswerText,
                            "difficulty": q.difficulty
                        } if (current_user_opt and current_user_opt.get("role") == "instructor" and course.instructor_id == current_user_opt.get("id")) else {})
                    } for q in course.assessment
                ],
                "isAssessmentCompleted": db.query(models.QuizResult).filter(
                    models.QuizResult.user_id == current_user_opt.get("id"),
                    models.QuizResult.course_id == course_id
                ).first() is not None if (current_user_opt and current_user_opt.get("role") == "learner") else False,
                "hasCertificate": db.query(models.Certificate).filter(
                    models.Certificate.user_id == current_user_opt.get("id"),
                    models.Certificate.course_id == course_id
                ).first() is not None if (current_user_opt and current_user_opt.get("role") == "learner") else False
        }
    except Exception as e:
        import traceback
        with open("backend_errors.log", "a") as f:
            f.write(f"\nError in get_course({course_id}):\n")
            f.write(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/courses/{course_id}/enroll")
def enroll_in_course(course_id: int, current_user: dict = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if already enrolled
    existing_enrolment = db.query(models.Enrolment).filter(
        models.Enrolment.user_id == current_user["id"],
        models.Enrolment.course_id == course_id
    ).first()
    
    if existing_enrolment:
        return {"message": "Already enrolled"}
    
    new_enrolment = models.Enrolment(
        user_id=current_user["id"],
        course_id=course_id
    )
    db.add(new_enrolment)
    db.commit()
    
    return {"message": "Enrolled successfully"}

@app.put("/api/instructor/enrolments/{enrolment_id}/accessibility")
def update_accessibility_status(enrolment_id: int, update: schemas.EnrolmentAccessibilityUpdate, current_user: dict = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user["role"] != "instructor":
        raise HTTPException(status_code=403, detail="Only instructors can toggle accessibility")
    
    enrolment = db.query(models.Enrolment).filter(models.Enrolment.id == enrolment_id).first()
    if not enrolment:
        raise HTTPException(status_code=404, detail="Enrolment not found")
    
    # Verify instructor owns the course
    if enrolment.course.instructor_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    enrolment.accessibility_enabled = update.accessibility_enabled
    db.commit()
    return {"message": "Accessibility status updated", "accessibility_enabled": enrolment.accessibility_enabled}

@app.get("/api/learner/courses/{course_id}/accessibility")
def get_learner_accessibility_status(course_id: int, current_user: dict = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    enrolment = db.query(models.Enrolment).filter(
        models.Enrolment.user_id == current_user["id"],
        models.Enrolment.course_id == course_id
    ).first()
    
    if not enrolment:
        raise HTTPException(status_code=404, detail="Enrolment not found")
    
    return {"accessibility_enabled": enrolment.accessibility_enabled}

@app.post("/modules/{module_id}/quiz/submit", response_model=schemas.QuizResultResponse)
def submit_quiz_result(module_id: int, result: schemas.QuizResultCreate, current_user: dict = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    try:
        module = db.query(models.Module).filter(models.Module.id == module_id).first()
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")
        
        correct_count = 0
        total_questions = len(module.quiz)
        
        if result.answers is not None:
            # Align with the order in CoursePage.jsx (indices 0..N)
            for i, q in enumerate(module.quiz):
                if i >= len(result.answers):
                    break
                
                user_answer = result.answers[i]
                if q.questionType == 'mcq' or (q.options and len(q.options) > 0):
                    try:
                        if int(user_answer) == q.correctOptionIndex:
                            correct_count += 1
                    except (ValueError, TypeError):
                        pass
                else: # descriptive
                    if str(user_answer).strip().lower() == (q.correctAnswerText or "").strip().lower():
                        correct_count += 1
        
        percentage = int((correct_count / total_questions * 100)) if total_questions > 0 else 0

        # Check if user already submitted a result for this module
        existing_result = db.query(models.QuizResult).filter(
            models.QuizResult.user_id == current_user["id"],
            models.QuizResult.module_id == module_id
        ).first()
        
        if existing_result:
            # Update existing result instead of failing
            existing_result.score = correct_count
            existing_result.total_questions = total_questions
            existing_result.answers = result.answers
            existing_result.completed_at = datetime.utcnow()
            db.commit()
            db.refresh(existing_result)
            new_result = existing_result
        else:
            new_result = models.QuizResult(
                user_id=current_user["id"],
                module_id=module_id,
                score=correct_count,
                total_questions=total_questions,
                answers=result.answers
            )
            db.add(new_result)
            db.commit()
            db.refresh(new_result)

        # Check for course completion and award badge
        course = module.course
        if course:
            total_modules = len(course.modules)
            completed_modules = db.query(models.QuizResult.module_id).filter(
                models.QuizResult.user_id == current_user["id"],
                models.QuizResult.module_id.in_([m.id for m in course.modules])
            ).distinct().count()

            if total_modules > 0 and completed_modules == total_modules:
                # Award Badge
                badge_name = f"{course.title} Graduate"
                badge = db.query(models.Badge).filter(models.Badge.name == badge_name).first()
                if not badge:
                    badge = models.Badge(name=badge_name, description=f"Completed {course.title}", icon="Award")
                    db.add(badge)
                    db.flush()
                
                # Use scalar ID from current_user
                user_id = current_user["id"]
                user_obj = db.query(models.User).get(user_id)
                
                if badge not in user_obj.badges:
                    user_obj.badges.append(badge)
                    notif = models.Notification(user_id=user_id, title="Badge Earned!", message=f"Earned '{badge_name}'", type="success")
                    db.add(notif)
                
                # Batch logic
                quiz_results = db.query(models.QuizResult).filter(
                    models.QuizResult.user_id == user_id,
                    models.QuizResult.module_id.in_([m.id for m in course.modules])
                ).all()
                
                t_score = 0
                t_count = 0
                for qr in quiz_results:
                    if qr.total_questions and qr.total_questions > 0:
                        t_score += (qr.score / qr.total_questions) * 100
                        t_count += 1
                
                if t_count > 0:
                    avg = t_score / t_count
                    b_name = "Bronze"
                    if avg >= 90: b_name = "Diamond"
                    elif avg >= 80: b_name = "Gold"
                    elif avg >= 70: b_name = "Silver"
                    
                    batch = db.query(models.Batch).filter(models.Batch.course_id == course.id, models.Batch.name == b_name).first()
                    if not batch:
                        batch = models.Batch(name=b_name, course_id=course.id, instructor_id=course.instructor_id)
                        db.add(batch)
                        db.flush()
                    
                    if user_obj not in batch.students:
                        batch.students.append(user_obj)
                        notif2 = models.Notification(user_id=user_id, title="Batch Assigned!", message=f"Assigned to {b_name} batch", type="info")
                        db.add(notif2)
                
                db.commit()

        return {
            "id": new_result.id,
            "user_id": new_result.user_id,
            "module_id": new_result.module_id,
            "score": new_result.score,
            "total_questions": new_result.total_questions,
            "completed_at": new_result.completed_at,
            "percentage": percentage,
            "correctCount": correct_count,
            "totalQuestions": total_questions,
            "review": [
                {
                    "id": q.id,
                    "questionText": q.questionText,
                    "questionType": q.questionType,
                    "options": [{"text": o.text} for o in q.options],
                    "correctOptionIndex": q.correctOptionIndex,
                    "correctAnswerText": q.correctAnswerText
                } for q in module.quiz
            ],
            "userAnswers": result.answers
        }

    except Exception as e:
        import traceback
        with open("quiz_submit_error.log", "a") as f:
            f.write(f"\n--- {datetime.now()} ---\n")
            f.write(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quizzes/{course_id}")
def get_quiz_questions(course_id: int, current_user: dict = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    # Check if already completed
    existing_result = db.query(models.QuizResult).filter(
        models.QuizResult.user_id == current_user["id"],
        models.QuizResult.course_id == course_id
    ).first()
    
    if existing_result:
        # Fetch questions based on stored IDs if available, otherwise course questions
        if existing_result.question_ids:
            questions = db.query(models.Question).filter(models.Question.id.in_(existing_result.question_ids)).all()
            q_map = {q.id: q for q in questions}
            sorted_review_questions = [q_map[qid] for qid in existing_result.question_ids if qid in q_map]
        else:
            sorted_review_questions = db.query(models.Question).filter(models.Question.course_id == course_id).all()
        
        # Return result and detailed review
        return {
            "completed": True,
            "score": existing_result.score,
            "totalQuestions": existing_result.total_questions,
            "percentage": int((existing_result.score / existing_result.total_questions * 100) if existing_result.total_questions and existing_result.total_questions > 0 else 0),
            "userAnswers": existing_result.answers,
            "completed_at": existing_result.completed_at,
            "certificate": db.query(models.Certificate).filter(models.Certificate.user_id == current_user["id"], models.Certificate.course_id == course_id).first() is not None,
            "review": [
                {
                    "id": q.id,
                    "questionText": q.questionText,
                    "questionType": q.questionType,
                    "options": [{"text": o.text} for o in q.options],
                    "correctOptionIndex": q.correctOptionIndex,
                    "correctAnswerText": q.correctAnswerText
                } for q in sorted_review_questions
            ]
        }

    # Check enrollment
    enrollment = db.query(models.Enrolment).filter(
        models.Enrolment.course_id == course_id,
        models.Enrolment.user_id == current_user["id"]
    ).first()
    if not enrollment:
        raise HTTPException(status_code=403, detail="You must be enrolled in the course to access the assessment.")
    
    questions = db.query(models.Question).filter(models.Question.course_id == course_id).all()
    
    return {
        "questions": [
            {
                "id": q.id,
                "questionText": q.questionText,
                "questionType": q.questionType,
                "options": [{"text": o.text} for o in q.options],
                # Do not return correct answers to the student!
            } for q in questions
        ]
    }

@app.post("/quizzes/{course_id}/adaptive/start")
def start_adaptive_quiz(course_id: int, current_user: dict = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    # Check if already completed
    existing_result = db.query(models.QuizResult).filter(
        models.QuizResult.user_id == current_user["id"],
        models.QuizResult.course_id == course_id
    ).first()
    
    if existing_result:
        # Fetch questions based on stored IDs if available
        if existing_result.question_ids:
            questions = db.query(models.Question).filter(models.Question.id.in_(existing_result.question_ids)).all()
            q_map = {q.id: q for q in questions}
            sorted_review_questions = [q_map[qid] for qid in existing_result.question_ids if qid in q_map]
        else:
            sorted_review_questions = db.query(models.Question).filter(models.Question.course_id == course_id).all()

        return {
            "completed": True,
            "score": existing_result.score,
            "totalQuestions": existing_result.total_questions,
            "percentage": int((existing_result.score / existing_result.total_questions * 100) if existing_result.total_questions > 0 else 0),
            "userAnswers": existing_result.answers,
            "certificate": db.query(models.Certificate).filter(models.Certificate.user_id == current_user["id"], models.Certificate.course_id == course_id).first() is not None,
            "review": [
                {
                    "id": q.id,
                    "questionText": q.questionText,
                    "questionType": q.questionType,
                    "options": [{"text": o.text} for o in q.options],
                    "correctOptionIndex": q.correctOptionIndex,
                    "correctAnswerText": q.correctAnswerText
                } for q in sorted_review_questions
            ]
        }

    # Check enrollment
    enrollment = db.query(models.Enrolment).filter(
        models.Enrolment.course_id == course_id,
        models.Enrolment.user_id == current_user["id"]
    ).first()
    if not enrollment:
         raise HTTPException(status_code=403, detail="Not enrolled")

    # Start with a medium question
    question = db.query(models.Question).filter(
        models.Question.course_id == course_id,
        models.Question.difficulty == "medium"
    ).first()

    if not question:
        # Try fallback to any question in DB
        question = db.query(models.Question).filter(models.Question.course_id == course_id).first()

    # If STILL no question, generate one via AI
    if not question:
        course = db.query(models.Course).get(course_id)
        if course:
            ai_q_data = rag.generate_single_adaptive_question(course.title, "medium", "mcq", course.description)
            if ai_q_data:
                new_q = models.Question(
                    questionText=ai_q_data.get("questionText"),
                    questionType=ai_q_data.get("questionType", "mcq"),
                    difficulty="medium",
                    course_id=course_id,
                    correctOptionIndex=ai_q_data.get("correctOptionIndex"),
                    correctAnswerText=ai_q_data.get("correctAnswerText")
                )
                db.add(new_q)
                db.flush()
                
                if ai_q_data.get("options"):
                    for opt in ai_q_data["options"]:
                        db.add(models.QuestionOption(text=opt["text"], question_id=new_q.id))
                
                db.commit()
                question = new_q
                print(f"AI Generated First Medium Question: {question.id}")

    if not question:
        raise HTTPException(status_code=404, detail="No questions found and AI generation failed.")

    return {
        "question": {
            "id": question.id,
            "questionText": question.questionText,
            "questionType": question.questionType,
            "difficulty": question.difficulty,
            "options": [{"text": o.text} for o in question.options]
        }
    }

@app.post("/quizzes/{course_id}/adaptive/next")
def next_adaptive_question(course_id: int, request: schemas.AdaptiveNextRequest, current_user: dict = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    # 1. Identify the last question answered (the last ID in answered_ids)
    if not request.answered_ids:
        raise HTTPException(status_code=400, detail="answered_ids cannot be empty")
    
    last_q_id = request.answered_ids[-1]
    last_q = db.query(models.Question).filter(models.Question.id == last_q_id).first()
    if not last_q:
        raise HTTPException(status_code=404, detail="Last question not found")

    # 2. Evaluate if the last answer was correct
    is_correct = False
    if last_q.questionType == "mcq":
        try:
            is_correct = int(request.last_answer) == last_q.correctOptionIndex
        except (ValueError, TypeError):
            is_correct = False
    else:
        is_correct = str(request.last_answer).strip().lower() == (last_q.correctAnswerText or "").strip().lower()

    # 3. Determine next difficulty
    diff_map = {"easy": 1, "medium": 2, "hard": 3}
    rev_diff_map = {1: "easy", 2: "medium", 3: "hard"}
    
    curr_level = diff_map.get(request.last_difficulty, 2)
    if is_correct:
        next_level = min(curr_level + 1, 3)
    else:
        next_level = max(curr_level - 1, 1)
    
    target_diff = rev_diff_map[next_level]
    
    # 4. Find next question in database with target difficulty
    question = db.query(models.Question).filter(
        models.Question.course_id == course_id,
        models.Question.difficulty == target_diff,
        ~models.Question.id.in_(request.answered_ids)
    ).first()
    
    # 5. If not in DB, try AI Generation for this specific difficulty
    if not question:
        course = db.query(models.Course).get(course_id)
        if course:
            topic = course.title
            context = course.description
            q_type = last_q.questionType if last_q else "mcq"
            
            ai_q_data = rag.generate_single_adaptive_question(topic, target_diff, q_type, context)
            
            if ai_q_data:
                # Save AI generated question
                new_q = models.Question(
                    questionText=ai_q_data.get("questionText"),
                    questionType=ai_q_data.get("questionType", "mcq"),
                    difficulty=target_diff,
                    course_id=course_id,
                    correctOptionIndex=ai_q_data.get("correctOptionIndex"),
                    correctAnswerText=ai_q_data.get("correctAnswerText")
                )
                db.add(new_q)
                db.flush()
                
                if ai_q_data.get("options"):
                    for opt in ai_q_data["options"]:
                        db.add(models.QuestionOption(text=opt["text"], question_id=new_q.id))
                
                db.commit()
                question = new_q
                print(f"AI Generated New {target_diff.upper()} Question: {question.id}")

    # 6. Final fallback: Any remaining question in DB
    if not question:
        question = db.query(models.Question).filter(
            models.Question.course_id == course_id,
            ~models.Question.id.in_(request.answered_ids)
        ).first()
        
    if not question:
        return {"finished": True}

    return {
        "finished": False,
        "question": {
            "id": question.id,
            "questionText": question.questionText,
            "questionType": question.questionType,
            "difficulty": question.difficulty,
            "options": [{"text": o.text} for o in question.options]
        }
    }

@app.post("/quizzes/{course_id}/submit")
def submit_course_quiz(course_id: int, request: schemas.QuizSubmitRequest, current_user: dict = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if request.is_adaptive:
        questions = db.query(models.Question).filter(models.Question.id.in_(request.question_ids)).all()
        # Sort questions to match the order of answer ids provided
        id_to_q = {q.id: q for q in questions}
        sorted_questions = [id_to_q[qid] for qid in request.question_ids if qid in id_to_q]
    else:
        sorted_questions = db.query(models.Question).filter(models.Question.course_id == course_id).all()

    score = 0
    total = len(sorted_questions)
    
    for i, q in enumerate(sorted_questions):
        if i >= len(request.answers): break
        user_answer = request.answers[i]
        
        if q.questionType == "mcq":
            if user_answer is not None and int(user_answer) == q.correctOptionIndex:
                score += 1
        else: # descriptive
            if str(user_answer).strip().lower() == (q.correctAnswerText or "").strip().lower():
                score += 1
                
    percentage = (score / total * 100) if total > 0 else 0
    
    # Save results (using module_id=None or create a separate table for final assessment results)
    # The models currently only have QuizResult with module_id.
    # We'll use module_id=None if allowed or just save it.
    # Looking at models.py, QuizResult has module_id = Column(Integer, ForeignKey("modules.id"))
    # it doesn't say nullable=False, so let's hope it works.
    
    # Check if already submitted
    existing_result = db.query(models.QuizResult).filter(
        models.QuizResult.user_id == current_user["id"],
        models.QuizResult.course_id == course_id
    ).first()
    if existing_result:
        raise HTTPException(status_code=400, detail="You have already completed the final assessment for this course.")

    res = models.QuizResult(
        user_id = current_user["id"],
        course_id = course_id,
        score = score, # score is already raw count here
        total_questions = total,
        answers = request.answers,
        question_ids = request.question_ids if request.is_adaptive else [q.id for q in sorted_questions]
    )
    db.add(res)
    db.commit()
    
    badge_awarded = False
    certificate_generated = False
    
    if percentage >= 50:
        # Award Certificate
        import uuid
        cert = models.Certificate(
            user_id = current_user["id"],
            course_id = course_id,
            certificate_code = f"CERT-{uuid.uuid4().hex[:8].upper()}"
        )
        db.add(cert)
        certificate_generated = True
        
        # Award Master Badge
        course = db.query(models.Course).get(course_id)
        badge_name = f"{course.title} Master"
        badge = db.query(models.Badge).filter(models.Badge.name == badge_name).first()
        if not badge:
            badge = models.Badge(name=badge_name, description=f"Mastered {course.title}", icon="Star")
            db.add(badge)
            db.flush()
        
        user = db.query(models.User).get(current_user["id"])
        if badge not in user.badges:
            user.badges.append(badge)
            badge_awarded = True

    db.commit()
    
    return {
        "score": score,
        "totalQuestions": total,
        "percentage": int(percentage),
        "badgeAwarded": badge_awarded,
        "certificate": certificate_generated
    }

# --- New Feature Endpoints ---

# Notifications
@app.get("/notifications", response_model=List[schemas.Notification])
def get_notifications(current_user: dict = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    return db.query(models.Notification).filter(models.Notification.user_id == current_user["id"]).order_by(models.Notification.created_at.desc()).all()

@app.put("/notifications/{notif_id}/read")
def mark_notification_read(notif_id: int, current_user: dict = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    notif = db.query(models.Notification).filter(
        models.Notification.id == notif_id,
        models.Notification.user_id == current_user["id"]
    ).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"message": "Notification marked as read"}

# Messaging
@app.post("/messages", response_model=schemas.Message)
def send_message(msg: schemas.MessageCreate, current_user: dict = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    new_msg = models.Message(
        sender_id=current_user["id"],
        receiver_id=msg.receiver_id,
        content=msg.content
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    return new_msg

@app.get("/messages", response_model=List[schemas.Message])
def get_my_messages(current_user: dict = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    return db.query(models.Message).filter(
        or_(
            models.Message.sender_id == current_user["id"],
            models.Message.receiver_id == current_user["id"]
        )
    ).order_by(models.Message.created_at.desc()).all()

# Batches
@app.post("/batches", response_model=schemas.Batch)
def create_batch(batch: schemas.BatchCreate, current_user: dict = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user["role"] != "instructor":
        raise HTTPException(status_code=403, detail="Only instructors can create batches")
    
    new_batch = models.Batch(
        name=batch.name,
        course_id=batch.course_id,
        instructor_id=current_user["id"],
        start_time=batch.start_time,
        end_time=batch.end_time
    )
    db.add(new_batch)
    db.commit()
    db.refresh(new_batch)
    return new_batch

@app.post("/batches/{batch_id}/students")
def assign_students_to_batch(batch_id: int, student_ids: List[int], current_user: dict = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user["role"] != "instructor":
        raise HTTPException(status_code=403, detail="Only instructors can assign students to batches")
    
    batch = db.query(models.Batch).filter(models.Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    if batch.instructor_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to manage this batch")
    
    # Clear existing students and re-assign? Or add new ones? 
    # Usually manual assignment replaces or adds. Let's do a set-based replacement for simplicity if the list is provided.
    students = db.query(models.User).filter(models.User.id.in_(student_ids), models.User.role == "learner").all()
    
    # Check if students are enrolled in the course
    enrolled_student_ids = [e.user_id for e in batch.course.enrolments]
    valid_students = [s for s in students if s.id in enrolled_student_ids]
    
    if len(valid_students) != len(student_ids):
        # Some students are not enrolled or don't exist
        print(f"Warning: Some student IDs were skipped for assignment to batch {batch_id}")

    batch.students = valid_students
    db.commit()

    # Create notifications for assigned students
    for student in valid_students:
        notif = models.Notification(
            user_id=student.id,
            title="Batch Assigned",
            message=f"You have been assigned to the '{batch.name}' batch for course '{batch.course.title}'.",
            type="info"
        )
        db.add(notif)
    
    db.commit()
    return {"message": f"Successfully assigned {len(valid_students)} students to batch."}

@app.get("/batches", response_model=List[schemas.Batch])
def get_batches(current_user: dict = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user["role"] == "instructor":
        batches = db.query(models.Batch).filter(models.Batch.instructor_id == current_user["id"]).all()
    else:
        # Learners can see batches they are in
        batches = db.query(models.Batch).join(models.Batch.students).filter(models.User.id == current_user["id"]).all()
    
    # Manually populate course_title if needed, though SQLAlchemy relationship might handle it if schema is right
    # To be explicit and avoid lazy loading issues in response model:
    for b in batches:
        b.course_title = b.course.title if b.course else "Unknown Course"
    
    return batches

# Badges
@app.get("/users/me/badges", response_model=List[schemas.Badge])
def get_my_badges(current_user: dict = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == current_user["id"]).first()
    return user.badges

@app.get("/badges/all", response_model=List[schemas.Badge])
def get_all_badges(db: Session = Depends(database.get_db)):
    return db.query(models.Badge).all()


# Certificates
@app.get("/users/me/certificates", response_model=List[schemas.CertificateResponse])
def get_my_certificates(current_user: dict = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    certs = db.query(models.Certificate).filter(models.Certificate.user_id == current_user["id"]).all()
    # Populate extra fields for the response model
    for cert in certs:
        cert.course_title = cert.course.title if cert.course else "Unknown Course"
        cert.user_name = cert.user.name if cert.user else "Unknown Learner"
    return certs

@app.get("/users/me/certificates/course/{course_id}", response_model=Optional[schemas.CertificateResponse])
def get_course_certificate(course_id: int, current_user: dict = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    cert = db.query(models.Certificate).filter(
        models.Certificate.user_id == current_user["id"],
        models.Certificate.course_id == course_id
    ).first()
    
    if cert:
        cert.course_title = cert.course.title if cert.course else "Unknown Course"
        cert.user_name = cert.user.name if cert.user else "Unknown Learner"
    
    return cert

@app.get("/courses/{course_id}/reports/performance")
def get_performance_report(course_id: int, current_user: dict = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if current_user["role"] != "instructor":
        raise HTTPException(status_code=403, detail="Only instructors can download performance reports")
    
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if course.instructor_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access reports for this course")
    
    # 1. Fetch Enrolled Students
    # Joining with Enrolment table to find all students for this course
    enrolled_users = db.query(models.User).join(models.Enrolment).filter(models.Enrolment.course_id == course_id).all()
    
    # 2. Prepare CSV Header
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student Name", "Email", "Progress (%)", "Module Quiz Avg (%)", "Final Assessment Status", "Final Grade (%)"])
    
    total_modules = len(course.modules)
    
    for student in enrolled_users:
        # Progress: Completed modules / total modules
        completed_results = db.query(models.QuizResult).filter(
            models.QuizResult.user_id == student.id,
            models.QuizResult.module_id.in_([m.id for m in course.modules])
        ).all()
        
        completed_count = len(completed_results)
        progress = (completed_count / total_modules * 100) if total_modules > 0 else 0
        
        # Module Average
        quiz_scores = []
        for r in completed_results:
            if r.total_questions and r.total_questions > 0:
                quiz_scores.append((r.score / r.total_questions) * 100)
        
        mod_avg = sum(quiz_scores) / len(quiz_scores) if quiz_scores else 0
        
        # Final Assessment
        final_result = db.query(models.QuizResult).filter(
            models.QuizResult.user_id == student.id,
            models.QuizResult.course_id == course_id
        ).first()
        
        final_status = "Completed" if final_result else "Not Attempted"
        final_score = int((final_result.score / final_result.total_questions * 100) if final_result and final_result.total_questions and final_result.total_questions > 0 else 0)
        
        writer.writerow([
            student.name,
            student.email,
            f"{int(progress)}%",
            f"{int(mod_avg)}%",
            final_status,
            f"{final_score}%" if final_result else "N/A"
        ])
    
    output.seek(0)
    sanitized_title = "".join(c for c in course.title if c.isalnum() or c in (" ", "_")).strip().replace(" ", "_")
    filename = f"Performance_Report_{sanitized_title}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

if __name__ == "__main__":
    import uvicorn
    print("Starting SQLAlchemy-based server on http://127.0.0.1:8000")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
