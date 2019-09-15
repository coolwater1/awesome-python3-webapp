#!/usr/bin/env python3
# -*- coding: utf-8 -*-

''''' 
@author: steve 
从东方财富网获取股票列表数据
'''  
 
import requests,time,os,xlwt,xlrd,random
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
from ExcelData import ExcelData
from multiprocessing import Process, Queue
from operator import itemgetter
from itertools import groupby
import pyautogui

class EastMoney(): 
    def _init_browser(self):
        start_time = time.time()
        # 给浏览器设置属性
        option = webdriver.ChromeOptions()
        # 设置默认隐藏，后台运行
        option.add_argument("headless")
        # 产生随机user-agent
        option.add_argument(UserAgent().random)
        browser = webdriver.Chrome(options=option)
        print('_init_browser %d second'% (time.time()-start_time))
        return browser

    def _request_url(self, browser, url):
        start_time = time.time()
        retry_time = 0
        while retry_time <= 3:
            try:
                print("请求url:"+url)
                browser.get(url)
                return True
            except Exception as e:
                print("%s%s" % (e,url))
                retry_time = retry_time + 1
        print('_request_url %d second'% (time.time()-start_time))
        return False

    # 含dict的list排序并去重
    def _distinct(self, items,key, reverse=False):
        key = itemgetter(key)
        items = sorted(items, key=key, reverse=reverse)
        return [next(v) for _, v in groupby(items, key=key)]

class EastMoneyStockList(EastMoney):
    def __init__(self, market_name):
        self._market_name = market_name

    def _get_url(self, market_name):
        market_list = {'沪深A股':'http://quote.eastmoney.com/center/gridlist.html#hs_a_board'\
                    ,'上证A股':'http://quote.eastmoney.com/center/gridlist.html#hs_a_board'\
                    ,'深圳A股':'http://quote.eastmoney.com/center/gridlist.html#sz_a_board'\
                    ,'中小板':'http://quote.eastmoney.com/center/gridlist.html#sme_board'\
                    ,'创业板':'http://quote.eastmoney.com/center/gridlist.html#gem_board'\
                    ,'科创板':'http://quote.eastmoney.com/center/gridlist.html#kcb_board'}
        return market_list[market_name]

    def parse_page(self):
        stock_list = []
        url = self._get_url(self._market_name)
        #启动浏览器
        browser = self._init_browser() 
        if not self._request_url(browser,url):
            return stock_list

        while True:
            # 等待list加载完成，不然抓取不到数据
            wait = WebDriverWait(browser, 10)
            wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='listview full']" )))

            # 解析网页
            soup = BeautifulSoup(browser.page_source, 'lxml')

            for tr in soup.find('div',class_='listview full').find('tbody').find_all('tr'):
                stock = {}
                span = tr.find('span')
                if span.contents[0] == '-':
                    continue
                a = tr.findAll('a')
                stock['code'] = a[0].contents[0]
                stock['名称'] = a[1].contents[0]

                stock_list.append(stock)
                print(stock)

            # 查找目标按钮
            try:
                btn_next = browser.find_element_by_xpath("//a[@class='next paginate_button']")
                btn_next.click()
                time.sleep(random.randint(1,2)+random.random()) #随机延时?.?s  以防封IP
            except NoSuchElementException:
                # print(e.msg)
                break

        #关闭浏览器          
        browser.quit()   
        # 按照code从小到大排序
        stock_list.sort(key=lambda k: (k.get('code', 0)))
        return stock_list

