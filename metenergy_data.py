import pandas as pd
import numpy as np
import os, urllib, warnings
from pathlib import Path
from entsoe import EntsoePandasClient

class metenergy_data(object):
    """
    This class provides energy data needed for power system modelling. The data includes:
    - Hourly electricity demand estimated using a regression model 
    - Hourly electricity demand per country from ENTSO-E
    - Wind power capacity factor from wind speed and specifying the wind turbine curve
    - PV capacity factor from temperature and solar radiation
    - Estimated weekly hydropower inflow from ENTSO-E
    - Installed power capacity from ENTSO-E
    """
    
    @staticmethod
    def get_demand_met(tmp:pd.Series, ssr:pd.Series, coefs:pd.Series, min_load:float, max_load:float, timeline = None) -> pd.Series:
        """
        This function returns a time-series of electricity demand based on a regression model. The used
        predictors are temperature (`tmp`) and solar radiation (`ssr`), in addition to the calendar data.
        The regression model calculates a normalised demand time-series but the returned time-series (a Pandas Series) 
        scale the normalised demand using `min_load` and `max_load` (the normalised demand is multiplied by `max_load` - `min_load` and then `min_load` is added). 

        Parameters
        ----------
        tmp: Pandas.Series
            Temporal time-series (with a DatetimeIndex) containing the air temperature (Kelvin are converted into celsius)
        ssr: Pandas.Series
            Temporal time-series (with a DatetimeIndex) containing the solar radiation (W m**-2)
        coefs: Pandas.Series
            Series with the following regression coefficients: `cool` (cooling degree days), `heat` (heating degree days), `holTRUE` (flag for holidays),
            `ssrd` (solar radiation), `hour01`-`hour24` (coefficient for each hour of the day), `wday01`-`wday07` (coefficients per day of the week)
        min_load: float
            minimum demand to consider for the final time-series
        max_load: float
            maximum demand to consider for the final time-series
        timeline: optional
            If provided, it replaces the DatetimeIndex in `tmp` and `ssr` (which must be the same) in the output time-series

        Returns
        -------
        pandas.Series:
            final time-series generated with the regression
        """
        # check inputs
        assert isinstance(tmp.index, pd.DatetimeIndex), "index of temperature series is not a datetime"
        assert isinstance(ssr.index, pd.DatetimeIndex), "index of solar radiation series is not a datetime"
        assert len(tmp) == len(ssr), 'Temperature and solar radiation with different length'

        # Assuming temperature in Kelvin
        if tmp.min() > 200:
            tmp = tmp - 273.15

        base_index = tmp.index if timeline is None else timeline

        # transform cool/heat
        cool = pd.Series(data = [0 if x < 24 else x - 24 for x in tmp], index = base_index)
        heat = pd.Series(data = [0 if x > 15 else 15 - x for x in tmp], index = base_index)

        # create predictors
        x = pd.DataFrame(
            index = base_index,
            data = {
                'cool': cool,
                'heat': heat,
                'ssrd': ssr,
                'hour01': (base_index.hour == 1)*1, 'hour02': (base_index.hour == 2)*1, 'hour03': (base_index.hour == 3)*1,
                'hour04': (base_index.hour == 4)*1, 'hour05': (base_index.hour == 5)*1, 'hour06': (base_index.hour == 6)*1,
                'hour07': (base_index.hour == 7)*1, 'hour08': (base_index.hour == 8)*1, 'hour09': (base_index.hour == 9)*1,
                'hour10': (base_index.hour == 10)*1, 'hour11': (base_index.hour == 11)*1, 'hour12': (base_index.hour == 12)*1,
                'hour13': (base_index.hour == 13)*1, 'hour14': (base_index.hour == 14)*1, 'hour15': (base_index.hour == 15)*1,
                'hour16': (base_index.hour == 16)*1, 'hour17': (base_index.hour == 17)*1, 'hour18': (base_index.hour == 18)*1,
                'hour19': (base_index.hour == 19)*1, 'hour20': (base_index.hour == 20)*1, 'hour21': (base_index.hour == 21)*1,
                'hour22': (base_index.hour == 22)*1, 'hour23': (base_index.hour == 23)*1,
                'wday01': (base_index.dayofweek == 0)*1,'wday02': (base_index.dayofweek == 1)*1,'wday03': (base_index.dayofweek == 2)*1,
                'wday04': (base_index.dayofweek == 3)*1,'wzoneday05': (base_index.dayofweek == 4)*1,'wday06': (base_index.dayofweek == 5)*1,
                'wday07': (base_index.dayofweek == 6)*1,
                'holTRUE': 0
            }
        )

        norm_load  = (x * coefs).sum(axis=1)
        final_load =    (norm_load * (max_load - min_load)) + min_load
        return final_load
        
    @staticmethod
    def get_demand_entsoe_zenodo(zone:str)->pd.DataFrame:
        """
        This function returns a time-series of electricity demand based on ENTSO-E data. The ENTSO-E data
        is downloaded from a set of files available on zenodo (https://doi.org/10.5281/zenodo.7182602).
        The data is available for the following zones: BE, DE, ES, FR, IT, NL, PL, PT, RO, SE

        Parameters
        ----------
        zone: str
            Selected ENTSO-E zone

        Returns
        -------
        pandas.DataFrame:
            time-series with load data
        """
        # download
        DATA_PATH = os.path.join(str(Path.home()), '.data_model')
        if not os.path.exists(DATA_PATH):
            os.makedirs(DATA_PATH)

        if zone in ['BE', 'DE', 'ES', 'FR', 'IT', 'NL', 'PL', 'RO', 'SE']:
            FILE_TARGET = os.path.join(DATA_PATH, f'{zone}_demand_20160101_20220901.parquet')
            if not os.path.exists(FILE_TARGET):
                response = urllib.request.urlretrieve(f'https://zenodo.org/record/7182603/files/{zone}_demand_20160101_20220901.parquet?download=1', 
                FILE_TARGET)

            dem = pd.read_parquet(FILE_TARGET)
            return dem
        else:
            warnings.warn(f'zone {zone} not available')
            
    @staticmethod
    def get_wind_cf(ws:pd.Series, curve_csv_path = 'content/Vestas_v110_2000MW_ECEM_turbine.csv', timeline = None) -> pd.DataFrame:
        """
        This function returns a time-series of wind power capacity factor calculated using a conversion model.
        
        Parameters
        ----------
        ws: pandas.Series
            Wind-speed hourly data
        curve_csv_path: str
            Path to the CSV defining the wind power curve used 
        timeline: optional
            If provided, it replaces the DatetimeIndex in `ws` in the output time-series


        Returns
        -------
        pandas.DataFrame:
            time-series with wind capacity factors
        """
        base_index = ws.index if timeline is None else timeline
        
        power_curve_data = pd.read_csv(curve_csv_path, names = ['ws', '', 'cf'], delimiter= '  ', engine='python')
        wp = metenergy_data._convert_to_windpower(np.array(ws), power_curve_data)

        return(pd.DataFrame(
            data = {'wp': wp},
            index = base_index
        ))

    @staticmethod
    def _convert_to_windpower(wind_speed_data,power_curve_data):
        # convert to an array
        power_curve_w = np.array(power_curve_data['ws'])
        power_curve_p = np.array(power_curve_data['cf'])

        #interpolate to fine resolution.
        pc_winds = np.linspace(0,50,501) # make it finer resolution 
        pc_power = np.interp(pc_winds,power_curve_w,power_curve_p)

        reshaped_speed = wind_speed_data.flatten()
        test = np.digitize(reshaped_speed,pc_winds,right=False) # indexing starts 
        #from 1 so needs -1: 0 in the next bit to start from the lowest bin.
        test[test ==len(pc_winds)] = 500 # make sure the bins don't go off the 
        #end (power is zero by then anyway)
        wind_power_flattened = 0.5*(pc_power[test-1]+pc_power[test])

        wind_power_cf = np.reshape(wind_power_flattened,(np.shape(wind_speed_data)))
        
        return(wind_power_cf)
    @staticmethod
    def get_PV_cf(tmp:pd.Series, ssr:pd.Series, timeline = None) -> pd.DataFrame:
        """
        This function takes in arrays of country_masked 2m temperature (celsius)
        and surface solar irradiance (Wm-2) and converts this into a time series
        of solar power capacity factor using the method from Bloomfield et al.,
        (2020) https://doi.org/10.1002/met.1858
        """
        # check inputs
        assert isinstance(tmp.index, pd.DatetimeIndex), "index of temperature series is not a datetime"
        assert isinstance(ssr.index, pd.DatetimeIndex), "index of solar radiation series is not a datetime"
        assert len(tmp) == len(ssr), 'Temperature and solar radiation with different length'

        # Assuming temperature in Kelvin
        if tmp.min() > 200:
            tmp = tmp - 273.15

        base_index = tmp.index if timeline is None else timeline

        # reference values, see Evans and Florschuetz, (1977)
        T_ref = 25. 
        eff_ref = 0.9 #adapted based on Bett and Thornton (2016)
        beta_ref = 0.0042
        G_ref = 1000.
 
        rel_efficiency_of_panel = eff_ref*(1 - beta_ref*(tmp - T_ref))
        capacity_factor_of_panel = np.nan_to_num(rel_efficiency_of_panel*
                                              (ssr/G_ref)) 
        return pd.DataFrame(
            data = {'sp': capacity_factor_of_panel},
            index = base_index
        )
    @staticmethod
    def get_inflow_entsoe(zone:str, timeline:pd.DatetimeIndex, MY_API_KEY:str)->pd.DataFrame:
        """
        Calculate the hydropower inflow using the weekly data on the ENTSO-E TP. 
        The inflow for the week *w* is estimated as:
        inflow(w) = storage_at_end_of_the_week(w) - storage_at_the_beginning_of_the_week(w) + hydro_generation(w)
        
        Parameters
        ----------
        zone: str
            Zone from the ENTSO-E 
        timeline: pandas.DatetimeIndex
            The period considered to download the data. It must be timezoned
        MY_API_KEY: str
            API KEY to use the ENTSO-E REST API

        Returns
        -------
        pandas.DataFrame:
            time-series with weekly inflow (MWh) with four columns: Hydro Water Reservoir (weekly generation), Storage (stored energy), lagged (delta storage), inflow
        
        """
        assert isinstance(timeline, pd.DatetimeIndex), "timeline must be a time index"
        assert (timeline.tzinfo is not None), "timeline must be timezoned"
        # Add to config
        client = EntsoePandasClient(api_key=MY_API_KEY)
        
        start = timeline.min()
        end   = timeline.max()

        hgen = client.query_generation(zone, start=start,end=end, psr_type='B12')
        hgen.index = hgen.index.tz_convert(None)
        hgen = hgen.loc[hgen.index.minute == 0]

        if isinstance(hgen.columns, pd.MultiIndex):
            hgen.columns = hgen.columns.get_level_values(1)
            hgen = hgen.loc[:, 'Actual Aggregated']
            hgen.name = 'Hydro Water Reservoir'

        sto = client.query_aggregate_water_reservoirs_and_hydro_storage(zone, start=start, end=end)
        sto.index = sto.index.tz_convert(None)

        sto_j = sto.reset_index().rename(columns = {0: 'storage'})
        sto_j['sto_index'] = sto_j['index']
        inf_df = hgen.reset_index().merge(sto_j, how = 'left', on = 'index')
        inf_df['sto_index'] = inf_df['sto_index'].fillna(method = 'ffill')
        inf_df = inf_df.groupby(['sto_index']).sum(numeric_only=True)
        inf_df['lagged'] = inf_df['storage'].diff().shift(-1)
        inf_df['inflow'] = inf_df['Hydro Water Reservoir'] + inf_df['lagged']

        return inf_df

    @staticmethod
    def get_demand_entsoe(zone:str, timeline:pd.DatetimeIndex, MY_API_KEY:str)->pd.Series:
        """
        This function returns the electricity demand for a specific zone using the API from the ENTSO-E Transparency Platform (see https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)

         Parameters
        ----------
        zone: str
            Zone from the ENTSO-E 
        timeline: pandas.DatetimeIndex
            The period considered to download the data. It must be timezoned
        MY_API_KEY: str
            API KEY to use the ENTSO-E REST API

        Returns
        -------
        pandas.DataFrame:
            time-series with electricity demand


        """
        assert isinstance(timeline, pd.DatetimeIndex), "timeline must be a time index"
        assert (timeline.tzinfo is not None), "timeline must be timezoned"
        # Add to config
        client = EntsoePandasClient(api_key=MY_API_KEY)

        start = timeline.min()
        end   = timeline.max()

        dem = client.query_load(zone, start = start, end = end)

        return dem[dem.index.minute == 0]

    @staticmethod
    def get_capacity_entsoe(zone:str, year:int, MY_API_KEY:str)->pd.DataFrame:
        """
        This function returns the installed capacity (MW) for a specific zone using the API from the ENTSO-E Transparency Platform (see https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)

         Parameters
        ----------
        zone: str
            Zone from the ENTSO-E 
        year: int
            Year for the installed capacity
        MY_API_KEY: str
            API KEY to use the ENTSO-E REST API

        Returns
        -------
        pandas.DataFrame:
            Table with the installed capacity in MW for each technology


        """
        # Add to config
        client = EntsoePandasClient(api_key=MY_API_KEY)

        cap = client.query_installed_generation_capacity(zone, 
        start=pd.Timestamp(year = year, month = 1, day = 1, tz = 'UTC'),
        end = pd.Timestamp(year = year+1, month = 1, day = 1, tz = 'UTC')
        )

        return(cap)
    
            

