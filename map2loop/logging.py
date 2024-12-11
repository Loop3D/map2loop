import logging
import map2loop


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
    if name in map2loop.loggers:
        return map2loop.loggers[name]
    logger = logging.getLogger(name)
    logger.addHandler(map2loop.ch)
    logger.propagate = False
    map2loop.loggers[name] = logger
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
    map2loop.ch.setLevel(level)

    for name in map2loop.loggers:
        logger = logging.getLogger(name)
        logger.setLevel(level)
    logger.info(f"Logging level set to {level}")
