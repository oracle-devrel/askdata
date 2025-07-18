import configparser
import logging

def setup_config():
    config_parser = configparser.ConfigParser()
    config_parser.read('config.ini')

    config = {}
    for section in config_parser.sections():
        config[section] = {key: convert_value(value) for key, value in config_parser[section].items()}


    return config

def convert_value(value):
    if value.lower() == 'true':
        return True
    elif value.lower() == 'false':
        return False
    else:
        try:
            return int(value)
        except ValueError:
            return value

def print_config():
    try:
        logger.debug(config)
        logger.info(f"Websocket SSL Enabled: {config['ssl']['enabled']}")
        logger.info(f"Identity Domain Token Authentication Enabled: {config['identity_domain']['enabled']}")
        logger.info(f"Database connection type: {config['database']['conn_type']}")
    except Exception as e:
        logger.error(f"error writing config to log: {e}")


def setup_logging():

    log_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    logger = logging.getLogger('auto_prompt_websocket')

    try:
        if config["logging"]["filename"] == 'stream':
            handler = logging.StreamHandler()
        else:
            handler = logging.FileHandler(config["logging"]["filename"])

        handler.setFormatter(format)
        handler.setLevel(log_levels.get(config["logging"]["level"]))
        logger.setLevel(log_levels.get(config["logging"]["level"]))

        logger.addHandler(handler)

        return logger

    except Exception as e:
        logger.error("error setting up log")

        return logger


config = setup_config()

logger = setup_logging()

print_config()