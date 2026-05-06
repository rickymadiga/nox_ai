from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime
from typing import Any, Dict
import logging
import sqlite3
import uuid

from nox_backend.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# 🔥 DATABASE INITIALIZATION AND MIGRATION
def init_builds_table():
    """Initialize and migrate builds table"""
    try:
        with sqlite3.connect("builds.db") as conn:
            # First, check if table exists
            table_exists = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='builds'
            """).fetchone()
            
            if not table_exists:
                # Create fresh table
                logger.info("[BUILDS] Creating new builds table")
                conn.execute("""
                    CREATE TABLE builds (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        project_name TEXT NOT NULL,
                        status TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        filename TEXT DEFAULT 'nox_app.zip',
                        size INTEGER DEFAULT 0
                    )
                """)
            else:
                # Migrate existing table by adding missing columns
                logger.info("[BUILDS] Migrating existing builds table")
                
                # Get all columns
                columns = conn.execute("PRAGMA table_info(builds)").fetchall()
                column_names = [col[1] for col in columns]
                
                now = datetime.utcnow().isoformat()
                
                # Add missing columns with constant defaults
                if 'status' not in column_names:
                    logger.info("[BUILDS] Adding status column")
                    conn.execute("ALTER TABLE builds ADD COLUMN status TEXT DEFAULT 'pending'")
                
                if 'created_at' not in column_names:
                    logger.info("[BUILDS] Adding created_at column")
                    conn.execute(f"ALTER TABLE builds ADD COLUMN created_at TIMESTAMP DEFAULT '{now}'")
                
                if 'updated_at' not in column_names:
                    logger.info("[BUILDS] Adding updated_at column")
                    conn.execute(f"ALTER TABLE builds ADD COLUMN updated_at TIMESTAMP DEFAULT '{now}'")
                
                if 'filename' not in column_names:
                    logger.info("[BUILDS] Adding filename column")
                    conn.execute("ALTER TABLE builds ADD COLUMN filename TEXT DEFAULT 'nox_app.zip'")
                
                if 'size' not in column_names:
                    logger.info("[BUILDS] Adding size column")
                    conn.execute("ALTER TABLE builds ADD COLUMN size INTEGER DEFAULT 0")
            
            # Create indexes
            try:
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_builds 
                    ON builds(user_id, created_at DESC)
                """)
            except Exception:
                pass
            
            try:
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_project_search 
                    ON builds(user_id, project_name)
                """)
            except Exception:
                pass
            
            conn.commit()
            logger.info("[BUILDS] Database table initialized and migrated successfully")
    except Exception as e:
        logger.error(f"[BUILDS] Table init error: {e}", exc_info=True)


# Initialize on startup
init_builds_table()


@router.get("/builds")
async def get_builds(
    user: str = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    🔥 Get build history for a user
    
    Query params:
        - limit: Max builds to return (default: 50, max: 100)
        - offset: Pagination offset (default: 0)
    
    Returns:
        {
            "builds": [...],
            "total": N,
            "limit": N,
            "offset": N
        }
    """
    try:
        user_id = str(user).lower().strip()
        logger.info(f"[BUILDS] Fetching builds for {user_id}: limit={limit}, offset={offset}")
        
        with sqlite3.connect("builds.db") as conn:
            conn.row_factory = sqlite3.Row
            
            # Get total count
            total = conn.execute(
                "SELECT COUNT(*) FROM builds WHERE user_id = ?",
                (user_id,)
            ).fetchone()[0]
            
            # Get paginated builds
            builds = conn.execute("""
                SELECT 
                    id,
                    user_id,
                    project_name,
                    COALESCE(status, 'pending') as status,
                    COALESCE(created_at, datetime('now')) as created_at,
                    COALESCE(updated_at, datetime('now')) as updated_at,
                    COALESCE(filename, 'nox_app.zip') as filename,
                    COALESCE(size, 0) as size
                FROM builds
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset)).fetchall()
            
            builds_list = [dict(b) for b in builds]
            
            logger.info(f"[BUILDS] Retrieved {len(builds_list)} builds for {user_id}")
            
            return {
                "status": "success",
                "builds": builds_list,
                "total": total,
                "limit": limit,
                "offset": offset,
                "count": len(builds_list)
            }
    
    except Exception as e:
        logger.error(f"[BUILDS] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve builds")


@router.get("/builds/stats")
async def get_build_stats(user: str = Depends(get_current_user)):
    """
    🔥 Get build statistics for a user
    
    Returns: Build stats including success rate
    """
    try:
        user_id = str(user).lower().strip()
        logger.info(f"[BUILD-STATS] Fetching stats for {user_id}")
        
        with sqlite3.connect("builds.db") as conn:
            stats = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN COALESCE(status, 'pending') = 'success' THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN COALESCE(status, 'pending') = 'failed' THEN 1 ELSE 0 END) as failed,
                    MIN(COALESCE(created_at, datetime('now'))) as oldest,
                    MAX(COALESCE(created_at, datetime('now'))) as latest
                FROM builds
                WHERE user_id = ?
            """, (user_id,)).fetchone()
            
            total = stats[0] or 0
            successful = stats[1] or 0
            failed = stats[2] or 0
            oldest = stats[3]
            latest = stats[4]
            
            success_rate = (successful / total * 100) if total > 0 else 0
            
            logger.info(f"[BUILD-STATS] {user_id}: {total} total, {success_rate:.1f}% success rate")
            
            return {
                "status": "success",
                "stats": {
                    "total_builds": total,
                    "successful": successful,
                    "failed": failed,
                    "success_rate": round(success_rate, 2),
                    "failure_rate": round(100 - success_rate, 2),
                    "latest_build": latest,
                    "oldest_build": oldest
                }
            }
    
    except Exception as e:
        logger.error(f"[BUILD-STATS] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve stats")


