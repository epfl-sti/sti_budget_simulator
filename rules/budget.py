import datetime
import logging
import os
from statistics import mean
import sys

import pandas as pd
from dateutil import rrule


project_folder = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(project_folder)
sys.path.insert(0, project_folder)
from settings import budget as settings

logger = logging.getLogger(__name__)

class __prof(object):
    def __init__(self):
        super().__init__()
        self.CF = None
        self.DoB = None
        self.retirementDate = None
        self.PATT_promotion = None
        self.PA_promotion = None
        self.PO_promotion = None
        self.PATT_budget = settings.PATT_YEARLY_BUDGET / 12
        self.PA_budget = ((settings.PATT_YEARLY_BUDGET + settings.PO_YEARLY_BUDGET) / 2) / 12
        self.PO_budget = settings.PO_YEARLY_BUDGET / 12


def main(params):
    """
    Calculates the expenses made over a period of time according to the regular budget rules

    parameters:
    params (dict): A dictionary object containing all the required information to run this simulation

    returns:
        (pd.DataFrame): a pandas dataframe containing all the ledger lines of this simulation
    """

    # TODO: check the parameters to make sure we have all the information we will be using

    logger.info("Starting budget simulation for CF {}".format(params['CF']))

    prof = __prof()
    prof.CF = params['CF']
    prof.DoB = params.get('DOB', None)
    prof.retirementDate = params.get('retirement', None)

    if prof.DoB is not None and prof.retirementDate is None:
        # The retirement date should be at the end of the year of the 'real' retirement date
        prof.retirementDate = datetime.datetime((prof.DoB + pd.offsets.DateOffset(years=65)).year, 12, 31)
    if prof.DoB is None and prof.retirementDate is not None:
        prof.DoB = prof.retirementDate - pd.offsets.DateOffset(years=65)

    prof.PATT_promotion = params.get('PATT promotion', None)
    prof.PA_promotion = params.get('PA promotion', None)
    prof.PO_promotion = params.get('PO promotion', None)

    if prof.PATT_promotion is None:
        if prof.PA_promotion is not None:
            prof.PATT_promotion = prof.PA_promotion - pd.offsets.DateOffset(months=settings.PATT_TO_PA_PERIOD)
        elif prof.PO_promotion is not None:
            prof.PATT_promotion = prof.PO_promotion - pd.offsets.DateOffset(months=settings.PATT_TO_PA_PERIOD) - pd.offsets.DateOffset(months=settings.PA_TO_PO_PERIOD)

    if prof.PA_promotion is None:
        if prof.PATT_promotion is not None:
            prof.PA_promotion = prof.PATT_promotion + pd.offsets.DateOffset(months=settings.PATT_TO_PA_PERIOD)
        elif prof.PO_promotion is not None:
            prof.PA_promotion = prof.PO_promotion - pd.offsets.DateOffset(months=settings.PA_TO_PO_PERIOD)

    if prof.PO_promotion is None:
        # We have decided to calculate from the PA promotion date instead of the PATT promotion date because the PA promotion is "closer" that PATT (hence we have a better chance to know it)
        if prof.PA_promotion is not None:
            prof.PO_promotion = prof.PA_promotion + pd.offsets.DateOffset(months=settings.PA_TO_PO_PERIOD)
        elif prof.PATT_promotion is not None:
            prof.PO_promotion = prof.PATT_promotion + pd.offsets.DateOffset(months=settings.PATT_TO_PA_PERIOD) + pd.offsets.DateOffset(months=settings.PA_TO_PO_PERIOD)

    prof.PATT_budget = params.get('PATT_yearly_budget' , settings.PATT_YEARLY_BUDGET) / 12
    prof.PO_budget = params.get('PO_yearly_budget', settings.PO_YEARLY_BUDGET) / 12
    prof.PA_budget = params.get('PA_yearly_budget', mean([prof.PATT_budget, prof.PO_budget])*12) / 12

    # calculate the date of the first bump in budget
    first_bump_budget_increase_date = prof.PATT_promotion+pd.offsets.DateOffset(months=settings.FIRST_STEP_BUDGET_PERIOD)

    # calculate the beginning of the second year as PO
    po_step1 = prof.PO_promotion + pd.offsets.DateOffset(years=1)

    # calculate the beginning of the third year as PO
    po_step2 = po_step1 + pd.offsets.DateOffset(years=1)

    # calculate the beginning of the fourth year as PO
    po_step3 = po_step2 + pd.offsets.DateOffset(years=1)

    # calculate the begnning of the full PO budget
    po_full = po_step3 + pd.offsets.DateOffset(years=1)

    milestones = {
        'DoB': prof.DoB,
        'patt_promotion': prof.PATT_promotion,
        'first_bump_budget_increase_date': first_bump_budget_increase_date,
        'pa_promotion': prof.PA_promotion,
        'po_promotion': prof.PO_promotion,
        'po_step1': po_step1,
        'po_step2': po_step2,
        'po_step3': po_step3,
        'po_full': po_full,
        'retirement': prof.retirementDate
    }

    # Now that we have the various milstones, we can build a list of periods with the required information.
    # This list is composed of tuples having 4 information:
    #   from: the date the period starts
    #   to: the date the period stops
    #   budget: the monthly budget during that period
    #   note: a note giving more details on that period
    periods = list()

    # Now that we have the various milestones of the academic rank, we can calculate the dates of the various events
    # Period 1 is between the PATT promotion and the first bump in the budget
    p1_from = prof.PATT_promotion
    p1_to = first_bump_budget_increase_date
    p1_budget = prof.PATT_budget
    p1_note = "Between the PATT promotion and the first bump in the budget"
    periods.append((p1_from, p1_to, p1_budget, p1_note))

    # Period 2 is between the first bump budget increase and the promotion as PA
    p2_from = first_bump_budget_increase_date
    p2_to = prof.PA_promotion
    p2_budget = p1_budget + (settings.FIRST_STEP_YEARLY_BUDGET_INCREASE / 12)
    p2_note = "Between the first bump budget increase and the promotion as PA"
    periods.append((p2_from, p2_to, p2_budget, p2_note))

    # Period 3 is between the promotion as PA and the promotion as PO
    p3 = (prof.PA_promotion, prof.PO_promotion)
    p3_from = prof.PA_promotion
    p3_to = prof.PO_promotion
    p3_budget = prof.PA_budget
    p3_note = "Between the promotion as PA and the promotion as PO"
    periods.append((p3_from, p3_to, p3_budget, p3_note))

    # Period 4 is the first year after the promotion as PO
    p4_from = prof.PO_promotion
    p4_to = po_step1
    pa_to_po_monthly_budget_increase = (prof.PO_budget - prof.PA_budget) / settings.NUMBER_OF_YEARS_TO_REACH_PO_BUDGET
    p4_budget = p3_budget + pa_to_po_monthly_budget_increase
    p4_note = "1st year after the promotion as PO"
    periods.append((p4_from, p4_to, p4_budget, p4_note))

    # Period 5 is the second year after the promotion as PO
    p5_from = po_step1
    p5_to = po_step2
    p5_budget = p4_budget + pa_to_po_monthly_budget_increase
    p5_note = "2nd year after the promotion as PO"
    periods.append((p5_from, p5_to, p5_budget, p5_note))

    # Period 6 is the third year after the promotion as PO
    p6 = (po_step2, po_step3)
    p6_from = po_step2
    p6_to = po_step3
    p6_budget = p5_budget + pa_to_po_monthly_budget_increase
    p6_note = "3rd year after the promotion as PO"
    periods.append((p6_from, p6_to, p6_budget, p6_note))

    # Period 7 is the fourth year after the promotion as PO
    p7_from = po_step3
    p7_to = po_full
    p7_budget = p6_budget + pa_to_po_monthly_budget_increase
    p7_note = "4th year after the promotion as PO"
    periods.append((p7_from, p7_to, p7_budget, p7_note))

    # Period 8 is the fourth year after the promotion as PO
    p8 = (po_full, prof.retirementDate)
    p8_from = po_full
    p8_to = prof.retirementDate
    p8_budget = prof.PO_budget
    p8_note = "Full PO budget"
    periods.append((p8_from, p8_to, p8_budget, p8_note))

    # Now that everything is in place, we can start the simulation
    start_date = params['start_date']
    end_date = params['end_date']

    return_value = pd.DataFrame(columns=['CF', 'date', 'budget', 'rule', 'note'])

    simulation_period = pd.date_range(start=start_date, end=end_date, freq="M")
    for current_month in simulation_period:
        current_budget = 0
        current_note = "outside of calculated values"

        for period in periods:
            if current_month >= period[0] and current_month < period[1]:
                current_budget = period[2]
                current_note = period[3]
                break

        return_value = return_value.append({'CF': params['CF'], 'date': current_month, 'budget': current_budget, 'rule': 'budget', 'note': current_note}, ignore_index=True)
    return milestones, return_value


if __name__ == "__main__":
    parameters = {}
    parameters['start_date'] = datetime.datetime(2019, 1, 1)
    parameters['end_date'] = datetime.datetime(2029, 1, 1)
    parameters['academic_rank'] = 'PA'
    parameters['in_rank_since'] = datetime.datetime(2018, 1, 1)
    parameters['CF'] = '1234'
    main(parameters)
