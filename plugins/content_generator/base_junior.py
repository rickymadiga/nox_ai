from typing import Dict, Any

class BaseJunior:
    """Base class for all juniors"""
    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement execute() method")