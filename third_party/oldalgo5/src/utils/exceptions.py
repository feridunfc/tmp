from __future__ import annotations

class AppError(Exception):
    """Base app error with a clean, user-readable message."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:  # pragma: no cover
        return self.message

class StrategyValidationError(AppError):
    """Raised when strategy parameters are invalid or no signals can be produced."""
    pass

class DataIntegrityError(AppError):
    """Raised when input data is missing columns, NaNs, or otherwise unusable."""
    pass
