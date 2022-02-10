#!/usr/bin/env python3

import re
import setuptools

long_description = open('README.md').read()

version = re.search(r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                    open('taxfinder/__init__.py').read()).group(1)

setuptools.setup(
    name='Taxfinder',
    version=version,
    author='Mathias Bockwoldt',
    author_email='mathias.bockwoldt@gmail.com',
    description='Helper function to work with NCBI taxonomy ids',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/MolecularBioinformatics/taxfinder',
    packages=setuptools.find_packages(),
	package_data={'taxfinder': ['db/*']},
    entry_points={'console_scripts': [
                                    'taxfinder_update = taxfinder.update:main'
                                    ]},
    classifiers=[
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
    ],
    python_requires='>=3.6',
)
