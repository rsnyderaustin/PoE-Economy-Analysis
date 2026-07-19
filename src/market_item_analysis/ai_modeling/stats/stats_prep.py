from sklearn.neighbors import KNeighborsRegressor
import logging

from src.market_item_analysis.ai_modeling.stats.data_prep import Prepper

from src.market_item_analysis.ai_modeling.stats.data import ListingModelData, QuantileTier
from src.market_item_analysis.ai_modeling.stats.neighborhood import NeighborhoodsSearch
from src.market_item_analysis.ai_modeling.visualizing import PlotService, PlotSpecs
from src.market_item_analysis.ai_modeling.config.listing_schema import ListingColumn

logger = logging.getLogger(__name__)


class StatsPrep:

    @classmethod
    def prep(cls,
             model_data: ListingModelData,
             quantile_tiers: list[QuantileTier]) -> Prepper:
        print("Pre-prepping DataFrame.")
        (
            model_data
            .drop_duplicates()
            .fillna(0)
            .create_log_target_col()
            .drop_nan_rows()
            .reset_index(drop=True)
            .drop_null_columns(max_percent_nulls=0.98)
            .drop_modal_columns(max_percent_mode=0.98)
            .drop_low_information_columns(threshold=0.01)
        )

        print("Creating neighborhoods.")
        neighborhoods = NeighborhoodsSearch(
            model_data=model_data
        ).get_neighborhoods()

        # Code below is just plotting
        PlotService.binned_median(model_data=model_data,
                                  col_name=ListingColumn.DAYS_SINCE_LEAGUE_START.value,
                                  plot_specs=PlotSpecs(
                                      title=
                                  )
                            title=f'{atype.capitalize()} {tier.capitalize()} Median Div Bins')

        plots.histogram(df_prep.price_column,
                        bins=100,
                        title=f'{atype.capitalize()} {tier.capitalize()} Divs')
        plots.histogram(df_prep.log_price_column,
                        bins=100,
                        title=f'{atype.capitalize()} {tier.capitalize()} Log Divs')

        plots.neighbor_distances_histogram(neighborhoods,
                                           title=f'{atype.capitalize()} {tier.capitalize()} Neighbor Distances Histogram')

        plots.number_of_neighbors_histogram(neighborhoods,
                                            title=f'{atype.capitalize()} {tier.capitalize()} Number of Neighbors Histogram')

        plots.binned_median(col_name='max_quality_pdps',
                            price_col_name=df_prep.price_col_name,
                            df=df_prep.df,
                            title=f'{atype.capitalize()} {tier.capitalize()} Pdps Bins',
                            bin_width=60)

        plots.plot_pca(df_prep.df,
                       df_prep.price_column,
                       title=f'{atype.capitalize()} {tier.capitalize()} PCA')

        return df_prep

