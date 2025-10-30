import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. DB URL을 환경변수에서 찾되, 없으면 sqlite로 fallback
DEFAULT_SQLITE_URL = "sqlite:///app.db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)

# 2. 엔진/세션 팩토리 생성
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

# 3. 예시 테이블 (필요 시 수정)
#    - 앱에서 로그/검색기록/요청기록 등을 남길 용도라고 가정
class SearchLog(Base):
    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String(500))
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# 4. 테이블이 없으면 생성
def init_db():
    Base.metadata.create_all(bind=engine)

# 5. 편의 함수들
def get_session():
    return SessionLocal()

def log_search(query: str, summary: str):
    session = get_session()
    try:
        row = SearchLog(query=query, summary=summary)
        session.add(row)
        session.commit()
    finally:
        session.close()

def get_recent_logs(limit: int = 20):
    session = get_session()
    try:
        rows = (
            session.query(SearchLog)
            .order_by(SearchLog.created_at.desc())
            .limit(limit)
            .all()
        )
        return rows
    finally:
        session.close()
