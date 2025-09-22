#!/usr/bin/env python3
"""
Script to create a test admin user
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Usuario
from app.core.security import hash_password

def create_test_user():
    """Create a test admin user"""

    # Get database session
    db_gen = get_db()
    db = next(db_gen)

    try:
        # Check if user already exists
        existing_user = db.query(Usuario).filter(Usuario.email == "admin@transpontual.com").first()
        if existing_user:
            print("User already exists!")
            return

        # Create new admin user
        user = Usuario(
            nome="Administrador",
            email="admin@transpontual.com",
            senha_hash=hash_password("admin123"),
            papel="admin",
            ativo=True
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        print("Admin user created successfully!")
        print(f"   Email: {user.email}")
        print(f"   Password: admin123")
        print(f"   Role: {user.papel}")

    except Exception as e:
        print(f"Error creating user: {e}")
        db.rollback()

    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()