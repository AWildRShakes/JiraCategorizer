# Jira Ticket Auto-Categorization Tool

## Overview
This tool automatically categorizes Jira tickets using OpenAI's GPT models. It analyzes ticket titles and summaries to determine appropriate service categories, request types, and priorities based on predefined criteria. The tool includes features like checkpointing, detailed logging, and comprehensive statistical reporting.

## Features
- Automated ticket classification using OpenAI's GPT models
- Service category and request type determination
- Priority classification based on impact and urgency
- Checkpoint system for resuming interrupted processes
- On-demand results generation
- Detailed logging and error handling
- Statistical reporting and analysis
- Command-line interface for easy operation

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd [repository-name]
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and configure your settings:
```bash
cp .env.example .env
```

4. Configure your environment variables in the `.env` file:
```plaintext
OPENAI_API_KEY=your_api_key_here
BATCH_SIZE=100
MAX_RETRIES=3
INPUT_FILE=JiraTicketExportTesting.xlsx
OUTPUT_FILE=output_JiraTicketExportTesting.xlsx
CHECKPOINT_DIR=data/checkpoints
LOG_LEVEL=INFO
MODEL_VERSION=gpt-4o-mini
REQUEST_TIMEOUT=30
```

## Usage

Basic commands:
```bash
# Process tickets
python main.py process

# Force start from beginning
python main.py process --force

# Change batch size
python main.py process --batch-size 50

# Generate current results file
python main.py save

# Clean up old files
python main.py cleanup

# Show version
python main.py version
```

### Generating Results
The `save` command can be used to generate Excel files with current results at any time:
- Can be run while processing is active or after completion
- Uses most recent checkpoint data if available
- Falls back to input file if no checkpoints exist
- Generates timestamped output files
- Safe to use during active processing

## Project Structure

### Configuration
- `config/settings.py`: Manages environment variables and configuration settings

### Utilities
- `utils/logging_setup.py`: Configures logging system with file and console handlers
- `utils/retry_decorator.py`: Implements retry mechanism for API calls

### Services
- `services/openai_client.py`: Handles OpenAI API interactions for ticket classification
- `services/schema_generator.py`: Generates JSON schemas for classification requests

### Core Logic
- `core/classifier.py`: Implements ticket classification logic
- `core/processor.py`: Manages main processing workflow

### Models
- `models/state.py`: Manages processing state and checkpointing

### Data Directory
- `data/checkpoints/`: Stores processing checkpoints
- `data/logs/`: Contains application logs
- `data/service_categories_and_types.json`: Defines service categories and request types

### Root Files
- `main.py`: Entry point with CLI interface
- `requirements.txt`: Lists project dependencies
- `.env.example`: Example environment configuration file

## Output Files
The tool generates several types of output files:
1. Main classification results (`output_JiraTicketExportTesting.xlsx`)
2. Statistical analysis report (`output_JiraTicketExportTesting_statistics.xlsx`)
3. On-demand results files (`results_YYYYMMDD_HHMMSS.xlsx`)

## Statistical Reports
The statistical analysis includes:
- Overall processing statistics
- Priority distribution
- Impact and urgency distributions
- Category-Priority correlation analysis
- Processing success rates

## Error Handling
- Automatic retries for API calls
- Detailed error logging
- Checkpoint system for process recovery
- Comprehensive error reporting in logs

## Development
To contribute to the project:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## Requirements
- Python 3.8+
- OpenAI API key
- Required Python packages (see requirements.txt)