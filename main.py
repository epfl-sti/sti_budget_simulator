import pandas as pd

from rules import budget
from settings import main as settings


def __get_parameters():
    params = pd.read_excel(settings.PARAMETERS_FILE)
    return params


def __dump_output(df):
    df.to_csv(settings.OUTPUT_FILE, index=False)


def main():
    params = __get_parameters()
    simulation_start = settings.START_DATE
    simulation_end = settings.END_DATE

    return_value = pd.DataFrame()

    for index, row in params.iterrows():
        run_params = {}
        run_params['initial_budget'] = row['initial budget']
        run_params['start_date'] = simulation_start
        run_params['end_date'] = simulation_end
        run_params['academic_rank'] = row['academic rank']
        run_params['in_rank_since'] = row['in rank since']
        run_params['CF'] = row['CF']
        run_params['DOB'] = row['DOB']
        run_params['PATT_yearly_budget'] = row['PATT yearly budget']
        run_params['PA_yearly_budget'] = row['PA yearly budget']
        run_params['PO_yearly_budget'] = row['PO yearly budget']
        milestones, current_df = budget.main(run_params)

        return_value = pd.concat([return_value, current_df], ignore_index=True)

    __dump_output(return_value)


if __name__ == "__main__":
    main()
