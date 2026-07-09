from fastapi import HTTPException, status


def not_found(error_code: str) -> HTTPException:
    """Raise a 404 carrying a stable, language-agnostic error code.

    Used both for genuinely missing resources and for authorization (IDOR):
    a resource that belongs to another team is reported as not found so the
    response never confirms its existence. As elsewhere, the frontend owns the
    translated copy; the backend only emits the `error_code`.
    """
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "statusCode": 404,
            "errorCode": error_code,
            "error": "Not Found",
        },
    )


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


def unprocessable(error_code: str) -> HTTPException:
    """Raise a 422 carrying a stable, language-agnostic error code.

    Used when a request is well-formed but violates a composition rule the
    schema cannot express (e.g. a starting XI that is not exactly one
    goalkeeper plus ten outfield players). As elsewhere, the frontend owns the
    translated copy; the backend only emits the `error_code`.
    """
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={
            "statusCode": 422,
            "errorCode": error_code,
            "error": "Unprocessable Entity",
        },
    )


def conflict(error_code: str) -> HTTPException:
    """Raise a 409 carrying a stable, language-agnostic error code.

    Used when a request collides with existing state (e.g. an email that is
    already registered). As with `unauthorized`, the frontend owns the
    translated copy; the backend only emits the `error_code`.
    """
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "statusCode": 409,
            "errorCode": error_code,
            "error": "Conflict",
        },
    )
