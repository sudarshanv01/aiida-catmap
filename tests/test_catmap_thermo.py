""" Tests for aiida-CatMAP calculations
"""
import os
from . import TEST_DIR


def test_process(catmap_code):
    """Test running a calculation
    note this does not test that the expected outputs are created of output parsing"""
    from aiida.plugins import DataFactory, CalculationFactory
    from aiida.engine import run
    from aiida.orm import SinglefileData
    from aiida.orm import SinglefileData, List, Dict, Int, Float, Str, Bool

    energies = SinglefileData(
        file=os.path.join(TEST_DIR, "input_files", 'energies.txt'))

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
        'surface_names':List(list=['Pt', 'Ag', 'Cu','Rh','Pd','Au','Ru','Ni']),
        'descriptor_names':List(list=['O_s','CO_s']),  
        'descriptor_ranges':List(list=[[-1,3],[-0.5,4]]), 
        'resolution':Int(1), 
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
            'options': {
                'max_wallclock_seconds': 120
            },
        },
    }

    computed_result = run(CalculationFactory('catmap'), **inputs)

    ## These two are default outputs - will always be there
    # assert 'coverage_map' in computed_result['retrieved']
    # assert 'rate_map' in computed_result
