import logging
import math

import numpy as np
import pandas as pd

from rules import adjustments, lab_budgets, lab_negotiated_budgets, non_lab_budgets
from settings import main as settings

logger = logging.getLogger(__name__)


def __dump_output(df):
    logger.info("Dumping output to file")
    logger.debug("file path: {}".format(settings.OUTPUT_FILE))
    df.to_excel(settings.OUTPUT_FILE, index=False)
    logger.info("done")


def __dump_milestones(milestones):
    df = pd.DataFrame(milestones)
    df.to_excel(settings.MILESTONES_OUTPUT_FILE, index=False)


def __final_cleanup(df):
    """
    Performs the last operations on the final dataframe.
    This includes:
    * add columns named year and month aimed at easing the manipulation of data in Excel
    """
    logger.info("Starting final cleanup")

    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    df = df[["CF", "date", "year", "month", "budget", "rule", "note"]]

    logger.info("done")
    return df


def main(params):
    logger.info("Started running the simulation")

    # boilerplate
    return_value = pd.DataFrame()

    # Lab budget rule
    logger.info("Running the lab budgets rules")
    run_params = {
        "start_date": params["simulation_start"],
        "end_date": params["simulation_end"],
    }
    current_df, milestones = lab_budgets.main(run_params)
    return_value = pd.concat([return_value, current_df], ignore_index=True)

    __dump_milestones(milestones)
    logger.info("done")

    # Fixed budgets
    logger.info("Running the fixed budgets rules")
    run_params = {
        "start_date": params["simulation_start"],
        "end_date": params["simulation_end"],
        "ledger": return_value,
    }
    df_fixed_budgets = lab_negotiated_budgets.main(run_params)
    return_value = pd.concat([return_value, df_fixed_budgets], ignore_index=True)
    logger.info("done")

    # Adjustments
    logger.info("Started running the adjustments rules")
    run_params = {
        "start_date": params["simulation_start"],
        "end_date": params["simulation_end"],
    }
    df_adjusments = adjustments.main(run_params)
    return_value = pd.concat([return_value, df_adjusments], ignore_index=True)
    logger.info("done")

    # Yearly budgets
    logger.info("Starting running the yearly budget rules")
    run_params = {
        "start_date": params["simulation_start"],
        "end_date": params["simulation_end"],
    }
    df_yearly_budgets = non_lab_budgets.main(run_params)
    return_value = pd.concat([return_value, df_yearly_budgets], ignore_index=True)
    logger.info("done")

    return_value = __final_cleanup(return_value)

    __dump_output(return_value)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    params = {
        "simulation_start": settings.START_DATE,
        "simulation_end": settings.END_DATE,
    }

    main(params)
