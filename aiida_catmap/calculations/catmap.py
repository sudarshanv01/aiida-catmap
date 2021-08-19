"""
Calculations provided by aiida_catmap.
"""
# pylint: disable=line-too-long
from aiida.common import datastructures
from aiida.engine import CalcJob
from aiida.orm import SinglefileData, List, Float, Dict, Str, Int, Bool


class CatMAPCalculation(CalcJob):
    """
    Tools to run CatMAP using AiiDa
    CatMAP is a micro-kinetic modelling package, more information is
    available here https://catmap.readthedocs.io/en/latest/
    """
    _INPUT_FILE_NAME = 'aiida.mkm'

    @classmethod
    def define(cls, spec):
        """Define inputs and outputs of the calculation."""
        # yapf: disable
        super(CatMAPCalculation, cls).define(spec)

        # set default values for AiiDA-CatMAP options
        # Right now the tool allows only serial runs this might change
        spec.inputs['metadata']['options']['resources'].default = {
            'num_machines': 1,
            'num_mpiprocs_per_machine': 1,
                }

        # new ports
        ## INPUTS

        ### Decide if you are doing electrocatalysis or thermal catalysis; not a catmap input
        spec.input('electrocatal', valid_type=Bool, help='If this is an electrocatalysis run, specify here', default=lambda: Bool(True))

        ### Reaction condition keys
        spec.input('energies', valid_type=SinglefileData, help='energies.txt that stores all the energy inputs')
        spec.input('scaler', valid_type=Str, help='Scaler to be used in the Kinetic model', default=lambda: Str('GeneralizedLinearScaler'))
        spec.input('rxn_expressions', valid_type=List, help='Reactions expressions')
        spec.input('surface_names', valid_type=List, help='Surfaces to calculate with energies in energies.txt')
        spec.input('descriptor_names', valid_type=List, help='Descriptors')
        spec.input('descriptor_ranges', valid_type=List, help='List of lists which has the two ranges')
        spec.input('resolution', valid_type=Int, help='Resolution of calculation')
        spec.input('temperature', valid_type=Float, help='temperature to run calculation at')
        spec.input('species_definitions', valid_type=Dict, help='Dict consisting of all species definitions')
        spec.input('gas_thermo_mode', valid_type=Str, help='Gas thermodynamics mode')
        spec.input('adsorbate_thermo_mode', valid_type=Str, help='Adsorbate thermodyamics mode')
        spec.input('scaling_constraint_dict', valid_type=Dict, help='Scaling constraints', required=False)
        spec.input('numerical_solver', valid_type=Str, help='Numerical solver to be used', required=False, default=lambda: Str('coverages'))
        spec.input('decimal_precision', valid_type=Int, help='Decimal precision of code')
        spec.input('tolerance', valid_type=Float, help='Tolerance of calculation')
        spec.input('max_rootfinding_iterations', valid_type=Int, help='Maximum root finding iterations')
        spec.input('max_bisections', valid_type=Int, help='Maximum bisections for root finding algorithm')
        spec.input('mkm_filename', valid_type=Str, required=False, default=lambda: Str(cls._INPUT_FILE_NAME))
        spec.input('data_file', valid_type=Str, required=False, default=lambda: Str('aiida.pickle'))
        spec.input('ideal_gas_params', valid_type=Dict, required=False, help='Ideal gas parameters to inferface with ASE')

        ### Keys for electrochemistry
        spec.input('voltage', valid_type=Float, required=False, help='Potential on an SHE scale')
        spec.input('electrochemical_thermo_mode', valid_type=List, help='Electrochemical thermodyamics mode', required=False)
        spec.input('pH', valid_type=Float, required=False, help='pH')
        spec.input('beta', valid_type=Float, required=False, default=lambda: Float(0.5))
        spec.input('potential_reference_scale', valid_type=Str, required=False, default=lambda: Str('SHE'))
        spec.input('extrapolated_potential', valid_type=Float, required=False, default=lambda: Float(0.0))
        spec.input('voltage_diff_drop', valid_type=Float, required=False, default=lambda: Float(0.0))
        spec.input('sigma_input', valid_type=List, required=False, default=lambda: List(list=['CH', 0]))
        spec.input('Upzc', valid_type=Float, required=False, default=lambda: Float(0.0))

        ## METADATA
        spec.inputs['metadata']['options']['parser_name'].default = 'catmap'
        spec.inputs['metadata']['options']['input_filename'].default = 'mkm_job.py'
        spec.inputs['metadata']['options']['output_filename'].default = 'aiida.out'

        ## OUTPUTS
        spec.output('log', valid_type=SinglefileData, help='Log file from CatMAP')
        spec.output('coverage_map', valid_type=List, help='Coverage Map generated after a completed CatMAP run')
        spec.output('rate_map', valid_type=List, help='Rate Map generated after a completed CatMAP run')
        spec.output('production_rate_map', valid_type=List, help='Production Rate Map generated after a completed CatMAP run')

        spec.exit_code(100, 'ERROR_MISSING_OUTPUT_FILES', message='Calculation did not produce all expected output files.')
        spec.exit_code(500, 'ERROR_NO_PICKLE_FILE', message='No information stored in the pickle file')


    def prepare_for_submission(self, folder):
        """
        Create input files.

        :param folder: an `aiida.common.folders.Folder` where the plugin should temporarily place all files needed by
            the calculation.
        :return: `aiida.common.datastructures.CalcInfo` instance
        """

        # set up the mkm file
        with folder.open(self.inputs.mkm_filename.value, 'w', encoding='utf8') as handle:

            ## Writing the reaction conditions
            handle.write(f"scaler = '{self.inputs.scaler.value}' \n")
            handle.write(f'rxn_expressions = {self.inputs.rxn_expressions.get_list()} \n')
            handle.write(f'surface_names = {self.inputs.surface_names.get_list()} \n')
            handle.write(f'descriptor_names = {self.inputs.descriptor_names.get_list()} \n')
            handle.write(f'descriptor_ranges = {self.inputs.descriptor_ranges.get_list()} \n')
            handle.write(f'resolution = {self.inputs.resolution.value} \n')
            handle.write(f'temperature = {self.inputs.temperature.value} \n')
            handle.write(f'species_definitions = {self.inputs.species_definitions.get_dict()} \n')
            handle.write(f"data_file = '{self.inputs.data_file.value}' \n")
            handle.write(f"input_file = '{self.inputs.energies.filename}' \n")
            handle.write(f"gas_thermo_mode = '{self.inputs.gas_thermo_mode.value}' \n")
            handle.write(f"adsorbate_thermo_mode = '{self.inputs.adsorbate_thermo_mode.value}' \n")
            # handle.write('ideal_gas_params = {d} \n'.format(d=self.inputs.ideal_gas_params.get_dict()))
            handle.write(f'scaling_constraint_dict = {self.inputs.scaling_constraint_dict.get_dict()} \n')

            ## Only related to electrochemistry
            if self.inputs.electrocatal.value == True: #pylint: disable=singleton-comparison
                if self.inputs.scaler.value == 'GeneralizedLinearScaler': #pylint: disable=singleton-comparison
                    handle.write(f'voltage = {self.inputs.voltage.value} \n')
                    handle.write(f'pH = {self.inputs.pH.value} \n')

                elif self.inputs.scaler.value != 'GeneralizedLinearScaler':
                    handle.write(f"potential_reference_scale = '{self.inputs.potential_reference_scale.value}' \n")
                    handle.write(f'extrapolated_potential = {self.inputs.extrapolated_potential.value} \n')
                    handle.write(f'voltage_diff_drop = {self.inputs.voltage_diff_drop.value} \n')
                    handle.write(f'sigma_input = {self.inputs.sigma_input.get_list()} \n')
                    handle.write(f'Upzc = {self.inputs.Upzc.value} \n')

                handle.write(f'beta = {self.inputs.beta.value} \n')
                for val in self.inputs.electrochemical_thermo_mode.get_list():
                    handle.write(f"electrochemical_thermo_mode = '{val}' \n")

            ## Write numerical data last
            handle.write(f'decimal_precision = {self.inputs.decimal_precision.value} \n')
            handle.write(f'tolerance = {self.inputs.tolerance.value} \n')
            handle.write(f'max_rootfinding_iterations = {self.inputs.max_rootfinding_iterations.value} \n')
            handle.write(f'max_bisections = {self.inputs.max_bisections.value} \n')
            handle.write(f"numerical_solver = '{self.inputs.numerical_solver.value}' \n")


        # write the simplest run command
        with folder.open(self.options.input_filename, 'w', encoding='utf8') as handle:
            handle.write('from catmap import ReactionModel \n')
            handle.write(f"mkm_file = '{self.inputs.mkm_filename.value}' \n")
            handle.write('model = ReactionModel(setup_file=mkm_file) \n')
            handle.write("model.output_variables += ['production_rate'] \n")
            handle.write('model.run() \n')

        codeinfo = datastructures.CodeInfo()
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.stdout_name = self.options.output_filename
        codeinfo.stdin_name = self.options.input_filename
        codeinfo.withmpi = self.inputs.metadata.options.withmpi

        # Prepare a `CalcInfo` to be returned to the engine
        calcinfo = datastructures.CalcInfo()
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = [
            (self.inputs.energies.uuid, self.inputs.energies.filename, self.inputs.energies.filename),
        ]
        calcinfo.retrieve_list = [self.metadata.options.output_filename, self.inputs.data_file.value]

        return calcinfo
