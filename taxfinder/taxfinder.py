#!/usr/bin/env python3

'''
This is the taxfinder module. Import TaxFinder from this module and
instanciate it to use its functions (instanciating is necessary for
caching).
'''

import logging
import os
import pickle
import sys

import pkg_resources


class TaxFinder():
	'''
	The TaxFinder class.
	'''

	def __init__(self):
		'''
		Initialize the TaxFinder class.
		'''

		ti_file, ti_pickle = self._discover_databases()

		#LEG self.acc2taxid = open(self._getFN('acc2taxid'), 'rb')
		#LEG with open(self._getFN('numLines')) as f:
		#LEG 	self.numLines = int(f.read().rstrip())

		try:
			# test if the pickled file is newer
			if os.path.getmtime(ti_pickle) > os.path.getmtime(ti_file):
				self.taxdb = pickle.load(open(ti_pickle, 'rb'))
			else:
				raise IOError
		except IOError:
			self.taxdb = {}
			with open(ti_file) as namefile:
				for line in namefile:
					# TaxID, Level, Parent, Rank, Name
					lline = line.split('\t')
					self.taxdb[int(lline[0])] = {
						'level': int(lline[1]),
						'parent': int(lline[2]),
						'rank': lline[3],
						'name': lline[4].rstrip(),
					}

			pickle.dump(self.taxdb, open(ti_pickle, 'wb'))

		self.lineage_cache = {}
		self.fast_lineage_cache = {}
		self.taxid_cache = {}


#	def _getFN(self, fn):
#		''' Gets absolute path for a given file that is in the same directory as this script '''
#
#		return os.path.join(self.path, fn)


	def _discover_databases(self):
		'''
		Test if the path to the database is known and if the database
		exists and is readable/writable.
		'''

		try:
			path = os.environ["TFPATH"]
		except KeyError:
			path = os.path.dirname(pkg_resources.resource_filename('taxfinder', 'db/taxinfo'))

		ti_file = os.path.join(path, 'taxinfo')
		ti_pickle = os.path.join(path, 'taxinfo.p')

		try:
			open(ti_pickle, 'ab')
		except IOError:
			logging.critical(f'The taxonomy database {ti_pickle} is not '
			'readable/writable. You can define your own path by setting '
			'the environment variable `TFPATH` to the path you want.')
			sys.exit(1)

		try:
			open(ti_file)
		except IOError:
			logging.critical(f'The taxonomy database {ti_file} is not '
			'readable. You can define your own path by setting the '
			'environment variable `TFPATH` to the path you want. You then '
			'have to run `taxfinder_update` from your command line.')
			sys.exit(1)

		if os.path.getsize(ti_file) == 0:
			logging.critical('Please run `taxfinder_update` from your '
			'command line to download and initialize the taxonomy database.')
			sys.exit(1)

		return ti_file, ti_pickle


#	def get_taxid(self, acc):
#		''' Finds the NCBI taxonomy id given an accession id '''
#
#		# Accessions are always uppercase and we only consider the accession without the version part
#		acc = acc.split('.')[0].upper()
#
#		# If we already looked for the accesion, get it from the cache
#		if acc in self.taxid_cache:
#			return self.taxid_cache[acc]
#
#		lo = 0
#		hi = self.numLines
#		x = acc.encode('utf-8')	# Turns the accession id into a bytestring
#
#		# Simple binary search in the sorted file with constant line length
#		while lo < hi:
#			mid = (lo + hi) >> 1
#			self.acc2taxid.seek(mid*20)
#			a = self.acc2taxid.read(12)
#			if x <= a:
#				hi = mid
#			else:
#				lo = mid + 1
#
#		self.acc2taxid.seek(lo*20)
#		rawread = self.acc2taxid.read(19).decode('utf-8')
#		testacc = rawread[:12].rstrip()
#
#		if testacc != acc:
#			taxid = 1
#		else:
#			taxid = int(rawread[12:].rstrip())
#
#		self.taxid_cache[acc] = taxid
#
#		return taxid

	def get_name_from_id(self, taxid):
		''' Returns the taxonomic name of the given taxid '''

		return self.taxdb[int(taxid)]['name']


	def get_tax_info(self, taxid):
		'''
		Get taxonomic information for the given taxid.
		:returns: {'taxid': int, 'level': int, 'parent': int, 'rank': str, 'name': str}
		'''

		taxid = int(taxid)

		try:
			taxinfo = self.taxdb[taxid]
			taxinfo['taxid'] = taxid
		except KeyError:
			#print('Taxid not found:', taxid)
			taxinfo = {'taxid': 1, 'level': 0, 'parent': 0, 'rank': 'no rank', 'name': 'unclassified'}

		return taxinfo


