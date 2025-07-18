from fastapi import APIRouter, HTTPException
from fastapi.staticfiles import StaticFiles
from service_controller import administrative_controller as controller
from helpers.config_json_helper import config_boostrap as confb

import logging
import constants
import psutil
import os
from datetime import datetime

logger = logging.getLogger(constants.REST_LAYER)

router = APIRouter()

ctrl : controller = controller()

#router.mount("/coverage", StaticFiles(directory="htmlcov"), name="coverage")

@router.get("/admin_read_metadata_os")
async def read_metadata_objectstore( ):
    """
    Ready the metadata.json file from the Object Store into the 
    into the local disk.
    <br><b>Uses the verbose flag for debugging.</b>

    |  Parameter   | Default | Description  |
    |--------------|---------|--------------|
    |              |         |              |

    """
    logger.info("Calling read metadata from object store")
    ret= ctrl.read_metadata_os( )
    logger.info(f" in api {ret}")
    return ret

@router.get("/admin_config")
async def admin_read_config():
    """
    Read the configuration file and present it.
    <br><b>Uses the verbose flag for debugging.</b>

    |  Parameter   | Default | Description  |
    |--------------|---------|--------------|
    |              |         |              |

    """
    logger.info("Config retreival")
    ret= ctrl.read_config()
    logger.info(f" in api {ret}")
    return ret

@router.post("/admin_reset_config_from_file")
async def admin_reset_config_from_file():
    """
    Read the configuration file and present it. It also reload the configuration file into memory.
    <u> NOTE: Because of the database connection, the code to reconnect to the database is not done. <u/>
    <br><b>Uses the verbose flag for debugging.</b>

    |  Parameter   | Default | Description  |
    |--------------|---------|--------------|
    |              |         |              |

    """
    logger.info("Config reset from file")
    ret= ctrl.reset_config_from_file()
    logger.info(f" in api {ret}")
    return ret

@router.get("/admin_os_file")
async def admin_get_os_file(filename):
    if filename is None:
        raise HTTPException(
            status_code=422,
            detail="Missing 'filename' parameter. It cannot be null."
        )
    logger.info("Operations read OS file")
    ret= ctrl.get_os_file(fn=filename)
    logger.info(f" in api {ret}")
    return ret

@router.put("/admin_os_file")
async def admin_put_os_file(filename, content):
    if filename is None and content is None:
        raise HTTPException(
            status_code=422,
            detail="Missing 'filename' and 'content' parameters. They cannot be null."
        )
    elif filename is None:
        raise HTTPException(
            status_code=422,
            detail="Missing 'filename' parameter. It cannot be null."
        )
    elif content is None:
        raise HTTPException(
            status_code=422,
            detail="Missing 'content' parameter. It cannot be null."
        )
    logger.info("Operations save OS file")
    ret= ctrl.put_os_file(fn=filename,content=content)
    logger.info(f" in api {ret}")
    return ret

@router.get("/list_os_files")
async def admin_list_os_file(bucket, prefix):
    """
    bucket = nl2sql
    prefix = finetune/jsonl/
    no front slash for the prefix
    """
    logger.info("Operations save OS file")
    ret= ctrl.list_os_file(bucket=bucket, prefix=prefix)
    logger.info(f" in api {ret}")
    return ret

@router.get("/set_logging_level")
async def set_logging_level(logger_name:str='REST', level: str='DEBUG'):
    newLevel=logging.getLevelNamesMapping()[level]
    the_logger = logging.getLogger(name=logger_name)
    the_logger.setLevel(level=newLevel)
    return {
            "logger":logger_name,
            "level":level,
            "level numerical":newLevel
            }

@router.get("/get_logger_list")
async def get_logger_list():
    loggers = list(logging.Logger.manager.loggerDict.keys())
    d : list = []

    level_mapping = logging.getLevelNamesMapping()
    inverted_mapping = {value: key for key, value in level_mapping.items()}

    for each in loggers:
        l = logging.getLogger(each).getEffectiveLevel()
        if l not in inverted_mapping:
            d.append(
                    {"name":each,
                    "level": str(l)
                    })
        else:
            d.append(
                    {"name":each,
                    "level":inverted_mapping[l]
                    })
    return d


@router.get("/get_info")
async def get_info():

    def get_version():
        with open('conf/version.txt', 'r') as f:
            return f.read().strip()
        #package_name = "nl2sql-trust".__name__
        #version = pkg_resources.get_distribution(package_name).version
        #logging.info(f"*************** VERSION {version}")
        
    def get_release():
        with open('conf/release.txt', 'r') as f:
            return f.read().strip()        

    # Get the current process
    process = psutil.Process(os.getpid())

    # Get the process start time (in seconds since the epoch)
    start_time = process.create_time()

    # Convert it to a human-readable format
    start_time_str = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')

    print(f"Process started at: {start_time_str}")
    
    return {
            "package":"nl2sql-trust",
            "version": get_version(),
            "release": get_release(),
            "started since": start_time_str,
            }