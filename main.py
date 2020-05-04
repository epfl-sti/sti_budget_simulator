import logging
import math

import numpy as np
import pandas as pd

from modules import datagenerator
from rules import adjustments, budget, fixed_budget
from settings import main as settings

logger = logging.getLogger(__name__)


def __generate_parameters():
    logger.info("started generating parameters file")
    # generate the base information based on the Excel file Audrey provided
    datagenerator.main()
    df = datagenerator.get_data()

    # We don't need all the data from the cached version
    df.drop(columns=["sciper", "academic rank", "appointment"], inplace=True)

    # One column needs to be renamed
    df.rename(columns={"DoB": "DOB"}, inplace=True)

    # empty columns need to be added
    df["retirement"] = None
    df["PATT yearly budget"] = None
    df["PA yearly budget"] = None
    df["PO yearly budget"] = None

    # dump as parameters file
    df.to_excel(settings.PARAMETERS_FILE, index=False)
    logger.info("done")


def __get_parameters():
    logger.info("getting parameters from file")
    logger.debug("Parameters file: {}".format(settings.PARAMETERS_FILE))
    params = pd.read_excel(settings.PARAMETERS_FILE)

    logger.info("done")
    return params


def __dump_output(df):
    logger.info("Dumping output to file")
    logger.debug("file path: {}".format(settings.OUTPUT_FILE))
    df.to_csv(settings.OUTPUT_FILE, index=False)
    logger.info("done")


def __dump_milestones(milestones):
    """
    expected content of dictionaries
    'DoB'
    'patt_promotion'
    'first_bump_budget_increase_date'
    'pa_promotion'
    'po_promotion'
    'po_step1
    'po_step2'
    'po_step3'
    'po_full'
    'retirement'
    """
    logger.info("dumping milestones to disk")
    logger.debug("output file path: {}".format(settings.MILESTONES_OUTPUT_FILE))
    logger.debug("Number of CFs: {}".format(len(milestones)))

    columns = [
        "CF",
        "DoB",
        "patt_promotion",
        "pa_promotion",
        "po_promotion",
        "retirement",
    ]
    df = pd.DataFrame(columns=columns)
    for key, value in milestones.items():
        CF = key
        DoB = value["DoB"]
        patt_promotion = value["patt_promotion"]
        pa_promotion = value["pa_promotion"]
        po_promotion = value["po_promotion"]
        retirement = value["retirement"]
        df.loc[len(df)] = [
            CF,
            DoB,
            patt_promotion,
            pa_promotion,
            po_promotion,
            retirement,
        ]
    df.to_csv(settings.MILESTONES_OUTPUT_FILE, index=False)


def __final_cleanup(df):
    """
    Performs the last operations on the final dataframe.
    This includes:
    * add a column named year aimed at easing the manipulation of data in Excel
    """
    logger.info("Starting final cleanup")

    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    logger.info("done")
    return df


def main():
    logger.info("Started running the simulation")
    return_value = pd.DataFrame()
    all_milestones = {}

    # Budget Rules
    # __generate_parameters()

    params = __get_parameters()
    simulation_start = settings.START_DATE
    simulation_end = settings.END_DATE

    logger.info("Started running the budget rules")
    for index, row in params.iterrows():
        run_params = {}
        run_params["start_date"] = simulation_start
        run_params["end_date"] = simulation_end
        run_params["CF"] = row["CF"]
        run_params["DOB"] = row["DOB"]
        if not pd.isnull(row["PATT promotion"]):
            run_params["PATT promotion"] = row["PATT promotion"]
        if not pd.isnull(row["PA promotion"]):
            run_params["PA promotion"] = row["PA promotion"]
        if not pd.isnull(row["PO promotion"]):
            run_params["PO promotion"] = row["PO promotion"]
        if not pd.isnull(row["retirement"]):
            run_params["retirement"] = row["retirement"]

        if not math.isnan(row["PATT yearly budget"]):
            run_params["PATT_yearly_budget"] = row["PATT yearly budget"]
        if not math.isnan(row["PA yearly budget"]):
            run_params["PA_yearly_budget"] = row["PA yearly budget"]
        if not math.isnan(row["PO yearly budget"]):
            run_params["PO_yearly_budget"] = row["PO yearly budget"]
        milestones, current_df = budget.main(run_params)

        return_value = pd.concat([return_value, current_df], ignore_index=True)
        all_milestones[row["CF"]] = milestones

    __dump_milestones(all_milestones)
    logger.info("done")

    # Fixed budgets
    logger.info("Running the fixed budgets rules")
    run_params = {
        "start_date": simulation_start,
        "end_date": simulation_end,
        "ledger": return_value,
    }
    df_fixed_budgets = fixed_budget.main(run_params)
    return_value = pd.concat([return_value, df_fixed_budgets], ignore_index=True)
    logger.info("done")

    # Adjustments
    logger.info("Started running the adjustments rules")
    run_params = {"start_date": simulation_start, "end_date": simulation_end}
    df_adjusments = adjustments.main(run_params)
    return_value = pd.concat([return_value, df_adjusments], ignore_index=True)
    logger.info("done")

    return_value = __final_cleanup(return_value)

    __dump_output(return_value)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    main()
