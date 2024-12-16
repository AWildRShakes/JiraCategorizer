# core/async_processor.py
import asyncio
import logging
import pandas as pd
from typing import Optional, List, Tuple
from tqdm.asyncio import tqdm
from config.settings import Config
from models import ProcessingState
from .async_classifier import AsyncTicketClassifier

class AsyncTicketProcessor:
    """Handles the parallel processing of tickets with async operations"""
    
    def __init__(self):
        self.classifier = AsyncTicketClassifier()
        self._processing_semaphore = asyncio.Semaphore(Config.PARALLEL_REQUESTS)
        self._last_checkpoint_count = 0  # Track tickets processed since last checkpoint
        
    async def process_tickets(self, state: Optional[ProcessingState] = None) -> None:
        """
        Process all tickets with parallel processing, checkpointing, and progress tracking
        
        Args:
            state: Optional ProcessingState object for resuming from checkpoint
        """
        try:
            # Initialize or load state and data
            df, state = self._initialize_processing(state)
            total_tickets = len(df)
            start_index = state.last_processed_index + 1
            
            # Ensure the new columns exist
            for col in ['New_Service_Category', 'New_Service_Request_Type', 'Priority']:
                if col not in df.columns:
                    df[col] = None
            
            # Process tickets in batches
            with tqdm(total=total_tickets, initial=start_index) as pbar:
                while start_index < total_tickets:
                    # Determine batch size
                    end_index = min(start_index + Config.PARALLEL_BATCH_SIZE, total_tickets)
                    batch_indices = range(start_index, end_index)
                    
                    # Process batch
                    try:
                        await self._process_batch(df, batch_indices, state, pbar)
                    except Exception as e:
                        logging.error(f"Error processing batch {start_index}-{end_index}: {str(e)}")
                        # Continue with next batch despite errors
                    
                    # Check if we need to create a checkpoint based on processed tickets
                    tickets_since_checkpoint = state.processed_count - self._last_checkpoint_count
                    if tickets_since_checkpoint >= Config.BATCH_SIZE:
                        self._handle_checkpoint(df, state.last_processed_index, state, total_tickets)
                        self._last_checkpoint_count = state.processed_count
                    
                    start_index = end_index
            
            # Save final results
            self._save_results(df, state)
            
        except Exception as e:
            logging.critical(f"Critical error in process_tickets: {str(e)}")
            raise
        
    async def _process_batch(self, df: pd.DataFrame, batch_indices: range, 
                           state: ProcessingState, pbar: tqdm) -> None:
        """Process a batch of tickets concurrently"""
        # Prepare batch data
        batch_tickets = [
            (df.iloc[i]['Ticket_Title'], df.iloc[i]['Ticket_Summary'])
            for i in batch_indices
        ]
        
        # Create tasks for parallel processing
        tasks = []
        for i, (title, summary) in zip(batch_indices, batch_tickets):
            task = self._process_single_ticket_task(df, i, title, summary, state, pbar)
            tasks.append(task)
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
    
    async def _process_single_ticket_task(self, df: pd.DataFrame, index: int, 
                                        title: str, summary: str, 
                                        state: ProcessingState, pbar: tqdm) -> None:
        """Process a single ticket with semaphore control"""
        async with self._processing_semaphore:
            try:
                # Get classifications
                category, request_type, priority = await self.classifier.classify_ticket(title, summary)
                
                # Update DataFrame - need to handle this carefully due to parallel access
                self._update_dataframe(df, index, category, request_type, priority)
                
                # Update state
                state.processed_count += 1
                state.last_processed_index = max(state.last_processed_index, index)
                
            except Exception as e:
                logging.error(f"Error processing ticket {index} '{title}': {str(e)}")
                state.error_count += 1
            finally:
                # Update progress bar
                pbar.update(1)
    
    def _update_dataframe(self, df: pd.DataFrame, index: int, 
                         category: Optional[str], request_type: Optional[str], 
                         priority: Optional[str]) -> None:
        """Thread-safe DataFrame update"""
        # Use loc for thread-safe access
        with pd.option_context('mode.chained_assignment', None):
            df.loc[index, 'New_Service_Category'] = category
            df.loc[index, 'New_Service_Request_Type'] = request_type
            df.loc[index, 'Priority'] = priority
    
    def _initialize_processing(self, state: Optional[ProcessingState]) -> Tuple[pd.DataFrame, ProcessingState]:
        """Initialize processing state and load data"""
        if state and state.checkpoint_file:
            checkpoint_data = ProcessingState.load_latest_checkpoint()
            if checkpoint_data:
                return self._load_from_checkpoint(checkpoint_data)
        
        return pd.read_excel(Config.INPUT_FILE), ProcessingState()

    def _load_from_checkpoint(self, checkpoint_data: dict) -> Tuple[pd.DataFrame, ProcessingState]:
        """Load processing state from checkpoint"""
        state = ProcessingState()
        state.last_processed_index = checkpoint_data['last_index']
        state.processed_count = checkpoint_data['processed_count']
        state.error_count = checkpoint_data['error_count']
        state.start_time = checkpoint_data['start_time']
        
        logging.info(f"Resuming from checkpoint. Last processed index: {state.last_processed_index}")
        return checkpoint_data['dataframe'], state

    def _handle_checkpoint(self, df: pd.DataFrame, index: int, state: ProcessingState, total_tickets: int) -> None:
        """Handle checkpoint creation and progress logging"""
        try:
            state.save_checkpoint(index, df)
            stats = state.get_progress_stats(total_tickets)
            logging.info(state.format_progress_message(stats))
        except Exception as e:
            logging.error(f"Error saving checkpoint at index {index}: {str(e)}")

    def _save_results(self, df: pd.DataFrame, state: ProcessingState) -> None:
        """Save final results and log statistics"""
        try:
            df.to_excel(Config.OUTPUT_FILE, index=False)
            stats = state.get_progress_stats(len(df))
            
            logging.info(f"""
            Processing completed:
            Total tickets processed: {stats['processed_count']}
            Successful: {stats['processed_count'] - stats['error_count']}
            Errors: {stats['error_count']}
            Total time: {stats['elapsed_time']/60:.2f} minutes
            Average rate: {stats['processing_rate']:.2f} tickets/sec
            Success rate: {stats['success_rate']:.2f}%
            """)
        except Exception as e:
            logging.error(f"Error saving final results: {str(e)}")
            raise