import os
import logging.config
import yaml

def setup_logging(default_path='logging.yaml', default_level=logging.INFO, env_key='LOG_CFG', capture_warnings=True):
    """Setup logging configuration
    Based on http://victorlin.me/posts/2012/08/good-logging-practice-in-python/
    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.load(f.read())
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)
    logging.captureWarnings(capture_warnings)