#	def getInfoFromHitDef(self, hitid, hitdef):
#		'''
#		Get all taxonomy information from a hit id and hit definition
#		(may include several species)
#		:returns: [{'taxid': int, 'level': int, 'parent': int, 'rank': str,
#			'name': str, 'acc': str, 'protname': str}, ...]
#		'''
#
#		hit = hitid + hitdef
#		reResults = re.findall(r'gi\|[0-9]+\|[^\|]+\|([^\|]+)\|([^>]+)', hit)
#
#		if not reResults:
#			reResults = re.findall(r'[a-z]+\|([^\|]+)\|([^>]+)', hit)
#
#		results = []
#
#		for r in reResults:
#			acc = r[0].strip()
#			protname = r[1].strip()
#
#			if '[' in protname:
#				protname = protname.split('[')[0].rstrip()
#
#			res = self.get_tax_info(self.get_taxid(acc))
#			res['acc'] = acc
#			res['protname'] = protname
#
#			results.append(res)
#
#		return results


	def get_species_from_subspecies(self, taxid):
		'''
		Given the taxid of a subspecies, returns the species or raises a
		ValueError if no species could be found.
		'''

		lineage = self.get_lineage_fast(int(taxid))
		for tid in lineage[::-1]:
			if self.get_tax_info(tid)['rank'] == 'species':
				return tid

		raise ValueError(f'No species found for {taxid}')


	def get_lowest_reasonable_taxon(self, taxid):
		'''
		Given a taxid, returns the taxid the closest species or higher
		level (that is not `no rank`) that does not contain 'sp.' in its
		name. Raises a ValueError if no "reasonable taxon" could be found.
		'''

		notok = {'no rank', 'subspecies', 'forma', 'varietas'}
		lineage = self.get_lineage_fast(int(taxid))
		for tid in lineage[::-1]:
			info = self.get_tax_info(tid)
			rank = info['rank']
			if rank not in notok and 'sp.' not in info['name']:
				return tid

		raise ValueError(f'No reasonable taxon found for {taxid}')


	def get_lineage(self, taxid, display = 'name'):
		'''
		Given a taxid, returns the lineage up to `root` as tuple. `display`
		configures how the lineage should be shown. If `display` is 'name',
		the taxonomic name will be used. If it is 'taxid', the taxid will
		be used. If it is anything else, name^taxid will be used.

		This method uses caching. If the lineage for a taxid was already
		found before, it will return that lineage in the `display` mode
		used in the first search, ignoring the current `display` value.

		If the taxid could not be found, an empty tuple will be returned.
		'''

		def reformat(lineage, display):
			if display == 'taxid':
				return tuple(int(l[0]) for l in lineage)
			if display == 'name':
				return tuple(l[1] for l in lineage)
			return tuple(l[1]+'^'+l[0] for l in lineage)


		taxid = int(taxid)

		if taxid in self.lineage_cache:
			return reformat(self.lineage_cache[taxid], display)

		orig_taxid = taxid
		lineage = []

		while taxid != 1:
			try:
				current = self.taxdb[taxid]
			except KeyError:
				self.lineage_cache[orig_taxid] = tuple()
				return tuple()
			lineage.append((str(taxid), current['name']))
			taxid = current['parent']

		lineage.append(('1', 'root'))

		lin = tuple(lineage[::-1])

		self.lineage_cache[orig_taxid] = lin

		return reformat(lin, display)


	def get_lineage_fast(self, taxid):
		'''
		Given a taxid, returns the lineage up to `root` as list. All elements will be taxids.
		This method is faster than `get_lineage`, so use this when you need many lineages.
		If the taxid could not be found, an empty tuple will be returned.
		'''

		orig_taxid = taxid

		if taxid in self.fast_lineage_cache:
			return self.fast_lineage_cache[taxid]

		lineage = []

		while taxid != 1:
			try:
				tax = self.taxdb[taxid]
			except KeyError:
				self.fast_lineage_cache[orig_taxid] = tuple()
				return tuple()
			lineage.append(taxid)
			taxid = tax['parent']

		lineage.append(1)

		lin = tuple(lineage[::-1])

		self.fast_lineage_cache[orig_taxid] = lin

		return lin
