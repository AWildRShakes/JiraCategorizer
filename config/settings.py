# config/settings.py
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    INPUT_FILE = os.getenv("INPUT_FILE", "JiraTicketExportTesting.xlsx")
    OUTPUT_FILE = os.getenv("OUTPUT_FILE", "output_JiraTicketExportTesting.xlsx")
    CHECKPOINT_DIR = os.getenv("CHECKPOINT_DIR", "checkpoints")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    MODEL_VERSION = os.getenv("MODEL_VERSION", "gpt-4o-mini")
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    # Addition to Config class
    PARALLEL_REQUESTS = int(os.getenv("PARALLEL_REQUESTS", "4"))  # Number of concurrent requests
    PARALLEL_BATCH_SIZE = int(os.getenv("PARALLEL_BATCH_SIZE", "8"))  # Size of batches to process in parallel
    
    # Add base directory configuration
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"
    LOG_DIR = DATA_DIR / "logs"
    OUTPUT_DIR = DATA_DIR / "output"
    
    @classmethod
    def setup_directories(cls):
        """Ensure all necessary directories exist"""
        for directory in [cls.DATA_DIR, cls.LOG_DIR, Path(cls.CHECKPOINT_DIR)]:
            directory.mkdir(parents=True, exist_ok=True)