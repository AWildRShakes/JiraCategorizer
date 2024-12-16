# services/openai_client.py
from openai import OpenAI
import json
import logging
from config.settings import Config
from utils.retry_decorator import create_retry_decorator

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(
            api_key=Config.OPENAI_API_KEY,
            timeout=Config.REQUEST_TIMEOUT
        )

    @create_retry_decorator("category_classification")
    def get_category_classification(self, title, summary, schema):
        """Get category classification using OpenAI with retries"""
        try:
            completion = self.client.chat.completions.create(
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

    @create_retry_decorator("request_type_classification")
    def get_request_type_classification(self, title, summary, category, schema):
        """Get request type classification using OpenAI with retries"""
        try:
            completion = self.client.chat.completions.create(
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
        
    @create_retry_decorator("priority_classification")
    def get_priority_classification(self, title: str, summary: str, schema: dict) -> dict:
        """Get priority classification using OpenAI with retries"""
        try:
            completion = self.client.chat.completions.create(
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