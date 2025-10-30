import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Bookmark(Base):
    __tablename__ = "bookmarks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, default="default_user")
    item_type = Column(String)
    item_id = Column(String)
    title = Column(String)
    category = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class LearningProgress(Base):
    __tablename__ = "learning_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, default="default_user")
    page_name = Column(String)
    completed = Column(Boolean, default=False)
    visited_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class QuizResult(Base):
    __tablename__ = "quiz_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, default="default_user")
    quiz_id = Column(String)
    score = Column(Integer)
    total_questions = Column(Integer)
    answers = Column(Text)
    completed_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        pass

def add_bookmark(item_type, item_id, title, category, user_id="default_user"):
    db = SessionLocal()
    try:
        existing = db.query(Bookmark).filter(
            Bookmark.user_id == user_id,
            Bookmark.item_id == item_id
        ).first()
        
        if existing:
            return False
        
        bookmark = Bookmark(
            user_id=user_id,
            item_type=item_type,
            item_id=item_id,
            title=title,
            category=category
        )
        db.add(bookmark)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error adding bookmark: {e}")
        return False
    finally:
        db.close()

def remove_bookmark(item_id, user_id="default_user"):
    db = SessionLocal()
    try:
        bookmark = db.query(Bookmark).filter(
            Bookmark.user_id == user_id,
            Bookmark.item_id == item_id
        ).first()
        
        if bookmark:
            db.delete(bookmark)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"Error removing bookmark: {e}")
        return False
    finally:
        db.close()

def get_bookmarks(user_id="default_user"):
    db = SessionLocal()
    try:
        bookmarks = db.query(Bookmark).filter(Bookmark.user_id == user_id).order_by(Bookmark.created_at.desc()).all()
        return bookmarks
    except Exception as e:
        print(f"Error getting bookmarks: {e}")
        return []
    finally:
        db.close()

def is_bookmarked(item_id, user_id="default_user"):
    db = SessionLocal()
    try:
        bookmark = db.query(Bookmark).filter(
            Bookmark.user_id == user_id,
            Bookmark.item_id == item_id
        ).first()
        return bookmark is not None
    except Exception as e:
        print(f"Error checking bookmark: {e}")
        return False
    finally:
        db.close()

def update_learning_progress(page_name, completed=False, user_id="default_user"):
    db = SessionLocal()
    try:
        progress = db.query(LearningProgress).filter(
            LearningProgress.user_id == user_id,
            LearningProgress.page_name == page_name
        ).first()
        
        if progress:
            progress.completed = completed
            progress.updated_at = datetime.utcnow()
        else:
            progress = LearningProgress(
                user_id=user_id,
                page_name=page_name,
                completed=completed
            )
            db.add(progress)
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error updating learning progress: {e}")
        return False
    finally:
        db.close()

def get_learning_progress(user_id="default_user"):
    db = SessionLocal()
    try:
        progress = db.query(LearningProgress).filter(LearningProgress.user_id == user_id).all()
        return progress
    except Exception as e:
        print(f"Error getting learning progress: {e}")
        return []
    finally:
        db.close()

def save_quiz_result(quiz_id, score, total_questions, answers, user_id="default_user"):
    db = SessionLocal()
    try:
        result = QuizResult(
            user_id=user_id,
            quiz_id=quiz_id,
            score=score,
            total_questions=total_questions,
            answers=str(answers)
        )
        db.add(result)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error saving quiz result: {e}")
        return False
    finally:
        db.close()

def get_quiz_results(user_id="default_user"):
    db = SessionLocal()
    try:
        results = db.query(QuizResult).filter(QuizResult.user_id == user_id).order_by(QuizResult.completed_at.desc()).all()
        return results
    except Exception as e:
        print(f"Error getting quiz results: {e}")
        return []
    finally:
        db.close()
