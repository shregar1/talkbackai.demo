import os
#
from start_utils import celery, logger


@celery.task(name='tasks.delete.delete_residual_file')
def delete_residual_file(file_path: str) -> None:

    logger.info(f"Deleting residual file: {file_path}")
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as err:
        logger.error(f"Error occured whilem deleting residual file : {err}")
        pass

    return None