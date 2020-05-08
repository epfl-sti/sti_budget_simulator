import logging
import os
import sys
from datetime import datetime

import pandas as pd


project_folder = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(project_folder)
sys.path.insert(0, project_folder)
from settings import lab_negotiated_budgets as settings

logger = logging.getLogger(__name__)


def __get_fixed_budgets():
    """
    Return a pandas dataframe with all the fixed budgets rules to be applied.

    returns:
        (pd.DataFrame): a pandas dataframe with all the fixed budgets rules.
    """

    logger.info("Getting fixed budgets from file")
    logger.debug(
        "Getting from {}!{}".format(
            settings.FIXED_BUDGETS_FILE_PATH, settings.FIXED_BUDGETS_SHEET_NAME
        )
    )

    fixed_budgets = pd.read_excel(
        settings.FIXED_BUDGETS_FILE_PATH, sheet_name=settings.FIXED_BUDGETS_SHEET_NAME,
    )
    fixed_budgets["budget"] = fixed_budgets["Annual amount"] / 12
    fixed_budgets.drop(columns=["Annual amount"], inplace=True)
    return fixed_budgets


def __get_calculated_budgets(ledger, start, end):
    """
    Return a pandas datafrane with all the budget lines that have calculated by the budget rules

    parameters:
        (pandas.DataFrame): The current ledger that contains all the rules calculated lines.
        (datetime.datetime): The start date of the simulation
        (datetime.datetime): The end date of the simulation

    returns:
        (pd.DataFrame): a pandas.DataFrame with all the ledger lines calculated by the budget rules
    """

    logger.info("Getting calculated budget lines.")
    logger.debug("Number of lines in ledger: {}".format(len(ledger)))
    logger.debug("Start date: {}".format(start))
    logger.debug("End date: {}".format(end))

    ledger = ledger.loc[
        (ledger["rule"] == "budget")
        & (ledger["date"] >= start)
        & (ledger["date"] <= end)
    ]
    ledger.drop(columns=["rule", "note"], inplace=True)

    logger.debug(("Number of lines in filtered ledger: {}".format(len(ledger))))
    return ledger


def main(parameters):
    """
    Returns a pandas dataframe with all the adjustments required to comply with budgets that are already fixed
    ATTENTION: It requires the current ledger with all the lines calculated by the budget rules in order to be able to calculate the correct adjustments.j

    parameters:
        parameters (dict): a dictionary of parameters values required to run this module
        parameters['start_date'] (datetime.datetime): The start date of the simulation
        parameters['end_date'] (datetime.datetime): The end date of the simulation
        parameters['ledger'] (pandas.DataFrame): The current ledger that contains all the lines calculated by the budget rules

    returns:
        (pandas.DataFrame): new lines to be added to the current ledger so the total of the budget by date matches the fixed budget figures
    """

    logger.info("Starting the calculate ledger for fixed budgets")
    logger.debug("Start of simulation: {}".format(parameters["start_date"]))
    logger.debug("End of simulation: {}".format(parameters["end_date"]))
    logger.debug(
        "Number of lines in current ledger: {}".format(len(parameters["ledger"]))
    )

    # Get the budget lines that have been already calculated
    calculated_budgets = __get_calculated_budgets(
        parameters["ledger"], parameters["start_date"], parameters["end_date"]
    )

    # Get the fixed budgets
    fixed_budgets = __get_fixed_budgets()

    # Boilerplate
    return_value = pd.DataFrame(
        columns=[
            "CF",
            "date",
            "budget",
            "theorical_budget",
            "real_budget",
            "rule",
            "note",
        ]
    )
    CFs = fixed_budgets["CF"].unique()
    logger.debug("Number of CFs: {}".format(len(CFs)))

    dates = pd.date_range(
        start=parameters["start_date"], end=parameters["end_date"], freq="M"
    )
    logger.debug("Number of dates: {}".format(len(dates)))

    # Loop over all the CFs and dates to generate the new lines in the ledger
    for current_CF in CFs:
        logger.debug("Current CF: {}".format(current_CF))

        for current_date in dates:
            logger.debug("Current date: {}".format(current_date))

            notes = list()

            try:
                real_budget = fixed_budgets.loc[
                    (fixed_budgets["CF"] == current_CF)
                    & (fixed_budgets["From"] <= current_date)
                    & (fixed_budgets["To"] >= current_date),
                    "budget",
                ].iloc[0]
                logger.debug("real_budget: {}".format(real_budget))
            except IndexError as ex:
                logger.debug("No real budget found.")
                real_budget = None

            if (
                calculated_budgets.loc[
                    (calculated_budgets["CF"] == current_CF), "budget"
                ].count()
                > 0
            ):
                calculated_budget = calculated_budgets.loc[
                    (calculated_budgets["CF"] == current_CF)
                    & (calculated_budgets["date"] == current_date),
                    "budget",
                ].iloc[0]
                logger.debug("Calculated budget: {}".format(calculated_budget))

            else:
                calculated_budget = 0
                notes.append("CF was not part of the calculated ones.")
                logger.debug(
                    "The CF was not part of the calculated ones. Setting the calculated budget to 0"
                )

            if real_budget:
                adjustment = real_budget - calculated_budget
            else:
                adjustment = 0

            if adjustment != 0:
                notes.append(
                    "{:.2f} adjustment because of difference between real budget ({:.2f}) and theorical budget ({:.2f}).".format(
                        adjustment, real_budget, calculated_budget
                    )
                )
                logger.debug("An adjustment has to be made: {}".format(adjustment))

                return_value = return_value.append(
                    {
                        "CF": current_CF,
                        "date": current_date,
                        "real_budget": real_budget,
                        "theorical_budget": calculated_budget,
                        "budget": adjustment,
                        "rule": "lab negotiated budgets",
                        "note": " ".join(notes),
                    },
                    ignore_index=True,
                )

    # cleanup of unused columns
    logger.debug("Cleaning up the DataFrame")
    return_value.drop(columns=["theorical_budget", "real_budget"], inplace=True)

    return return_value


if __name__ == "__main__":
    parameters = {}
    parameters["start_date"] = datetime(2019, 1, 1)
    parameters["end_date"] = datetime(2029, 1, 1)
    parameters["ledger"] = pd.DataFrame(
        columns=["CF", "date", "budget", "rule", "note"]
    )
    print(main(parameters))
