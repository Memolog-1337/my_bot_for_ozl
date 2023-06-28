import os
import datetime
import json
import random
import csv
import pandas as pd

from time import sleep

from selenium.webdriver import Chrome, ChromeOptions
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

from bs4 import BeautifulSoup

from pandas.core.series import Series

pd.options.mode.chained_assignment = None


PROXY_LIST: list = [
]
PATH_TO_CHROMEDRIVER: str = ()
DELIVERY_TIME = '+9 нед'
LOGIN = ''
PASSWORD = ''
URL_URM = ''
ARROW_URL = 'https://www.arrow.com/en/products/search?cat=&q='
MOUSER_URL: str = 'https://www.mouser.com'
QUEST_URL: str = 'https://www.mouser.com/c/?q='
PROM_URL: str = 'https://www.promelec.ru/search/?query='
LSCS_URL: str = 'https://www.lcsc.com'
LCSC_URL_QUEST: str = 'https://www.lcsc.com/search?q='


class StealthBrowser:
    proxy: str
    options = ChromeOptions()  # нужен typing

    def __init__(self) -> None:
        self.proxy: str = random.choice(PROXY_LIST)
        # Разобраться в этих настройках
        self.options.add_argument('--proxy-server=%s' % self.proxy)
        self.options.add_argument('--profile-directory=Profile 1')
        self.options.add_experimental_option(
            'excludeSwitches',
            ['enable-automation']
        )
        # self.options.add_argument('--headless')
        self.options.add_experimental_option('useAutomationExtension', False)
        self.browser = Chrome(
            executable_path=PATH_TO_CHROMEDRIVER,
            options=self.options
        )  # Вынести параметр в объявление класса и сделать tuping
        stealth(
            self.browser,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True
        )

    def get_url(self, url):  # typing
        self.browser.get(url)

    def get_soup_info(self):  # typing
        return BeautifulSoup(self.browser.page_source, 'lxml')


class Parser:

    def __init__(
            self,
            input_excel_name: str,
            output_excel_name: str,
            done_products_file_name: str
    ) -> None:
        self.input_excel_name = input_excel_name
        self.output_excel_name = output_excel_name
        self.done_products_file_name = done_products_file_name

        with open(input_excel_name, 'rb') as input_excel:
            self.input_excel: pd = pd.read_excel(
                input_excel,
                sheet_name='TDSheet'
            )  # проверить typing

        self.output_excel: pd = pd.read_excel(
            output_excel_name,
            sheet_name='Sheet1'
        )  # проверить typing
        self.partnumbers: list = []
        self.quantities: list = []
        self.start_index: int = 0
        self.base = DataBase(self.done_products_file_name)
        self.base.create_base()  # typing

    def get_partnumbers_and_quantities(self) -> None:
        partnumbers: Series = self.input_excel['PART #']  # проверить typing
        quantities: Series = self.input_excel["Q'TY(PCS) "]  # проверить typing
        for partnumber in partnumbers:
            partnumber: str = str(partnumber).replace('\n', '')
            self.partnumbers.append(partnumber)
        for quantity in quantities:
            quantity: str = str(quantity).replace(' ', '')
            self.quantities.append(int(quantity))
        self.start_index = self.base.check_data_base(
            self.partnumbers,
            self.quantities
        )


class DataBase:
    done_products: json = {}
    done_products_file_name: str

    def __init__(self, done_products_file_name: str) -> None:
        self.done_products_file_name = done_products_file_name

    def reload(self) -> None:
        json.dump(self.done_products, open(self.done_products_file_name, 'w'))

    def create_base(self) -> None:
        if os.path.exists(self.done_products_file_name):
            self.done_products = json.load(
                open(self.done_products_file_name, 'r')
            )
        else:
            self.reload()

    def check_data_base(self, partnumbers: list, quantities: list) -> int:
        start_index: int = 0

        for index, partnumber in enumerate(partnumbers):
            check_index: str = (
                f'{str(index)}/{partnumber}/{quantities[index]}'
            )
            if check_index in self.done_products.keys():
                start_index += 1
            else:
                break
        return start_index

    def to_base(self, index, product):
        self.done_products[index] = product.to_json()
        self.reload()


class Product:  # dataclasses?

    def __init__(
            self,
            partnumber: str,
            index: int,
            quantity: int
    ) -> None:
        self.partnumber = partnumber
        self.index = index
        self.quantity = quantity
        self.stock = 0
        self.price = 1


class MouserProduct(Product):

    def __init__(self, partnumber: str, index: int, quantity: int):
        super().__init__(partnumber, index, quantity)
        self.plan_postavki = {}
        self.mouser_code = '' 
        self.eccn_code = 'NO ECCN'
        self.maximum = 0
        self.alternative_partnumber = None
        self.step = 1


class UsualProduct(Product):

    def __init__(self, partnumber: str, index: int, quantity: int):
        super().__init__(partnumber, index, quantity)
        self.min_part_quan = 0
        self.min_order_quan = 0
        self.to_dop_info = []
        self.articule = 'Неизвестно'

    def is_nan(self, num: str) -> bool:
        return num != num


