# Logging Configuration Guide

## Overview

The logging system is configured to handle multiple log outputs with different levels and formats across your healthcare assistant prototype.

## Files Created

1. **`src/logger.py`** - Main logging configuration module
2. **`config/logging.json`** - JSON configuration file (optional, for external config)

## Features

- **Console Output**: Real-time INFO level logs to stdout
- **File Logging**: Full DEBUG level logs with rotation (10MB max per file)
- **Error Logging**: Separate error.log for ERROR and above
- **Module-Specific Loggers**: Different log levels per module
- **Auto Rotation**: Logs rotate when reaching 10MB (keeps 5 backups)

## Log Directory Structure

```
project_root/
  logs/
    app.log        # Main application log
    error.log      # Error-only log
    app.log.1      # Rotated backups
    error.log.1
    ...
```

## Usage Examples

### Basic Setup (Auto-initialized)

```python
from src.logger import get_logger

logger = get_logger(__name__)
logger.info("Application started")
logger.error("Something went wrong")
```

### Manual Setup with Debug Mode

```python
from src.logger import setup_logging, get_logger

# Initialize with debug mode
setup_logging(debug=True)

logger = get_logger(__name__)
logger.debug("Detailed debug information")
```

### Custom Log Levels

```python
from src.logger import setup_logging, get_logger

# Initialize with custom log level
setup_logging(log_level="DEBUG")
```

## Log Levels by Module

| Module | Console | File | Purpose |
|--------|---------|------|---------|
| `src.agents` | DEBUG | DEBUG | Agent logic debugging |
| `src.api` | INFO | DEBUG | API endpoint logging |
| `src.ingestion` | DEBUG | DEBUG | Data ingestion pipeline |
| `src.storage` | DEBUG | DEBUG | Vector store & knowledge graph |
| `src.tools` | DEBUG | DEBUG | Tool execution |
| `langchain` | INFO | INFO | LangChain framework logs |
| `chromadb` | WARNING | WARNING | ChromaDB warnings only |

## Configuration Customization

### To change log levels:

Edit `LOGGING_CONFIG` in `src/logger.py`:

```python
"src.agents": {
    "level": "INFO",  # Change from DEBUG to INFO
    "handlers": ["console", "file", "error_file"],
    "propagate": False,
},
```

### To add a new module logger:

```python
"src.my_new_module": {
    "level": "DEBUG",
    "handlers": ["console", "file", "error_file"],
    "propagate": False,
},
```

### To load from JSON config:

```python
import logging.config
import json

with open('config/logging.json', 'r') as f:
    config = json.load(f)
    logging.config.dictConfig(config)
```

## Best Practices

1. **Use module-level loggers**: Always use `get_logger(__name__)` in each module
2. **Appropriate levels**:
   - `DEBUG`: Detailed diagnostic information
   - `INFO`: Confirmation that things are working
   - `WARNING`: Something unexpected
   - `ERROR`: A serious problem
   - `CRITICAL`: A very serious problem

3. **Structured logging**:
   ```python
   logger.info(f"Processing user: {user_id}")
   logger.error(f"Failed to process: {user_id}", exc_info=True)
   ```

## Integration with Main Application

Add to your `src/api/main.py` or entry point:

```python
from src.logger import setup_logging, get_logger

# Initialize logging early
setup_logging(debug=False)  # Set to True for development
logger = get_logger(__name__)

logger.info("Healthcare Assistant API Starting...")

# ... rest of your application
```
