# Jira Auto-Categorization Project Documentation

## Project Overview

The JiraCategorizer project is a sophisticated tool designed to streamline the classification and processing of Jira tickets using advanced AI models. It employs OpenAI's GPT models for automated categorization, combining robust error handling, state management, and detailed logging.

## CLI Commands

### Command: process
Processes Jira tickets and categorizes them.

#### Options:
- `--force`: Force start from beginning, ignore checkpoints
- `--batch-size`: Override default batch size
- `--parallel-requests`: Override number of parallel requests

### Command: save
Generates an Excel file with current processing results.
- Can be run while processing is active or after completion
- Uses latest checkpoint data if available
- Falls back to input file if no checkpoints exist
- Generates timestamped output files
- Preserves all data and formatting

### Command: cleanup
Clean up old checkpoints and log files.

### Command: version
Display version information.

## Project Structure

### Core Components
- **main.py**: CLI interface and application entry point with async support
- **config/settings.py**: Environment-based configuration management
- **core/classifier.py**: OpenAI-based ticket classification logic
- **core/async_classifier.py**: Asynchronous ticket classification implementation
- **core/processor.py**: Batch processing implementation
- **core/async_processor.py**: Parallel processing implementation with async support

### Models
- **models/state.py**: Processing state and checkpoint management

### Services
- **services/openai_client.py**: OpenAI API interaction layer
- **services/async_openai_client.py**: Asynchronous OpenAI API interaction layer
- **services/schema_generator.py**: JSON schema generation for API requests

### Utilities
- **utils/logging_setup.py**: Application-wide logging configuration
- **utils/retry_decorator.py**: API retry logic implementation

## Detailed Component Documentation

### File: models/state.py
Manages processing state and checkpoint functionality.

#### Class: ProcessingState
Handles state management and checkpointing of the processing job.

##### Attributes:
- `processed_count`: Number of processed tickets
- `error_count`: Number of processing errors
- `start_time`: Processing start timestamp
- `last_processed_index`: Index of last processed ticket
- `checkpoint_file`: Current checkpoint file path
- `save_current_results() -> bool`: Saves current results to Excel file
  - Attempts to use latest checkpoint data first
  - Falls back to input file if no checkpoint exists
  - Generates timestamped output files
  - Returns success/failure status
  - Thread-safe for concurrent access

##### Methods:
- `_ensure_checkpoint_dir()`: Creates checkpoint directory if needed
- `save_checkpoint(index: int, df: pd.DataFrame)`: Saves current state and data
- `_cleanup_old_checkpoints(keep_last: int = 5)`: Maintains recent checkpoints
- `load_latest_checkpoint()`: Retrieves most recent checkpoint data
- `get_progress_stats(total_tickets: int)`: Calculates processing statistics
- `format_progress_message(stats: dict)`: Formats progress for display

## File: main.py
Main entry point for the application with CLI interface.

### Functions:
- `initialize_environment()`: Sets up required directories and configures logging system
- `check_prerequisites()`: Validates presence of required files and API key before processing
- `handle_checkpoint()`: Manages checkpoint loading with user confirmation
- `cli()`: Main Click command group for CLI interface
- `process(force: bool, batch_size: Optional[int])`: Processes Jira tickets with optional force restart and batch size
- `cleanup()`: Removes old checkpoints and log files
- `version()`: Displays version information and model details

## File: config/settings.py
Configuration management using environment variables.

### Class: Config
Static configuration class managing all application settings.

#### Class Attributes:
- Various environment variables (API_KEY, BATCH_SIZE, etc.)
- Directory path configurations
- `PARALLEL_REQUESTS`: Number of concurrent ticket classifications (default: 4)
- `PARALLEL_BATCH_SIZE`: Size of batches for parallel processing (default: 8)

#### Methods:
- `setup_directories()`: Creates necessary directory structure for the application

## File: core/classifier.py
Handles ticket classification logic using OpenAI API.

### Class: TicketClassifier
Manages the classification of individual tickets.

#### Methods:
- `classify_ticket(title: str, summary: str)`: Main classification method returning category, request type, and priority
- `_get_category(title: str, summary: str)`: Internal method for category classification
- `_get_request_type(title: str, summary: str, category: str)`: Internal method for request type classification

## File: core/async_classifier.py
Handles asynchronous ticket classification using OpenAI API.

### Class: AsyncTicketClassifier
Manages the parallel classification of tickets.

#### Methods:
- `classify_ticket(title: str, summary: str)`: Asynchronous classification method returning category, request type, and priority
- `classify_tickets_batch(tickets: list)`: Processes multiple tickets concurrently
- Schema caching for improved performance

## File: core/processor.py
Manages the batch processing of tickets.

### Class: TicketProcessor
Handles bulk ticket processing with checkpointing.

#### Methods:
- `process_tickets(state: Optional[ProcessingState])`: Main processing loop for all tickets
- `_initialize_processing(state: Optional[ProcessingState])`: Sets up initial processing state
- `_load_from_checkpoint(checkpoint_data: dict)`: Restores processing state from checkpoint
- `_process_single_ticket(df: pd.DataFrame, index: int, state: ProcessingState)`: Processes individual ticket
- `_handle_checkpoint(df: pd.DataFrame, index: int, state: ProcessingState, total_tickets: int)`: Manages checkpoint creation
- `_handle_error(error: Exception, index: int, state: ProcessingState)`: Error handling for processing failures
- `_save_results(df: pd.DataFrame, state: ProcessingState)`: Saves final results and statistics

## File: core/async_processor.py
Manages parallel processing of tickets with async support.

### Class: AsyncTicketProcessor
Handles concurrent ticket processing with checkpointing.

