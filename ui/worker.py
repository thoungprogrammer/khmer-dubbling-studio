"""
Worker Thread - Runs the dubbing pipeline in a background thread
so the UI stays responsive during processing.
"""
from PyQt6.QtCore import QThread, pyqtSignal
from core.pipeline import DubbingPipeline, PipelineConfig


class DubbingWorker(QThread):
    """Background worker that runs the full dubbing pipeline."""
    
    progress = pyqtSignal(str)       # Progress message
    finished = pyqtSignal(dict)      # Output paths on success
    error = pyqtSignal(str)          # Error message on failure
    segments_ready = pyqtSignal(list) # Emitted after transcription + translation
    
    def __init__(self, config: PipelineConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.pipeline = None
    
    def run(self):
        """Execute the pipeline in this thread."""
        try:
            self.pipeline = DubbingPipeline(
                config=self.config,
                progress_callback=self._on_progress
            )
            
            result = self.pipeline.run()
            
            # Emit segments for subtitle editor
            if self.pipeline.segments:
                self.segments_ready.emit(self.pipeline.segments)
            
            self.finished.emit(result)
        
        except InterruptedError:
            self.error.emit("Processing was cancelled.")
        except Exception as e:
            import traceback
            self.error.emit(f"{str(e)}\n\n{traceback.format_exc()}")
    
    def _on_progress(self, message: str):
        self.progress.emit(message)
    
    def cancel(self):
        """Request cancellation of the pipeline."""
        if self.pipeline:
            self.pipeline.cancel()