class EastMoneyConcept(EastMoney):
    def _init_browser_forground(self):
        start_time = time.time()
        # 给浏览器设置属性
        option = webdriver.ChromeOptions()
        # 设置默认隐藏，后台运行
        # option.add_argument("headless")
        # 产生随机user-agent
        option.add_argument(UserAgent().random)
        browser = webdriver.Chrome(options=option)
        browser.maximize_window()
        print('_init_browser_forground %d second'% (time.time()-start_time))
        return browser

    def _code2url(self, code):
        code_map = {'60': 'sh', '00':'sz', '30':'sz','688':'sh'}
        code_str = ''
        if isinstance(code, int):
            code_str = str(code)
        elif isinstance(code, float):
            code_str = str(code)
        elif isinstance(code, str):
            code_str = code
        for item in code_map:
            if code_str.startswith(item):
                return "http://quote.eastmoney.com/concept/" + code_map[item] + code_str + ".html"
   
    def _pre_load(self,browser):
        try:
            # start_time = time.time()
            # 找到筹码分布的按钮---通过xpath
            btn_cmfb_xpath = "//a[text()='筹码分布']"
            # 等待响应完成
            wait = WebDriverWait(browser, 10)
            wait.until(EC.presence_of_element_located((By.XPATH, btn_cmfb_xpath)))
            # 查找目标按钮
            btn_cmfb = browser.find_element_by_xpath(btn_cmfb_xpath)
            # 找到按钮后单击
            btn_cmfb.click()

            # 等待筹码分布的元素显示出来，不然解析数据的时候抓取不到相关数据
            wait = WebDriverWait(browser, 10)
            # wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='__emchatrs3_cmfb']" )))
            # wait.until(EC.visibility_of_element_located((By.XPATH, "//div[@class='__emchatrs3_cmfb']" )))
            wait.until(EC.text_to_be_present_in_element((By.XPATH,"//div[@class='__emchatrs3_cmfb']"),u'集中度'))
            # print('_pre_load %d second'% (time.time()-start_time))
            return True
        except Exception as e:
            print("%s" % (e))
            return False

    def parse_page_cmfb_today(self):
        cmfb_data = {}
        url = self._get_url(self._code)
        browser = self._init_browser()
        if not self._request_url(browser,url):
            return cmfb_data
        if not self._pre_load(browser):
            return cmfb_data
        
        cmfb_data = self._parse_page_cmfb_data(browser)
        browser.quit()
        return cmfb_data

    # 解析网页获取筹码分布数据并返回数据
    def _parse_page_cmfb_data(self, browser):
        COLUMN_LIST = ('日期','获利比例','亏损比例','平均成本','90%成本','90成本集中度','70%成本','70成本集中度')
        count = len(COLUMN_LIST)
        data = {}
        index = 0
        # 解析网页
        # start_time = time.time()
        soup = BeautifulSoup(browser.page_source, 'lxml')
        for span in soup.find(class_="__emchatrs3_cmfb").find_all('span'):
            if index >= count:
                break
            data[COLUMN_LIST[index]] = span.contents[0]
            index = index + 1
        # print('_parse_page_cmfb_data %d second'% (time.time()-start_time))
        print(data)   
        return data

    def _parse_page_stock_info_history(self, browser):
        CMFB_COLUMN = ('日期','获利比例','亏损比例','平均成本','90%成本','90成本集中度','70%成本','70成本集中度')
        BASE_INFO = ('日期','开盘','收盘','最高','最低','涨跌幅','涨跌额','成交量','成交额','振幅','换手率')
        
        data = {}
        
        # 解析网页
        # start_time = time.time()

        index = 0
        count = len(CMFB_COLUMN)
        soup = BeautifulSoup(browser.page_source, 'lxml')
        for span in soup.find(class_="__emchatrs3_cmfb").find_all('span'):
            if index >= count:
                break
            data[CMFB_COLUMN[index]] = span.contents[0]
            index += 1

        index = 0
        count = len(BASE_INFO)
        for span in soup.find(class_="__popfloatwin").find_all('span'):
            if index >= count:
                break
            if index > 0:
                data[BASE_INFO[index]] = span.contents[0]
            index += 1

        # print('_parse_page_stock_info_history %d second'% (time.time()-start_time))
        # print(data)   
        return data

    def _get_history(self, browser, code):
        data_list = []

        url = self._code2url(code)
        # 如果网页加载失败,直接返回
        if not self._request_url(browser,url):
            print("网页加载失败: " + url)
            return data_list
        if not self._pre_load(browser):
            print("网页加载失败: " + url)
            return data_list
        
        # 移动滚动条定位到某个元素，使这个元素在可见区域，一般在最顶上
        target = browser.find_element_by_xpath("//div[@class='kr-box']")
        # target = browser.find_element_by_xpath(btn_cmfb_xpath)
        browser.execute_script("arguments[0].scrollIntoView();", target)

        time.sleep(2)
        # 移动到某个起始位置
        START_X = 0
        START_Y = 0 
        END_X = 0
        MOVE_X = 0
        screenWidth,screenHeight = pyautogui.size()
        # print("screenWidth : " + str(screenWidth))
        if screenWidth == 1366 :
            START_X = 350
            END_X = 996
            START_Y = 485
            MOVE_X = 8
        elif screenWidth == 1920:
            START_X = 544    
            END_X = 1350
            START_Y = 666
            MOVE_X = 10
        else:
            print("不能匹配到屏幕尺寸，请增加")
            return
        currentX= START_X
        currentY= START_Y

        pyautogui.moveTo(START_X, START_Y)
        time.sleep(2)

        while currentX < END_X:
            data = self._parse_page_stock_info_history(browser)
            data_list.append(data)

            # #  鼠标向右移动x像素
            currentX = currentX + MOVE_X
            pyautogui.moveTo(currentX, currentY)
            # 等待筹码分布的元素显示出来，不然解析数据的时候抓取不到相关数据
            wait = WebDriverWait(browser, 10)
            # wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='__emchatrs3_cmfb']" )))
            # wait.until(EC.visibility_of_element_located((By.XPATH, "//div[@class='__emchatrs3_cmfb']" )))
            wait.until(EC.text_to_be_present_in_element((By.XPATH,"//div[@class='__emchatrs3_cmfb']"),u'集中度'))

        # data_list 需要去重和排序
        # print(data_list)
        # print(len(data_list))
        data_list = self._distinct(data_list, '日期')
        # print(len(data_list))
        # print(data_list)
        return data_list

    def get_history_by_code(self, code, root_path):
        browser = self._init_browser_forground()
        data_list = self._get_history(browser,code)
        save_path = root_path + code + '.xls'
        # excel = ExcelData(save_path)
        # excel.write_excel(data_list)
        self._save_data(code, save_path, data_list)
        browser.close()
        browser.quit()

    def get_history_by_stock_list_path(self, stock_list_path, root_path):
        browser = self._init_browser_forground()
        excel = ExcelData(stock_list_path)
        stock_list = excel.read_excel()
        error_code_list = []
        for stock in stock_list:
            code = stock['code']
            if not isinstance(code, str):
                code = str(code)
            error_code = {}
            data_list = self._get_history(browser,code)
            save_path = root_path + code + '.xls'
            if not self._save_data(code, save_path, data_list):
                error_code['code'] = code
                error_code_list.append(error_code)
        
        if len(error_code_list) > 0:
            date = time.strftime('%Y%m%d%H%M%S')
            error_stock_list_path = stock_list_path[:-3]+'errorlist'+date+'.xls'
            excel = ExcelData(error_stock_list_path)
            excel.write_excel(error_code_list)

        browser.close()
        browser.quit()
        

    def _save_data(self, code, save_path, data_list):
        excel_data = ExcelData(save_path)
       
        try:
            excel_data.write_excel(data_list)
            print("数据已保存到文件： " + save_path)
            return True
        except FileNotFoundError:
            print(save_path + "----创建失败(上级目录不存在)")
            date = time.strftime('%Y%m%d%H%M%S')
            excel_data = ExcelData(code + '-'+ date + ".xls")
            excel_data.write_excel(data_list)
            print("数据已保存到临时文件：" + os.getcwd() + '\\' + code + '-'+ date + ".xls")
            return True
        except PermissionError:
            print(save_path + "----创建失败(文件已经被打开)")
            date = time.strftime('%Y%m%d%H%M%S')
            excel_data = ExcelData(code + '-' + date + ".xls")
            excel_data.write_excel(data_list)
            print("数据已保存到临时文件：" + os.getcwd() + '\\' + code + '-'+ date + ".xls")
            return True
        except Exception:
            return False
        

       
    # def run(self):
    #     data_list = self._get_data()
    #     self._save_data(data_list)
        
 
 
def main():
    date = time.strftime('%Y%m%d')

    # east_stock_list = EastMoneyStockList('科创板')
    # stock_list = east_stock_list.parse_page()
    # print(stock_list)

    concept = EastMoneyConcept()
    # concept.get_history_by_code('000002')
    # concept.get_history_by_code('000002','D:\\pythonData\\股票数据\\')
    concept.get_history_by_stock_list_path('D:\\pythonData\\股票列表\\沪深A股Data20190908.xls','D:\\pythonData\\股票数据\\')
    # concept.parse_page_cmfb_today()
    # # 获取科创板所有股票列表
    # url = "http://quote.eastmoney.com/center/gridlist.html#sz_a_board"
    # save_path = 'D:\\pythonData\\股票数据\\'+"深A" + 'Data'+date+'.xls'
    # test = East(url,save_path)
    # test.run()
    
    # 获取A股所有股票列表
    # url = "http://quote.eastmoney.com/center/gridlist.html#hs_a_board"
    # save_path = 'D:\\pythonData\\股票数据\\'+"沪深A股" + 'Data'+date+'.xls'
    # test = East(url,save_path)
    # test.run()   
 
 
 
if __name__ == '__main__':
    main()
	
	
	