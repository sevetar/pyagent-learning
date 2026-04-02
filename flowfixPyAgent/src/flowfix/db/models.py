from sqlalchemy import Column, BigInteger, String, Text, DateTime, Integer, Index, JSON
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Ticket(Base):
    """工单主表"""
    __tablename__ = "ticket"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    device_id = Column(BigInteger, nullable=True)
    device_name = Column(String(100), nullable=True)

    title = Column(String(255), nullable=True)
    symptom = Column(Text, nullable=True)

    status = Column(String(50), nullable=False, default="CREATED")
    priority = Column(String(20), default="MEDIUM")
    assigned_to = Column(BigInteger, nullable=True)

    version = Column(Integer, default=0)

    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_status", "status"),
        Index("idx_device_id", "device_id"),
    )


class TicketProcess(Base):
    """工单处理记录表"""
    __tablename__ = "ticket_process"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ticket_id = Column(BigInteger, nullable=False)
    operator_id = Column(BigInteger, nullable=False)
    operator_role = Column(String(50), nullable=True)

    action = Column(String(50), nullable=False)
    cause = Column(Text, nullable=True)
    solution = Column(Text, nullable=True)
    result = Column(String(50), nullable=True)
    remark = Column(Text, nullable=True)

    create_time = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index("idx_ticket_id", "ticket_id"),
        Index("idx_operator_id", "operator_id"),
    )


class TicketLog(Base):
    """工单流转日志表"""
    __tablename__ = "ticket_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ticket_id = Column(BigInteger, nullable=False)
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=False)
    operator_id = Column(BigInteger, nullable=True)
    event_type = Column(String(50), nullable=True)
    remark = Column(Text, nullable=True)
    create_time = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index("idx_ticket_id", "ticket_id"),
    )


class Repairman(Base):
    """维修员表"""
    __tablename__ = "repairman"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    skill_tags = Column(JSON, nullable=True)
    current_load = Column(Integer, default=0)
    avg处理时长 = Column(Integer, default=0)
    is_available = Column(String(10), default="true")

    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
