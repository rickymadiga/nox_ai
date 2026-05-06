import logging
import os
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ExecutorAgent:
    """
    Applies fixed code changes to the file system.
    Handles file creation, updates, and backup operations.
    """

    def __init__(self, runtime):
        self.runtime = runtime
        self.name = "executor"
        self.backup_enabled = True
        self.backup_dir = ".backups"
        logger.info("ExecutorAgent initialized")

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute file changes from fixes.

        Args:
            task: Dictionary containing:
                - fixes: Dictionary of fixed file content
                - fixed_files: Alias for fixes
                - target_dir: Optional target directory
                - create_backup: Whether to create backups
                - dry_run: If True, don't actually write files

        Returns:
            Dictionary containing:
                - success: Whether execution succeeded
                - executed_files: List of files that were updated
                - backup_location: Location of backup if created
                - messages: Execution messages
        """
        try:
            fixes = task.get("fixes", {}) or task.get("fixed_files", {})
            target_dir = task.get("target_dir", ".")
            create_backup = task.get("create_backup", self.backup_enabled)
            dry_run = task.get("dry_run", False)

            logger.info(f"Starting execution of {len(fixes)} file changes (dry_run={dry_run})")

            if not fixes:
                logger.warning("No fixes provided to execute")
                return {
                    "success": False,
                    "executed_files": [],
                    "messages": ["No fixes to execute"],
                    "error": "Empty fixes dictionary"
                }

            executed_files = []
            messages = []
            backup_location = None

            # Create backup if requested
            if create_backup and not dry_run:
                backup_location = await self._create_backup(target_dir)
                if backup_location:
                    messages.append(f"Backup created at: {backup_location}")

            # Apply fixes
            for file_path, content in fixes.items():
                try:
                    full_path = os.path.join(target_dir, file_path)

                    if dry_run:
                        logger.info(f"[DRY RUN] Would update: {full_path}")
                        messages.append(f"[DRY RUN] Would update: {file_path}")
                    else:
                        # Create directories if needed
                        os.makedirs(os.path.dirname(full_path), exist_ok=True)

                        # Write the file
                        with open(full_path, "w", encoding="utf-8") as f:
                            f.write(content)

                        logger.info(f"Updated: {full_path}")
                        messages.append(f"Updated: {file_path}")
                        executed_files.append(file_path)

                except Exception as e:
                    logger.error(f"Error writing file {file_path}: {str(e)}", exc_info=True)
                    messages.append(f"ERROR writing {file_path}: {str(e)}")

            success = len(executed_files) > 0 or dry_run

            result = {
                "success": success,
                "executed_files": executed_files,
                "backup_location": backup_location,
                "messages": messages,
                "files_count": len(executed_files),
                "dry_run": dry_run
            }

            logger.info(
                f"Execution complete: {len(executed_files)} files updated, "
                f"Success={success}"
            )
            return result

        except Exception as e:
            logger.error(f"Error in executor: {str(e)}", exc_info=True)
            return {
                "success": False,
                "executed_files": [],
                "messages": [],
                "error": str(e)
            }

    async def _create_backup(self, target_dir: str) -> Optional[str]:
        """Create a backup of the target directory."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.backup_dir, f"backup_{timestamp}")

            os.makedirs(self.backup_dir, exist_ok=True)

            if os.path.exists(target_dir):
                shutil.copytree(target_dir, backup_path, dirs_exist_ok=True)
                logger.info(f"Backup created: {backup_path}")
                return backup_path
            else:
                logger.warning(f"Target directory not found for backup: {target_dir}")
                return None

        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def _verify_files(target_dir: str, files: List[str]) -> bool:
        """Verify that files were written correctly."""
        for file_path in files:
            full_path = os.path.join(target_dir, file_path)
            if not os.path.exists(full_path):
                logger.error(f"File verification failed: {full_path} not found")
                return False

        return True