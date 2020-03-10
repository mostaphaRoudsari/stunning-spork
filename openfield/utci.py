import numpy as np
from ladybug.epw import EPW
from ladybug_comfort.collection.utci import UTCI
from ladybug.datacollection import HourlyContinuousCollection
from ladybug.psychrometrics import wet_bulb_from_db_rh
_wbt = np.vectorize(wet_bulb_from_db_rh)


def universal_thermal_climate_index(epw_file: str, mean_radiant_temperature: HourlyContinuousCollection, wind: int = 1, evaporative_cooling: bool = False):
    """
    Calculate the Universal Thermal Climate Index
    :param epw_file: Weather-file with location and climatic conditions for simulation
    :param mean_radiant_temperature: Mean radiant temperature hourly collection
    :param wind: 0 if no wind to be included (0.01m/s), 1 if wind speed should use the values in the EPW file, or 2+ is wind is fixed at a speed of 2m/s+
    :return universal_thermal_climate_index:
    """

    # Read weather-file
    epw = EPW(epw_file)

    # Get wind-speed values based on user choice
    wind_speed = 0.01 if wind == 0 else epw.wind_speed if wind == 1 else wind

    # Recalculate dry-bulb temperature if evaporative cooling is to be introduced
    if evaporative_cooling:
        wbt = np.array(_wbt(epw.dry_bulb_temperature.values, epw.relative_humidity, epw.atmospheric_station_pressure.values))
        dbt_ec = np.array(epw.dry_bulb_temperature.values) - ((np.array(epw.dry_bulb_temperature.values) - wbt) * 0.7)
        epw.dry_bulb_temperature.values = dbt_ec

    # Calculate UTCI values
    utci = UTCI(epw.dry_bulb_temperature, epw.relative_humidity, mean_radiant_temperature, wind_speed).universal_thermal_climate_index

    print("Universal Thermal Climate Index calculation completed")

    return utci
