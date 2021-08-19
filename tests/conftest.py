"""pytest fixtures for simplified testing."""
from __future__ import absolute_import
import pytest  # pylint: disable=import-error
pytest_plugins = ['aiida.manage.tests.pytest_fixtures']  # pylint: disable=invalid-name


@pytest.fixture
def fixture_localhost(aiida_localhost):
    """Return a localhost ``Computer``."""
    localhost = aiida_localhost
    localhost.set_default_mpiprocs_per_machine(1)
    return localhost


@pytest.fixture
def generate_parser():
    """Fixture to load a parser class for testing parsers."""
    def _generate_parser(entry_point_name):
        """Fixture to load a parser class for testing parsers.
        :param entry_point_name: entry point name of the parser class
        :return: the `Parser` sub class
        """
        from aiida.plugins import ParserFactory
        return ParserFactory(entry_point_name)

    return _generate_parser


@pytest.fixture(scope='function')
def fixture_sandbox():
    """Return a ``SandboxFolder``."""
    from aiida.common.folders import SandboxFolder
    with SandboxFolder() as folder:
        yield folder


@pytest.fixture
def generate_code(fixture_localhost):  # pylint: disable=redefined-outer-name
    """Return a ``Code`` instance configured for testing."""
    def _generate_code(entry_point_name):
        from aiida.common import exceptions
        from aiida.orm import Code

        label = f'test.{entry_point_name}'

        try:
            return Code.objects.get(label=label)  # pylint: disable=no-member
        except exceptions.NotExistent:
            return Code(
                label=label,
                input_plugin_name=entry_point_name,
                remote_computer_exec=[fixture_localhost, '/bin/true'],
            )

    return _generate_code


@pytest.fixture
def generate_calc_job():
    """Fixture to construct a new ``CalcJob`` instance and call ``prepare_for_submission``.
    The fixture will return the ``CalcInfo`` returned by
    ``prepare_for_submission`` and the temporary folder that was
    passed to it, into which the raw input files will have been written.
    """
    def _generate_calc_job(folder, entry_point_name, inputs=None):
        """Fixture to generate a mock ``CalcInfo`` for testing calculation jobs."""
        from aiida.engine.utils import instantiate_process
        from aiida.manage.manager import get_manager
        from aiida.plugins import CalculationFactory

        manager = get_manager()
        runner = manager.get_runner()

        process_class = CalculationFactory(entry_point_name)
        process = instantiate_process(runner, process_class, **inputs)

        calc_info = process.prepare_for_submission(folder)

        return calc_info

    return _generate_calc_job


@pytest.fixture
def generate_calc_job_node():
    """Fixture to generate a mock `CalcJobNode` for testing parsers."""
    from aiida import orm
    import collections  # pylint: disable=syntax-error

    def flatten_inputs(inputs, prefix=''):
        """This function follows roughly the same logic
        as `aiida.engine.processes.process::Process._flatten_inputs`."""
        flat_inputs = []
        for key, value in inputs.items():
            if isinstance(value, collections.abc.Mapping):
                flat_inputs.extend(
                    flatten_inputs(value, prefix=prefix + key + '__'))
            else:
                flat_inputs.append((prefix + key, value))
        return flat_inputs

    def _generate_calc_job_node(entry_point_name,
                                computer,
                                test_name=None,
                                inputs=None,
                                attributes=None):
        """Fixture to generate a mock `CalcJobNode` for testing parsers.
        :param entry_point_name: entry point name of the calculation class
        :param computer: a `Computer` instance
        :param test_name: relative path of directory
        :param inputs: any optional nodes to add as input links to the corrent CalcJobNode
        :param attributes: any optional attributes to set on the node
        :return: `CalcJobNode` instance with an attached `FolderData` as the `retrieved` node
        """
        # pylint: disable=too-many-locals
        import os
        from aiida.common import LinkType
        from aiida.plugins.entry_point import format_entry_point_string

        entry_point = format_entry_point_string('aiida.calculations',
                                                entry_point_name)

        node = orm.CalcJobNode(computer=computer, process_type=entry_point)
        node.set_option('resources', {
            'num_machines': 1,
            'num_mpiprocs_per_machine': 1
        })
        node.set_option('max_wallclock_seconds', 1800)

        if attributes:
            node.set_attribute_many(attributes)

        if inputs:
            metadata = inputs.pop('metadata', {})
            options = metadata.get('options', {})

            for name, option in options.items():
                node.set_option(name, option)

            for link_label, input_node in flatten_inputs(inputs):
                input_node.store()
                node.add_incoming(input_node,
                                  link_type=LinkType.INPUT_CALC,
                                  link_label=link_label)

        node.store()

        if test_name is not None:
            basepath = os.path.dirname(os.path.abspath(__file__))
            filepath = os.path.join(basepath, 'parsers', 'fixtures', 'catmap',
                                    test_name)

            retrieved = orm.FolderData()
            retrieved.put_object_from_tree(filepath)
            retrieved.add_incoming(node,
                                   link_type=LinkType.CREATE,
                                   link_label='retrieved')
            retrieved.store()

            remote_folder = orm.RemoteData(computer=computer,
                                           remote_path='/tmp')
            remote_folder.add_incoming(node,
                                       link_type=LinkType.CREATE,
                                       link_label='remote_folder')
            remote_folder.store()

        return node

    return _generate_calc_job_node


