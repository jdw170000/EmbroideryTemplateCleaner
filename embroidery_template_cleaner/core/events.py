from dataclasses import dataclass
from enum import Enum, auto

# --- Events from Worker to GUI ---

@dataclass
class StatusUpdate:
    """Sent by the worker to update the GUI with a progress message."""
    message: str

@dataclass
class RequestConfirmation:
    """
    Sent by the worker when it needs the user to confirm an action.
    The worker will pause until a UserConfirmationResponse is sent back.
    """
    path: str
    files_in_dir: list[str]

class RetrySkipAbortChoice(Enum):
    """Enumerates the possible user choices for a failed operation."""
    RETRY = auto()
    SKIP = auto()
    ABORT = auto()

@dataclass
class RequestRetrySkipAbort:
    """
    Sent by the worker when a recoverable error occurs. The worker
    will pause until a RetrySkipAbortResponse is received.
    """
    operation_description: str # e.g., "deleting file" or "removing directory"
    path: str
    error_message: str

@dataclass
class CleaningResult:
    """Sent when the cleaning operation finishes successfully."""
    deleted_files_count: int
    target_dir: str

@dataclass
class ErrorOccurred:
    """Sent when a fatal error stops the cleaning operation."""
    message: str
    traceback: str | None = None


# --- Events from GUI to Worker ---

@dataclass
class UserConfirmationResponse:
    """Sent by the GUI in response to a RequestConfirmation event."""
    accepted: bool

@dataclass
class RetrySkipAbortResponse:
    """Sent by the GUI in response to a RequestRetrySkipAbort event."""
    choice: RetrySkipAbortChoice

# --- Type Aliases for clarity in function signatures ---

# An Event is any message sent FROM the worker TO the GUI.
type Event = StatusUpdate | RequestConfirmation | RequestRetrySkipAbort | CleaningResult | ErrorOccurred

# A Response is any message sent FROM the GUI TO the worker.
type Response = UserConfirmationResponse | RetrySkipAbortResponse