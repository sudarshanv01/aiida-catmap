"""Tests for aiida-catmap."""
from aiida.common import datastructures
from aiida_catmap.calculations.catmap import CatMAPCalculation


def test_default(fixture_sandbox, generate_calc_job, generate_inputs_catmap,
                 file_regression):
    """Test a default ``CatMAPCalculation``."""
    entry_point_name = 'catmap'
    inputs = generate_inputs_catmap()

    calc_info = generate_calc_job(fixture_sandbox, entry_point_name, inputs)

    assert isinstance(calc_info, datastructures.CalcInfo)
    assert isinstance(calc_info.codes_info[0], datastructures.CodeInfo)

    with fixture_sandbox.open(CatMAPCalculation._INPUT_FILE_NAME) as handle:  # pylint: disable=protected-access
        input_written = handle.read()

    # Checks on the files written to the sandbox folder as raw input
    file_regression.check(input_written, encoding='utf-8', extension='.in')