@pytest.fixture
def generate_inputs_catmap(generate_code, generate_energy_file):  # pylint: disable=redefined-outer-name
    """Generate inputs for an ``CatMAPCalculation``."""
    from aiida.orm import List, Int, Float, Str, Bool, Dict

    def _generate_inputs_catmap():

        species_definitions = {}
        species_definitions['CO_g'] = {
            'pressure': 1.
        }  #define the gas pressures
        species_definitions['O2_g'] = {'pressure': 1. / 3.}
        species_definitions['CO2_g'] = {'pressure': 0}
        species_definitions['s'] = {
            'site_names': ['111'],
            'total': 1
        }  #define the site

        scaling_constraint_dict = {
            'O_s': ['+', 0, None],
            'CO_s': [0, '+', None],
            'O-CO_s': 'initial_state',
            'O-O_s': 'final_state',
        }
        inputs = {
            'electrocatal':
            Bool(False),
            'energies':
            generate_energy_file(),
            'code':
            generate_code('catmap'),
            'rxn_expressions':
            List(list=[
                '*_s + CO_g -> CO*',
                '2*_s + O2_g <-> O-O* + *_s -> 2O*',
                'CO* +  O* <-> O-CO* + * -> CO2_g + 2*',
            ]),
            'surface_names':
            List(list=['Pt', 'Ag', 'Cu', 'Rh', 'Pd', 'Au', 'Ru', 'Ni']),
            'descriptor_names':
            List(list=['O_s', 'CO_s']),
            'descriptor_ranges':
            List(list=[[-1, 3], [-0.5, 4]]),
            'resolution':
            Int(1),
            'temperature':
            Float(500),
            'species_definitions':
            Dict(dict=species_definitions),
            'gas_thermo_mode':
            Str('shomate_gas'),
            'adsorbate_thermo_mode':
            Str('frozen_adsorbate'),
            'scaling_constraint_dict':
            Dict(dict=scaling_constraint_dict),
            'decimal_precision':
            Int(150),
            'numerical_solver':
            Str('coverages'),
            'tolerance':
            Float(1e-20),
            'max_rootfinding_iterations':
            Int(100),
            'max_bisections':
            Int(3),
            'metadata': {
                'description':
                "Test job submission with the aiida_catmap plugin",
                'options': {
                    'max_wallclock_seconds': 120
                },
            },
        }

        return inputs

    return _generate_inputs_catmap


@pytest.fixture
def generate_energy_file():
    """Return a `SingefileData` node."""
    from pathlib import Path
    from aiida.plugins import DataFactory

    def _generate_energy_file():
        """Return a `KpointsData` with a mesh of npoints in each direction."""

        SinglefileData = DataFactory('singlefile')  # pylint: disable=invalid-name
        path_to_file = Path(__file__).parent / 'input_files' / 'energies.txt'
        single_file = SinglefileData(path_to_file)

        return single_file

    return _generate_energy_file
