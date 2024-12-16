# services/async_openai_client.py
from openai import AsyncOpenAI
import json
import logging
from config.settings import Config
from typing import Dict, Optional
import asyncio
from functools import wraps

def create_async_retry_decorator(operation_name):
    """Create an async retry decorator with custom configuration and logging"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 1
            while attempt <= Config.MAX_RETRIES:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == Config.MAX_RETRIES:
                        logging.error(f"Final attempt failed for {operation_name}: {str(e)}")
                        raise
                    
                    wait_time = min(2 ** attempt * 1, 10)  # Exponential backoff capped at 10 seconds
                    logging.warning(
                        f"Retrying {operation_name} - Attempt {attempt}/{Config.MAX_RETRIES}. "
                        f"Exception: {type(e).__name__}: {str(e)}. "
                        f"Waiting {wait_time} seconds..."
                    )
                    await asyncio.sleep(wait_time)
                    attempt += 1
            
            raise Exception(f"Failed to complete {operation_name} after {Config.MAX_RETRIES} attempts")
        return wrapper
    return decorator

class AsyncOpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=Config.OPENAI_API_KEY,
            timeout=Config.REQUEST_TIMEOUT
        )

    @create_async_retry_decorator("category_classification")
    async def get_category_classification(self, title: str, summary: str, schema: dict) -> Optional[str]:
        """Get category classification using OpenAI with retries"""
        try:
            completion = await self.client.chat.completions.create(
                model=Config.MODEL_VERSION,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert system designed to classify Jira tickets into appropriate service categories. You will analyze the ticket title and summary to determine the most appropriate category. Your response must strictly conform to the provided JSON schema."
                    },
                    {
                        "role": "user",
                        "content": f"Please classify this Jira ticket:\nTitle: {title}\nSummary: {summary}"
                    }
                ],
                response_format={"type": "json_object"},
                functions=[{
                    "name": "classify_category",
                    "description": "Classify a ticket into a service category",
                    "parameters": schema
                }],
                function_call={"name": "classify_category"}
            )
            
            response = json.loads(completion.choices[0].message.function_call.arguments)
            return response.get('category')
        except Exception as e:
            logging.error(f"Error in category classification for ticket '{title}': {str(e)}")
            raise

    @create_async_retry_decorator("request_type_classification")
    async def get_request_type_classification(self, title: str, summary: str, category: str, schema: dict) -> Optional[str]:
        """Get request type classification using OpenAI with retries"""
        try:
            completion = await self.client.chat.completions.create(
                model=Config.MODEL_VERSION,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert system designed to classify Jira tickets into appropriate service request types. You will analyze the ticket title and summary to determine the most appropriate request type within the given category. Your response must strictly conform to the provided JSON schema."
                    },
                    {
                        "role": "user",
                        "content": f"Please classify this Jira ticket in category '{category}':\nTitle: {title}\nSummary: {summary}"
                    }
                ],
                response_format={"type": "json_object"},
                functions=[{
                    "name": "classify_request_type",
                    "description": "Classify a ticket into a service request type",
                    "parameters": schema
                }],
                function_call={"name": "classify_request_type"}
            )
            
            response = json.loads(completion.choices[0].message.function_call.arguments)
            return response.get('request_type')
        except Exception as e:
            logging.error(f"Error in request type classification for ticket '{title}': {str(e)}")
            raise

    @create_async_retry_decorator("priority_classification")
    async def get_priority_classification(self, title: str, summary: str, schema: dict) -> Optional[Dict[str, str]]:
        """Get priority classification using OpenAI with retries"""
        try:
            completion = await self.client.chat.completions.create(
                model=Config.MODEL_VERSION,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert system designed to classify IT service tickets based on their impact and urgency levels. Analyze the ticket details and determine appropriate impact, urgency, and resulting priority levels according to the provided guidelines. Your response must strictly conform to the provided JSON schema."
                    },
                    {
                        "role": "user",
                        "content": f"Please assess the priority of this ticket:\nTitle: {title}\nSummary: {summary}"
                    }
                ],
                response_format={"type": "json_object"},
                functions=[{
                    "name": "classify_priority",
                    "description": "Classify a ticket's priority based on impact and urgency",
                    "parameters": schema
                }],
                function_call={"name": "classify_priority"}
            )
            
            response = json.loads(completion.choices[0].message.function_call.arguments)
            return {
                'impact': response.get('impact'),
                'urgency': response.get('urgency'),
                'priority': response.get('priority')
            }
        except Exception as e:
            logging.error(f"Error in priority classification for ticket '{title}': {str(e)}")
            raise

    async def classify_ticket_complete(self, title: str, summary: str, category_schema: dict, 
                                    request_type_schema: dict, priority_schema: dict) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Perform complete ticket classification with all three API calls"""
        try:
            # Get category first
            category = await self.get_category_classification(title, summary, category_schema)
            if not category:
                return None, None, None

            # Get request type using the category
            request_type = await self.get_request_type_classification(title, summary, category, request_type_schema)
            if not request_type:
                return category, None, None

            # Get priority classification
            priority_info = await self.get_priority_classification(title, summary, priority_schema)
            if not priority_info:
                return category, request_type, None

            return category, request_type, priority_info.get('priority')
        except Exception as e:
            logging.error(f"Error in complete ticket classification for '{title}': {str(e)}")
            return None, None, None