"""
    def to_json(self):
        plan_postavki_for_json = {}
        for key, value in self.plan_postavki.items():
            if str(type(key).__name__) == 'date':
                plan_postavki_for_json[]
            else:
                plan_postavki_for_json[key] = value

        json_product = {
            'partnumber': self.partnumber,
            'index': self.index,
            'quantity': self.quantity,
            'stock': self.stock,
            'price': self.price,
            'mouser_code': self.mouser_code,
            'eccn_code': self.eccn_code,
            'maximum': self.maximum
        }

        return json_product
"""


class MouserPartnumberParser(Parser):

    def check_partnumber_info(self, partnumber, index, quantity):
        product = MouserProduct(
            partnumber,
            index,
            quantity,
        )

        while not product.plan_postavki:
            self.check_partnumber_page(product)
        print(product.partnumber + ' Done!')

        return product

    def check_partnumbers_info(self):  # typing

        for index, partnumber in enumerate(
                self.partnumbers,
                start=self.start_index
        ):
            product = MouserProduct(
                partnumber,
                index,
                int(self.quantities[index])
            )

            while not product.plan_postavki:
                self.check_partnumber_page(product)

            print(product.partnumber + ' Done!')
            # index_to_base = (
            #     f'{str(index)}/{partnumber}/{self.quantities[index]}'
            # )
            # self.base.to_base(index_to_base, product)

            if product.alternative_partnumber is not None:

                if self.is_alternative_better(
                        product,
                        product.alternative_partnumber
                ):
                    self.to_excel(product.alternative_partnumber, index, True)
                    continue

            self.to_excel(product, index, False)

        self.input_excel.to_excel(self.output_excel_name, index=False)

    def check_partnumber_page(self, product: MouserProduct) -> None:
        browser = StealthBrowser()
        print(product.partnumber)

        if '#' in product.partnumber:
            partnumber_for_url = product.partnumber.split('#')
            partnumber_for_url = partnumber_for_url[0]
            browser.get_url(QUEST_URL + partnumber_for_url[0:-product.step])

        elif '+' in product.partnumber:
            partnumber_for_url = product.partnumber.split('+')
            partnumber_for_url = partnumber_for_url[0]
            browser.get_url(QUEST_URL + partnumber_for_url[0:-product.step])

        else:
            browser.get_url(QUEST_URL + product.partnumber[0:-product.step])

        soup = browser.get_soup_info()
        self.what_page(product, soup, browser)
        browser.browser.close()

    def what_page(self, product, soup, browser):
        is_main_page = soup.find('div', id='pdpMainContentDiv')

        if is_main_page:
            print('main page')
            self.main_page(product, soup, browser)
            return

        is_result_page = soup.find('div', id='searchResultsTbl')

        if is_result_page:
            print('result page')
            self.result_page(product, soup, browser)
            return

        is_error_page = soup.find('div', class_='alert-danger')

        if is_error_page:
            print('error page')
            product.plan_postavki['message'] = 'Непонятно'
            return

        is_wtf_page = soup.find('div', id='errorpage')

        if is_wtf_page:
            product.step = product.step + 1
            self.check_partnumber_page(product)

        return

    def main_page(self, product, soup, browser, is_alternative=False) -> None:

        self.check_eccn(product, soup)
        self.check_mouser_code(product, soup)

        is_in_stock = self.is_in_stock(product, soup)

        if is_in_stock:
            self.check_price(product, soup)
            self.check_alternative_page(soup, product, browser, is_alternative)
            return

        order_dates = soup.findAll('div', class_='onOrderDate')
        order_quantitys = soup.findAll('div', class_='onOrderQuantity')
        message = 'Notify me when product is in stock'

        if len(order_dates) <= 2:
            product.plan_postavki['message'] = 'Нет даты'
            self.check_alternative_page(soup, product, browser, is_alternative)
            return

        elif (
                order_dates[0].text.strip() == ''
                or message in order_dates[0].text.strip()
                and order_dates[1].text.strip() == ''
        ):
            product.plan_postavki['message'] = 'Нет даты'
            self.check_alternative_page(soup, product, browser, is_alternative)
            return

        first_message = 'View Expected Dates'
        second_mesage = 'You can still purchase this product for backorder'
        first_message_index = None
        second_mesage_index = None

        for index, order_date in enumerate(order_dates):
            order_date = order_date.text.strip()
            if first_message in order_date:
                first_message_index = index
            if second_mesage in order_date:
                second_mesage_index = index

        if first_message_index is not None:
            order_dates.pop(first_message_index)
            order_quantitys.pop(first_message_index)

        if second_mesage_index is not None:
            order_dates.pop(second_mesage_index)
            order_quantitys.pop(second_mesage_index)

        for index, order_date in enumerate(order_dates):
            order_date = order_date.text.strip()
            if 'Expected' in order_date:
                order_quantity = self.to_normal_quantity(
                    order_quantitys[index].text.strip()
                )
                date = self.to_normal_date(order_date)
                product.plan_postavki[date] = f'{order_quantity}шт'
                if order_quantity >= product.quantity:
                    self.check_price(product, soup)

        self.check_alternative_page(soup, product, browser, is_alternative)

    def result_page(self, product, soup, browser):
        results = soup.findAll('a', class_='text-nowrap')
        result_url = False

        for result in results:
            result_text = result.text.strip()
            if product.partnumber.lower() == result_text.lower():
                result_url = result['href']
                browser.get_url(MOUSER_URL + result_url)
                soup = browser.get_soup_info()
                self.what_page(product, soup, browser)
                break

        if not result_url:
            product.plan_postavki['message'] = 'Не нашел'

    def is_in_stock(self, product, soup) -> bool:
        in_stock = soup.find('h2', class_='pdp-pricing-header')

        if not in_stock:
            return False

        in_stock = in_stock.text.strip()

        if 'In Stock:' in in_stock:
            in_stock = in_stock.replace('In Stock: ', '')
            in_stock = self.to_normal_quantity(in_stock)
        else:
            in_stock = 0

        if in_stock >= product.quantity:
            product.plan_postavki['message'] = 'STOCK'
            product.stock = in_stock
            return True

        product.stock = in_stock
        return False

    def check_price(self, product, soup):
        table = soup.find('table', class_='pricing-table')

        if not table:
            return

        table = table.find('tbody')
        table_rows = table.findAll('tr')
        cut_tape_index = 0
        full_real_index = len(table_rows) - 1
	
        for index, row in enumerate(table_rows):
            if row.find('th', id='cuttapehdr'):
                cut_tape_index = index + 1
            if row.find('th', id='reelammohdr'):
                full_real_index = index - 1
        quote_href = table_rows[full_real_index].find('a')
        if quote_href:
            if quote_href.text.strip() == 'Quote':
                full_real_index = full_real_index - 1
        check_maximum_cut = table_rows[full_real_index].find('button').text.strip()
        check_maximum_cut = self.to_normal_quantity(check_maximum_cut)
        if product.quantity >= check_maximum_cut:
            price = table_rows[full_real_index].find(
                'td',
                headers='unitpricecolhdr'
            )
            product.price = self.to_normal_price(price)
            return

        table_rows = table_rows[cut_tape_index:full_real_index + 1]

        for index, row in enumerate(table_rows):
            if not row.find('button'):
                continue

            quantity_in_table = row.find('button').text.strip()
            quantity_in_table = self.to_normal_quantity(quantity_in_table)
            if quantity_in_table > product.quantity:
                price = table_rows[index - 1].find(
                    'td',
                    headers='unitpricecolhdr'
                )
                product.price = self.to_normal_price(price)
                print(quantity_in_table, product.quantity, product.price)
                return

    def to_normal_price(self, price) -> float:
        price = price.text.strip()
        price = price.replace(' ', '')
        price = price.replace('$', '')
        price = price.replace('\n', '')
        if ',' in price:
            price = price.replace(',', '')
        return float(price)

    def to_normal_quantity(self, quantity: str) -> int:
        if ',' in quantity:
            return int(quantity.replace(',', ''))
        else:
            return int(quantity)

    def to_normal_date(self, date):
        month_list = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5,
            'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10,
            'Nov': 11, 'Dec': 12
        }
        date = date.replace('Expected ', '')

        if '/' in date:
            date = date.split('/')
            date = datetime.date(int(date[2]), int(date[0]), int(date[1]))

        if '-' in date:
            date = date.split('-')
            date[1] = month_list[date[1]]
            date[2] = '20' + str(date[2])
            date = datetime.date(int(date[2]), int(date[1]), int(date[0]))

        return date

    def check_eccn(self, product, soup):
        compliance_table = soup.find('div', class_='compliance-table')

        if not compliance_table:
            return

        compliances = compliance_table.findAll('dt')

        for index, compliance in enumerate(compliances):
            compliance = compliance.text.strip()
            if 'ECCN' in compliance:
                compliance_code = compliance_table.findAll('dd')
                product.eccn_code = compliance_code[index].text.strip()
                return

    def check_mouser_code(self, product,
                          soup):  # плохо, что тут намешаны функции
        mouser_code = soup.find(
            'span',
            id='spnMouserPartNumFormattedForProdInfo'
        )

        if mouser_code:
            product.mouser_code = mouser_code.text.strip()
        else:
            product.mouser_code = 'Непонятно'
        try:
            check_partnumber = soup.find('div', class_='pdp-product-card-header')
            check_partnumber = check_partnumber.text.strip()

            if check_partnumber.lower() != product.partnumber.lower():
                product.mouser_code = f'ANALOG/{product.mouser_code}'
        except Exception:
            product.mouser_code = 'Проверить'
            return

        product.maximum = self.check_maximum(soup)

    def check_maximum(self, soup):
        maximum = soup.find('div', id='minmultdisplaytext')
        if maximum:
            maximum = maximum.text.strip()
            maximum = maximum.replace(' ', '')
            if 'Maximum:' in maximum:
                maximum = maximum.split('Maximum:')
                maximum = int(maximum[1])
                return maximum
        return 0

    def check_alternative_page(self, soup, product, browser, is_alternative):
        if is_alternative:
            return False

        print('check_alternative_page')

        alternative_packaging = soup.find('div', id='pdpAltPackaging')
        if alternative_packaging is None:
            return False

        alternative_packaging = alternative_packaging.find('a')
        alternative_partnumber = alternative_packaging.text.strip()
        alternative_packaging_href = alternative_packaging['href']
        print(alternative_packaging_href)
        browser.get_url(MOUSER_URL + alternative_packaging_href)
        product.alternative_partnumber = MouserProduct(
            alternative_partnumber,
            product.index,
            product.quantity
        )
        soup = browser.get_soup_info()
        self.main_page(product.alternative_partnumber, soup, browser, True)

    def is_alternative_better(self, product, alternative_product):

        if product.stock == 0 and 'message' in product.plan_postavki:
            return True

        if product.stock < product.quantity <= alternative_product.stock:
            return True

        if product.maximum and alternative_product.maximum:
            if (
                    product.maximum * 2 < product.quantity <= alternative_product.maximum * 2
            ):
                return True

        if (
                'message' in product.plan_postavki
                and 'message' in alternative_product.plan_postavki
        ):
            return False

        product_date = list(product.plan_postavki.keys())
        product_date = product_date[0]
        alternative_date = list(alternative_product.plan_postavki.keys())
        alternative_date = alternative_date[0]
        try:
            if (
                alternative_date < product_date
                and (
                int(alternative_product.plan_postavki[alternative_date].replace('шт', ''))
                > product.quantity
                )
            ):
                delta = product_date - alternative_date
                if 30 < delta.days < 180:
                    return True
        except Exception:
            return False
        
        return False

    def to_excel(self, product, index, is_alternative):
        # достать все из БД

        if is_alternative:
            for_package = 'Аналог/'
        else:
            for_package = ''
        if 'message' in product.plan_postavki.keys():
            for_package = for_package + product.plan_postavki['message']
        else:
            value_sum = 0

            for date, quantity in product.plan_postavki.items():
                value_sum = value_sum + int(quantity.replace('шт', ''))
                for_package = for_package + self.date_for_package(date, quantity)

                if value_sum >= product.quantity:
                    break

        old_package = self.input_excel['PACKAGE'][index]

        if old_package != old_package:
            old_package = ''

        if not product.stock:
            self.input_excel['PACKAGE'][index] = (
                f'{product.eccn_code}/{for_package}/{old_package}'
            )
        else:
            self.input_excel['PACKAGE'][index] = (
                f'Сток:{product.stock}/{product.eccn_code}/{for_package}/{old_package}'
            )

        self.input_excel['U/P(US$)'][index] = str(product.price)

        if 0 < product.maximum < product.quantity:
            self.input_excel['REMARK'][index] = (
                f'Maximum:{product.maximum}/{product.mouser_code}'
            )
        else:
            self.input_excel['REMARK'][index] = product.mouser_code

    def date_for_package(self, date, quantity):
        today = datetime.date.today()
        delta = date - today
        delta_weeks = delta.days // 7 + 9

        if delta_weeks <= 18:
            delta = f'{str(delta_weeks)} недель;'
        else:
            delta_months = delta_weeks // 4.3
            delta_months = int(delta_months)
            delta = f'{str(delta_months)} месяцев;'

        date = date.strftime('%d-%m-%Y')
        return f'{date}{DELIVERY_TIME}/({quantity}/{delta})'


