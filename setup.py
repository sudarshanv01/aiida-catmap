from setuptools import setup, find_packages
import json

if __name__ == '__main__':
    setup(
        name='aiida-catmap',
        packages=['aiida_catmap'], 
        entry_points={
            'aiida.calculations':['catmap = aiida_catmap.calculations:CatMAPCalculation'], 
            'aiida.parsers':['catmap = aiida_catmap.parsers:CatMAPParser'],
            }
        )
