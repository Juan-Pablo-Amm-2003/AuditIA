from typing import Dict, Any

def get_current_user() -> Dict[str, Any]:
    """Mock authentication - replace with real JWT auth later."""
    return {"id": 1, "username": "test_user"}