class KompelParametricaParser(Parser):
    csv_file_name: str = 'C:\\python_apps\\ozl_bot\\my_bot_for_ozl\\for_urm.csv'
    # csv_file_name: str = 'G:\\PythonProd\\my_bot_for_ozl\\for_urm.csv'
    csv_file = None

    def get_partnumbers_and_quantities(self) -> None:
        partnumbers: Series = self.input_excel['Партномер']  # проверить typing
        quantities: Series = self.input_excel['Кол-во']  # проверить typing
        for partnumber in partnumbers:
            partnumber: str = str(partnumber).replace('\n', '')
            self.partnumbers.append(partnumber)
        for quantity in quantities:
            quantity: str = str(quantity).replace(' ', '')
            self.quantities.append(int(quantity))
        self.start_index = self.base.check_data_base(
            self.partnumbers,
            self.quantities
        )

    def check_purtnumbers_info_kompel(self):
        self.to_csv()
        browser = StealthBrowser()
        self.login_kompel(browser)
        table_kompel = self.get_table_kompel(browser)
        self.to_excel_kompel(table_kompel)

        self.input_excel.to_excel(self.output_excel_name, index=False)

    def to_csv(self):
        self.csv_file = open(self.csv_file_name, 'w', newline='')
        writer = csv.writer(self.csv_file)

        for i in range(len(self.input_excel['Партномер'])):
            if '%' in self.input_excel['Партномер'][i]:
                continue
            writer.writerow(
                [self.input_excel['Партномер'][i].replace('\n', ''),
                 self.input_excel['Производитель'][i],
                 self.input_excel['Кол-во'][i]])
        self.csv_file.close()

    def login_kompel(self, browser):
        browser.get_url(URL_URM)
        soup = browser.get_soup_info()
        login_info = soup.find('div', id='logon_message_text')

        if login_info is not None:
            browser.browser.find_element(By.ID, 'username').send_keys(LOGIN)
            browser.browser.find_element(By.ID, 'password_input').send_keys(
                PASSWORD)
            browser.browser.find_element(By.NAME, 'Login').click()

        # else выдать ошибку о неудачном логгировании

    def get_table_kompel(self, browser):
        browser.browser.find_element(By.ID, 'urm_search_button').click()
        browser.browser.find_element(By.NAME, 'uploadFile').send_keys(
            self.csv_file_name)
        sleep(10)
        browser.browser.find_element(By.NAME, 'uploadButton').click()
        wait = WebDriverWait(browser.browser, 3000)
        wait.until(ec.presence_of_element_located((By.ID, 'search_results')))
        soup = browser.get_soup_info()
        soup = soup.find('table', id='search_results')
        table_kompel = soup.findAll('tr')
        browser.browser.close()
        return table_kompel

    def to_excel_kompel(self, table):
        print('self.partnumbers is')
        print(self.partnumbers)
        for index, partnumber in enumerate(self.input_excel['Партномер']):
            partnumber = partnumber.replace('\n', '')

            if '%' in partnumber:
                self.input_excel['Цена'][index] = 1
                continue

            info_kompel = self.find_in_table(table, partnumber,
                                             self.quantities[index])
            print(partnumber, info_kompel['quantity_in_stock'])

            if self.input_excel['ДопИнформация'][index] != self.input_excel['ДопИнформация'][index]:
                self.input_excel['ДопИнформация'][index] = ''

            if int(info_kompel['quantity_in_stock']) == 0 or int(info_kompel['quantity_in_stock']) * 5 <= self.quantities[index]:
                info_kompel_dms = self.check_dms_info(table, partnumber, self.quantities[index])
                print(info_kompel_dms)
                if info_kompel_dms:
                    self.input_excel['ДопИнформация'][index] = '/'.join(info_kompel_dms['доп.инфо']) + f'/{self.input_excel["ДопИнформация"][index]}'
                    self.input_excel['Цена'][index] = info_kompel_dms['price']
                else:
                    self.input_excel['Цена'][index] = 1

            elif int(info_kompel['quantity_in_stock']) <= self.quantities[
                index] and int(info_kompel['quantity_in_stock']) * 5 > self.quantities[index]:
                self.input_excel['ДопИнформация'][
                    index] = f'Stock:{info_kompel["quantity_in_stock"]}/{self.input_excel["ДопИнформация"][index]}'
                self.input_excel['Цена'][index] = 1

            elif int(info_kompel['quantity_in_stock']) > self.quantities[
                index]:
                self.input_excel['ДопИнформация'][
                    index] = f'Stock:{info_kompel["quantity_in_stock"]}/{self.input_excel["ДопИнформация"][index]}'
                self.input_excel['Цена'][index] = info_kompel['price']
                continue

            else:
                self.input_excel['Цена'][index] = 1

    def find_in_table(self, table, part, quantity):

        for tr in table:
            td_list = tr.findAll('td')

            if len(td_list) < 6:
                continue

            if td_list[6].find('a') is None:
                continue

            name = td_list[6].find('a').text.strip()

            if part.lower() in name.lower():
                quantity_in_stock = td_list[9].text.strip()

                if quantity_in_stock == '0':
                    return {
                        'quantity_in_stock': quantity_in_stock,
                        'price': 1.0
                    }

                if 'Распродажа' in td_list[11].text.strip():
                    price = td_list[11].findAll('span')
                    price = price[1].text.strip()
                    price = float(price.replace(',', '.'))
                    return {
                        'quantity_in_stock': quantity_in_stock,
                        'price': price
                    }

                for i in range(12, 24, 2):

                    if td_list[i].text.strip() is None:
                        break

                    if int(td_list[i].text.strip()) > quantity:
                        price = td_list[i - 1].find('span')
                        price = price.text.strip()
                        price = float(price.replace(',', '.'))
                        return {
                            'quantity_in_stock': quantity_in_stock,
                            'price': price
                        }

        return {
            'quantity_in_stock': 0,
            'price': 1
        }

    def check_dms_info(self, table, partnumber, quantity):
        print('check_dms_info', partnumber)
        for index, tr in enumerate(table):
            td_list = tr.findAll('td')
            if len(td_list) < 6:
                continue

            if td_list[6].find('a') is None:
                continue

            name = td_list[6].find('a').text.strip()
            dms = None

            if partnumber.lower() in name.lower():
                print(f'{partnumber} was found')
                dms = table[index + 1].find('table', class_='dms')

                if dms is None:
                    print('DMS is None')
                    continue

            else:
                continue

            if dms is not None:
                return self.check_dms_table(dms, partnumber, quantity)
            else:
                return False

    def check_dms_table(self, dms, partnumber, quantity):
        print('check_dms_table', partnumber)
        table = dms.find('tbody')
        table = table.findAll('tr')
        start_index = None
        end_index = None
        result = {
                'доп.инфо': [],
                'price': 1.0
            }

        for index, tr in enumerate(table):
            for td in tr.findAll('td'):
                if 'рабочи' in td.text.strip():
                    start_index = index
                    break
                if start_index is not None:
                    break

        if start_index is None:
            return False

        table = table[start_index:]

        for index, tr in enumerate(table[1:]):
            for td in tr.findAll('td'):
                if 'рабочи' in td or 'недели' in td:
                    end_index = index
                    break
                if start_index is not None:
                    break

        print(start_index, end_index)

        if end_index is not None:
            table = table[:end_index]

        first_row = table[0].findAll('td')

        if 'склад' not in first_row[-2].text.strip():
            result['доп.инфо'].append('ДМС')
        else:
            result['доп.инфо'].append('Едет')

        result['доп.инфо'].append(first_row[4].text.strip())
        moq = int(first_row[5].text.strip())
        mpq = int(first_row[7].text.strip())
        in_stock = int(first_row[9].text.strip())

        if mpq != 1:
            result['доп.инфо'].append(f'MPQ {mpq}')

        if moq != 1:
            result['доп.инфо'].append(f'MIN {moq}')

        if in_stock * 5 <= quantity:
            result['доп.инфо'].append(f'ДМС только {in_stock}')
            return result
        elif in_stock <= quantity < in_stock * 5:
            result['доп.инфо'].append(f'Только {in_stock}!!')
            price = table[-1].find('span', class_='price_mst').text.strip()
            result['price'] = float(price.replace(',', '.'))
            return result
        else:
            result['доп.инфо'].append(f'{in_stock}шт')

        if int(first_row[6].text.strip()) >= quantity:
            price = table[0].find('span', class_='price_mst').text.strip()
            result['price'] = float(price.replace(',', '.'))
            return result

        for index, row in enumerate(table[1:]):
            rows = row.findAll('td')
            if int(rows[2].text.strip()) >= quantity:
                price = row.find('span', class_='price_mst').text.strip()
                result['price'] = float(price.replace(',', '.'))
                return result

        result['price'] = 1

        return result


