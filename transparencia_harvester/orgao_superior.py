# -*- coding: utf-8 -*-
"""
Orgão Superior
===================


"""
#    Copyright (C) 2016 by
#    Rion Brattig Correia <rionbr@gmail.com>
#    All rights reserved.
#    MIT license.

import numpy as np
import pandas as pd
import requests
from lxml import etree
import urlparse
#
from db import DB

__name__ = 'harvest_orgao_superior'
__author__ = """\n""".join(['Rion Brattig Correia <rionbr@gmail.com>'])
__all__ = ['OrgaoSuperior']
#
#
#
class OrgaoSuperior(object):
	"""

	"""
	def __init__(self, verbose=False):
	
		self.url = 'http://www.portaldatransparencia.gov.br/servidores/OrgaoExercicio-ListaOrgaosSuperiores.asp?bogus=1&Pagina=%d'
		self.verbose = verbose

	def harvest(self):
		"""

		"""
		#
		# Collect the first page, and identify how many pages there are
		#
		page = requests.get(self.url)
		tree = etree.HTML(page.content, etree.HTMLParser(encoding="windows-1252"))
		_, n_pages = tree.xpath('//div[@id="paginacao"]/p[@class="paginaAtual"]')[0].text.split('/')
		#
		if self.verbose:
			print 'Pages found: %d' % (int(n_pages))
		#
		# Loop Pagination
		#
		for i_page in np.arange(1, int(n_pages)+1):

			if self.verbose:
				print 'Page: %d/%d' % (i_page, int(n_pages))

			if i_page>1:
				page = requests.get(self.url % (i_page))
				tree = etree.HTML(page.content, etree.HTMLParser(encoding="windows-1252"))

			lista = tree.xpath('//div[@id="listagem"]/table')[0]
			
			items = []
			for i, item in enumerate(lista, start=0):
				
				if i ==0:
					continue
				
				_id, name, n_servidores = item.xpath('td')

				items.append( (_id.text, name[0].text.title(), int(n_servidores.text)) )
			
			# To DataFrame
			df = pd.DataFrame(items, columns=['id_orgao_superior','name','n_servidores'])
			
			# Insert into MySQL
			status = DB().DataFrameToMySQL(df, table='orgao_superior')
#
#
#
if __name__ == '__main__':
	
	OrgaoSuperior(verbose=True).harvest()



