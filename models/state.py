# models/state.py
import time
import pickle
import logging
from pathlib import Path
import pandas as pd
from datetime import datetime
from config.settings import Config

class ProcessingState:
    """Handles the state management and checkpointing of the processing job"""
    
    def __init__(self):
        self.processed_count = 0
        self.error_count = 0
        self.start_time = time.time()
        self.last_processed_index = -1
        self.checkpoint_file = None
        self._ensure_checkpoint_dir()

    def _ensure_checkpoint_dir(self):
        """Ensure checkpoint directory exists"""
        Path(Config.CHECKPOINT_DIR).mkdir(parents=True, exist_ok=True)

    def save_checkpoint(self, index: int, df: pd.DataFrame) -> None:
        """
        Save current processing state and dataframe to checkpoint file
        
        Args:
            index: Current processing index
            df: Current state of the dataframe
        """
        try:
            self.checkpoint_file = Path(Config.CHECKPOINT_DIR) / f"checkpoint_{int(time.time())}.pkl"
            
            checkpoint_data = {
                'last_index': index,
                'processed_count': self.processed_count,
                'error_count': self.error_count,
                'start_time': self.start_time,
                'dataframe': df,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self.checkpoint_file, 'wb') as f:
                pickle.dump(checkpoint_data, f)
            
            logging.info(f"Checkpoint saved: {self.checkpoint_file}")
            
            # Clean up old checkpoints
            self._cleanup_old_checkpoints()
            
        except Exception as e:
            logging.error(f"Failed to save checkpoint: {str(e)}")
            raise

    def _cleanup_old_checkpoints(self, keep_last: int = 5) -> None:
        """
        Remove old checkpoints, keeping only the most recent ones
        
        Args:
            keep_last: Number of most recent checkpoints to keep
        """
        try:
            checkpoints = sorted(
                Path(Config.CHECKPOINT_DIR).glob("checkpoint_*.pkl"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # Remove old checkpoints
            for checkpoint in checkpoints[keep_last:]:
                checkpoint.unlink()
                logging.debug(f"Removed old checkpoint: {checkpoint}")
                
        except Exception as e:
            logging.warning(f"Failed to cleanup old checkpoints: {str(e)}")

    @classmethod
    def load_latest_checkpoint(cls):
        """
        Load the most recent checkpoint if available
        
        Returns:
            dict: Checkpoint data if found, None otherwise
        """
        try:
            checkpoint_dir = Path(Config.CHECKPOINT_DIR)
            if not checkpoint_dir.exists():
                return None
            
            checkpoints = list(checkpoint_dir.glob("checkpoint_*.pkl"))
            if not checkpoints:
                return None
            
            latest_checkpoint = max(checkpoints, key=lambda x: x.stat().st_mtime)
            
            with open(latest_checkpoint, 'rb') as f:
                checkpoint_data = pickle.load(f)
                
            logging.info(f"Loaded checkpoint from: {latest_checkpoint}")
            return checkpoint_data
            
        except Exception as e:
            logging.error(f"Failed to load checkpoint: {str(e)}")
            return None

    def get_progress_stats(self, total_tickets: int) -> dict:
        """
        Calculate and return current progress statistics
        
        Args:
            total_tickets: Total number of tickets to process
            
        Returns:
            dict: Dictionary containing progress statistics
        """
        elapsed_time = time.time() - self.start_time
        rate = self.processed_count / elapsed_time if elapsed_time > 0 else 0
        remaining = (total_tickets - self.last_processed_index - 1) / rate if rate > 0 else 0
        success_rate = ((self.processed_count - self.error_count) / self.processed_count * 100) if self.processed_count > 0 else 0
        
        return {
            'processed_count': self.processed_count,
            'error_count': self.error_count,
            'elapsed_time': elapsed_time,
            'processing_rate': rate,
            'estimated_remaining_time': remaining,
            'success_rate': success_rate,
            'current_index': self.last_processed_index + 1,
            'total_tickets': total_tickets
        }

    def format_progress_message(self, stats: dict) -> str:
        """
        Format progress statistics into a human-readable message
        
        Args:
            stats: Dictionary of progress statistics
            
        Returns:
            str: Formatted progress message
        """
        return (
            f"Progress: {stats['current_index']}/{stats['total_tickets']} tickets | "
            f"Rate: {stats['processing_rate']:.2f} tickets/sec | "
            f"Est. remaining time: {stats['estimated_remaining_time']/60:.2f} minutes | "
            f"Success rate: {stats['success_rate']:.2f}%"
        )
        
    def save_current_results(self) -> bool:
        """
        Save current results to Excel file, whether processing is running or not
        
        Returns:
            bool: True if save was successful, False otherwise
        """
        try:
            # First try to get latest checkpoint data
            checkpoint_data = self.load_latest_checkpoint()
            
            if checkpoint_data:
                df = checkpoint_data['dataframe']
                source = "checkpoint"
            else:
                # If no checkpoint, try to load original input file
                input_file = Path(Config.INPUT_FILE)
                if not input_file.exists():
                    logging.error("No checkpoint found and input file does not exist")
                    return False
                    
                df = pd.read_excel(Config.INPUT_FILE)
                source = "input"
            
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path(Config.OUTPUT_DIR) / f"results_{timestamp}.xlsx"
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save DataFrame to Excel
            df.to_excel(output_path, index=False)
            
            logging.info(f"Results saved to: {output_path} (source: {source})")
            return True
            
        except Exception as e:
            logging.error(f"Failed to save results: {str(e)}")
            return False