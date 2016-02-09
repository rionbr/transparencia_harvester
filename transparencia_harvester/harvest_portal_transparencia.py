# coding=utf-8
## Attempt to harvest the Portal da Transparencia do Brasil



import numpy as np
import pandas as pd


from lxml import html, etree
import requests
import urlparse
import os.path
import csv

#
# SQL Create Tables
#



#
# Loop all Universities, Harvest all Servidores
#
s_csv_file = 'data/harvest_servidores.csv'
if not os.path.isfile(s_csv_file):
	print 'Status: No CSV File found. Starting from beginning'
	dfS = pd.DataFrame(columns=['sid','university','name','cpf','basico_bruto','data'])
else:
	print 'Status: CSV File Found. Restarting Harvest'
	dfS = pd.read_csv(s_csv_file, encoding='utf-8', index_col=0, dtype={'sid':np.int64,'uid':np.int64})


def dfS_save(data):
	global s_csv_file
	global dfS
	#	
	dft = pd.DataFrame(data, columns=['sid','uid','university','name','cpf', 'orgao','basico_bruto','data'])
	dft.set_index('sid', inplace=True)
	dfS = dfS.append(dft, ignore_index=False)
	dfS.to_csv(s_csv_file,
		columns=['uid','university','name','cpf', 'orgao','basico_bruto','data'],
		index_label='sid',
		dtype={'uid':np.int64,'sid':np.int64},
		encoding='utf-8')
	

print '--- Harvesting Servidores ---'

#
# Loop through all universities
#


for _, dfUt in dfU.iterrows():
	uid, uname = dfUt['uid'], dfUt['name']
	servidores = []
	print '--- University for: %s' % (uname)
	#
	# Collect the first page
	#
	session = requests.Session()
	u_page = session.get('http://www.portaldatransparencia.gov.br/servidores/OrgaoExercicio-ListaServidores.asp?CodOrg=%d' % (uid))
	u_tree = etree.HTML(u_page.content, etree.HTMLParser(encoding="windows-1252"))
	_, n_pages = u_tree.xpath('//div[@id="paginacao"]/p[@class="paginaAtual"]')[0].text.split('/')

	for i_page in np.arange(1, int(n_pages)+1):
		print 'Page: %d/%d' % (i_page, int(n_pages))

		if i_page>1:
			session = requests.Session()
			u_page = session.get('http://www.portaldatransparencia.gov.br/servidores/OrgaoExercicio-ListaServidores.asp?CodOrg=%d&Pagina=%d' % (uid,i_page))
			u_tree = etree.HTML(u_page.content, etree.HTMLParser(encoding="windows-1252"))

		lista = u_tree.xpath('//div[@id="listagem"]/table')[0]

		for i, s_item in enumerate(lista, start=0):
			if i ==0:
				continue
			cpf, name, orgao = s_item.xpath('td')
			
			sid, id_orgao = urlparse.parse_qs(urlparse.urlparse(name[0].attrib['href']).query).values()
			sid, id_orgao = int(sid[0]), int(id_orgao[0])
			cpf = cpf.text.strip()
			name = name[0].text.strip()
			orgao = orgao.text.strip()

			# Skipping -- Already harvested
			print 'Harvesting: %s (%d) from %s' % (name, sid, orgao)
			if sid in dfS.index.values:
				print 'skipping'
				continue
			
			# Get Detailed Information on Servidor - Cargos
			s_page = session.get('http://www.portaldatransparencia.gov.br/servidores/OrgaoExercicio-DetalhaServidor.asp?IdServidor=%d&CodOrgao=%d' % (sid, id_orgao))
			s_tree = etree.HTML(s_page.content, etree.HTMLParser(encoding="windows-1252"))
			cargos = s_tree.xpath('//div[@id="listagemConvenios"]/table/tr/td')
			c_list = []
			for j, cargo in enumerate(cargos, start=1):
				c_item = cargo.xpath('table/tbody/tr')
				if len(c_item):
					c_string = ''
					for z, r_item in enumerate(c_item, start=1):
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
						c_string += k + v 
						if z < len(c_item):
							c_string += u'|'

					c_list.append(c_string)

			# Get Financial Information on Servidor
			f_page = session.get('http://www.portaldatransparencia.gov.br/servidores/Servidor-DetalhaRemuneracao.asp?Op=2&IdServidor=%d&CodOrgao=%d&CodOS=15000&bInformacaoFinanceira=True&Ano=2015&Mes=11' % (sid, id_orgao))
			f_tree = etree.HTML(f_page.content, etree.HTMLParser(encoding="windows-1252"))

			financeiro = f_tree.xpath('//div[@id="listagemConvenios"]/table/tbody/tr[@class="remuneracaodetalhe"]')
			
			basico_bruto = None
			for f_item in financeiro:
				tds = f_item.xpath('td')
				if len(tds) == 4:
					if tds[1].text == u'Remuneração básica bruta':
						basico_bruto = tds[2].text
						basico_bruto = float(basico_bruto.replace('.','').replace(',','.'))
					break
			servidores.append( (sid, uid, uname, name, cpf, orgao, basico_bruto, c_list) )
		# Save New Page
		dfS_save(servidores)




