"""
Session management for user authentication
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, List
import logging

from .models import UserSession

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages user sessions for authentication"""
    
    def __init__(self):
        self._sessions: Dict[str, UserSession] = {}  # In-memory session store
        self._user_sessions: Dict[str, List[str]] = {}  # user_id -> session_ids
    
    async def create_session(self, session: UserSession) -> bool:
        """Create a new user session"""
        try:
            self._sessions[session.session_id] = session
            
            # Track sessions by user
            if session.user_id not in self._user_sessions:
                self._user_sessions[session.user_id] = []
            self._user_sessions[session.user_id].append(session.session_id)
            
            logger.info(f"Created session {session.session_id} for user {session.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get session by ID"""
        session = self._sessions.get(session_id)
        
        if session and session.is_expired:
            # Clean up expired session
            await self.invalidate_session(session_id)
            return None
        
        return session
    
    async def update_session(self, session: UserSession) -> bool:
        """Update existing session"""
        try:
            if session.session_id in self._sessions:
                self._sessions[session.session_id] = session
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error updating session: {e}")
            return False
    
    async def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session"""
        try:
            session = self._sessions.get(session_id)
            if session:
                # Remove from user sessions tracking
                if session.user_id in self._user_sessions:
                    user_sessions = self._user_sessions[session.user_id]
                    if session_id in user_sessions:
                        user_sessions.remove(session_id)
                    
                    # Clean up empty user session list
                    if not user_sessions:
                        del self._user_sessions[session.user_id]
                
                # Remove session
                del self._sessions[session_id]
                logger.info(f"Invalidated session {session_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error invalidating session: {e}")
            return False
    
    async def invalidate_user_sessions(self, user_id: str) -> int:
        """Invalidate all sessions for a user"""
        try:
            session_ids = self._user_sessions.get(user_id, []).copy()
            count = 0
            
            for session_id in session_ids:
                if await self.invalidate_session(session_id):
                    count += 1
            
            logger.info(f"Invalidated {count} sessions for user {user_id}")
            return count
            
        except Exception as e:
            logger.error(f"Error invalidating user sessions: {e}")
            return 0
    
    async def extend_session(self, session_id: str, hours: int = 24) -> bool:
        """Extend session expiration"""
        try:
            session = await self.get_session(session_id)
            if session and session.is_valid:
                session.extend_session(hours)
                await self.update_session(session)
                logger.info(f"Extended session {session_id} by {hours} hours")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error extending session: {e}")
            return False
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        try:
            expired_sessions = []
            
            for session_id, session in self._sessions.items():
                if session.is_expired:
                    expired_sessions.append(session_id)
            
            count = 0
            for session_id in expired_sessions:
                if await self.invalidate_session(session_id):
                    count += 1
            
            if count > 0:
                logger.info(f"Cleaned up {count} expired sessions")
            
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0
    
    async def get_user_sessions(self, user_id: str) -> List[UserSession]:
        """Get all active sessions for a user"""
        try:
            session_ids = self._user_sessions.get(user_id, [])
            sessions = []
            
            for session_id in session_ids:
                session = await self.get_session(session_id)
                if session and session.is_valid:
                    sessions.append(session)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []
    
    async def get_session_count(self) -> int:
        """Get total number of active sessions"""
        await self.cleanup_expired_sessions()
        return len(self._sessions)
    
    async def get_user_session_count(self, user_id: str) -> int:
        """Get number of active sessions for a user"""
        sessions = await self.get_user_sessions(user_id)
        return len(sessions)
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get session information for debugging"""
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        return {
            'session_id': session.session_id,
            'user_id': session.user_id,
            'created_at': session.created_at.isoformat(),
            'expires_at': session.expires_at.isoformat(),
            'last_activity': session.last_activity.isoformat(),
            'is_valid': session.is_valid,
            'is_expired': session.is_expired,
            'ip_address': session.ip_address,
            'user_agent': session.user_agent
        }