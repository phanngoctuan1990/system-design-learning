"""
User Models - User authentication and profile
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    """Authentication user"""
    id: Optional[int]
    username: str
    password_hash: str
    created_at: Optional[float] = None


@dataclass
class Address:
    """Master address entry"""
    id: int
    country: str
    province: str
    district: str


@dataclass
class UserProfile:
    """User profile with address"""
    id: Optional[int]
    user_id: int
    full_name: Optional[str] = None
    email: Optional[str] = None
    address_id: Optional[int] = None
    address_detail: Optional[str] = None
    address: Optional[Address] = None  # Populated on read
