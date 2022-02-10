#!/usr/bin/env python3

import argparse
import io
import logging
import os
import pkg_resources
import tarfile
import urllib.request


def main():

	parser = argparse.ArgumentParser(description='Update the taxonomy lineage database.')

	parser.add_argument('--url', default='https://ftp.ncbi.nih.gov/pub/taxonomy/taxdump.tar.gz', help='The URL to load the taxonomy lineage database from. Default is %(default)s')

	args = parser.parse_args()

	url = args.url

	ti_file = discover_database()

	print('Download the taxonomy dump from NCBI')
	print(url)
	response = urllib.request.urlopen(url)
	compressed = io.BytesIO(response.read())

	# Open as tar object (with gz compression)
	tar = tarfile.open(fileobj=compressed, mode='r:gz')

	# Extract names.dmp and nodes.dmp
	names = tar.extractfile('names.dmp')
	nodes = tar.extractfile('nodes.dmp')

	lineage_info = {}  # data[taxid] = [depth, parent, rank, name]

	print('Reading names.dmp')
	for line in names:
		lline = line.decode('utf8').split('\t|\t')
		# taxid, name, uniqueName, nameClass
		if lline[3] == 'scientific name\t|\n':
			lineage_info[lline[0]] = ['@', '@', '@', lline[1]]

	print('Reading nodes.dmp')
	for line in nodes:
		lline = line.decode('utf8').split('\t|\t')
		# taxid, parentTaxid, rank, *others
		lineage_info[lline[0]][1] = lline[1]
		lineage_info[lline[0]][2] = lline[2]

	print('Writing taxinfo')

	with open(ti_file, 'w') as out:
		for taxid in sorted(data.keys()):
			# TaxID, Level, Parent, Rank, Name
			level = 0
			tid = taxid
			while tid != '1':
				tid = data[tid][1]
				level += 1
			data[taxid][0] = str(level)
			out.write('{}\t{}\n'.format(taxid, '\t'.join(data[taxid])))


def discover_database(self):
	'''
	Test if the path to the database is known and if the database exists and is writable.
	'''

	try:
		path = os.environ["TFPATH"]
	except KeyError:
		path = os.path.dirname(pkg_resources.get_resource_filename('taxfinder', 'db/taxinfo'))

	ti_file = os.path.join(path, 'taxinfo')

	try:
		open(ti_file, 'a')
	except IOError:
		logging.critical(f'The taxonomy database {ti_file} is not readable/writable. You can define your own path by setting the environment variable `TFPATH` to the path you want.')
		sys.exit(1)

	return ti_file