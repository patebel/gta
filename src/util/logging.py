import logging
import os
import traceback

LOG_FILENAME = None
LOG_PROMPTS = True
LOG_RESPONSE = True

if LOG_FILENAME:
    os.makedirs(os.path.dirname(LOG_FILENAME), exist_ok=True)
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        filename=LOG_FILENAME,
                        filemode='a')
else:
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger()


def log_debug(message):
    logger.debug(message)


def log_prompt(request_type, prompt):
    if LOG_PROMPTS:
        logger.debug(f'[PROMPT] [{request_type}]\n{prompt}')


def log_response(request_type, prompt):
    if LOG_RESPONSE:
        logger.debug(f'[RESPONSE] [{request_type}]\n{prompt}')


def log_info(message):
    logger.info(message)


def log_warning(message):
    logger.warning(message)


def log_error(e):
    logging.error(f"####################\n\n"
                  f"{e}\n\n{traceback.format_exc()}"
                  f"\n\n#######################################################\n\n")


def log_error_without_trace(e):
    logging.error(e)


def log_critical(message):
    logger.critical(message)
