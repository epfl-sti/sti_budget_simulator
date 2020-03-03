import datetime
import logging
import os
import sys

import pandas as pd


project_folder = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(project_folder)
sys.path.insert(0, project_folder)
from settings import adjustments as settings

logger = logging.getLogger(__name__)


def __get_adjustments_rules():
    df = pd.read_excel(settings.ADJUSTMENTS_RULES_FILE_PATH)
    return df

def main(params):
    logger.info("Started main adjustments routine")
    logger.debug(params)

    return_value = pd.DataFrame(columns=['CF', 'date', 'budget', 'rule', 'note'])

    simulation_period = pd.date_range(start=params['start_date'], end=params['end_date'], freq="M")

    rules = __get_adjustments_rules()
    for date in simulation_period:
        for index, rule in rules.iterrows():
            if date >= rule['From'] and date <= rule['To']:
                return_value = return_value.append({'CF': rule['CF'], 'date': date, 'budget': rule['Monthly amount'], 'rule': 'adjustments', 'note': rule['Note']}, ignore_index=True)
    return return_value


if __name__ == "__main__":
    params = {
        "start_date": datetime.datetime(1995, 1, 1),
        "end_date": datetime.datetime(2100, 1, 1),
    }
    main(params)