class PromelectronicaParser(Parser):

    def get_partnumbers_and_quantities(self) -> None:
        partnumbers: Series = self.input_excel['Партномер']  # проверить typing
        quantities: Series = self.input_excel['Кол-во']  # проверить typing
        for partnumber in partnumbers:
            partnumber: str = str(partnumber).replace('\n', '')
            self.partnumbers.append(partnumber)
        for quantity in quantities:
            quantity: str = str(quantity).replace(' ', '')
            self.quantities.append(int(quantity))
        self.start_index = self.base.check_data_base(
            self.partnumbers,
            self.quantities
        )

    def check_partnumbers_info_prom(self):  # typing

        for index, partnumber in enumerate(
                self.partnumbers,
                start=self.start_index
        ):
            product = UsualProduct(
                partnumber,
                index,
                int(self.quantities[index])
            )
            dop_info = self.input_excel['ДопИнформация'][index]

            if not product.is_nan(dop_info):
                product.to_dop_info.append(dop_info)

            self.check_partnumber_page_prom(product)
            print(product.partnumber + ' Done!')
            self.to_excel_prom(product)

        self.input_excel.to_excel(self.output_excel_name, index=False)

    def check_partnumber_page_prom(self, product):
        browser = StealthBrowser()
        print(product.partnumber)

        # Реализовать изменение знаков в партномере

        browser.get_url(PROM_URL + product.partnumber)

        soup = browser.get_soup_info()
        self.what_page_prom(product, soup, browser)
        browser.browser.close()

    def what_page_prom(self, product, soup, browser):
        is_main_page = soup.find('div', class_='box-product')

        if is_main_page:
            print('main page')
            self.main_page_prom(product, soup)
            return

        is_result_page = soup.find('div', class_='product-preview')

        if is_result_page:
            print('result page')
            self.result_page_prom(product, soup, browser)
            return

        return

    def main_page_prom(self, product, soup):
        self.check_articule_prom(product, soup)
        table = self.find_main_table_prom(soup)

        if not table:
            return

        if not self.is_in_stock_prom(product, table):
            return

        self.check_min_and_moq_prom(product, table)

        if product.min_order_quan <= product.quantity <= product.stock:
            self.check_price_prom(product, table)

        print(product.partnumber, product.min_order_quan, product.min_part_quan, product.stock, product.price)

    def find_main_table_prom(self, soup):
        product_tables = soup.find('div', class_='popup-product-table')
        product_tables = product_tables.findAll('div',
                                                class_='js-accordion-wrap')
        result_table = False

        try:
            for table in product_tables:
                title = table.find('div', class_='popup-product-table__title')
                if title.text.strip() == 'Оптовый склад «Промэлектроника»':
                    result_table = table
                    break

        except Exception:
            return False

        return result_table

    def is_in_stock_prom(self, product, table):
        try:
            in_stock = table.find('div', class_='col-table_4')
            in_stock = in_stock.find('span', class_='table-list__counter')
            in_stock = in_stock.text.strip()
            in_stock = in_stock.replace('шт', '')
            in_stock = int(in_stock.replace(' ', ''))

        except Exception as e:
            return False

        product.stock = in_stock
        return True

    def check_articule_prom(self, product, soup):
        try:
            partnumber_on_main_page = soup.find('div', class_='popup-product-inf__articul')
            partnumber_on_main_page = partnumber_on_main_page.text.strip()

            if partnumber_on_main_page.lower() != product.partnumber.lower():
                product.to_dop_info.append(f'Замена:{partnumber_on_main_page}')

            articule = soup.find('div', class_='product-table')
            articule = articule.find('div', class_='product-table__title')
            articule = articule.find('span')
            product.articule = articule.text.strip()

        except Exception:
            product.to_dop_info.append('Проверить!!!')
            return

    def check_min_and_moq_prom(self, product, table):

        try:
            min_part_quan = table.find('div', class_='col-table_5')
            min_part_quan = min_part_quan.find(
                'span',
                class_='table-list__counter'
            )
            min_part_quan = min_part_quan.text.strip()
            min_part_quan = min_part_quan.replace('шт', '')
            min_part_quan = int(min_part_quan.replace(' ', ''))
            print('MPQ', min_part_quan)
            product.min_part_quan = min_part_quan

            min_order_quan = table.find('div', class_='col-table_7')
            min_order_quan = min_order_quan.find(
                'div',
                class_='table-list__mob-min'
            )
            min_order_quan = min_order_quan.find(
                'span',
                class_='table-list__counter'
            )
            min_order_quan = min_order_quan.text.strip()
            min_order_quan = min_order_quan.replace('шт', '')
            min_order_quan = min_order_quan.replace('Мин:', '')
            min_order_quan = int(min_order_quan.replace(' ', ''))
            print('MOQ', min_order_quan)
            product.min_order_quan = min_order_quan

        except Exception as e:
            print(e)
            return

    def check_price_prom(self, product, table):
        print('checking price')
        try:
            quantities = table.find('div', class_='col-table_1')
            quantities = quantities.findAll('span', class_='table-list__stocke')
            prices = table.find('div', class_='col-table_2')
            prices = prices.findAll('span', class_='table-list__total-price')

        except Exception as e:
            return

        last_quantity = quantities[-1].text.strip()
        last_quantity = int(last_quantity.replace('+', ''))

        if product.quantity >= last_quantity:
            price = prices[-1].text.strip()
            price = price.replace(' ', '')
            price = price.replace('₽', '')
            price = float(price.replace(',', '.'))
            product.price = price
            return

        for index, quantity in enumerate(quantities):
            quantity = quantity.text.strip()
            print(quantity)
            quantity = int(quantity.replace('+', ''))

            if quantity > product.quantity:
                price = prices[index-1].text.strip()
                price = price.replace(' ', '')
                price = price.replace('₽', '')
                price = float(price.replace(',', '.'))
                print(price)
                product.price = price
                return

    def result_page_prom(self, product, soup, browser):
        partnumbers = soup.findAll('div', class_='table-list__item')

        for partnumber in partnumbers:
            partnumber_url = partnumber.find('a', class_='product-preview__title')
            partnumber = partnumber_url.text.strip()
            if product.partnumber.lower() in partnumber.lower():
                browser.get_url(partnumber_url['href'])
                soup = browser.get_soup_info()
                self.what_page_prom(product, soup, browser)
                break

    def to_excel_prom(self, product):
        print('to_excel')
        print(product.partnumber, product.min_order_quan, product.min_part_quan, product.stock, product.price, product.to_dop_info)
        index = product.index

        if not product.min_part_quan:
            product.to_dop_info.append('MPQ:???')
        elif product.min_part_quan != 1:
            product.to_dop_info.append(f'MPQ:{product.min_part_quan}')

        if not product.min_order_quan:
            product.to_dop_info.append('MOQ:???')
        elif product.min_order_quan != 1:
            product.to_dop_info.append(f'MOQ:{product.min_order_quan}')

        product.to_dop_info.append(f'Сток:{product.stock}')
        product.to_dop_info.reverse()

        print(product.to_dop_info)

        if product.to_dop_info:
            self.input_excel['ДопИнформация'][index] = '/'.join(product.to_dop_info)

        self.input_excel['Примечание'][index] = product.articule
        self.input_excel['Цена'][index] = product.price


