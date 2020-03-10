from ladybug.epw import EPW
from ladybug_comfort.collection.solarcal import HorizontalSolarCal
from ladybug.datacollection import HourlyContinuousCollection
from .ground import Ground

def mean_radiant_temperature(epw_file: str, direct_horizontal_solar: HourlyContinuousCollection = None,
                             diffuse_horizontal_solar: HourlyContinuousCollection = None, ground: Ground = None,
                             is_shaded: bool = False):
    """
    Calculate the Mean Radiant Temperature from solar and ground radiation components
    :param epw_file: Weather-file with location and climatic conditions for simulation
    :param direct_horizontal_solar: Radiation from the sun
    :param diffuse_horizontal_solar: Radiation from the sky
    :param ground: Ground object
    :param is_shaded: Calculate MRT under shaded or unshaded conditions
    :return mean_radiant_temperature: Mean Radiant Temperature
    """

    # Check that the ground is shaded/unshaded in the same way for both the surface temperature calculation and this calculation
    if (ground is not None) & (ground.is_shaded != is_shaded):
        raise ValueError("Ground surface temperature calculation {} shaded but this calculation {}. These should match!".format("is" if ground.is_shaded else "isn't", "is" if is_shaded else "isn't"))

    # Factor the visible surface temperature based on exposure to ground (50% in open field)
    ground.surface_temperature.values = [i * 0.5 for i in ground.surface_temperature.values]

    mrt = HorizontalSolarCal(location=EPW(epw_file).location, direct_horizontal_solar=direct_horizontal_solar, diffuse_horizontal_solar=diffuse_horizontal_solar, longwave_mrt=ground.surface_temperature, fraction_body_exposed=0 if is_shaded else 1, floor_reflectance=ground.reflectivity).mean_radiant_temperature

    print("Mean radiant temperature calculation completed")

    return mrt
