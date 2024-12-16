# core/classifier.py
import logging
from typing import Tuple, Optional
from services import OpenAIService, SchemaGenerator

class TicketClassifier:
    """Handles the classification of Jira tickets using OpenAI API"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.schema_generator = SchemaGenerator()
        
    def classify_ticket(self, title: str, summary: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Classify a single ticket with category, request type, and priority
        
        Args:
            title: Ticket title
            summary: Ticket summary
            
        Returns:
            Tuple[Optional[str], Optional[str], Optional[str]]: Category, request type, and priority level
        """
        try:
            logging.debug(f"Processing ticket: '{title}'")
            start_time = logging.log_timing(f"Classification of ticket '{title}'")
            
            # Get category classification
            category = self._get_category(title, summary)
            if not category:
                logging.warning(f"Failed to get category for ticket: '{title}'")
                return None, None, None
            
            # Get request type classification
            request_type = self._get_request_type(title, summary, category)
            if not request_type:
                logging.warning(f"Failed to get request type for ticket: '{title}' in category '{category}'")
                return category, None, None
                
            # Get priority classification
            priority_schema = self.schema_generator.create_priority_schema()
            priority_info = self.openai_service.get_priority_classification(title, summary, priority_schema)
            if not priority_info:
                logging.warning(f"Failed to get priority for ticket: '{title}'")
                return category, request_type, None
            
            # Extract priority level from priority_info dictionary
            priority_level = priority_info.get('priority')
            
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                logging.log_timing(f"Classification of ticket '{title}'", start_time)
            logging.debug(f"Successfully classified ticket '{title}': "
                        f"Category='{category}', RequestType='{request_type}', "
                        f"Priority='{priority_level}'")
            
            return category, request_type, priority_level
                
        except Exception as e:
            logging.error(f"Error classifying ticket '{title}': {str(e)}")
            return None, None, None

    def _get_category(self, title: str, summary: str) -> Optional[str]:
        """Get category classification for a ticket"""
        try:
            schema = self.schema_generator.create_category_schema()
            return self.openai_service.get_category_classification(title, summary, schema)
        except Exception as e:
            logging.error(f"Error in category classification: {str(e)}")
            return None

    def _get_request_type(self, title: str, summary: str, category: str) -> Optional[str]:
        """Get request type classification for a ticket within a category"""
        try:
            schema = self.schema_generator.create_request_type_schema(category)
            return self.openai_service.get_request_type_classification(
                title, summary, category, schema
            )
        except Exception as e:
            logging.error(f"Error in request type classification: {str(e)}")
            return None