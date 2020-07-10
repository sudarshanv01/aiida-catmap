"""
Calculations provided by aiida_catmap.

Register calculations via the "aiida.calculations" entry point in setup.json.
"""
from aiida.common import datastructures
from aiida.engine import CalcJob
from aiida.orm import SinglefileData
from aiida.plugins import DataFactory


class CatMAPCalculation(CalcJob):
    """
    AiiDA plugin for running Descriptor based Micro-kinetic modelling 
    code CatMAP. 

    :TODO: Implement more than just SingeFileData related tags
    """

    @classmethod
    def define(cls, spec):
        """Define inputs and outputs of the calculation."""
        # yapf: disable
        super(CatMAPCalculation, cls).define(spec)

        # set default values for AiiDA-CatMAP options
        spec.inputs['metadata']['options']['resources'].default = {
                'num_machines': 1,
                'num_mpiprocs_per_machine': 1,
                }

        # new ports
        ## INPUTS
        spec.input('run_file', valid_type=SinglefileData, help='File with instructions on how to run')
        spec.input('mkm_file', valid_type=SinglefileData, help='.mkm file that has all the inputs to CatMAP')
        spec.input('energies', valid_type=SinglefileData, help='energies.txt that stores all the energy inputs')
        ## METADATA
        spec.inputs['metadata']['options']['parser_name'].default = 'catmap'
        spec.inputs['metadata']['options']['input_filename'].default = 'run_catmap.py'
        spec.inputs['metadata']['options']['output_filename'].default = 'aiida.out'
        ## OUTPUTS
        spec.output('log', valid_type=SinglefileData, help='Log file from CatMAP')

        spec.exit_code(100, 'ERROR_MISSING_OUTPUT_FILES', message='Calculation did not produce all expected output files.')


    def prepare_for_submission(self, folder):
        """
        Create input files.

        :param folder: an `aiida.common.folders.Folder` where the plugin should temporarily place all files needed by
            the calculation.
        :return: `aiida.common.datastructures.CalcInfo` instance
        """

        codeinfo = datastructures.CodeInfo()
        
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.stdout_name = self.metadata.options.output_filename
        codeinfo.withmpi = self.inputs.metadata.options.withmpi

        # Prepare a `CalcInfo` to be returned to the engine
        calcinfo = datastructures.CalcInfo()
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = [
            (self.inputs.mkm_file.uuid, self.inputs.mkm_file.filename, self.inputs.mkm_file.filename),
            (self.inputs.energies.uuid, self.inputs.energies.filename, self.inputs.energies.filename),
            (self.inputs.run_file.uuid, self.inputs.run_file.filename, self.inputs.run_file.filename),
        ]
        calcinfo.retrieve_list = [self.metadata.options.output_filename]

        return calcinfo
