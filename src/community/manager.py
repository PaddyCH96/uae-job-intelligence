"""Community features for opt-in sharing and bookmarking.

Provides save/share job insights, saved searches, and community browsing.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional

import structlog

logger = structlog.get_logger()


class CommunityManager:
    """Manage community features with opt-in only approach."""
    
    def __init__(self, db_session):
        self.db_session = db_session
        
    def create_user_profile(self, user_id: str, opt_in: bool = False) -> Dict:
        """Create or update user profile with opt-in consent."""
        query = """
        INSERT INTO analytics.dim_user_profile (user_id, opt_in, created_at, updated_at)
        VALUES (:user_id, :opt_in, :now, :now)
        ON CONFLICT (user_id) DO UPDATE SET
            opt_in = :opt_in,
            updated_at = :now
        RETURNING user_id, opt_in, created_at
        """
        
        result = self.db_session.execute(query, {
            'user_id': user_id,
            'opt_in': opt_in,
            'now': datetime.now()
        })
        
        row = result.fetchone()
        logger.info("user_profile_created", user_id=user_id, opt_in=opt_in)
        
        return {
            'user_id': row[0],
            'opt_in': row[1],
            'created_at': row[2].isoformat()
        }
    
    def save_insight(self, user_id: str, job_ids: List[str], notes: str = "") -> Dict:
        """Save job insights for a user (requires opt-in)."""
        # Check opt-in
        if not self._check_opt_in(user_id):
            raise ValueError("User has not opted in to community features")
        
        insight_id = str(uuid.uuid4())
        
        query = """
        INSERT INTO analytics.user_shared_insights 
            (id, user_id, job_ids, notes, shared, created_at)
        VALUES 
            (:id, :user_id, :job_ids, :notes, FALSE, :now)
        RETURNING id, user_id, job_ids, notes, created_at
        """
        
        result = self.db_session.execute(query, {
            'id': insight_id,
            'user_id': user_id,
            'job_ids': job_ids,
            'notes': notes,
            'now': datetime.now()
        })
        
        row = result.fetchone()
        logger.info("insight_saved", user_id=user_id, insight_id=insight_id)
        
        return {
            'id': row[0],
            'user_id': row[1],
            'job_ids': row[2],
            'notes': row[3],
            'created_at': row[4].isoformat()
        }
    
    def share_insight(self, user_id: str, insight_id: str) -> bool:
        """Share an insight publicly (requires opt-in)."""
        if not self._check_opt_in(user_id):
            raise ValueError("User has not opted in to community features")
        
        query = """
        UPDATE analytics.user_shared_insights
        SET shared = TRUE, shared_at = :now
        WHERE id = :insight_id AND user_id = :user_id
        """
        
        self.db_session.execute(query, {
            'insight_id': insight_id,
            'user_id': user_id,
            'now': datetime.now()
        })
        
        logger.info("insight_shared", user_id=user_id, insight_id=insight_id)
        return True
    
    def save_search(self, user_id: str, search_criteria: Dict, email_digest: bool = False) -> Dict:
        """Save a search query for later."""
        if not self._check_opt_in(user_id):
            raise ValueError("User has not opted in to community features")
        
        search_id = str(uuid.uuid4())
        
        query = """
        INSERT INTO analytics.user_saved_searches
            (id, user_id, search_criteria, email_digest, created_at)
        VALUES
            (:id, :user_id, :criteria, :email_digest, :now)
        RETURNING id, user_id, search_criteria, email_digest, created_at
        """
        
        result = self.db_session.execute(query, {
            'id': search_id,
            'user_id': user_id,
            'criteria': search_criteria,
            'email_digest': email_digest,
            'now': datetime.now()
        })
        
        row = result.fetchone()
        logger.info("search_saved", user_id=user_id, search_id=search_id)
        
        return {
            'id': row[0],
            'user_id': row[1],
            'search_criteria': row[2],
            'email_digest': row[3],
            'created_at': row[4].isoformat()
        }
    
    def get_user_insights(self, user_id: str) -> List[Dict]:
        """Get all saved insights for a user."""
        query = """
        SELECT id, job_ids, notes, shared, created_at
        FROM analytics.user_shared_insights
        WHERE user_id = :user_id
        ORDER BY created_at DESC
        """
        
        result = self.db_session.execute(query, {'user_id': user_id})
        insights = []
        for row in result:
            insights.append({
                'id': row[0],
                'job_ids': row[1],
                'notes': row[2],
                'shared': row[3],
                'created_at': row[4].isoformat()
            })
        return insights
    
    def delete_user_data(self, user_id: str) -> bool:
        """Delete all user data (privacy compliance)."""
        # Delete insights
        self.db_session.execute(
            "DELETE FROM analytics.user_shared_insights WHERE user_id = :user_id",
            {'user_id': user_id}
        )
        
        # Delete saved searches
        self.db_session.execute(
            "DELETE FROM analytics.user_saved_searches WHERE user_id = :user_id",
            {'user_id': user_id}
        )
        
        # Delete profile
        self.db_session.execute(
            "DELETE FROM analytics.dim_user_profile WHERE user_id = :user_id",
            {'user_id': user_id}
        )
        
        logger.info("user_data_deleted", user_id=user_id)
        return True
    
    def _check_opt_in(self, user_id: str) -> bool:
        """Check if user has opted in to community features."""
        query = """
        SELECT opt_in FROM analytics.dim_user_profile
        WHERE user_id = :user_id
        """
        
        result = self.db_session.execute(query, {'user_id': user_id})
        row = result.fetchone()
        
        return row is not None and row[0] is True