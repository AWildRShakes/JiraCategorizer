# core/processor.py
import logging
import pandas as pd
from typing import Optional, Tuple
from tqdm import tqdm
from config.settings import Config
from models import ProcessingState
from .classifier import TicketClassifier

class TicketProcessor:
    """Handles the processing of all tickets in the dataset"""
    
    def __init__(self):
        self.classifier = TicketClassifier()
        
    def process_tickets(self, state: Optional[ProcessingState] = None) -> None:
        """
        Process all tickets with checkpointing and progress tracking
        
        Args:
            state: Optional ProcessingState object for resuming from checkpoint
        """
        try:
            # Initialize or load state and data
            df, state = self._initialize_processing(state)
            total_tickets = len(df)
            start_index = state.last_processed_index + 1
            
            # Ensure the new columns exist
            if 'New_Service_Category' not in df.columns:
                df['New_Service_Category'] = None
            if 'New_Service_Request_Type' not in df.columns:
                df['New_Service_Request_Type'] = None
            if 'Priority' not in df.columns:
                df['Priority'] = None
            
            # Main processing loop with progress bar
            with tqdm(total=total_tickets, initial=start_index) as pbar:
                for i in range(start_index, total_tickets):
                    try:
                        self._process_single_ticket(df, i, state)
                        self._handle_checkpoint(df, i, state, total_tickets)
                    except Exception as e:
                        self._handle_error(e, i, state)
                    finally:
                        pbar.update(1)
            
            # Save final results
            self._save_results(df, state)
            
        except Exception as e:
            logging.critical(f"Critical error in process_tickets: {str(e)}")
            raise

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

    def _process_single_ticket(self, df: pd.DataFrame, index: int, state: ProcessingState) -> None:
        """Process a single ticket"""
        row = df.iloc[index]
        new_category, new_request_type, priority_level = self.classifier.classify_ticket(
            row['Ticket_Title'],
            row['Ticket_Summary']
        )
        
        # Use loc to safely set values for the current row
        df.loc[index, 'New_Service_Category'] = new_category
        df.loc[index, 'New_Service_Request_Type'] = new_request_type
        df.loc[index, 'Priority'] = priority_level
        state.processed_count += 1

    def _handle_checkpoint(self, df: pd.DataFrame, index: int, state: ProcessingState, total_tickets: int) -> None:
        """Handle checkpoint creation and progress logging"""
        if index % Config.BATCH_SIZE == 0:
            state.save_checkpoint(index, df)
            stats = state.get_progress_stats(total_tickets)
            logging.info(state.format_progress_message(stats))

    def _handle_error(self, error: Exception, index: int, state: ProcessingState) -> None:
        """Handle processing errors"""
        state.error_count += 1
        logging.error(f"Failed to process ticket {index}: {str(error)}")

    def _save_results(self, df: pd.DataFrame, state: ProcessingState) -> None:
        """Save final results and log statistics"""
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