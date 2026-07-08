from fastapi import HTTPException, status


def unauthorized(error_code: str) -> HTTPException:
    """Raise a 401 carrying a stable, language-agnostic error code.

    The frontend maps `error_code` to a translated message for the user's
    locale; the backend never emits user-facing text.
    """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "statusCode": 401,
            "errorCode": error_code,
            "error": "Unauthorized",
        },
    )
