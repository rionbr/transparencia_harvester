# -*- coding: utf-8 -*-
"""
DB Connection
===================

MySQL Database connection methods
"""
#    Copyright (C) 2016 by
#    Rion Brattig Correia <rionbr@gmail.com>
#    All rights reserved.
#    MIT license.
import pandas as pd
import mysql.connector
from mysql.connector import errorcode
from sqlalchemy import create_engine
import os
import json

__name__ = 'db'
__author__ = """\n""".join(['Rion Brattig Correia <rionbr@gmail.com>'])
__all__ = ['DataFrameToMySQL', 'MySQLToDataFrame']
#
#
#
class DB(object):

	def __init__(self):

		with open('db_config.json', 'r') as f:
			d = json.load(f)
			CONFIG = d['mysql_config']
		
		self.engine = create_engine('mysql+mysqlconnector://%s:%s@%s:%s/%s' % (CONFIG['user'],CONFIG['pass'],CONFIG['host'], CONFIG['port'], CONFIG['schema']), echo=False)

	def DataFrameToMySQL(self, df, table):
		"""

		"""
		try:
			df.to_sql(name=table, con=self.engine, if_exists='append', index=False)
		except Exception, e:
			return e
		else:
			return True

	def MySQLToDataFrame(self, sql, index_col=None):
		"""

		"""
		try:
			df = pd.read_sql(sql, con=self.engine, index_col=index_col)
		except Exception, e:
			return e
		else:
			return df

