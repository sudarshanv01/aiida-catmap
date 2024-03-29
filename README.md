# aiida-catmap

AiiDA plugin which interfaces with the descriptor based analysis code CatMAP. 

For more information about CatMAP itself visit: https://catmap.readthedocs.io/en/latest/


## Features
Allows running of CatMAP through the AiiDA interface, so far only the following have been implemented

- CatMAPCalculation: Runs CatMAP on any configured computer, stores coverages, rates as output nodes

Note:

As of now, the input.txt files (containing DFT computed energies) are passed as SinglefileData, this will change soon. 
Inputs to create the run files are passed directly

## Installation

```shell
pip install aiida-catmap
verdi quicksetup  # better to set up a new profile
verdi plugin list aiida.calculations  # should now show your calclulation plugins
```

## Usage

Here goes a complete example of how to submit a test calculation using this plugin.

A quick demo of how to submit a calculation:
```shell
verdi daemon start     # make sure the daemon is running
cd examples
./example_01.py        # run test calculation
verdi process list -a  # check record of calculation
```


## License

MIT


## Contact

vijays@fysik.dtu.dk

