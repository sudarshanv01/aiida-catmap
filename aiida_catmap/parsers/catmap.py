"""
Parsers provided by aiida_catmap.

Register parsers via the "aiida.parsers" entry point in setup.json.
"""
import pickle  # pylint: disable=syntax-error
from aiida.parsers.parser import Parser


class CatMAPParser(Parser):
    """
    Parser class for parsing output of calculation.
    """
    def __init__(self, node):  # pylint: disable=useless-super-delegation
        """
        Initialize Parser instance

        :param node: ProcessNode of calculation
        :param type node: :class:`aiida.orm.ProcessNode`
        """
        super(CatMAPParser, self).__init__(node)

    def parse(self, **kwargs):  # pylint: disable=too-many-locals, inconsistent-return-statements
        """
        Parse outputs, store results in database.
        :returns: an exit code, if parsing fails (or nothing if parsing succeeds)
        """
        from aiida.orm import SinglefileData, List

        output_filename = self.node.get_option('output_filename')
        pickle_filename = self.node.inputs.data_file.value

        # Check that folder content is as expected
        files_retrieved = self.retrieved.list_object_names()
        files_expected = [output_filename, pickle_filename]
        # Note: set(A) <= set(B) checks whether A is a subset of B
        if not set(files_expected) <= set(files_retrieved):
            self.logger.error(
                f"Found files '{files_retrieved}', expected to find '{files_expected}'"
            )
            return self.exit_codes.ERROR_MISSING_OUTPUT_FILES

        # add output file
        self.logger.info(f"Parsing '{output_filename}'")
        with self.retrieved.open(output_filename, 'rb') as handle:
            output_node = SinglefileData(file=handle)
        self.out('log', output_node)

        # Parsing the pickle file
        self.logger.info(f"Parsing '{pickle_filename}'")
        # pickledata = pickle.load(self.retrieved.open(pickle_filename, 'rb'))
        with self.retrieved.open(pickle_filename, 'rb') as handle:
            pickledata = pickle.load(handle)
        try:
            coverage_data = [[a[0], list(map(float, a[1]))]
                             for a in pickledata['coverage_map']]
        except KeyError:
            return self.exit_codes.ERROR_NO_PICKLE_FILE

        ## Choose not to change the mpmath format
        ## the downside is that mpmath must then be present
        ## wherever this is being parsed
        rate_data = [[a[0], list(map(float, a[1]))]
                     for a in pickledata['rate_map']]
        production_data = [[a[0], list(map(float, a[1]))]
                           for a in pickledata['production_rate_map']]

        coverage_map = List(list=coverage_data)
        rate_map = List(list=rate_data)
        production_map = List(list=production_data)

        ## The three main outputs
        ## The solution to the kinetic model - coverages
        ## The rate and the production rate also provided
        self.out('coverage_map', coverage_map)
        self.out('rate_map', rate_map)
        self.out('production_rate_map', production_map)
