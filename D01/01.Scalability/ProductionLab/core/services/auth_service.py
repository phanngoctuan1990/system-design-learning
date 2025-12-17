"""
Auth Service - User registration and login logic
"""
import bcrypt
import uuid
import json
from typing import Optional, Dict, Any
from ..domain import User, UserProfile
from ..interfaces.database_port import DatabasePort
from ..interfaces.cache_port import CachePort


class AuthService:
    SESSION_TTL = 3600  # 1 hour
    
    def __init__(self, db: DatabasePort, cache: CachePort = None):
        self.db = db
        self.cache = cache
    
    def register(self, username: str, password: str, 
                 full_name: str = None, email: str = None,
                 address_id: int = None, address_detail: str = None) -> Dict[str, Any]:
        """
        Register a new user.
        Uses transaction to ensure consistency:
        - If user_profile insert fails, auth_user is rolled back
        """
        # Check if username exists
        existing = self.db.fetch_one(
            "SELECT id FROM auth_user WHERE username = %s", (username,)
        )
        if existing:
            return {"success": False, "error": "Username already exists"}
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        try:
            # Use transaction for atomicity
            with self.db.transaction() as tx:
                # Create auth_user
                user_id = tx.insert(
                    "INSERT INTO auth_user (username, password_hash) VALUES (%s, %s)",
                    (username, password_hash)
                )
                
                # Create user_profile
                tx.insert(
                    """INSERT INTO user_profile 
                       (user_id, full_name, email, address_id, address_detail) 
                       VALUES (%s, %s, %s, %s, %s)""",
                    (user_id, full_name, email, address_id, address_detail)
                )
            
            return {
                "success": True,
                "user_id": user_id,
                "message": "User registered successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Registration failed: {str(e)}"
            }
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user, create session, and return user info"""
        # Get user
        user_row = self.db.fetch_one(
            "SELECT id, username, password_hash FROM auth_user WHERE username = %s",
            (username,)
        )
        
        if not user_row:
            return {"success": False, "error": "Invalid username or password"}
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user_row['password_hash'].encode('utf-8')):
            return {"success": False, "error": "Invalid username or password"}
        
        # Create session in cache
        session_id = str(uuid.uuid4())
        if self.cache:
            session_data = json.dumps({
                "user_id": user_row['id'],
                "username": user_row['username']
            })
            self.cache.set(f"auth_session:{session_id}", session_data, ttl=self.SESSION_TTL)
        
        # Get profile
        profile = self._get_user_profile(user_row['id'])
        
        return {
            "success": True,
            "session_id": session_id,
            "user": {
                "id": user_row['id'],
                "username": user_row['username'],
                **profile
            }
        }
    
    def logout(self, session_id: str) -> Dict[str, Any]:
        """Logout user by removing session from cache"""
        if self.cache:
            self.cache.delete(f"auth_session:{session_id}")
        return {"success": True, "message": "Logged out successfully"}
    
    def get_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get full user profile by ID"""
        user_row = self.db.fetch_one(
            "SELECT id, username, created_at FROM auth_user WHERE id = %s", (user_id,)
        )
        if not user_row:
            return None
        
        profile = self._get_user_profile(user_id)
        
        return {
            "id": user_row['id'],
            "username": user_row['username'],
            "created_at": str(user_row['created_at']) if user_row.get('created_at') else None,
            **profile
        }
    
    def _get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Internal helper to get user profile with address"""
        profile = self.db.fetch_one(
            """SELECT up.*, ma.country, ma.province, ma.district
               FROM user_profile up
               LEFT JOIN master_address ma ON up.address_id = ma.id
               WHERE up.user_id = %s""",
            (user_id,)
        )
        
        if not profile:
            return {"full_name": None, "email": None, "address": None}
        
        return {
            "full_name": profile.get('full_name'),
            "email": profile.get('email'),
            "address": {
                "country": profile.get('country'),
                "province": profile.get('province'),
                "district": profile.get('district'),
                "detail": profile.get('address_detail')
            } if profile.get('address_id') else None
        }

