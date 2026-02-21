import os
import structlog
from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging import correlation_paths

# Configure structured logging
def configure_logger() -> Logger:
    """Configure and return a structured logger with AWS Lambda Powertools."""
    
    # Get log level from environment variable
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    # Create logger with Powertools
    logger = Logger(
        service="real-estate-observability",
        level=log_level,
        sample_rate=1.0,  # Do not drop logs by sampling
        log_uncaught_exceptions=True,
    )
    
    return logger

# Global logger instance
logger = configure_logger()

def get_logger() -> Logger:
    """Get the configured logger instance."""
    return logger
