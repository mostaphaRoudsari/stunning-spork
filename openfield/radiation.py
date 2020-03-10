import pathlib
import tempfile
import pandas as pd

from ladybug.datacollection import HourlyContinuousCollection
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.header import Header
from ladybug.datatype.energyflux import DirectHorizontalIrradiance, DiffuseHorizontalIrradiance
from honeybee.radiance.sky.skymatrix import SkyMatrix
from honeybee.radiance.analysisgrid import AnalysisGrid
from honeybee.radiance.recipe.annual.gridbased import GridBased


def run(epw_file: str, case_name: str=None, output_directory: str = None):
    """
    Calculate the open-field irradiation from the sky, split into direct-from-sun, and diffuse-from-sky-dome components
    :param epw_file: Weather-file with location and climatic conditions for simulation
    :param case_name: Name of case being simulated
    :param output_directory: Location of generated outputs
    :return DirectHorizontalIrradiance, DiffuseHorizontalIrradiance:
    """

    case_name = "openfield" if case_name is None else case_name
    output_directory = pathlib.Path(tempfile.gettempdir()) if output_directory is None else output_directory

    # Preparation
    epw_file = pathlib.Path(epw_file)
    output_directory = pathlib.Path(output_directory)

    # Prepare Radiance case for radiation incident on exposed test-point
    smx = SkyMatrix.from_epw_file(epw_file)
    ag = AnalysisGrid.from_points_and_vectors([[0, 0, 1.2]], name="OpenField")
    recipe = GridBased(sky_mtx=smx, analysis_grids=[ag], simulation_type=1)

    # Run annual irradiance simulation
    command_file = recipe.write(target_folder=output_directory, project_name=case_name)
    recipe.run(command_file=command_file)

    # Read Radiance results
    total = pd.read_csv(output_directory / case_name / "gridbased_annual" / "result" / "total..scene..default.ill",
                        skiprows=6, sep="\t", header=None, ).T.dropna() / 179
    direct = pd.read_csv(output_directory / case_name / "gridbased_annual" / "result" / "direct..scene..default.ill",
                         skiprows=6, sep="\t", header=None, ).T.dropna() / 179
    diffuse = (total - direct)[0].values
    sun = (pd.read_csv(output_directory / case_name / "gridbased_annual" / "result" / "sun..scene..default.ill",
                       skiprows=6, sep="\t", header=None, ).T.dropna() / 179)[0].values

    sun = HourlyContinuousCollection(header=Header(DirectHorizontalIrradiance(), unit="W/m2", analysis_period=AnalysisPeriod()), values=sun)
    diffuse = HourlyContinuousCollection(header=Header(DiffuseHorizontalIrradiance(), unit="W/m2", analysis_period=AnalysisPeriod()), values=diffuse)

    print("Direct and diffuse solar radiation simulation completed")

    return sun, diffuse
