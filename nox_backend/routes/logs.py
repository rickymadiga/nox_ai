from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import StreamingResponse
import asyncio
import json
import sqlite3
import logging
from datetime import datetime
from typing import Optional

from nox_backend.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/admin/forge-stats")
async def forge_stats(user: str = Depends(get_current_user), request: Request = None):
    """
    🔥 Get forge statistics and build metrics

    Returns: Complete forge stats including builds, users, success rates
    """
    try:
        # Admin check
        if user != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized - admin only")

        logger.info("[FORGE-STATS] Fetching statistics")

        with sqlite3.connect("builds.db") as conn:
            # Total builds
            total_builds = conn.execute("SELECT COUNT(*) FROM builds").fetchone()[0]

            # Builds by user (top 10)
            per_user = conn.execute("""
                SELECT user_id, COUNT(*) as count
                FROM builds
                GROUP BY user_id
                ORDER BY count DESC
                LIMIT 10
            """).fetchall()

            # Builds by date (last 7 days)
            last_7_days = conn.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM builds
                WHERE created_at >= datetime('now', '-7 days')
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """).fetchall()

            # Average builds per user
            avg_builds = conn.execute("""
                SELECT AVG(user_builds)
                FROM (
                    SELECT COUNT(*) as user_builds
                    FROM builds
                    GROUP BY user_id
                )
            """).fetchone()[0]

            # Most used project names
            top_projects = conn.execute("""
                SELECT project_name, COUNT(*) as count
                FROM builds
                GROUP BY project_name
                ORDER BY count DESC
                LIMIT 5
            """).fetchall()

            # Build timing stats
            timing_stats = conn.execute("""
                SELECT 
                    MIN(created_at) as first_build,
                    MAX(created_at) as last_build,
                    COUNT(*) as total
                FROM builds
            """).fetchone()

        logger.info(f"[FORGE-STATS] Retrieved stats: {total_builds} total builds")

        return {
            "status": "success",
            "stats": {
                "total_builds": total_builds,
                "unique_users": len(per_user),
                "avg_builds_per_user": round(avg_builds, 2) if avg_builds else 0,
                "first_build": timing_stats[0] if timing_stats[0] else None,
                "last_build": timing_stats[1] if timing_stats[1] else None,
            },
            "top_users": [
                {"user": r[0], "count": r[1]} for r in per_user
            ],
            "top_projects": [
                {"name": r[0], "count": r[1]} for r in top_projects
            ],
            "builds_by_date": [
                {"date": r[0], "count": r[1]} for r in last_7_days
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[FORGE-STATS] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


@router.get("/admin/forge-logs")
async def forge_logs(
    user: str = Depends(get_current_user),
    request: Request = None,
    limit: int = Query(100, ge=1, le=1000),
    user_filter: Optional[str] = Query(None)
):
    """
    🔥 Get forge execution logs

    Query params:
        - limit: Max logs to return (default: 100, max: 1000)
        - user_filter: Filter logs by user_id

    Returns: {"logs": [...], "count": N}
    """
    try:
        # Admin check
        if user != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized - admin only")

        limit = min(limit, 1000)  # Cap at 1000

        logger.info(f"[FORGE-LOGS] Fetching logs (limit: {limit}, filter: {user_filter})")

        # Get logs from engine runtime
        all_logs = []
        if hasattr(request.app.state.engine.runtime, "get_all_logs"):
            try:
                all_logs = request.app.state.engine.runtime.get_all_logs()
            except Exception as e:
                logger.warning(f"[FORGE-LOGS] Could not fetch all logs: {e}")

        # Filter by user if provided
        if user_filter:
            filtered_logs = [log for log in all_logs if isinstance(log, dict) and log.get("user_id") == user_filter]
        else:
            filtered_logs = all_logs

        # Return latest logs
        recent_logs = filtered_logs[-limit:] if len(filtered_logs) > limit else filtered_logs

        logger.info(f"[FORGE-LOGS] Retrieved {len(recent_logs)} logs")

        return {
            "status": "success",
            "logs": recent_logs,
            "count": len(recent_logs),
            "total_available": len(filtered_logs),
            "user_filter": user_filter
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[FORGE-LOGS] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Logs retrieval failed: {str(e)}")


@router.get("/admin/forge-logs/stream")
async def forge_logs_stream(user: str = Depends(get_current_user), request: Request = None):
    """
    🔥 Stream forge logs in real-time (Server-Sent Events)

    Returns: Server-Sent Event stream
    """
    try:
        # Admin check
        if user != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized - admin only")

        logger.info("[FORGE-LOGS-STREAM] Starting log stream")

        async def log_stream():
            """Generate log stream"""
            last_index = 0
            timeout_count = 0
            max_timeout = 120  # 2 minutes

            while timeout_count < max_timeout:
                try:
                    # Get current logs
                    all_logs = []
                    if hasattr(request.app.state.engine.runtime, "get_all_logs"):
                        try:
                            all_logs = request.app.state.engine.runtime.get_all_logs()
                        except Exception:
                            pass

                    # Send new logs since last index
                    if last_index < len(all_logs):
                        for log in all_logs[last_index:]:
                            log_data = {
                                "log": log,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                            yield f"data: {json.dumps(log_data)}\n\n"
                        last_index = len(all_logs)
                        timeout_count = 0  # Reset timeout on new logs
                    else:
                        timeout_count += 1

                    await asyncio.sleep(1)

                except Exception as e:
                    logger.error(f"[FORGE-LOGS-STREAM] Error: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
                    await asyncio.sleep(1)

            logger.info("[FORGE-LOGS-STREAM] Stream timeout")
            yield f"data: {json.dumps({'message': '[TIMEOUT] Stream ended'})}\n\n"

        return StreamingResponse(
            log_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[FORGE-LOGS-STREAM] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Stream failed")


@router.get("/admin/forge-logs/search")
async def forge_logs_search(
    query: str,
    user: str = Depends(get_current_user),
    request: Request = None,
    limit: int = Query(50, ge=1, le=1000)
):
    """
    🔥 Search through forge logs

    Query params:
        - query: Search term (required)
        - limit: Max results (default: 50)

    Returns: {"results": [...], "count": N}
    """
    try:
        # Admin check
        if user != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized - admin only")

        if not query or len(query.strip()) < 2:
            raise HTTPException(status_code=400, detail="Query must be at least 2 characters")

        logger.info(f"[FORGE-LOGS-SEARCH] Searching for: {query}")

        # Get all logs
        all_logs = []
        if hasattr(request.app.state.engine.runtime, "get_all_logs"):
            try:
                all_logs = request.app.state.engine.runtime.get_all_logs()
            except Exception:
                pass

        # Search (case-insensitive)
        search_query = query.lower()
        results = []

        for log in all_logs:
            if isinstance(log, dict):
                # Search in all string values
                log_str = json.dumps(log).lower()
                if search_query in log_str:
                    results.append(log)
            elif isinstance(log, str):
                if search_query in log.lower():
                    results.append(log)

        # Limit results
        limited_results = results[-limit:] if len(results) > limit else results

        logger.info(f"[FORGE-LOGS-SEARCH] Found {len(limited_results)} results")

        return {
            "status": "success",
            "query": query,
            "results": limited_results,
            "count": len(limited_results),
            "total_found": len(results)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[FORGE-LOGS-SEARCH] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/admin/build-metrics")
async def build_metrics(user: str = Depends(get_current_user)):
    """
    🔥 Get detailed build metrics

    Returns: Build success rates, timing, and performance stats
    """
    try:
        # Admin check
        if user != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized - admin only")

        logger.info("[BUILD-METRICS] Fetching metrics")

        with sqlite3.connect("builds.db") as conn:
            # Success/failure counts
            stats = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
                FROM builds
            """).fetchone()

            total = stats[0]
            successful = stats[1] or 0
            failed = stats[2] or 0
            success_rate = (successful / total * 100) if total > 0 else 0

        logger.info(f"[BUILD-METRICS] Success rate: {success_rate:.1f}%")

        return {
            "status": "success",
            "metrics": {
                "total_builds": total,
                "successful": successful,
                "failed": failed,
                "success_rate": round(success_rate, 2),
                "failure_rate": round(100 - success_rate, 2)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BUILD-METRICS] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Metrics retrieval failed")


@router.get("/admin/logs/clear")
async def clear_logs(user: str = Depends(get_current_user), request: Request = None):
    """
    🔥 Clear all logs (admin only)

    Returns: {"message": "Logs cleared"}
    """
    try:
        # Admin check
        if user != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized - admin only")

        logger.info("[LOGS-CLEAR] Clearing all logs")

        # Clear runtime logs
        if hasattr(request.app.state.engine.runtime, "clear_all_logs"):
            request.app.state.engine.runtime.clear_all_logs()

        logger.info("[LOGS-CLEAR] ✅ Logs cleared")

        return {
            "status": "success",
            "message": "All logs cleared"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[LOGS-CLEAR] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Clear failed")