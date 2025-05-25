from data_transforming import ListingsTransforming
from shared import env_loader
from stat_analysis.stats_prep import StatsPrep


class PricePredictModelBuilder:

    def build(self):
        psql_table_name = env_loader.get_env("PSQL_TRAINING_TABLE")
        training_data = self.psql_manager.fetch_table_data(psql_table_name)
        model_df = ListingsTransforming.to_price_predict_df(rows=training_data)

        atype_dfs = model_df.groupby('atype')

        for atype, atype_df in atype_dfs.items():
            atype_df = StatsPrep.prep_dataframe(df=atype_df, price_column='exalts')

            if atype_df is None:  # This only happens if no column in the atype_df has enough of a correlation
                continue

            model = build_price_predict_model(df=atype_df, atype=str(atype), price_column='exalts')
            self.files_manager.model_data[ModelPath.PRICE_PREDICT_MODEL] = model
            self.files_manager.save_data(paths=[ModelPath.PRICE_PREDICT_MODEL])