@router.get("/builds/{build_id}")
async def get_build(build_id: str, user: str = Depends(get_current_user)):
    """
    🔥 Get specific build details
    
    Returns: Complete build information
    """
    try:
        user_id = str(user).lower().strip()
        logger.info(f"[BUILD] Fetching build {build_id} for {user_id}")
        
        with sqlite3.connect("builds.db") as conn:
            conn.row_factory = sqlite3.Row
            
            build = conn.execute("""
                SELECT *
                FROM builds
                WHERE id = ? AND user_id = ?
            """, (build_id, user_id)).fetchone()
            
            if not build:
                logger.warning(f"[BUILD] Build {build_id} not found for {user_id}")
                raise HTTPException(status_code=404, detail="Build not found")
            
            build_dict = dict(build)
            logger.info(f"[BUILD] Retrieved build {build_id}")
            
            return {
                "status": "success",
                "build": build_dict
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BUILD] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve build")


@router.get("/builds/search")
async def search_builds(
    query: str,
    user: str = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100)
):
    """
    🔥 Search builds by project name
    
    Query params:
        - query: Search term (required)
        - limit: Max results (default: 50)
    
    Returns: Matching builds
    """
    try:
        if not query or len(query.strip()) < 2:
            raise HTTPException(status_code=400, detail="Query must be 2+ characters")
        
        user_id = str(user).lower().strip()
        search_term = f"%{query.lower()}%"
        
        logger.info(f"[BUILD-SEARCH] Searching for '{query}' for {user_id}")
        
        with sqlite3.connect("builds.db") as conn:
            conn.row_factory = sqlite3.Row
            
            builds = conn.execute("""
                SELECT *
                FROM builds
                WHERE user_id = ? AND LOWER(project_name) LIKE ?
                ORDER BY COALESCE(created_at, datetime('now')) DESC
                LIMIT ?
            """, (user_id, search_term, limit)).fetchall()
            
            builds_list = [dict(b) for b in builds]
            
            logger.info(f"[BUILD-SEARCH] Found {len(builds_list)} results for '{query}'")
            
            return {
                "status": "success",
                "query": query,
                "results": builds_list,
                "count": len(builds_list)
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BUILD-SEARCH] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Search failed")


@router.post("/builds/record")
async def record_build(
    project_name: str,
    status: str = "success",
    filename: str = "nox_app.zip",
    size: int = 0,
    user: str = Depends(get_current_user)
):
    """
    🔥 Record a new build
    
    Returns: Created build record
    """
    try:
        user_id = str(user).lower().strip()
        build_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        logger.info(f"[BUILD-RECORD] Recording build for {user_id}: {project_name}")
        
        with sqlite3.connect("builds.db") as conn:
            conn.execute("""
                INSERT INTO builds (id, user_id, project_name, status, filename, size, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (build_id, user_id, project_name, status, filename, size, now, now))
            
            conn.commit()
            
            logger.info(f"[BUILD-RECORD] Build {build_id} recorded")
            
            return {
                "status": "success",
                "build_id": build_id,
                "message": "Build recorded"
            }
    
    except Exception as e:
        logger.error(f"[BUILD-RECORD] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to record build")


@router.get("/builds/history")
async def get_build_history(
    user: str = Depends(get_current_user),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """
    Get build history for the current user
    - Returns the N most recent builds (latest first)
    - Supports pagination via limit/offset
    """
    try:
        user_id = str(user).lower().strip()
        with sqlite3.connect("builds.db") as conn:
            conn.row_factory = sqlite3.Row
            # Get total count for this user
            total = conn.execute(
                "SELECT COUNT(*) FROM builds WHERE user_id = ?", (user_id,)
            ).fetchone()[0]
            # Fetch builds (paginated)
            builds = conn.execute("""
                SELECT 
                    id, project_name, status, filename, size,
                    COALESCE(created_at, datetime('now')) as created_at,
                    COALESCE(updated_at, created_at) as updated_at
                FROM builds
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset)).fetchall()

        builds_list = [dict(row) for row in builds]
        return {
            "status": "success",
            "total": total,
            "count": len(builds_list),
            "limit": limit,
            "offset": offset,
            "history": builds_list
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch build history: {e}")