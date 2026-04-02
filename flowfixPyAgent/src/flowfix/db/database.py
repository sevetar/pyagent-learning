from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from flowfix.config import get_settings

settings = get_settings()

mysql_engine = create_engine(
    settings.mysql_url,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    echo=False,
)

MySQLSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=mysql_engine)


@contextmanager
def get_mysql_session() -> Session:
    """MySQL会话上下文管理器"""
    session = MySQLSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_mysql_tables():
    """初始化MySQL表"""
    from flowfix.db.models import Base
    Base.metadata.create_all(bind=mysql_engine)
