from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    Numeric,
    Boolean,
    JSON,
    Float,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.database import Base



class UsageStats(Base):
    __tablename__ = "usage_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False)
    total_messages = Column(Integer, default=0)
    unique_users = Column(Integer, default=0)
    avg_response_time_ms = Column(Float, default=0.0)
    rag_queries = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_path = Column(String(500), nullable=False)
    content = Column(Text)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Relationship to chunks
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(JSON)  # Store as JSON array
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to document
    document = relationship("Document", back_populates="chunks")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    client_code = Column(String(100), unique=True, index=True, nullable=False)
    address = Column(String(255), nullable=True)

    users = relationship("UserClient", back_populates="client")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    clients = relationship("UserClient", back_populates="user")
    chat_logs = relationship("ChatLog", back_populates="user")


class UserClient(Base):
    __tablename__ = "user_clients"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    is_primary = Column(Integer, default=1)  # 1=true, 0=false (simple for now)

    user = relationship("User", back_populates="clients")
    client = relationship("Client", back_populates="users")


class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)

    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    user_message = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=True)

    intent = Column(String(100), nullable=True)       # e.g. "order_status"
    data_source = Column(String(50), nullable=True)   # e.g. "sql", "rag", "both"

    user = relationship("User", back_populates="chat_logs")


class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    model_name = Column(String(255), nullable=False)
    serial_number = Column(String(100), unique=True, index=True, nullable=False)
    category = Column(String(100), nullable=True)  # e.g. "ultrasound", "xray"
    purchase_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="active")  # active, inactive, maintenance

    client = relationship("Client")
    orders = relationship("Order", back_populates="equipment")
    warranties = relationship("Warranty", back_populates="equipment")
    amc_contracts = relationship("AMCContract", back_populates="equipment")
    maintenance = relationship("ScheduledMaintenance", back_populates="equipment")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=True)
    status = Column(String(50), default="pending")  # pending, confirmed, shipped, delivered
    order_date = Column(DateTime(timezone=True), server_default=func.now())
    expected_delivery_date = Column(DateTime(timezone=True), nullable=True)
    tracking_number = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client")
    equipment = relationship("Equipment", back_populates="orders")


class Warranty(Base):
    __tablename__ = "warranties"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    coverage_details = Column(Text, nullable=True)
    status = Column(String(50), default="active")  # active, expired

    equipment = relationship("Equipment", back_populates="warranties")


class AMCContract(Base):
    __tablename__ = "amc_contracts"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    sla_details = Column(Text, nullable=True)  # Service Level Agreement details
    status = Column(String(50), default="active")  # active, expired
    cost = Column(Numeric(10, 2), nullable=True)

    equipment = relationship("Equipment", back_populates="amc_contracts")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="open")  # open, in_progress, resolved, closed
    priority = Column(String(50), default="medium")  # low, medium, high, critical
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    client = relationship("Client")
    user = relationship("User")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="USD")  # USD, EUR, etc.
    status = Column(String(50), default="pending")  # pending, paid, overdue
    invoice_date = Column(DateTime(timezone=True), server_default=func.now())
    due_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client")
    payments = relationship("Payment", back_populates="invoice")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_date = Column(DateTime(timezone=True), server_default=func.now())
    method = Column(String(50), nullable=True)  # credit_card, bank_transfer, check

    invoice = relationship("Invoice", back_populates="payments")


class ScheduledMaintenance(Base):
    __tablename__ = "scheduled_maintenance"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    scheduled_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), default="scheduled")  # scheduled, in_progress, completed
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    equipment = relationship("Equipment", back_populates="maintenance")