"""
Seed Data — Pre-populate customer_users and staff_users tables.

Usage:
    python -m src.database.seed_users

Creates demo users so the frontend works out of the box.
"""

import sys
import os
import logging

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.auth_operations import (
    CustomerUserOperations,
    StaffUserOperations,
    hash_password,
)
from src.database.models import CustomerUser, StaffUser

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────
#  Customer demo accounts
# ────────────────────────────────────────────

CUSTOMER_SEEDS = [
    {
        'email': 'suman@example.com',
        'password': 'test@123',
        'full_name': 'Suman Ghosh',
        'father_name': 'Ramesh Ghosh',
        'phone': '+91 98765 43210',
        'gender': 'male',
        'marital_status': 'married',
        'permanent_address': '12, Park Street, Kolkata, WB 700016',
        'current_address': '45, MG Road, Bengaluru, KA 560001',
    },
    {
        'email': 'priya@example.com',
        'password': 'priya@123',
        'full_name': 'Priya Sharma',
        'father_name': 'Anil Sharma',
        'phone': '+91 87654 32100',
        'gender': 'female',
        'marital_status': 'single',
        'permanent_address': '78, Gandhi Nagar, Jaipur, RJ 302015',
        'current_address': '78, Gandhi Nagar, Jaipur, RJ 302015',
    },
    {
        'email': 'rahul@example.com',
        'password': 'rahul@123',
        'full_name': 'Rahul Verma',
        'father_name': 'Suresh Verma',
        'phone': '+91 76543 21000',
        'gender': 'male',
        'marital_status': 'single',
        'permanent_address': '34, Nehru Place, New Delhi, DL 110019',
        'current_address': '22, Indiranagar, Bengaluru, KA 560038',
    },
    {
        'email': 'anita@example.com',
        'password': 'anita@123',
        'full_name': 'Anita Patel',
        'father_name': 'Mahesh Patel',
        'phone': '+91 65432 10000',
        'gender': 'female',
        'marital_status': 'married',
        'permanent_address': '56, SG Highway, Ahmedabad, GJ 380015',
        'current_address': '56, SG Highway, Ahmedabad, GJ 380015',
    },
]


# ────────────────────────────────────────────
#  Staff / Admin demo accounts
# ────────────────────────────────────────────

STAFF_SEEDS = [
    {
        'username': 'admin',
        'email': 'admin@claimsportal.com',
        'password': 'admin123',
        'full_name': 'Admin User',
        'employee_id': 'EMP-001',
        'department': 'IT',
        'designation': 'System Administrator',
        'role': 'admin',
        'access_level': 3,
        'phone': '+91 99999 00001',
    },
    {
        'username': 'adjuster',
        'email': 'adjuster@claimsportal.com',
        'password': 'staff2024',
        'full_name': 'Ajay Adjuster',
        'employee_id': 'EMP-101',
        'department': 'Claims',
        'designation': 'Claims Adjuster',
        'role': 'adjuster',
        'access_level': 1,
        'phone': '+91 99999 00101',
    },
    {
        'username': 'manager',
        'email': 'manager@claimsportal.com',
        'password': 'manager@1',
        'full_name': 'Meera Manager',
        'employee_id': 'EMP-201',
        'department': 'Management',
        'designation': 'Senior Manager',
        'role': 'manager',
        'access_level': 2,
        'phone': '+91 99999 00201',
    },
    {
        'username': 'fraud_analyst',
        'email': 'fraud@claimsportal.com',
        'password': 'fraud@123',
        'full_name': 'Farhan Fraud Analyst',
        'employee_id': 'EMP-301',
        'department': 'Fraud',
        'designation': 'Senior Fraud Analyst',
        'role': 'adjuster',
        'access_level': 2,
        'phone': '+91 99999 00301',
    },
    {
        'username': 'viewer',
        'email': 'viewer@claimsportal.com',
        'password': 'viewer@123',
        'full_name': 'Vijay Viewer',
        'employee_id': 'EMP-401',
        'department': 'Claims',
        'designation': 'Claims Viewer',
        'role': 'viewer',
        'access_level': 1,
        'phone': None,
    },
]


def seed_customers(session=None):
    """Insert demo customer users."""
    ops = CustomerUserOperations(session)
    created = 0
    for data in CUSTOMER_SEEDS:
        try:
            ops.register(**data)
            created += 1
        except ValueError as e:
            logger.info(f"Skipped customer {data['email']}: {e}")
    logger.info(f"Seeded {created}/{len(CUSTOMER_SEEDS)} customer users")
    return created


def seed_staff(session=None):
    """Insert demo staff users."""
    ops = StaffUserOperations(session)
    created = 0
    for data in STAFF_SEEDS:
        try:
            ops.create_staff(**data)
            created += 1
        except ValueError as e:
            logger.info(f"Skipped staff {data['username']}: {e}")
    logger.info(f"Seeded {created}/{len(STAFF_SEEDS)} staff users")
    return created


def seed_all(session=None):
    """Seed all demo users."""
    customers = seed_customers(session)
    staff = seed_staff(session)
    return {'customers': customers, 'staff': staff}


# ────────────────────────────────────────────
#  CLI entry point
# ────────────────────────────────────────────

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s  %(message)s')

    print("\n╔══════════════════════════════════════════╗")
    print("║   ClaimsPortal — Seed Users Database     ║")
    print("╚══════════════════════════════════════════╝\n")

    result = seed_all()

    print(f"\n✅  Customers seeded: {result['customers']}")
    print(f"✅  Staff seeded:     {result['staff']}")

    print("\n── Customer Accounts ──────────────────────")
    for c in CUSTOMER_SEEDS:
        print(f"   {c['email']:30s} / {c['password']}")

    print("\n── Staff Accounts ────────────────────────")
    for s in STAFF_SEEDS:
        print(f"   {s['username']:20s} / {s['password']:15s} ({s['role']}, {s['department']})")

    print()
