import logging

loggers = {}

ch = ch = logging.StreamHandler()
formatter = logging.Formatter("%(levelname)s: %(asctime)s: %(filename)s:%(lineno)d -- %(message)s")
ch.setFormatter(formatter)
ch.setLevel(logging.WARNING)
def get_levels():
    """dict for converting to logger levels from string


    Returns
    -------
    dict
        contains all strings with corresponding logging levels.
    """
    return {
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "debug": logging.DEBUG,
    }


def getLogger(name: str):
    """Get a logger object with a specific name


    Parameters
    ----------
    name : str
        name of the logger object

    Returns
    -------
    logging.Logger
        logger object
    """
    if name in loggers:
        return loggers[name]
    logger = logging.getLogger(name)
    logger.addHandler(ch)
    logger.propagate = False
    loggers[name] = logger
    return logger


logger = getLogger(__name__)


def set_level(level: str):
    """Set the level of the logging object


    Parameters
    ----------
    level : str
        level of the logging object
    """
    levels = get_levels()
    level = levels.get(level, logging.WARNING)
    ch.setLevel(level)

    for name in loggers:
        logger = logging.getLogger(name)
        logger.setLevel(level)
    logger.info(f"Logging level set to {level}")
