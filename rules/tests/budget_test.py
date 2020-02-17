from .. import budget
import pandas as pd


class TestBudget:

    def test_promotions_dates_get_calculated_correctly_when_starting_as_PATT(self):
        import datetime
        parameters = {}
        # parameters['initial_budget'] = 0
        parameters['start_date'] = datetime.datetime.now()
        parameters['end_date'] = datetime.datetime.now() + pd.offsets.DateOffset(years=10)
        parameters['academic_rank'] = 'PATT'
        parameters['in_rank_since'] = datetime.datetime(2000, 1, 1)
        parameters['CF'] = '1234'
        milestones = {}
        df = pd.DataFrame()
        milestones, df = budget.main(parameters)

        pa_promotion = datetime.datetime(2006, 10, 1)
        po_promotion = datetime.datetime(2013, 7, 1)

        assert milestones['patt_promotion'] == parameters['in_rank_since']
        assert milestones['pa_promotion'] == pa_promotion
        assert milestones['po_promotion'] == po_promotion

    def test_promotions_dates_get_calculated_correctly_when_starting_as_PA(self):
        import datetime
        parameters = {}
        # parameters['initial_budget'] = 0
        parameters['start_date'] = datetime.datetime.now()
        parameters['end_date'] = datetime.datetime.now() + pd.offsets.DateOffset(years=10)
        parameters['academic_rank'] = 'PA'
        parameters['in_rank_since'] = datetime.datetime(2006, 10, 1)
        parameters['CF'] = '1234'
        milestones = {}
        df = pd.DataFrame()
        milestones, df = budget.main(parameters)

        patt_promotion = datetime.datetime(2000, 1, 1)
        pa_promotion = datetime.datetime(2006, 10, 1)
        po_promotion = datetime.datetime(2013, 7, 1)

        assert milestones['patt_promotion'] == patt_promotion
        assert milestones['pa_promotion'] == pa_promotion
        assert milestones['po_promotion'] == po_promotion

    def test_promotions_dates_get_calculated_correctly_when_starting_as_PO(self):
        import datetime
        parameters = {}
        # parameters['initial_budget'] = 0
        parameters['start_date'] = datetime.datetime.now()
        parameters['end_date'] = datetime.datetime.now() + pd.offsets.DateOffset(years=10)
        parameters['academic_rank'] = 'PO'
        parameters['in_rank_since'] = datetime.datetime(2013, 7, 1)
        parameters['CF'] = '1234'
        milestones = {}
        df = pd.DataFrame()
        milestones, df = budget.main(parameters)

        patt_promotion = datetime.datetime(2000, 1, 1)
        pa_promotion = datetime.datetime(2006, 10, 1)
        po_promotion = datetime.datetime(2013, 7, 1)

        assert milestones['patt_promotion'] == patt_promotion
        assert milestones['pa_promotion'] == pa_promotion
        assert milestones['po_promotion'] == po_promotion

    def test_budget_values_get_calculated_correctly_when_simulation_is_larger_than_career(self):
        import datetime
        parameters = {}
        # parameters['initial_budget'] = 0
        parameters['start_date'] = datetime.datetime(1995,1,1)
        parameters['end_date'] = parameters['start_date'] + pd.offsets.DateOffset(years=100)
        parameters['academic_rank'] = 'PATT'
        parameters['in_rank_since'] = datetime.datetime(2000, 1, 1)
        parameters['CF'] = '1234'
        milestones = {}
        df = pd.DataFrame()
        milestones, df = budget.main(parameters)

        # Check that the first entry in the ledger (31.01.1995 - the prof is not yet PATT) is equal to 0
        assert df[df['date']==df['date'].min()]['budget'].all() == 0

        # Check that the last entry in the ledger (31.12.2094 - prof has retired) is equal to 0
        assert df[df['date']==df['date'].max()]['budget'].all() == 0

        # Check that when the prof becomes PATT, he gets the PATT budget (between 31.01.2000 and 31.12.2002 - 36 months)
        assert df.loc[df['date']==datetime.datetime(2000,1,31),'budget'].all() == (445000/12)

        # Check the PATT + bump budget
        assert df.loc[df['date']==datetime.datetime(2003,1,31),'budget'].all() == 42500 # (445000+65000) / 12

        # Check the PA budget
        assert df.loc[df['date']==datetime.datetime(2006,10,31),'budget'].all() == ((445000+1000000)/2)/12

        # Check the full PO budget
        assert df.loc[df['date']==datetime.datetime(2017,7,31),'budget'].all() == (1000000/12)
