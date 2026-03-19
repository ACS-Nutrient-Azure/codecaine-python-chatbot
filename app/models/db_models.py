from sqlalchemy import Column, String, Integer, TIMESTAMP, Text, Boolean, BIGINT, Date, Numeric, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class ChatbotUserData(Base):
    __tablename__ = "chatbot_userdata"
    
    cognito_id = Column(String(36), primary_key=True)
    chat_birth_dt = Column(Date)
    chat_gender = Column(Integer)
    chat_height = Column(Numeric(5, 1))
    chat_weight = Column(Numeric(5, 1))
    chat_allergies = Column(String(255))
    chat_chron_diseases = Column(String(255))
    chat_current_conditions = Column(String(255))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())

class ChatbotAnalysisResult(Base):
    __tablename__ = "chatbot_analysis_result"
    
    chat_result_id = Column(BIGINT, primary_key=True, autoincrement=True)
    cognito_id = Column(String(36), nullable=False)
    chat_summary = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())

class ChatbotSupplements(Base):
    __tablename__ = "chatbot_supplements"
    
    chat_current_id = Column(BIGINT, primary_key=True, autoincrement=True)
    cognito_id = Column(String(36), nullable=False)
    chat_product_name = Column(String(255))
    chat_serving_amount = Column(Integer)
    chat_serving_per_day = Column(Integer)
    chat_daily_total_amount = Column(Integer)
    chat_is_active = Column(Boolean)
    chat_ingredients = Column(JSON)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
