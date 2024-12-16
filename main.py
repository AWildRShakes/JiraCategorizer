# main.py
import sys
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional
import click
from config.settings import Config
from utils import setup_logging
from models import ProcessingState
from core import AsyncTicketProcessor

def initialize_environment() -> None:
    """Initialize the application environment"""
    try:
        # Setup required directories
        Config.setup_directories()
        
        # Configure logging
        setup_logging()
        
        logging.info("Environment initialized successfully")
        logging.info(f"Parallel processing configured for {Config.PARALLEL_REQUESTS} concurrent tickets")
        logging.info(f"Using batch size of {Config.PARALLEL_BATCH_SIZE} for parallel processing")
    except Exception as e:
        print(f"Failed to initialize environment: {str(e)}")
        sys.exit(1)

def check_prerequisites() -> None:
    """Check all prerequisites before starting processing"""
    try:
        # Check if input file exists
        input_file = Path(Config.INPUT_FILE)
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        # Check if service categories file exists
        categories_file = Config.DATA_DIR / 'service_categories_and_types.json'
        if not categories_file.exists():
            raise FileNotFoundError(f"Service categories file not found: {categories_file}")
        
        # Check API key
        if not Config.OPENAI_API_KEY:
            raise ValueError("OpenAI API key not found in environment variables")
            
        logging.info("All prerequisites checked successfully")
    except Exception as e:
        logging.critical(f"Prerequisites check failed: {str(e)}")
        raise

def handle_checkpoint() -> Optional[ProcessingState]:
    """Handle checkpoint loading based on user input"""
    latest_checkpoint = ProcessingState.load_latest_checkpoint()
    if latest_checkpoint:
        if click.confirm("Found existing checkpoint. Resume from checkpoint?", default=True):
            state = ProcessingState()
            state.checkpoint_file = latest_checkpoint
            return state
    return None

class AsyncClickGroup(click.Group):
    """Custom Click Group that handles async command execution"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._async_commands = set()

    def command(self, *args, **kwargs):
        is_async = kwargs.pop('is_async', False)
        decorator = super().command(*args, **kwargs)
        if is_async:
            def wrapper(f):
                cmd = decorator(f)
                self._async_commands.add(cmd.name)
                return cmd
            return wrapper
        return decorator

    def invoke(self, ctx):
        cmd_name = ctx.protected_args[0] if ctx.protected_args else None
        if cmd_name in self._async_commands:
            cmd = self.get_command(ctx, cmd_name)
            if cmd is None:
                return super().invoke(ctx)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Set up signal handlers
                for sig in (signal.SIGINT, signal.SIGTERM):
                    try:
                        loop.add_signal_handler(
                            sig,
                            lambda s=sig: asyncio.create_task(handle_shutdown(loop))
                        )
                    except NotImplementedError:
                        # Windows doesn't support add_signal_handler
                        pass

                return loop.run_until_complete(super().invoke(ctx))
            except KeyboardInterrupt:
                logging.warning("\nInterrupt received - initiating shutdown...")
                loop.run_until_complete(handle_shutdown(loop))
            finally:
                try:
                    loop.close()
                except Exception as e:
                    logging.error(f"Error closing event loop: {str(e)}")

async def handle_shutdown(loop):
    """Handle graceful shutdown on SIGINT/SIGTERM"""
    try:
        logging.warning("\nShutdown signal received. Cleaning up...")
        
        # Cancel all running tasks
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        
        # Send cancellation to all tasks
        for task in tasks:
            task.cancel()
        
        logging.info(f"Cancelling {len(tasks)} outstanding tasks...")
        
        # Wait briefly for tasks to acknowledge cancellation
        await asyncio.wait(tasks, timeout=2.0)
        
        # Force stop any remaining tasks
        remaining = [t for t in tasks if not t.done()]
        if remaining:
            logging.warning(f"{len(remaining)} tasks did not terminate cleanly")
            
    except Exception as e:
        logging.error(f"Error during shutdown: {str(e)}")
    finally:
        # Force stop the event loop
        loop.stop()
        logging.info("Shutdown complete")
        
        # Force exit if we're really stuck
        import os
        os._exit(1)

@click.group(cls=AsyncClickGroup)
def cli():
    """Jira Ticket Categorization Tool"""
    pass

@cli.command(is_async=True)
@click.option('--force', is_flag=True, help='Force start from beginning, ignore checkpoints')
@click.option('--batch-size', type=int, help='Override default batch size')
@click.option('--parallel-requests', type=int, help='Override number of parallel requests')
async def process(force: bool, batch_size: Optional[int], parallel_requests: Optional[int]):
    """Process Jira tickets and categorize them"""
    try:
        # Initialize environment
        initialize_environment()
        
        # Update configuration if options provided
        if batch_size:
            Config.PARALLEL_BATCH_SIZE = batch_size
            logging.info(f"Batch size overridden to: {batch_size}")
        
        if parallel_requests:
            Config.PARALLEL_REQUESTS = parallel_requests
            logging.info(f"Parallel requests overridden to: {parallel_requests}")
        
        # Check prerequisites
        check_prerequisites()
        
        # Handle checkpoint
        state = None if force else handle_checkpoint()
        
        # Initialize processor and start processing
        processor = AsyncTicketProcessor()
        await processor.process_tickets(state)
        
        logging.info("Processing completed successfully")
        
    except KeyboardInterrupt:
        logging.warning("Process interrupted by user. Progress has been saved in the latest checkpoint.")
        sys.exit(1)
    except Exception as e:
        logging.critical(f"Critical error in main process: {str(e)}")
        sys.exit(1)

@cli.command()
def cleanup():
    """Clean up old checkpoints and log files"""
    try:
        # Clean up old checkpoints
        checkpoint_dir = Path(Config.CHECKPOINT_DIR)
        if checkpoint_dir.exists():
            checkpoints = list(checkpoint_dir.glob("checkpoint_*.pkl"))
            if click.confirm(f"Found {len(checkpoints)} checkpoints. Delete all?", default=False):
                for checkpoint in checkpoints:
                    checkpoint.unlink()
                click.echo("All checkpoints deleted.")
        
        # Clean up old log files
        log_dir = Path(Config.LOG_DIR)
        if log_dir.exists():
            log_files = list(log_dir.glob("*.log"))
            if click.confirm(f"Found {len(log_files)} log files. Delete all?", default=False):
                for log_file in log_files:
                    log_file.unlink()
                click.echo("All log files deleted.")
                
    except Exception as e:
        logging.error(f"Error during cleanup: {str(e)}")
        sys.exit(1)
        
@cli.command(is_async=True)  # Mark as async
async def save():  # Make function async
    """Generate Excel file with current results"""
    print("Save command started")  # Debug print at very start
    try:
        # Initialize environment for logging
        initialize_environment()
        
        # Create ProcessingState instance
        state = ProcessingState()
        
        if state.save_current_results():
            click.echo("Results file generated successfully. Check the output directory.")
        else:
            click.echo("Could not generate results. No checkpoint or input file found.")
            
    except Exception as e:
        logging.error(f"Error generating results: {str(e)}")
        click.echo(f"Failed to generate results: {str(e)}")
        sys.exit(1)

@cli.command()
def version():
    """Display version information"""
    click.echo("Jira Ticket Categorization Tool v1.0.0")
    click.echo(f"Using OpenAI Model: {Config.MODEL_VERSION}")
    click.echo(f"Parallel Processing: {Config.PARALLEL_REQUESTS} concurrent tickets")

if __name__ == "__main__":
    # Import signal here to avoid issues on Windows
    import signal
    cli()