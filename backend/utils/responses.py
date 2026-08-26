"""
Standard response helpers so EVERY endpoint returns the same shape:

  success: { "success": true,  "message": "...", "data": {...} }
  error:   { "success": false, "message": "..." }

This matters a lot for the frontend: JavaScript can always trust
`data.success` and `data.data` instead of guessing between five
possible field names (which was one of the original bugs).
"""


def success_response(message: str, data=None):
    return {
        "success": True,
        "message": message,
        "data": data if data is not None else {}
    }


def error_response(message: str):
    return {
        "success": False,
        "message": message
    }
