from eppy.modeleditor import IDF
import pandas as pd
import tempfile
import pathlib
from io import StringIO
import subprocess

from ladybug.epw import EPW
from ladybug.datacollection import HourlyContinuousCollection
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.header import Header
from ladybug.datatype.temperature import Temperature


class Ground(object):
    def __init__(self, thickness=0.2, reflectivity=0.35, emissivity=0.9, conductivity=1.1, density=2250, specific_heat=1000):
        self.thickness = thickness
        self.reflectivity = reflectivity
        self.emissivity = emissivity
        self.conductivity = conductivity
        self.density = density
        self.specific_heat = specific_heat

        self.surface_temperature = None
        self.is_shaded = None
        self.epw = None

    def __repr__(self):
        return_string = "Ground: \n"
        for k, v in self.__dict__.items():
            return_string += "- {}: {}\n".format(k, v)
        return return_string

    def calculate_surface_temperature(self, epw_file: str, idd_file: str, case_name: str = None, output_directory: str = None, is_shaded: bool = False):
        """
        Calculate the surface temperature of the ground typology using EnergyPlus
        :param epw_file: Weather-file with location and climatic conditions for simulation
        :param idd_file: Location of EnergyPlus IDD file (to enable reference of IDF objects and simulation)
        :param case_name: Name of case being simulated
        :param output_directory: Location of generated outputs
        :param is_shaded:
        :return ground_surface_temperature:
        """

        # Assign to object and locate outputs
        self.epw = epw_file
        self.is_shaded = is_shaded
        case_name = "openfield" if case_name is None else case_name
        output_directory = pathlib.Path(tempfile.gettempdir()) if output_directory is None else output_directory

        # Load monthly ground temperature from weather-file
        monthly_ground_temperatures = EPW(epw_file).monthly_ground_temperature[0.5].values

        # Reference Eplus program
        idd_file = pathlib.Path(idd_file)
        eplus = idd_file.parent / "energyplus.exe"
        IDF.setiddname(str(idd_file))

        # Construct folder structure for eplus case
        eplus_output_path = pathlib.Path(output_directory) / case_name / "ground_surface_temperature"
        eplus_output_path.mkdir(parents=True, exist_ok=True)
        idf_file = eplus_output_path / "in.idf"
        eso_file = eplus_output_path / "eplusout.eso"

        # Construct case for simulation
        idf = IDF(StringIO(""))

        # Define base building object
        building = idf.newidfobject("BUILDING")
        building.Name = "ground"
        building.North_Axis = 0
        building.Terrain = "City"
        building.Solar_Distribution = "FullExterior"
        building.Maximum_Number_of_Warmup_Days = 25
        building.Minimum_Number_of_Warmup_Days = 6

        # Set shadow calculation to once per hour
        shadowcalculation = idf.newidfobject("SHADOWCALCULATION")
        shadowcalculation.Calculation_Method = "TimestepFrequency"
        shadowcalculation.Calculation_Frequency = 1
        shadowcalculation.Maximum_Figures_in_Shadow_Overlap_Calculations = 3000

        # Define ground material

        material = idf.newidfobject("MATERIAL")
        material.Name = "ground_material"
        material.Roughness = "MediumRough"
        material.Thickness = self.thickness
        material.Conductivity = self.conductivity
        material.Density = self.density
        material.Specific_Heat = self.specific_heat
        material.Thermal_Absorptance = self.emissivity
        material.Solar_Absorptance = 1 - self.reflectivity
        material.Visible_Absorptance = 1 - self.reflectivity

        # Define ground construction
        construction = idf.newidfobject("CONSTRUCTION")
        construction.Name = "ground_construction"
        construction.Outside_Layer = "ground_material"

        # Set global geometry rules
        globalgeometryrules = idf.newidfobject("GLOBALGEOMETRYRULES")
        globalgeometryrules.Starting_Vertex_Position = "UpperLeftCorner"
        globalgeometryrules.Vertex_Entry_Direction = "Counterclockwise"
        globalgeometryrules.Coordinate_System = "Relative"

        # Define ground zone
        zone = idf.newidfobject("ZONE")
        zone.Name = "ground_zone"

        # Add ground surfaces (as a closed zone)
        ground_x, ground_y, ground_z = 200, 200, 1
        vertex_groups = [
            [[-ground_x / 2, ground_y / 2, 0], [-ground_x / 2, -ground_y / 2, 0], [ground_x / 2, -ground_y / 2, 0],
             [ground_x / 2, ground_y / 2, 0]],
            [[ground_x / 2, -ground_y / 2, -ground_z], [-ground_x / 2, -ground_y / 2, -ground_z],
             [-ground_x / 2, ground_y / 2, -ground_z], [ground_x / 2, ground_y / 2, -ground_z]],
            [[-ground_x / 2, ground_y / 2, 0], [-ground_x / 2, ground_y / 2, -ground_z],
             [-ground_x / 2, -ground_y / 2, -ground_z], [-ground_x / 2, -ground_y / 2, 0]],
            [[ground_x / 2, -ground_y / 2, 0], [ground_x / 2, -ground_y / 2, -ground_z],
             [ground_x / 2, ground_y / 2, -ground_z], [ground_x / 2, ground_y / 2, 0]],
            [[ground_x / 2, ground_y / 2, 0], [ground_x / 2, ground_y / 2, -ground_z],
             [-ground_x / 2, ground_y / 2, -ground_z], [-ground_x / 2, ground_y / 2, 0]],
            [[-ground_x / 2, -ground_y / 2, 0], [-ground_x / 2, -ground_y / 2, -ground_z],
             [ground_x / 2, -ground_y / 2, -ground_z], [ground_x / 2, -ground_y / 2, 0]]
        ]

        for n, vg in enumerate(vertex_groups):
            gnd = idf.newidfobject("BUILDINGSURFACE:DETAILED")
            gnd.Name = "ground_surface_{}".format(n)
            gnd.Surface_Type = "Roof" if n == 0 else "Floor" if n == 1 else "Wall"
            gnd.Construction_Name = "ground_construction"
            gnd.Zone_Name = "ground_zone"
            gnd.Outside_Boundary_Condition = "Outdoors" if n == 0 else "Ground"
            gnd.Sun_Exposure = "SunExposed" if n == 0 else "Nosun"
            gnd.Wind_Exposure = "WindExposed" if n == 0 else "Nowind"
            for nnn, vgx in enumerate(vg):
                setattr(gnd, "Vertex_{}_Xcoordinate".format(nnn + 1), vgx[0])
                setattr(gnd, "Vertex_{}_Ycoordinate".format(nnn + 1), vgx[1])
                setattr(gnd, "Vertex_{}_Zcoordinate".format(nnn + 1), vgx[2])

        # Set ground temperatures using EPW monthly values
        groundtemperature = idf.newidfobject("SITE:GROUNDTEMPERATURE:BUILDINGSURFACE")
        for i, j in list(zip(*[pd.date_range("2018", "2019", freq="1M").strftime("%B"), monthly_ground_temperatures])):
            setattr(groundtemperature, "{}_Ground_Temperature".format(i), j)

        # Add shading if the case is shaded
        if is_shaded:
            shd_schedule_limits = idf.newidfobject("SCHEDULETYPELIMITS")
            shd_schedule_limits.Name = "shade_schedule_type_limit"
            shd_schedule_limits.Lower_Limit_Value = 0
            shd_schedule_limits.Upper_Limit_Value = 1
            shd_schedule_limits.Numeric_Type = "Continuous"

            shd_schedule_constant = idf.newidfobject("SCHEDULE:CONSTANT")
            shd_schedule_constant.Name = "shade_schedule_constant"
            shd_schedule_constant.Schedule_Type_Limits_Name = "shade_schedule_type_limit"
            shd_schedule_constant.Hourly_Value = 0

            shade_x = 200
            shade_y = 200
            shade_z = 4
            shade_vertex_groups = [
                [[-shade_x / 2, -shade_y / 2, shade_z], [-shade_x / 2, -shade_y / 2, 0], [shade_x / 2, -shade_y / 2, 0],
                 [shade_x / 2, -shade_y / 2, shade_z]],
                [[shade_x / 2, -shade_y / 2, shade_z], [shade_x / 2, -shade_y / 2, 0], [shade_x / 2, shade_y / 2, 0],
                 [shade_x / 2, shade_y / 2, shade_z]],
                [[shade_x / 2, shade_y / 2, shade_z], [shade_x / 2, shade_y / 2, 0], [-shade_x / 2, shade_y / 2, 0],
                 [-shade_x / 2, shade_y / 2, shade_z]],
                [[-shade_x / 2, shade_y / 2, shade_z], [-shade_x / 2, shade_y / 2, 0], [-shade_x / 2, -shade_y / 2, 0],
                 [-shade_x / 2, -shade_y / 2, shade_z]],
                [[shade_x / 2, shade_y / 2, shade_z], [-shade_x / 2, -shade_y / 2, shade_z],
                 [shade_x / 2, -shade_y / 2, shade_z], [shade_x / 2, shade_y / 2, shade_z]]
            ]
            for n, vg in enumerate(shade_vertex_groups):
                shd = idf.newidfobject("SHADING:BUILDING:DETAILED")
                shd.Name = "shade_surface_{}".format(n)
                shd.Transmittance_Schedule_Name = "shade_schedule_constant"
                for nnn, vgx in enumerate(vg):
                    setattr(shd, "Vertex_{}_Xcoordinate".format(nnn + 1), vgx[0])
                    setattr(shd, "Vertex_{}_Ycoordinate".format(nnn + 1), vgx[1])
                    setattr(shd, "Vertex_{}_Zcoordinate".format(nnn + 1), vgx[2])

        # Set output variables for Eplus run - only top surface of ground considered here
        outputvariable = idf.newidfobject("OUTPUT:VARIABLE")
        outputvariable.Key_Value = "ground_surface_0"
        outputvariable.Variable_Name = "Surface Outside Face Temperature"
        outputvariable.Reporting_Frequency = "hourly"

        # Write Eplus file
        idf.saveas(idf_file)

        # Run Eplus simulation
        cmd = '"{0:}" -a -w "{1:}" -d "{2:}" "{3:}"'.format(eplus.absolute(), epw_file, eplus_output_path, idf_file)
        subprocess.call(cmd, shell=True)

        # Read surface temperature results
        with open(eso_file, "r") as f:
            data = f.read().split("\n")

            # Find key
            for n, i in enumerate(data):
                if i == "End of Data Dictionary":
                    split_part = n

            _vars = [j.split(",")[-1].replace(" !Hourly", "") for j in data[7:split_part]]

            surface_temperature = [float(item) for sublist in
                     [[k.split(",")[1:][0] for k in j[1:]] for j in chunk(data[split_part + 2:-3], n=len(_vars) + 1)]
                     for
                     item in sublist]

        self.surface_temperature = HourlyContinuousCollection(header=Header(Temperature(), unit="C", analysis_period=AnalysisPeriod()), values=surface_temperature)

        print("Ground surface temperature simulation completed")

        return self.surface_temperature


def chunk(enumerable, n=1):
    return [list(enumerable[i:i + n]) for i in range(0, len(enumerable), n)]
