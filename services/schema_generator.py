# services/schema_generator.py
import json
from pathlib import Path
from config.settings import Config

class SchemaGenerator:
    def __init__(self):
        self.service_structure = self._load_service_structure()

    def _load_service_structure(self):
        """Load service categories and types from JSON file"""
        service_file = Config.DATA_DIR / 'service_categories_and_types.json'
        try:
            with open(service_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Service categories file not found at {service_file}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in service categories file at {service_file}")

    def create_category_schema(self):
        """Create JSON schema for category classification with descriptions"""
        categories = [cat['name'] for cat in self.service_structure['Service Categories']]
        
        schema_description = "Available categories and their purposes:\n"
        for cat in self.service_structure['Service Categories']:
            schema_description += f"\n• {cat['name']}:\n"
            for rt in cat['request_types']:
                schema_description += f"  - {rt['name']}: {rt['description']}\n"

        return {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": categories,
                    "description": schema_description
                }
            },
            "required": ["category"],
            "additionalProperties": False
        }

    def create_request_type_schema(self, category):
        """Create JSON schema for request type classification with descriptions"""
        request_types = []
        request_descriptions = "Available request types for this category:\n"
        
        # Find the matching category and its request types
        for cat in self.service_structure['Service Categories']:
            if cat['name'] == category:
                request_types = [rt['name'] for rt in cat['request_types']]
                for rt in cat['request_types']:
                    request_descriptions += f"\n• {rt['name']}: {rt['description']}"
                break

        return {
            "type": "object",
            "properties": {
                "request_type": {
                    "type": "string",
                    "enum": request_types,
                    "description": request_descriptions
                }
            },
            "required": ["request_type"],
            "additionalProperties": False
        }
        
    def create_priority_schema(self):
        """Create JSON schema for priority classification with streamlined guidelines"""
        priority_description = """
    Priority Matrix (Impact vs Urgency):
    - P1: High Impact + High Urgency
    - P2: (High Impact + Medium Urgency) or (Medium Impact + High Urgency)
    - P3: (High Impact + Low Urgency) or (Medium Impact + Medium Urgency) or (Low Impact + High Urgency)
    - P4: (Medium Impact + Low Urgency) or (Low Impact + Medium/Low Urgency)

    Impact Levels (based on scope of effect):
    - High: Entire location/dept (251+ employees), 10,001+ customers, safety issues, or company reputation
    - Medium: 101-250 employees, 1,001-10,000 customers, or business unit impact
    - Low: Up to 100 employees or 1,000 customers

    Urgency Levels (based on resolution timing):
    - High: Complete service outage, safety risk, data breach, strict deadline (<5 days), no workaround
    - Medium: Severe impact with temporary workaround, leadership impact, upcoming deadline (>5 days)
    - Low: Limited impact with readily available workaround, no critical timeline
    """

        return {
            "type": "object",
            "properties": {
                "impact": {
                    "type": "string",
                    "enum": ["High", "Medium", "Low"],
                    "description": "Assess the scope and severity of the issue's effect"
                },
                "urgency": {
                    "type": "string",
                    "enum": ["High", "Medium", "Low"],
                    "description": "Assess how quickly the issue needs resolution"
                },
                "priority": {
                    "type": "string",
                    "enum": ["P1", "P2", "P3", "P4"],
                    "description": "Final priority based on impact and urgency matrix"
                }
            },
            "required": ["impact", "urgency", "priority"],
            "description": priority_description
        }