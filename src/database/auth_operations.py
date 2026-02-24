"""Auth Database Operations — CRUD for CustomerUser and StaffUser tables."""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import hashlib
import hmac
import os
import uuid
import logging

from sqlalchemy.orm import Session

from .models import CustomerUser, StaffUser
from .operations import DatabaseOperations

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────
#  Password hashing (PBKDF2-HMAC-SHA256)
# ────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with random salt."""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100_000)
    return salt.hex() + ':' + key.hex()


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against a stored hash."""
    try:
        salt_hex, key_hex = stored_hash.split(':')
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        actual_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100_000)
        return hmac.compare_digest(actual_key, expected_key)
    except Exception:
        return False


# ────────────────────────────────────────────
#  Customer Operations
# ────────────────────────────────────────────

class CustomerUserOperations(DatabaseOperations):
    """CRUD operations for customer/policyholder users."""

    def register(
        self,
        email: str,
        password: str,
        full_name: str,
        father_name: str,
        phone: str,
        gender: str,
        marital_status: str,
        permanent_address: str,
        current_address: str,
    ) -> CustomerUser:
        """Register a new customer. Raises ValueError if email already exists."""
        session = self._get_session()
        try:
            existing = session.query(CustomerUser).filter_by(email=email.strip().lower()).first()
            if existing:
                raise ValueError("An account with this email already exists.")

            user = CustomerUser(
                id=str(uuid.uuid4()),
                email=email.strip().lower(),
                password_hash=hash_password(password),
                full_name=full_name.strip(),
                father_name=father_name.strip(),
                phone=phone.strip(),
                gender=gender,
                marital_status=marital_status,
                permanent_address=permanent_address.strip(),
                current_address=current_address.strip(),
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            logger.info(f"Customer registered: {user.email} ({user.id})")
            return user
        except ValueError:
            raise
        except Exception as e:
            session.rollback()
            logger.error(f"Customer registration failed: {e}")
            raise

    def authenticate(self, email: str, password: str) -> Optional[CustomerUser]:
        """Authenticate a customer by email + password. Returns user or None."""
        session = self._get_session()
        user = session.query(CustomerUser).filter_by(
            email=email.strip().lower(), is_active=True
        ).first()

        if not user or not verify_password(password, user.password_hash):
            return None

        # Update last login
        user.last_login = datetime.utcnow()
        session.commit()
        logger.info(f"Customer authenticated: {user.email}")
        return user

    def find_by_email(self, email: str) -> Optional[CustomerUser]:
        """Find customer by email."""
        session = self._get_session()
        return session.query(CustomerUser).filter_by(email=email.strip().lower()).first()

    def find_by_id(self, user_id: str) -> Optional[CustomerUser]:
        """Find customer by ID."""
        session = self._get_session()
        return session.query(CustomerUser).filter_by(id=user_id).first()

    def update_profile(self, user_id: str, **kwargs) -> Optional[CustomerUser]:
        """Update customer profile fields."""
        session = self._get_session()
        user = session.query(CustomerUser).filter_by(id=user_id).first()
        if not user:
            return None
        for key, val in kwargs.items():
            if hasattr(user, key) and key not in ('id', 'email', 'password_hash', 'created_at'):
                setattr(user, key, val)
        user.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(user)
        return user

    def list_customers(self, limit: int = 50, offset: int = 0) -> List[CustomerUser]:
        """List all customers with pagination."""
        session = self._get_session()
        return session.query(CustomerUser).order_by(
            CustomerUser.created_at.desc()
        ).offset(offset).limit(limit).all()

    def count_customers(self) -> int:
        """Count total registered customers."""
        session = self._get_session()
        return session.query(CustomerUser).count()

    def to_dict(self, user: CustomerUser) -> Dict[str, Any]:
        """Serialize customer user (no password hash)."""
        return {
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'father_name': user.father_name,
            'phone': user.phone,
            'gender': user.gender,
            'marital_status': user.marital_status,
            'permanent_address': user.permanent_address,
            'current_address': user.current_address,
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'created_at': user.created_at.isoformat() if user.created_at else None,
        }


# ────────────────────────────────────────────
#  Staff Operations
# ────────────────────────────────────────────

LOCKOUT_DURATION_MINUTES = 30
MAX_FAILED_ATTEMPTS = 5


class StaffUserOperations(DatabaseOperations):
    """CRUD operations for admin/staff users."""

    def create_staff(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str,
        employee_id: str,
        department: str,
        role: str = "adjuster",
        access_level: int = 1,
        designation: str = None,
        phone: str = None,
    ) -> StaffUser:
        """Create a new staff user. Raises ValueError if username/email/employee_id already exists."""
        session = self._get_session()
        try:
            # Check uniqueness
            if session.query(StaffUser).filter_by(username=username.strip()).first():
                raise ValueError(f"Username '{username}' is already taken.")
            if session.query(StaffUser).filter_by(email=email.strip().lower()).first():
                raise ValueError(f"Email '{email}' is already registered.")
            if session.query(StaffUser).filter_by(employee_id=employee_id.strip()).first():
                raise ValueError(f"Employee ID '{employee_id}' already exists.")

            staff = StaffUser(
                id=str(uuid.uuid4()),
                username=username.strip(),
                email=email.strip().lower(),
                password_hash=hash_password(password),
                full_name=full_name.strip(),
                employee_id=employee_id.strip(),
                department=department,
                role=role,
                access_level=access_level,
                designation=designation,
                phone=phone,
            )
            session.add(staff)
            session.commit()
            session.refresh(staff)
            logger.info(f"Staff created: {staff.username} ({staff.role})")
            return staff
        except ValueError:
            raise
        except Exception as e:
            session.rollback()
            logger.error(f"Staff creation failed: {e}")
            raise

    def authenticate(self, username: str, password: str) -> Optional[StaffUser]:
        """Authenticate staff by username + password. Handles lockout."""
        session = self._get_session()
        staff = session.query(StaffUser).filter_by(
            username=username.strip(), is_active=True
        ).first()

        if not staff:
            return None

        # Check lockout
        if staff.locked_until and staff.locked_until > datetime.utcnow():
            logger.warning(f"Staff account locked: {staff.username}")
            return None

        if not verify_password(password, staff.password_hash):
            staff.failed_login_attempts += 1
            if staff.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                staff.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                logger.warning(f"Staff locked after {MAX_FAILED_ATTEMPTS} failed attempts: {staff.username}")
            session.commit()
            return None

        # Success — reset failed attempts
        staff.failed_login_attempts = 0
        staff.locked_until = None
        staff.last_login = datetime.utcnow()
        session.commit()
        logger.info(f"Staff authenticated: {staff.username} (role={staff.role})")
        return staff

    def find_by_username(self, username: str) -> Optional[StaffUser]:
        """Find staff by username."""
        session = self._get_session()
        return session.query(StaffUser).filter_by(username=username.strip()).first()

    def find_by_employee_id(self, employee_id: str) -> Optional[StaffUser]:
        """Find staff by employee ID."""
        session = self._get_session()
        return session.query(StaffUser).filter_by(employee_id=employee_id.strip()).first()

    def list_staff(self, department: str = None, limit: int = 50, offset: int = 0) -> List[StaffUser]:
        """List staff users, optionally filtered by department."""
        session = self._get_session()
        q = session.query(StaffUser)
        if department:
            q = q.filter_by(department=department)
        return q.order_by(StaffUser.created_at.desc()).offset(offset).limit(limit).all()

    def count_staff(self) -> int:
        """Count total staff users."""
        session = self._get_session()
        return session.query(StaffUser).count()

    def deactivate(self, staff_id: str) -> bool:
        """Deactivate a staff account."""
        session = self._get_session()
        staff = session.query(StaffUser).filter_by(id=staff_id).first()
        if not staff:
            return False
        staff.is_active = False
        staff.updated_at = datetime.utcnow()
        session.commit()
        return True

    def to_dict(self, staff: StaffUser) -> Dict[str, Any]:
        """Serialize staff user (no password hash)."""
        return {
            'id': staff.id,
            'username': staff.username,
            'email': staff.email,
            'full_name': staff.full_name,
            'phone': staff.phone,
            'employee_id': staff.employee_id,
            'department': staff.department,
            'designation': staff.designation,
            'role': staff.role,
            'access_level': staff.access_level,
            'is_active': staff.is_active,
            'last_login': staff.last_login.isoformat() if staff.last_login else None,
            'created_at': staff.created_at.isoformat() if staff.created_at else None,
        }
