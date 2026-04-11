import uuid
from datetime import datetime
from typing import List, Dict, Any

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Text,
    text,
    PrimaryKeyConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from app.domain.models.session import Session

class SessionModel(Base):
    """会话 ORM 模型"""
    __tablename__ = "sessions"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_sessions_id"),
    )

    id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, default=lambda: str(uuid.uuid4())) # 会话 ID
    sandbox_id: Mapped[str] = mapped_column(String(255), nullable=False) # 沙箱 ID
    task_id: Mapped[str] = mapped_column(String(255), nullable=False) # 任务 ID
    title: Mapped[str] = mapped_column(String(255), nullable=False, server_default=text("''::character varying")) # 会话标题
    unread_message_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0")) # 未读消息数量
    latest_message: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text")) # 最后一条消息
    latest_message_at: Mapped[datetime] = mapped_column(DateTime, nullable=True) # 最后一条消息时间
    events: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb")) # 事件列表
    files: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb")) # 文件列表
    memories: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb")) # 记忆列表
    status: Mapped[str] = mapped_column(String(255), nullable=False, server_default=text("''::character varying")) # 会话状态
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)")) # 更新时间
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)")) # 创建时间

    @classmethod
    def from_domain(cls, session: Session) -> "SessionModel":
        """将领域模型转换为 ORM 模型"""
        return cls(
            # 基础字段：使用 BaseModel 提供的 Python 字典转换格式
            **session.model_dump(
                mode="python",
                exclude={"memories", "files", "events", "updated_at", "created_at"},
            ),
            # 复杂字段：使用 BaseModel 提供的 JSON 字典转换格式
            **session.model_dump(
                mode="json",
                include={"memories", "files", "events"},
            )
        )

    def to_domain(self) -> Session:
        """将 ORM 模型转换为领域模型"""
        return Session.model_validate(self, from_attributes=True)

    def update_from_domain(self, session: Session) -> None:
        """根据领域模型更新 ORM 模型"""
        # 1. 基础字段：Python 模式
        base_data = session.model_dump(
            mode="python",
            exclude={"memories", "files", "events", "updated_at", "created_at"},
        )
        # 2. 复杂字段：JSON 模式
        complex_data = session.model_dump(
            mode="json",
            include={"memories", "files", "events"},
        )
        # 3. 更新 ORM 模型
        for field, value in {**base_data, **complex_data}.items():
            setattr(self, field, value)