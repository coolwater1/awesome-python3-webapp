#!/usr/bin/env python3
#coding:utf-8  
''''' 
@author: steve 
get stock list

'''''  
from eastmoney import EastMoneyStockList
import os,shutil,time

def get_stock_list():
    date = time.strftime('%Y%m%d%H%M%S')
    east = EastMoneyStockList()
    save_path = 'D:\\OneDrive\\stock\\list\\'+ 'hs_a_board'+ '.xls'
    if (os.path.exists(save_path)):
        bak_path = save_path[:-4]+ date + '.xls'
        shutil.copy(save_path, bak_path)
    east.get_stock_list('hs_a_board',save_path, except_code_list=['300','688']) #去除300，688开头的
    # east.get_stock_list('hs_a_board',save_path)

if __name__ == '__main__':
    get_stock_list()


