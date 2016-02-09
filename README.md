Transparencia Harvester
=======================

A tool to harvester the Brazilian (Portal da Transparencia)[http://www.portaldatransparencia.gov.br/] from the Open Data Portal of the Federal Government.

Why do we need this?
Because the download function does not have all the information science would expect.

What does this do?
Harvesters (scrapes the pages) and inserts into a MySQL database.


How to Harvest
--------------

### Step 1: Create the MySQL tables (see statements below).

### Step 2: Populate `orgao_superior` (aka Ministérios)

```python
from orgao_superior import OrgaoSuperior

OrgaoSuperior(verbose=True).harvest()
```

### Step 3: Populate `orgao` (aka Instituições)

Here you have to give the number of the [O]rgao [S]uperior you want to collect.
In the example below `15000` is the 'Ministério da Educação'.

```python
from orgao import Orgao
Orgao(verbose=True).harvest(codOS=15000)
```

### Step 4: Populate `servidor` (aka Trabalhadores)

First, get the list of `orgao` you want to fill in with workers.
Then look through all of them and retrieve the general information for every worker.
You might want to have an input to help on the process (see below).

```python
from orgao import Orgao
dfO = Orgao().getDF()

for id_orgao, dft in dfO.iterrows():

	ans = raw_input(u'Harvest `%s`? [y/n]:' % dft['name'])
	if ans == 'y':
		s = Servidor(verbose=True)
		s.harvest(id_orgao=id_orgao)	
	else:
		print 'Skipping Orgao'
```
Note: DF stands for Pandas DataFrame.

### Step 5: Populate `cargo` (optional: aka position)

STILL NOT 100%

```python
TODO
```

Note: a worker may have more than one position.
He can also be allocated in a different `orgao` than that of his initial contract.
This process may take a lof time depending on how much data you want.



### Step 6: Populate `remuneracao` (optional; aka finances)



```python
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
```

Note: this process may take a lot of time, depending on how much data you want.


Resources
----------

### How do I know count the number of `servidor` per `orgao`?

```sql
SELECT o.*, (SELECT count(*) FROM servidor WHERE id_orgao=o.id_orgao) as count FROM orgao o;
``` 

MySQL CREATE Tables statements
--------------------------------

```sql
DROP TABLE IF EXISTS servidor_cargo;
DROP TABLE IF EXISTS servidor_remuneracao;
DROP TABLE IF EXISTS servidor;
DROP TABLE IF EXISTS orgao;
DROP TABLE IF EXISTS orgao_superior;


CREATE TABLE orgao_superior
(
	id_orgao_superior VARCHAR(10) NOT NULL,
	name VARCHAR(255) NOT NULL,
	n_servidores INT(10) UNSIGNED,
	
	PRIMARY KEY (id_orgao_superior)
) ENGINE=INNODB;


CREATE TABLE orgao
(
	id_orgao INT(10) UNSIGNED NOT NULL,
	id_orgao_superior VARCHAR(5)NOT NULL,
	name VARCHAR(255) NOT NULL,
	n_servidores INT(10) UNSIGNED,
	
	PRIMARY KEY (id_orgao),
	INDEX (id_orgao_superior),
	FOREIGN KEY (id_orgao_superior) REFERENCES orgao_superior(id_orgao_superior) ON DELETE RESTRICT ON UPDATE CASCADE 
) ENGINE=INNODB;

CREATE TABLE servidor
(
	id_servidor INT(10) UNSIGNED NOT NULL,
	id_orgao INT(10) UNSIGNED NOT NULL,
	name VARCHAR(255) NOT NULL,
	cpf VARCHAR(14),

	PRIMARY KEY (id_servidor),
	INDEX (id_orgao),
	FOREIGN KEY (id_orgao) REFERENCES orgao(id_orgao) ON DELETE RESTRICT ON UPDATE CASCADE 
) ENGINE=INNODB;

CREATE TABLE servidor_cargo
(
	id_cargo INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
	id_servidor INT(10) UNSIGNED NOT NULL,
	cargo VARCHAR(255),
	funcao VARCHAR(255),
	classe VARCHAR(10),
	padrao VARCHAR(10),
	referencia VARCHAR(10),
	nivel VARCHAR(10),
	jornada VARCHAR(15),
	
	PRIMARY KEY (id_cargo),
	INDEX (id_servidor),
	FOREIGN KEY (id_servidor) REFERENCES servidor(id_servidor) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=INNODB;

CREATE TABLE servidor_remuneracao
(
	id_remuneracao INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
	id_servidor INT(10) UNSIGNED NOT NULL,
	date DATE NOT NULL,
	basica_bruta FLOAT NOT NULL,
	
	PRIMARY KEY (id_remuneracao),
	INDEX (id_servidor),
	FOREIGN KEY (id_servidor) REFERENCES servidor(id_servidor) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=INNODB;
```