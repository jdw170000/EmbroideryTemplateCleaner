import queue
import traceback
from typing import Generator

from .configuration import Configuration
from .cleaner import clean_directory_generator, OperationAbortedError
from .events import (
    Event,
    Response,
    RequestConfirmation,
    RequestRetrySkipAbort,
    CleaningResult,
    ErrorOccurred,
)

def run_cleaning_task(
    config: Configuration,
    update_queue: queue.Queue,
    response_queue: queue.Queue
):
    """
    This function is executed in a background thread. It runs the core
    cleaning generator and manages the communication with the GUI via queues.

    Args:
        config: The application configuration.
        update_queue: A queue to send events (e.g., StatusUpdate) to the GUI.
        response_queue: A queue to receive responses (e.g., UserConfirmationResponse)
                        from the GUI.
    """
    generator: Generator[Event, Response, int] | None = None
    try:
        # Create an instance of our main generator
        generator = clean_directory_generator(config)
        
        # Start iterating through the generator's events
        event = next(generator)

        while True:
            if isinstance(event, (RequestConfirmation, RequestRetrySkipAbort)):
                # The generator needs user input.
                # 1. Send the request to the GUI.
                update_queue.put(event)
                
                # 2. Wait for the GUI's response. This blocks the worker thread.
                response = response_queue.get()
                
                # 3. Send the GUI's response back into the generator to resume it.
                event = generator.send(response)
            else:
                # For simple status updates, just pass them to the GUI.
                update_queue.put(event)
                # Get the next event from the generator.
                event = next(generator)
    
    except OperationAbortedError as e:
        # The user selected "Abort" from a RetrySkipAbort dialog
        error_event = ErrorOccurred(message=str(e))
        update_queue.put(error_event)

    except StopIteration as e:
        # The generator has finished successfully.
        deleted_files_count = e.value
        result = CleaningResult(
            deleted_files_count=deleted_files_count,
            target_dir=str(config.target_directory)
        )
        update_queue.put(result)

    except Exception as e:
        # An unhandled exception occurred within the generator.
        tb_str = traceback.format_exc()
        error_event = ErrorOccurred(
            message=f"A critical error occurred: {e}",
            traceback=tb_str
        )
        update_queue.put(error_event)

    finally:
        # Ensure the generator is closed properly
        if generator:
            generator.close()