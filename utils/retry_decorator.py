# utils/retry_decorator.py
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging
from config.settings import Config

def create_retry_decorator(operation_name):
    """Create a retry decorator with custom configuration and logging"""
    def log_retry(retry_state):
        if retry_state.attempt_number > 1:  # Only log actual retries
            exception = retry_state.outcome.exception()
            logging.warning(
                f"Retrying {operation_name} - Attempt {retry_state.attempt_number}/{Config.MAX_RETRIES}. "
                f"Exception: {type(exception).__name__}: {str(exception)}"
            )

    def log_success(retry_state):
        if retry_state.attempt_number > 1:  # Only log if there were retries
            logging.debug(
                f"Successfully completed {operation_name} after {retry_state.attempt_number} attempts"
            )

    return retry(
        stop=stop_after_attempt(Config.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((Exception)),
        before=log_retry,
        after=log_success
    )