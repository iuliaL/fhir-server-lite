from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from sqlalchemy.exc import OperationalError
from typing import Any
from sqlalchemy.orm import Session


# Define retry decorator for database operations
def with_db_retry(func):
    """
    Decorator that adds retry logic to database operations.
    Retries up to 3 times with a 2 second delay between attempts.
    """

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(OperationalError),
        reraise=True,
    )
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@with_db_retry
def safe_add(db: Session, obj: Any) -> None:
    """Safely add an object to the database with retry logic"""
    db.add(obj)


@with_db_retry
def safe_commit(db: Session) -> None:
    """Safely commit changes to the database with retry logic"""
    db.commit()


@with_db_retry
def safe_refresh(db: Session, obj: Any) -> None:
    """Safely refresh an object from the database with retry logic"""
    db.refresh(obj)


@with_db_retry
def safe_delete(db: Session, obj: Any) -> None:
    """Safely delete an object from the database with retry logic"""
    db.delete(obj)


@with_db_retry
def save_and_refresh(db: Session, obj: Any) -> None:
    """
    Helper function to add an object to the database, commit the transaction,
    and refresh the object, all with retry logic.

    Args:
        db: The database session
        obj: The object to save and refresh
    """
    db.add(obj)
    db.commit()
    db.refresh(obj)


def safe_db_operation(db: Session, obj: Any = None, operation: str = None) -> None:
    """
    Perform a database operation safely with retries.

    Args:
        db: The database session
        obj: The object to operate on (for add, refresh, delete operations)
        operation: The operation to perform ('add', 'commit', 'refresh', 'delete')
    """
    if operation == "add" and obj is not None:
        safe_add(db, obj)
    elif operation == "commit":
        safe_commit(db)
    elif operation == "refresh" and obj is not None:
        safe_refresh(db, obj)
    elif operation == "delete" and obj is not None:
        safe_delete(db, obj)
