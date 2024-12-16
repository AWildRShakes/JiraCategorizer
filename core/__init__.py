from .classifier import TicketClassifier
from .processor import TicketProcessor
from .async_processor import AsyncTicketProcessor
import logging
from typing import Optional

__all__ = ['TicketClassifier', 'TicketProcessor','AsyncTicketProcessor']

# Add custom logging functions
def log_timing(message: str, start_time: Optional[float] = None) -> Optional[float]:
    """
    Log timing information for operations
    
    Args:
        message: Message to log
        start_time: Optional start time for operation
        
    Returns:
        float: Current time if start_time is None, else None
    """
    import time
    current_time = time.time()
    
    if start_time is not None:
        duration = current_time - start_time
        logging.info(f"{message} completed in {duration:.2f} seconds")
        return None
    
    return current_time

# Add custom logging function to logging module
logging.log_timing = log_timing