class LcscParser(Parser):

    def check_partnumbers_info_lcsc(self):
        for index, partnumber in enumerate(
                self.partnumbers,
                start=self.start_index
        ):
            product = UsualProduct(
                partnumber,
                index,
                int(self.quantities[index])
            )
            dop_info = self.input_excel['PACKAGE'][index]
            if not product.is_nan(dop_info):
                product.to_dop_info.append(dop_info)

            self.check_partnumber_page_lcsc(product)
            print(product.partnumber + ' Done!')
            self.to_excel_lcsc(product)

        self.input_excel.to_excel(self.output_excel_name, index=False)

    def check_partnumber_page_lcsc(self, product):
        browser = StealthBrowser()
        print(product.partnumber)

        # Реализовать изменение знаков в партномере

        browser.get_url(LCSC_URL_QUEST + product.partnumber)
        soup = browser.get_soup_info()
        self.what_page_lcsc(product, soup, browser)
        browser.browser.close()

    def what_page_lcsc(self, product, soup, browser):
        """diolog_window = soup.find('div', class_='v-dialog')

        if diolog_window:
            browser.browser.find_element(By.TAG_NAME, 'input').click()
            browser.browser.find_element(By.TAG_NAME, 'button').click()
            browser.get_url(LCSC_URL_QUEST + product.partnumber)
            soup = browser.get_soup_info()
            self.what_page_lcsc(product, soup, browser)"""
        is_main_page = soup.find('div', class_='product-detail')

        if is_main_page:
            print('main page')
            self.main_page_lcsc(product, soup)
            return

        is_result_page = soup.find('div', class_='product-table')

        if is_result_page:
            print('result page')
            self.result_page_lcsc(product, soup, browser)
            return

        is_empty_page = soup.find('div', class_='empty')

        if is_empty_page:
            print('no results')
            return

        return

    def main_page_lcsc(self, product, soup):
        self.check_articule_lcsc(product, soup)

        if not self.is_in_stock_lcsc(product, soup):
            return

        self.check_min_and_moq_lcsc(product, soup)

        if product.min_order_quan <= product.quantity <= product.stock:
            self.check_price_lcsc(product, soup)

        print(product.partnumber, product.min_order_quan, product.min_part_quan, product.stock, product.price)

    def check_articule_lcsc(self, product, soup):
        try:
            table = soup.find('table', class_='info-table')
            rows = table.findAll('tr')
            partnumber_on_main_page = ''

            for row in rows:
                td_tags_in_row = row.findAll('td')
                for index, td in enumerate(td_tags_in_row):
                    if 'Mfr. Part #' in td.text.strip():
                        partnumber_on_main_page = td_tags_in_row[index+1].text.strip()
                    if 'LCSC Part #' in td.text.strip():
                        articule = td_tags_in_row[index+1].text.strip()
                    if 'Manufacturer' in td.text.strip():
                        manufacturer = td_tags_in_row[index + 1].text.strip()

            product.to_dop_info.append(manufacturer)

            if partnumber_on_main_page.lower() != product.partnumber.lower():
                product.to_dop_info.append(f'Замена:{partnumber_on_main_page}')

            product.articule = articule

        except Exception:
            product.to_dop_info.append('Проверить!!!')
            return

    def is_in_stock_lcsc(self, product, soup):
        try:
            stock_info = soup.find('div', class_='head')
            stock = stock_info.find('div').text.strip()
            stock = stock.replace('In Stock: ', '')
            product.stock = int(stock)

        except Exception as e:
            print(e)
            return False

        return True

    def check_min_and_moq_lcsc(self, product, soup):

        try:
            mpq_moq_info = soup.find('div', class_='buy-tips')
            mpq_moq_info = mpq_moq_info.text.strip()
            mpq_moq_info = mpq_moq_info.replace(':', '')
            mpq_moq_info = mpq_moq_info.replace('  ', '')
            min_order_quan, min_part_quan = mpq_moq_info.split(' ')

            min_part_quan = int(min_part_quan.replace('Multiples', ''))
            print('MPQ', min_part_quan)
            product.min_part_quan = min_part_quan
            min_order_quan = int(min_order_quan.replace('Minimum', ''))
            print('MOQ', min_order_quan)
            product.min_order_quan = min_order_quan

        except Exception as e:
            print(e)
            return

    def check_price_lcsc(self, product, soup):
        print('checking price')
        try:
            table = soup.find('div', class_='ladder-price')
            table = table.find('table', class_='main-table')
            quantities = table.findAll('td', class_='tbody-num')
            prices = table.findAll('span')
            last_quantity = quantities[-1].text.strip()
            last_quantity = int(last_quantity.replace('+', ''))

            if product.quantity >= last_quantity:
                price = prices[-1].text.strip()
                price = price.replace(' ', '')
                price = price.replace('US$', '')
                price = float(price)
                product.price = price
                return

            for index, quantity in enumerate(quantities):
                quantity = quantity.text.strip()
                print(quantity)
                quantity = int(quantity.replace('+', ''))

                if quantity > product.quantity:
                    price = prices[index-1].text.strip()
                    price = price.replace(' ', '')
                    price = price.replace('US$', '')
                    price = float(price)
                    print(price)
                    product.price = price
                    return
        except Exception as e:
            print(e)
            return

    def result_page_lcsc(self, product, soup, browser):
        raws = soup.find('div', class_='product-table')
        raws = raws.findAll('div', class_='table-area')
        raws = raws[1].find('tbody')
        raws = raws.findAll('tr')

        for raw in raws:
            td_tags = raw.findAll('td')
            partnumber_url = td_tags[4].find('a')
            partnumber = partnumber_url.text.strip()
            if product.partnumber.lower() in partnumber.lower():
                browser.get_url(LSCS_URL + partnumber_url['href'])
                soup = browser.get_soup_info()
                self.what_page_lcsc(product, soup, browser)
                break

    def to_excel_lcsc(self, product):
        print('to_excel')
        print(product.partnumber, product.min_order_quan, product.min_part_quan, product.stock, product.price, product.to_dop_info)
        index = product.index

        if not product.min_part_quan:
            product.to_dop_info.append('MPQ:???')
        elif product.min_part_quan != 1:
            product.to_dop_info.append(f'MPQ:{product.min_part_quan}')

        if not product.min_order_quan:
            product.to_dop_info.append('MOQ:???')
        elif product.min_order_quan != 1:
            product.to_dop_info.append(f'MOQ:{product.min_order_quan}')

        product.to_dop_info.append(f'Сток:{product.stock}')
        product.to_dop_info.reverse()

        print(product.to_dop_info)

        if product.to_dop_info:
            self.input_excel['PACKAGE'][index] = '/'.join(product.to_dop_info)

        self.input_excel['REMARK'][index] = product.articule
        self.input_excel['U/P(US$)'][index] = product.price
