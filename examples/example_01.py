"""Run a test calculation on localhost.

Usage: ./example_01.py
"""
from os import path
from aiida_catmap import helpers
from aiida import cmdline, engine
from aiida.plugins import DataFactory, CalculationFactory
import click
from aiida.orm import SinglefileData, List, Dict, Int, Float, Str, Bool

INPUT_DIR = path.join(path.dirname(path.realpath(__file__)), 'input_files')


def test_run(catmap_code):
    """Run a calculation on the localhost computer.

    Uses test helpers to create AiiDA Code on the fly.
    """
    if not catmap_code:
        # get code
        computer = helpers.get_computer()
        catmap_code = helpers.get_code(entry_point='catmap', computer=computer)

    # Prepare input parameters

    SinglefileData = DataFactory('singlefile')
    energies = SinglefileData(
        file=path.join(INPUT_DIR, 'energies.txt'))

    species_definitions = {}
    species_definitions['CO_g'] = {'pressure':1.} #define the gas pressures
    species_definitions['O2_g'] = {'pressure':1./3.}
    species_definitions['CO2_g'] = {'pressure':0}
    species_definitions['s'] = {'site_names': ['111'], 'total':1} #define the site

    ## Make sure scaling has the "right" coefficients
    scaling_constraint_dict = {
                           'O_s':['+',0,None],
                           'CO_s':[0,'+',None],
                           'O-CO_s':'initial_state',
                           'O-O_s':'final_state',
                           }

    # set up calculation
    inputs = {
        'electrocatal': Bool(False), # Thermal catalysis run
        'energies':energies, # File with all energies
        'code': catmap_code, # Code to run with
        'rxn_expressions':List(list=[
                            '*_s + CO_g -> CO*',
                            '2*_s + O2_g <-> O-O* + *_s -> 2O*',
                            'CO* +  O* <-> O-CO* + * -> CO2_g + 2*',
                                ]), # list of reactions
        # list of surfaces
        'surface_names':List(list=['Pt', 'Ag', 'Cu','Rh','Pd','Au','Ru','Ni']),
        'descriptor_names':List(list=['O_s','CO_s']),  
        'descriptor_ranges':List(list=[[-1,3],[-0.5,4]]), 
        'resolution':Int(30), 
        'temperature':Float(500), 
        'species_definitions':Dict(dict=species_definitions), 
        'gas_thermo_mode':Str('shomate_gas'), 
        'adsorbate_thermo_mode':Str('frozen_adsorbate'), 
        'scaling_constraint_dict':Dict(dict=scaling_constraint_dict), 
        'decimal_precision':Int(150), 
        'numerical_solver':Str('coverages'),
        'tolerance':Float(1e-20), 
        'max_rootfinding_iterations':Int(100), 
        'max_bisections':Int(3), 
        'metadata': {
            'description': "Test job submission with the aiida_catmap plugin",
        },
    }

    from aiida.engine import submit
    future = submit(CalculationFactory('catmap'), **inputs)
    # result = engine.run(CalculationFactory('catmap'), **inputs)
    # computed_result = result['log'].get_content()


@click.command()
@cmdline.utils.decorators.with_dbenv()
@cmdline.params.options.CODE()
def cli(code):
    """Run example.

    Example usage: $ ./example_01.py --code diff@localhost

    Alternative (creates diff@localhost-test code): $ ./example_01.py

    Help: $ ./example_01.py --help
    """
    test_run(code)


if __name__ == '__main__':
    cli()  # pylint: disable=no-value-for-parameter
