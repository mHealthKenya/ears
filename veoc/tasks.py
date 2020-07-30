from celery.decorators import task
from celery.utils.log import get_task_logger
import json
import http.client
# import request

from veoc.utils import save_dhis_idsr_data

logger = get_task_logger(__name__)

@task(name="pull_dhis_idsr_data")
def pull_dhis_idsr_data(org_units, url):
    """pulls data from dhis2 in batches and saves the data into weoc database"""

    print('inside task method')
    logger.info("saving DHIS2 - idsr MOH505 data")
    return save_dhis_idsr_data(org_units, url)
