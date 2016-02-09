# -*- coding: utf-8 -*-
"""
Servidor
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
from datetime import datetime
#
from db import DB

__name__ = 'servidor'
__author__ = """\n""".join(['Rion Brattig Correia <rionbr@gmail.com>'])
__all__ = ['Servidor']
#
#
#
class Servidor(object):
	"""

	"""
	def __init__(self, verbose=False):
	
		self.url_lista = 'http://www.portaldatransparencia.gov.br/servidores/OrgaoExercicio-ListaServidores.asp?codOrg=%d&Pagina=%d'
		self.url_cargo = 'http://www.portaldatransparencia.gov.br/servidores/OrgaoExercicio-DetalhaServidor.asp?IdServidor=%d&CodOrgao=%d'
		self.url_financeiro = 'http://www.portaldatransparencia.gov.br/servidores/Servidor-DetalhaRemuneracao.asp?Op=2&IdServidor=%d&bInformacaoFinanceira=True&Ano=%s&Mes=%s'
		self.verbose = verbose
		self.session = requests.Session()

	def harvest(self, id_orgao):
		"""

		"""
		#
		# Collect the first page, and identify how many pages there are
		#
		page = self.session.get(self.url_lista % (id_orgao, 1))
		tree = etree.HTML(page.content, etree.HTMLParser(encoding="windows-1252"))
		_, n_pages = tree.xpath('//div[@id="paginacao"]/p[@class="paginaAtual"]')[0].text.split('/')

		if self.verbose:
			print 'Pages found: %d' % (int(n_pages))
		#
		# Loop all Pages to insert information into DB
		#
		for i_page in np.arange(1, int(n_pages)+1):

			if self.verbose:
				print 'Page: %d/%d' % (i_page, int(n_pages))

			if i_page>1:
				page = requests.get(self.url_lista % (id_orgao, i_page))
				tree = etree.HTML(page.content, etree.HTMLParser(encoding="windows-1252"))

			lista = tree.xpath('//div[@id="listagem"]/table')[0]

			items = []
			for i, item in enumerate(lista, start=0):

				if i ==0:
					continue

				cpf, name, orgao = item.xpath('td')

				_id, id_orgao = urlparse.parse_qs(urlparse.urlparse(name[0].attrib['href']).query).values()
				_id, id_orgao = int(_id[0]), int(id_orgao[0])
				name = name[0].text.strip().title()
				cpf = cpf.text.strip()

				items.append( (_id, id_orgao, name, cpf) )

			# To DataFrame
			df = pd.DataFrame(items, columns=['id_servidor','id_orgao','name','cpf'])

			# Insert into MySQL
			status = DB().DataFrameToMySQL(df, table='servidor')
	
	def harvest_cargos(self, id_servidor, id_orgao):
		"""
		STILL NOT 100%, the html page has several problems.
		"""
		page = self.session.get(self.url_cargo % (id_servidor, id_orgao))
		tree = etree.HTML(page.content, etree.HTMLParser(encoding="windows-1252"))
		cargos = tree.xpath('//div[@id="listagemConvenios"]/table/tr/td')
		
		items = []

		for j, item in enumerate(cargos, start=1):

			cargo = None
			funcao = None
			classe = None
			padrao = None
			referencia = None
			nivel = None
			clist = []
			#
			trs = item.xpath('table/tbody/tr')
			
			# This is a blank tr with no information inside
			if len(trs) <=1:
				continue
			

			string = ''
			for z, r_item in enumerate(trs, start=1):
				kv = r_item.xpath('td')

				k = kv[0].text
				try:
					v = kv[1][0].text
				except:
					try:
						v = kv[1].text
					except:
						v = ''

				k = k.replace(unichr(160), '-')
				k = k.replace('- -', '-')
				k = k.strip()
				v = v.replace(unichr(160), '') if v is not None else v
				v = v.strip() if v is not None else ''
				
				if k == u'Cargo Emprego:':
					cargo = v
				if k == u'-Classe:':
					classe = v
				if k == u'-Sigla - Descrição:':
					funcao = v
				if k == u'-Padrão:':
					padrao = v
				if k == u'-Refência:':
					referencia = v
				if k == u'-Nível:':
					nivel = v
				if k == u'Jornada de Trabalho:':
					jornada = v

				string += k + v 
				if z < len(item):
					string += u'|'

				clist.append(string)

			items.append( (id_servidor, cargo, funcao, classe, padrao, referencia, nivel, clist) )

		# To DataFrame
		df = pd.DataFrame(items, columns=['id_servidor','cargo','funcao','classe','padrao','referencia','nivel','data'])
		print df
		# Insert into MySQL
		#status = DB().DataFrameToMySQL(df, table='servidor_cargos')
	

	def harvest_financeiro(self, id_servidor):

		now = datetime.now()
		year, month = now.strftime("%Y-%m").split('-')

		page = self.session.get(self.url_financeiro % (id_servidor, year, month))
		tree = etree.HTML(page.content, etree.HTMLParser(encoding="windows-1252"))

		# Get all the available Year-Month data
		yearmonth = []
		meses = tree.xpath('//div[@id="navegacaomeses"]/a')
		for mes in meses:
			print mes.attrib
			d = urlparse.parse_qs(urlparse.urlparse(mes.attrib['href']).query)
			year = d['Ano'][0]
			month = d['Mes'][0]
			yearmonth.append( (year, month) )

		items = []
		for i, (year, month) in enumerate(yearmonth, start=1):
			
			date = datetime.strptime('%s-%s-05' % (year,month), '%Y-%m-%d')
			#date = '%s-%s-05' % (year,month)
			
			# We already have the first page, remember?
			if i>1:
				page = self.session.get(self.url_financeiro % (id_servidor, year, month))
				tree = etree.HTML(page.content, etree.HTMLParser(encoding="windows-1252"))
			
			financeiro = tree.xpath('//div[@id="listagemConvenios"]/table/tbody/tr[@class="remuneracaodetalhe"]')
		
			basico_bruto = None
			for item in financeiro:
				tds = item.xpath('td')
				if len(tds) == 4:
					print tds[2].text
					if tds[1].text == u'Remuneração básica bruta':
						print 'EYS'
						basico_bruto = tds[2].text
						print '=',basico_bruto
						basico_bruto = float(basico_bruto.replace('.','').replace(',','.'))
					
					print basico_bruto
					items.append( (id_servidor, date, basico_bruto) )
					break

		# To DataFrame
		df = pd.DataFrame(items, columns=['id_servidor','date','basico_bruto'])

		# Insert into MySQL
		status = DB().DataFrameToMySQL(df, table='servidor_remuneracao')

	def getDFServidor(self, id_orgao=None):
		"""

		"""
		sqlWhere = ('WHERE id_orgao = %d' % id_orgao) if id_orgao is not None else ''
		sql = "SELECT * from servidor %s" % (sqlWhere) 
		return DB().MySQLToDataFrame(sql, index_col=['id_servidor','id_orgao'])

#
#
#
if __name__ != '__main__':
	
	#
	# Harvest List of Servidores
	#	
	"""
	from orgao import Orgao
	dfO = Orgao().getDF()

	for id_orgao, dft in dfO.iterrows():

		ans = raw_input(u'Harvest `%s`? [y/n]:' % dft['name'])
		if ans == 'y':
			s = Servidor(verbose=True)
			s.harvest(id_orgao=id_orgao)	
		else:
			print 'Skipping Orgao'
	"""
	#
	# Harvest Cargos for Servidores
	#
	"""
	s = Servidor(verbose=True)
	dfS = s.getDFServidor(id_orgao)
	for (id_servidor, id_orgao), dft in dfS.iterrows():
		s.harvest_cargos(id_servidor=id_servidor, id_orgao=id_orgao)
	"""

	Servidor().harvest_cargos(id_servidor=1000770, id_orgao=15000)


	#
	# Harvest Financeiro for Servidores
	#
	"""
	from orgao import Orgao
	from servidor import Servidor

	dfO = Orgao().getDF()

	for id_orgao, dfot in dfO.iterrows():
		ans = raw_input(u'Harvest financials from `%s` servidores? [y/n]:' % dft['name'])
		if ans == 'y':
			dfS = Servidor().getDFServidor()
			for id_servidor, dfst in dfS.iterrows():
				Servidor(verbose=True).harvest_financeiro(id_servidor=id_servidor)
		else:
			print 'Skipping Orgao'
	"""