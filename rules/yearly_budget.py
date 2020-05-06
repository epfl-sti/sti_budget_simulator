import logging
import os
import re
import sys
from datetime import datetime

import pandas as pd


project_folder = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(project_folder)
sys.path.insert(0, project_folder)

from settings import yearly_budget as settings

logger = logging.getLogger(__name__)


def __get_yearly_budgets():
    """
    return the DataFrame containing the yearly budgets
    """
    df = pd.read_excel(settings.YEARLY_BUDGET_FILE_PATH)
    df.fillna(0, inplace=True)
    return df


def __calculate_ledger(df, params):
    """
    Turns the dataframe from the yearly budget format (1 line per CF, 1 column per year and 1 yearly budget amount in each cell)
    into ledger entries that can be output directly
    """
    columns = list(df.columns)

    years = []
    pattern = r"\d{4}"
    [years.append(column) for column in columns if re.match(pattern, str(column))]
    years.sort()

    rows_list = []
    for cf_index, cf_row in df.iterrows():
        for year in years:
            time_points = pd.date_range(
                start=datetime(year, 1, 1), end=datetime(year, 12, 31), freq="M"
            )
            for current_time_point in time_points:
                if (
                    current_time_point >= params["start_date"]
                    and current_time_point <= params["end_date"]
                ):
                    CF = cf_row["CF"]
                    budget = cf_row[year] / 12
                    rule = "yearly budget"
                    row_dict = {
                        "CF": CF,
                        "date": current_time_point,
                        "budget": budget,
                        "rule": rule,
                        "note": "",
                    }
                    rows_list.append(row_dict)

    return pd.DataFrame(rows_list)


def main(params):
    df = __get_yearly_budgets()
    df = __calculate_ledger(df, params)
    return df


if __name__ == "__main__":
    run_params = {
        "start_date": datetime.now(),
        "end_date": datetime(
            datetime.now().year + 10, datetime.now().month, datetime.now().day
        ),
    }
    print(main(run_params))
