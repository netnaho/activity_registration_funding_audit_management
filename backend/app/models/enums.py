from enum import Enum


class UserRole(str, Enum):
    APPLICANT = "applicant"
    REVIEWER = "reviewer"
    FINANCIAL_ADMIN = "financial_admin"
    SYSTEM_ADMIN = "system_admin"


class RegistrationStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    SUPPLEMENTED = "supplemented"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELED = "canceled"
    PROMOTED_FROM_WAITLIST = "promoted_from_waitlist"


class MaterialStatus(str, Enum):
    PENDING_SUBMISSION = "pending_submission"
    SUBMITTED = "submitted"
    NEEDS_CORRECTION = "needs_correction"


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class SeverityLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
