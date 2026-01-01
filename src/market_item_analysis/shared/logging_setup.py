
import logging
import logging.config


def setup_logging():
    """Sets up the logging configuration using dictConfig."""
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,

        # --- Formatters (How the log entry looks) ---
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'error_format': {
                'format': '%(asctime)s - %(name)s - (PID:%(process)d) - %(levelname)s - %(message)s - (Location: %(pathname)s:%(lineno)d)'
            },
        },

        # --- Handlers (Where the log entry goes) ---
        'handlers': {
            'main_file_handler': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'standard',
                'filename': 'application.log', # All logs go here
                'maxBytes': 10485760, # 10MB
                'backupCount': 5,
                'level': 'INFO', # Log INFO and higher
            },
            'error_file_handler': {
                'class': 'logging.FileHandler',
                'formatter': 'error_format',
                'filename': 'error.log', # ONLY errors go here
                'level': 'ERROR', # Log ERROR and higher
            },
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'level': 'WARNING', # Only WARNINGs and higher to the console
            },
        },

        # --- Loggers (The loggers you call in your code) ---
        'loggers': {
            # This is the root logger that all module loggers will inherit from
            '': {
                'handlers': ['main_file_handler', 'error_file_handler', 'console'],
                'level': 'INFO',
                'propagate': True,
            },
            # You can define a specific logger, but typically the root is enough
            'my_module_name': {
                'handlers': ['main_file_handler'],
                'level': 'DEBUG',
                'propagate': False, # Stop propagation to the root logger handlers
            }
        }
    }

    logging.config.dictConfig(logging_config)
