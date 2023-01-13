import cdsapi
import shutil

c = cdsapi.Client()

c.retrieve(
    'sis-energy-derived-reanalysis',
    {
        'format': 'zip',
        'variable': [
            '2m_air_temperature', 'surface_downwelling_shortwave_radiation', 
        ],
        'spatial_aggregation': 'country_level',
        'temporal_aggregation': 'hourly',
    },
    'meteorology-data.zip')

c.retrieve(
        'sis-energy-derived-reanalysis',
        {
            'format': 'zip',
            'variable': 'hydro_power_generation_rivers',
            'spatial_aggregation': 'country_level',
            'energy_product_type': 'capacity_factor_ratio',
            'temporal_aggregation': 'daily',
        },
        'ror.zip')


c.retrieve(
    'sis-energy-derived-reanalysis',
    {
        'format': 'zip',
        'variable': 'wind_power_generation_onshore',
        'spatial_aggregation': 'country_level',
        'energy_product_type': 'capacity_factor_ratio',
        'temporal_aggregation': 'hourly',
    },
    'won.zip')

c.retrieve(
    'sis-energy-derived-reanalysis',
    {
        'format': 'zip',
        'variable': 'wind_power_generation_offshore',
        'spatial_aggregation': 'maritime_country_level',
        'energy_product_type': 'capacity_factor_ratio',
        'temporal_aggregation': 'hourly',
    },
    'wof.zip')
shutil.unpack_archive('ror.zip', '.')
shutil.unpack_archive('won.zip', '.')
shutil.unpack_archive('wof.zip', '.')
shutil.unpack_archive('meteorology-data.zip', '.')