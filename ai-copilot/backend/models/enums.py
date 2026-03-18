from __future__ import annotations

import enum


class ChannelEnum(str, enum.Enum):
    CHAT = "chat"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    SLACK = "slack"
    TEAMS = "teams"
    VOICE = "voice"
    VIDEO = "video"


class SenderTypeEnum(str, enum.Enum):
    CUSTOMER = "customer"
    AGENT = "agent"
    SYSTEM = "system"
    AI = "ai"


class TicketStatusEnum(str, enum.Enum):
    OPEN = "open"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ConversationStatusEnum(str, enum.Enum):
    OPEN = "open"
    PENDING = "pending"
    CLOSED = "closed"


class PriorityEnum(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class DocumentStatusEnum(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class UserRoleEnum(str, enum.Enum):
    ADMIN = "admin"
    AGENT = "agent"
    VIEWER = "viewer"
    API = "api"
    FRAUD_SPECIALIST = "fraud_specialist"
    LOAN_OFFICER = "loan_officer"


class TicketCategoryEnum(str, enum.Enum):
    FRAUD = "fraud"
    OTP_ISSUE = "otp_issue"
    PASSWORD_RESET = "password_reset"
    TECHNICAL = "technical"
    GENERAL = "general"


class AgentStatusEnum(str, enum.Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
