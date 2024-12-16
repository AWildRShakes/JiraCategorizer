# core/async_classifier.py
import asyncio
import logging
from typing import Tuple, Optional
from services import AsyncOpenAIService, SchemaGenerator

class AsyncTicketClassifier:
    """Handles the asynchronous classification of Jira tickets using OpenAI API"""
    
    def __init__(self):
        self.openai_service = AsyncOpenAIService()
        self.schema_generator = SchemaGenerator()
        # Cache schemas to avoid regenerating them for each ticket
        self._category_schema = None
        self._priority_schema = None
        
    async def classify_ticket(self, title: str, summary: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Classify a single ticket with category, request type, and priority asynchronously
        
        Args:
            title: Ticket title
            summary: Ticket summary
            
        Returns:
            Tuple[Optional[str], Optional[str], Optional[str]]: Category, request type, and priority level
        """
        try:
            logging.debug(f"Processing ticket: '{title}'")
            start_time = logging.log_timing(f"Classification of ticket '{title}'")
            
            # Initialize schemas if not already cached
            if not self._category_schema:
                self._category_schema = self.schema_generator.create_category_schema()
            if not self._priority_schema:
                self._priority_schema = self.schema_generator.create_priority_schema()
            
            # Get initial category to determine request type schema
            category = await self._get_category(title, summary)
            if not category:
                logging.warning(f"Failed to get category for ticket: '{title}'")
                return None, None, None
            
            # Generate request type schema based on category
            request_type_schema = self.schema_generator.create_request_type_schema(category)
            
            # Perform complete classification
            category, request_type, priority_level = await self.openai_service.classify_ticket_complete(
                title,
                summary,
                self._category_schema,
                request_type_schema,
                self._priority_schema
            )
            
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                logging.log_timing(f"Classification of ticket '{title}'", start_time)
            
            if category and request_type and priority_level:
                logging.debug(f"Successfully classified ticket '{title}': "
                            f"Category='{category}', RequestType='{request_type}', "
                            f"Priority='{priority_level}'")
            else:
                logging.warning(f"Partial or failed classification for ticket '{title}': "
                              f"Category='{category}', RequestType='{request_type}', "
                              f"Priority='{priority_level}'")
            
            return category, request_type, priority_level
                
        except Exception as e:
            logging.error(f"Error classifying ticket '{title}': {str(e)}")
            return None, None, None

    async def _get_category(self, title: str, summary: str) -> Optional[str]:
        """Get category classification for a ticket"""
        try:
            if not self._category_schema:
                self._category_schema = self.schema_generator.create_category_schema()
            return await self.openai_service.get_category_classification(title, summary, self._category_schema)
        except Exception as e:
            logging.error(f"Error in category classification: {str(e)}")
            return None

    async def classify_tickets_batch(self, tickets: list[tuple[str, str]]) -> list[tuple[Optional[str], Optional[str], Optional[str]]]:
        """
        Classify a batch of tickets concurrently
        
        Args:
            tickets: List of (title, summary) tuples
            
        Returns:
            List of (category, request_type, priority) tuples
        """
        try:
            results = await asyncio.gather(
                *(self.classify_ticket(title, summary) for title, summary in tickets),
                return_exceptions=True
            )
            
            # Handle any exceptions in the results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logging.error(f"Error processing ticket '{tickets[i][0]}': {str(result)}")
                    processed_results.append((None, None, None))
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            logging.error(f"Error in batch classification: {str(e)}")
            return [(None, None, None)] * len(tickets)