#### Methods:
- `process_tickets(state: Optional[ProcessingState])`: Main processing loop with parallel execution
- `_process_batch(df: pd.DataFrame, batch_indices: range)`: Processes a batch of tickets concurrently
- `_process_single_ticket_task(df: pd.DataFrame, index: int)`: Processes individual ticket with semaphore control
- Maintains all existing checkpoint and error handling functionality

## File: services/openai_client.py
Handles all interactions with the OpenAI API.

### Class: OpenAIService
Manages OpenAI API calls with retry logic and error handling.

#### Methods:
- `get_category_classification(title, summary, schema)`: Classifies ticket into service category
- `get_request_type_classification(title, summary, category, schema)`: Determines request type within category
- `get_priority_classification(title, summary, schema)`: Assesses ticket priority based on impact and urgency

## File: services/async_openai_client.py
Handles asynchronous interactions with the OpenAI API.

### Class: AsyncOpenAIService
Manages concurrent OpenAI API calls with retry logic and rate limiting.

#### Methods:
- `get_category_classification(title, summary, schema)`: Async category classification
- `get_request_type_classification(title, summary, category, schema)`: Async request type classification
- `get_priority_classification(title, summary, schema)`: Async priority assessment
- `classify_ticket_complete(title, summary, schemas)`: Complete ticket classification as atomic operation

## File: services/schema_generator.py
Generates JSON schemas for OpenAI API requests.

### Class: SchemaGenerator
Manages creation of classification schemas.

#### Methods:
- `_load_service_structure()`: Loads service categories and types from JSON configuration
- `create_category_schema()`: Generates schema for category classification
- `create_request_type_schema(category)`: Creates schema for request type classification
- `create_priority_schema()`: Builds schema for priority assessment

## File: utils/logging_setup.py
Configures application-wide logging.

### Functions:
- `setup_logging()`: Configures logging with:
  - File-based logging for all levels
  - Separate error log file
  - Console output
  - Custom formatting
  - Quieting of third-party loggers

## File: utils/retry_decorator.py
Implements retry logic for API calls.

### Functions:
- `create_retry_decorator(operation_name)`: Creates a customized retry decorator with:
  - Exponential backoff
  - Maximum retry attempts
  - Custom logging for retry attempts
  - Success logging
  - Exception handling

## Key Features Implementation

### Parallel Processing
- Concurrent ticket processing with configurable parallelism
- Rate limit awareness across parallel requests
- Semaphore-based request limiting
- Atomic ticket classification operations
- Efficient batch processing
- Safe DataFrame updates in parallel context
- Progress tracking for parallel operations

### State Management and Checkpointing
- Automatic state persistence through checkpoints
- Progress tracking with detailed statistics
- Checkpoint cleanup management
- Recovery from interruptions
- Progress reporting with estimated completion times

### API Integration
- Robust OpenAI API integration with retry logic
- JSON schema-based request formatting
- Comprehensive error handling
- Custom timeout configuration

### Schema Management
- Dynamic schema generation based on service structure
- Support for multiple classification dimensions
- Detailed descriptions for AI model context
- JSON validation enforcement

### Logging System
- Multi-level logging (INFO, DEBUG, ERROR)
- Separate error logging
- Timestamp-based log files
- Console and file output
- Third-party logger management

### Retry Mechanism
- Exponential backoff strategy
- Configurable maximum attempts
- Detailed retry logging
- Success tracking
- Exception-based retry decisions

## Processing Statistics
The system tracks and reports various metrics:
- Processed ticket count
- Error rate and count
- Processing speed (tickets/second)
- Estimated remaining time
- Success rate percentage
- Progress tracking (current/total tickets)
- Elapsed processing time

### Results Generation
- On-demand Excel file generation
- Timestamp-based file naming
- Checkpoint-aware data sourcing
- Thread-safe file operations
- Progress preservation
- Async command support
- Real-time access to current results

## Important Dependencies
- OpenAI API for classification
- pandas for data handling
- Click for CLI interface
- tqdm for progress tracking
- tenacity for retry logic
- logging for error and progress tracking

## Project Features
- **Automated Classification**: Uses AI to categorize tickets based on title and summary
- **Checkpoint System**: Enables recovery from interruptions and process resumption
- **Progress Monitoring**: Real-time statistics and progress tracking
- **Error Recovery**: Comprehensive error handling and retry mechanisms
- **Scalability**: Designed for processing large datasets through batching
- **Extensibility**: Modular design for easy feature additions
- **Robust Logging**: Detailed logging system for monitoring and debugging
- **Parallel Processing**: Concurrent ticket classification with configurable parallel requests
- **Rate Limit Management**: Smart handling of API rate limits across parallel requests
- **Atomic Operations**: Complete ticket classification handled as single unit
- **Async Support**: Full async implementation for improved performance

## Notes
- **Data Handling**: Efficiently processes large datasets through batching
- **Error Recovery**: Multiple layers of error handling and recovery mechanisms
- **Modularity**: Easy to extend and customize classification logic
- **Multi-dimensional Classification**: Supports category, request type, and priority classification
- **Monitoring**: Comprehensive logging and progress tracking
- **State Management**: Robust checkpoint and recovery system
- **Performance Optimization**: Configurable batch sizes and timeout settings
- **Parallel Processing**: Efficient concurrent processing with rate limit awareness
- **Thread Safety**: Robust handling of parallel DataFrame updates and state management
- **Configurable Parallelism**: Adjustable parallel requests and batch sizes
- **Atomic Operations**: Complete ticket classification (category, type, priority) handled as single unit

The system is designed to be both robust and maintainable, with careful attention to error handling, state management, and processing efficiency. The modular architecture allows for easy extensions and modifications to meet specific needs.