from fastapi import HTTPException, status


def unauthorized(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "statusCode": 401,
            "message": message,
            "error": "Unauthorized",
        },
    )
