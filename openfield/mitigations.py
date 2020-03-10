import pandas as pd
from ladybug.datacollection import HourlyContinuousCollection

from .ground import Ground
from . import utci, mrt


def utci_comparison(epw_file: str, idd_file: str, direct_horizontal_solar: HourlyContinuousCollection = None, diffuse_horizontal_solar: HourlyContinuousCollection = None):
    """
    Generate sets of UTCI values under various mitigation conditions.
    :param epw_file: Weather-file with location and climatic conditions for simulation
    :param idd_file: Location of EnergyPlus IDD file (to enable reference of IDF objects and simulation)
    :param direct_horizontal_solar: Radiation from the sun
    :param diffuse_horizontal_solar: Radiation from the sky
    :return: Dictionary of mitigations and UTCI values associated with these
    """

    d = {}
    for ground_reflectivity in [0.25, 0.40]:
        # Define the ground
        gnd = Ground(reflectivity=ground_reflectivity)

        for shaded in [True, False]:
            # Calculate surface temperature
            gnd.calculate_surface_temperature(epw_file, idd_file, is_shaded=shaded)

            # Calculate ground surface temperature
            mean_radiant_temperature = mrt.mean_radiant_temperature(epw_file, direct_horizontal_solar,
                                                                    diffuse_horizontal_solar, ground=gnd,
                                                                    is_shaded=shaded)

            for evap_cool in [True, False]:
                for wind in [0, 2]:

                    case_id = "Baseline"
                    case_id += "_Shaded" if shaded else ""
                    case_id += "_CoolPavement" if ground_reflectivity == 0.40 else ""
                    case_id += "_EvaporativeCooling" if evap_cool else ""
                    case_id += "_Wind" if wind == 2 else "_NoWind"
                    print("Calculating UTCI for {}".format(case_id))

                    # Calculate universal thermal climate index
                    universal_thermal_climate_index = utci.universal_thermal_climate_index(epw_file, mean_radiant_temperature, wind=wind, evaporative_cooling=evap_cool)

                    d[case_id] = universal_thermal_climate_index.values

    return d
