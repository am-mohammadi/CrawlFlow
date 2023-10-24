# -*- coding: utf-8 -*-
"""
Created on Sat Jun 24 11:58:39 2023

@author: Amirmahdi Mohammadi
"""
# import CrawlTypes

import requests
# from bs4 import BeautifulSoup
import pandas as pd
import time
# import numpy as np
# from datetime import datetime
import pickle
from tqdm import tqdm
# import re
import json
import sqlite3
import os


class Handler:
    '''
    
    This is the main class
    '''
    def __init__(self, name):
        #Name of the project
        self.name=name
        
        #Initialize____________________________________________________________
        self.request=Request()
        
        #Type of crawling. you need to set classes from CrawlTypes to this variable
        self.type=None
        
        #Data will be stored tables. 
        self.tables={}
        
        
        #Params________________________________________________________________
        
        #Steps for checkpoint 
        self.chk_point_interval=20
        
        #If set True, data will be stored to a local .db file
        self.send2db=True
        
        #Path for saving Vars object. it will be a relative path
        self.object_save_path=f'{name}_object.pkl'
        
        #Directory of the project
        self.directory=''
        
        self.object_columns_method = 'none'  #to_str/drop/none
        
        
        
        
        
        
    def init(self):
        '''
        Initializing

        Returns
        -------
        None.

        '''
        self.vars=Vars()
        self.request.type=self.type
        self.path=self.directory+self.name+'/'
        if not os.path.exists(self.path):
            os.makedirs(self.path)
    
    def item_get_data(self, url):
        '''
        Running data2rows function and send requests

        Parameters
        ----------
        url : string
            DESCRIPTION.

        Returns
        -------
        dict
            dictionary of tables that stored in one request

        '''
        request_data=self.request.get(url)
        if self.request.failed:
            self.vars.missed_urls+=[url]
            return {}
        tables_rows=self.data2rows(request_data)
        return tables_rows
        
        
    
    def run(self, url_list, resume=False, dynamic=False):
        '''
         Running crawling process
 
         Parameters
         ----------
         url_list : list
             list of urls for crawling.
         resume : bool, optional
             Resuming process. The default is False.
         dynamic : bool, optional
             Is your crawling urls dynamic or not. The default is False.
 
         Returns
         -------
         None.
 
         '''

        if resume:
            #Resuimng process
            self.vars = self.read()
            print('Resuming from', self.vars.counter)
        
        if not dynamic:
            for counter in tqdm(range(self.vars.counter, len(url_list))):
                self.vars.counter=counter
                url=url_list[counter]
                self.url=url
                tables_rows=self.item_get_data(url)
                self.run_handle(tables_rows)
        else:
            while not self.vars.done:
                if self.vars.next_url is None:
                    url=url_list[0]
                else:
                    url=self.vars.next_url
                tables_rows=self.item_get_data(url)
                self.run_handle(tables_rows)
                print('Request number:', self.vars.counter)
                self.vars.counter+=1
            
                
    def run_handle(self, tables_rows):
        '''
        Handles appeding tables_rows to tables and doing checkpoint

        Parameters
        ----------
        tables_rows : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        '''
        for table_name in tables_rows:
            if table_name in self.tables.keys():
                self.tables[table_name]+=tables_rows[table_name]
            else:
                self.tables[table_name]=tables_rows[table_name]
        if ((self.vars.counter%self.chk_point_interval==0 or self.vars.done) 
        and  self.vars.counter>0):
            self.chk_point()
        
        
        
    def chk_point(self):
        '''
        Checkpoint the data and vars

        Returns
        -------
        None.

        '''
        try:
            self.sendDB(self.tables, 
                      )
            self.flush_tables()
            self.write(self.vars)
            self.vars.tables_created=True
            print('Chkpoint.')
        except Exception as e:
            print('Chkpoint failed, maybe next time', e)
        
    def flush_tables(self):
        for table_name in self.tables:
            self.tables[table_name]=[]
    
    def sendDB(self, df):
        '''
        Sending to DB

        Parameters
        ----------
        df : TYPE
            DESCRIPTION.
        create_table : TYPE, optional
            DESCRIPTION. The default is False.

        Returns
        -------
        None.

        '''
        con = sqlite3.connect(f"{self.path}{self.name}_DB.db")
        cur = con.cursor()
        for table_name in df:
            try:
                table=pd.json_normalize(df[table_name])
                table=table.where(pd.notnull(table), None)
                for col in table.columns:
                    if table[col].dtype == 'O':
                        if self.object_columns_method == 'to_str':
                            table[col] = table[col].astype('str')
                            print(table_name, col, 'converted to string.')
                        elif self.object_columns_method == 'drop':
                            table.drop(columns=[col], inplace = True)
                            print(table_name, col, 'dropped.')
                            
                    
                if table_name not in self.vars.DB_tables: 
                    columns=[x.replace('.', '_') for x in table.columns]
                    columns='indexx, '+', '.join(columns)
                    cur.execute(f"CREATE TABLE {table_name}({columns})")
                    print(f'{table_name} table created with {len(table.columns)} columns.')
                    self.vars.DB_tables.append(table_name)
                    self.vars.columns[table_name]=table.columns.to_list()
                table=df_col_review(table, self.vars.columns[table_name])
                data = tuple(table.itertuples())
                wildcards = ','.join(['?'] * (len(table.columns)+1))
                insert_sql = f'INSERT INTO {table_name} VALUES (%s)' % wildcards
                # if table_name=='connetions':
                #     print(table)
                cur.executemany(insert_sql, data)
            except Exception as e:
                print('sendDB failed', table_name, e)
        con.commit()
        cur.close()


        
    def readDB(self, table):
        '''
        Reading from database

        Parameters
        ----------
        table : string
            table name.

        Returns
        -------
        df : DataFrame
            table.

        '''
        con = sqlite3.connect(f"{self.path}{self.name}_DB.db")
        # cur = con.cursor()
        df = pd.read_sql(f'select * from {table}', con)
        con.close()
        return df
 
        
    def export(self, df=[], name=''):
        df = pd.json_normalize(df)
        df.to_csv(f'{self.name}.csv', index=False, encoding='utf-8-sig')
        print(name, 'exported')

    def export_tables(self):
        '''
        Export all tables to csv file

        Returns
        -------
        None.

        '''
        path=self.path+'/data/'
        if not os.path.exists(path):
            os.makedirs(path)
        for table_name in self.vars.DB_tables:
            table=self.readDB(table_name)
            table.to_csv(f'{path}{table_name}.csv', index=False, encoding='utf-8-sig')

    def write(self, obj):
        '''
        Write the vars object

        Parameters
        ----------
        obj : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        '''
        with open(self.path+self.object_save_path, 'wb') as outp:
            pickle.dump(obj, outp, pickle.HIGHEST_PROTOCOL)

    def read(self):
        '''
        Read vars object

        Returns
        -------
        obj : TYPE
            DESCRIPTION.

        '''
        with open(self.path+self.object_save_path, 'rb') as inp:
            obj = pickle.load(inp)
            return obj
  
    def get(self, dic, keys):
        '''
        get value of deep dictionary with list of keys.

        Parameters
        ----------
        dic : dict
            Your dictionary.
        keys : list
            list of keys that you want to go in depth.

        Returns
        -------
        dic : TYPE
            final value.

        '''
        for key in keys:
            if key in dic.keys():
                dic=dic[key]
                if dic is None:
                    return None
            else:
                return None
        return dic
  

class Vars():
    def __init__(self):
        self.counter=0
        self.missed_urls=[]
        self.tables_created=False
        self.DB_tables=[]
        self.done=False
        self.next_url=None
        
        self.columns={}
        
    

    
class Request:
    def __init__(self):
        self.headers={}
        self.cookies={}
        self.params={}
        self.type=None
        
        self.max_retries=5
        self.sleep_time=None
        
        self.status_sleep_time=10
        
        self.timeout=10
        
        self.dynamic_url=None
        
        self.kwargs={}
        
        self.method='get'
        
        self.bypass_status_codes=[]
        
    def read_headers(self, path):
        with open(path) as f:
            self.headers = json.load(f)
            
    def read_cookies(self, path):
        with open(path) as f:
            self.cookies = json.load(f)
    
        
    def get(self, url):
        status = 0
        tries = 0
        self.failed = False
        while status != 200:
            if tries>=self.max_retries:
                print('Max retry, skipped')
                self.failed = True
                return
            tries+= 1
            try:
                if status!=0 :
                    print('sleeping...', status, url)
                    time.sleep(tries*self.status_sleep_time)
                if self.dynamic_url is not None:
                    url=self.dynamic_url
                if self.method=='get':
                    response = requests.get(url, headers=self.headers, 
                                            cookies=self.cookies, params=self.params, 
                                            timeout=self.timeout, **self.kwargs)
                elif self.method=='post':
                    response = requests.post(url, headers=self.headers, 
                                            cookies=self.cookies, params=self.params, 
                                            timeout=self.timeout, **self.kwargs)
                    
                status = response.status_code
                if status in self.bypass_status_codes:
                    return {'status_code': status}
                if status == 404:
                    print('Faliled, 404')
                    self.failed = True
                    return
                
            except Exception as e:
                print('req get', e)
                time.sleep(5)
        if self.sleep_time is not None:
            time.sleep(self.sleep_time)
        data=self.type.process_response(response)
        return data

def df_col_review(df, columns):
    for col in columns:
        if col not in df.columns:
            df[col]=None
    df=df[columns]
    return df

def DB2csv(path, table):
    con = sqlite3.connect(path)
    # cur = con.cursor()
    df = pd.read_sql(f'select * from {table}', con)
    con.close()
    df.to_csv(f'{path}.csv', index=False, encoding='utf-8-sig')
    print('exported to', path)