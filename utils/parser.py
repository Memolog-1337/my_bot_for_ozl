import os
import datetime
import json
import random

from selenium.webdriver import Chrome, ChromeOptions
from selenium_stealth import stealth
from bs4 import BeautifulSoup
import pandas as pd
from pandas.core.series import Series

pd.options.mode.chained_assignment = None

MOUSER_URL: str = 'https://www.mouser.com'
QUEST_URL: str = 'https://www.mouser.com/c/?q='
PROXY_LIST: list = [
    '45.85.163.25:8000',
    '45.85.162.24:8000',
    '45.85.163.97:8000',
    '45.85.161.86:8000',
    '45.85.163.50:8000',
]
PATH_TO_CHROMEDRIVER: str = ('D:\\Ycheba\\PythonED\\'
                             'Chromedriver\\chromedriver.exe')
DELIVERY_TIME = '+8 нед'


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
    partnumbers: list = []
    quantities: list = []
    input_excel_name: str
    output_excel_name: str
    done_products_file_name: str
    start_index: int

    def __init__(
            self,
            input_excel_name: str,
            output_excel_name: str,
            done_products_file_name: str
    ) -> None:
        self.input_excel_name = input_excel_name
        self.output_excel_name = output_excel_name
        self.done_products_file_name = done_products_file_name
        self.input_excel: pd = pd.read_excel(
            input_excel_name,
            sheet_name='Лист1'
        )  # проверить typing
        self.output_excel: pd = pd.read_excel(
            output_excel_name,
            sheet_name='Sheet1'
        )  # проверить typing
        self.base = DataBase(self.done_products_file_name)
        self.base.create_base()  # typing

    def get_partnumbers_and_quantities(self) -> None:
        partnumbers: Series = self.input_excel['PART #']  # проверить typing
        quantities: Series = self.input_excel['QTY(PCS)']  # проверить typing
        for partnumber in partnumbers:
            partnumber: str = str(partnumber).replace('\n', '')
            self.partnumbers.append(partnumber)
        for quantity in quantities:
            quantity: str = str(quantity).replace(' ', '')
            self.quantities.append(quantity)
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

            # index_to_base = (
            #     f'{str(index)}/{partnumber}/{self.quantities[index]}'
            # )
            # self.base.to_base(index_to_base, product)
            self.to_excel(product, index)

        self.input_excel.to_excel(self.output_excel_name)

    def check_partnumber_page(self, product: MouserProduct) -> None:
        browser = StealthBrowser()

        if '#' in product.partnumber:
            partnumber_for_url = product.partnumber.split('#')
            partnumber_for_url = partnumber_for_url[0]
            browser.get_url(QUEST_URL + partnumber_for_url)

        elif '+' in product.partnumber:
            partnumber_for_url = product.partnumber.split('+')
            partnumber_for_url = partnumber_for_url[0]
            browser.get_url(QUEST_URL + partnumber_for_url)

        else:
            browser.get_url(QUEST_URL + product.partnumber)

        soup = browser.get_soup_info()
        self.what_page(product, soup, browser)
        browser.browser.close()

    def what_page(self, product, soup, browser):
        is_main_page = soup.find('div', id='pdpMainContentDiv')

        if is_main_page:
            self.main_page(product, soup, browser, False)
            return

        is_result_page = soup.find('div', id='searchResultsTbl')

        if is_result_page:
            self.result_page(product, soup, browser)
            return

        is_error_page = soup.find('div', class_='alert-danger')

        if is_error_page:
            product.plan_postavki['message'] = 'Непонятно'
            return

        return

    def main_page(self, product, soup, browser, is_alternative) -> None:
        """
                partnumber_on_page = soup.find('div', id='pdpProdInfo')
                partnumber_on_page = partnumber_on_page.find('h1',
                                                             class_='panel-title')
                partnumber_on_page = partnumber_on_page.text.strip()
        """

        self.check_eccn(product, soup)
        self.check_mouser_code(product, soup)

        is_in_stock = self.is_in_stock(product, soup)

        if is_in_stock:
            self.check_price(product, soup)
            return

        order_dates = soup.findAll('div', class_='onOrderDate')
        order_quantitys = soup.findAll('div', class_='onOrderQuantity')
        message = 'Notify me when product is in stock'

        if len(order_dates) <= 2:
            product.plan_postavki['message'] = 'Нет даты'
            return
        elif order_dates[0].text.strip() == '' or message in order_dates[0].text.strip() and order_dates[1].text.strip() == '':
            product.plan_postavki['message'] = 'Нет даты'
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

        if not is_alternative:
            self.check_alternative_page(soup, product, browser)

    def result_page(self, product, soup, browser):
        results = soup.findAll('a', class_='text-nowrap')
        for result in results:
            result_text = result.text.strip()
            if product.partnumber == result_text:
                result_url = result['href']
                browser.get_url(MOUSER_URL + result_url)
                soup = browser.get_soup_info()
                self.what_page(product, soup, browser)

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
        full_real_index = len(table_rows)-1

        for index, row in enumerate(table_rows):
            if row.find('th', id='cuttapehdr'):
                cut_tape_index = index + 1
            if row.find('th', id='reelammohdr'):
                full_real_index = index - 1

        if table_rows[full_real_index].find('a').text.strip() == 'Quote':
            full_real_index = full_real_index - 1

        check_maximum_cut = table_rows[full_real_index].find('a').text.strip()
        check_maximum_cut = self.to_normal_quantity(check_maximum_cut)
        if product.quantity >= check_maximum_cut:
            price = table_rows[full_real_index].find(
                'td',
                headers='unitpricecolhdr'
            )
            product.price = self.to_normal_price(price)
            return

        table_rows = table_rows[cut_tape_index:full_real_index]

        for index, row in enumerate(table_rows):
            if not row.find('a'):
                continue

            quantity_in_table = row.find('a').text.strip()
            quantity_in_table = self.to_normal_quantity(quantity_in_table)

            if quantity_in_table > product.quantity:
                price = table_rows[index-1].find(
                    'td',
                    headers='unitpricecolhdr'
                )
                product.price = self.to_normal_price(price)
                return

    def to_normal_price(self, price) -> float:
        price = price.text.strip()
        price = price.replace(' ', '')
        price = price.replace('$', '')
        price = price.replace('\n', '')
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

    def check_mouser_code(self, product, soup):  # плохо, что тут намешаны функции
        mouser_code = soup.find(
            'span',
            id='spnMouserPartNumFormattedForProdInfo'
        )

        if mouser_code:
            product.mouser_code = mouser_code.text.strip()
        else:
            product.mouser_code = 'Непонятно'

        check_partnumber = soup.find('div', class_='pdp-product-card-header')
        check_partnumber = check_partnumber.text.strip()
        if check_partnumber.lower() != product.partnumber.lower():
            product.mouser_code = f'ANALOG/{product.mouser_code}'

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

    def check_alternative_page(self, soup, product, browser):
        alternative_packaging = soup.find('div', id='pdpAltPackaging')

        if alternative_packaging is None:
            return False

        alternative_packaging = alternative_packaging.find('a')
        alternative_partnumber = alternative_packaging.text.strip()
        alternative_packaging_href = alternative_packaging['href']
        browser.get(MOUSER_URL + alternative_packaging_href)
        alternative_product = MouserProduct(
            alternative_partnumber,
            product.index,
            product.quantity
        )
        soup = browser.get_soup_info()
        self.main_page(alternative_product, soup, browser, True)

        if self.is_alternative_better(product, alternative_product):
            product = alternative_product

    def is_alternative_better(self, product, alternative_product):

        if product.stock == 0 and 'message' in product.plan_postavki:
            return True

        if product.stock < product.quantity <= alternative_product.quantity:
            return True

        if product.maximum and alternative_product.maximum:
            if (
                product.maximum*2 < product.quantity <= alternative_product.maximum*2
            ):
                return True

        if (
            'message' in product.plan_postavki
            and 'message' in alternative_product.plan_postavki
        ):
            return False

        product_date = product.plan_postavki.keys()
        product_date = product_date[0]
        product_date = product_date
        alternative_date = alternative_product.plan_postavki.keys()
        alternative_date = alternative_date[0]

        if (
            alternative_date < product_date
            and alternative_product.plan_postavki[alternative_date] > product.quantity
        ):
            delta = product_date - alternative_date
            if 30 < delta.days < 180:
                return True

        return False

    def to_excel(self, product, index):
        # достать все из БД
        for_package = ''
        if 'message' in product.plan_postavki.keys():
            for_package = product.plan_postavki['message']
        else:
            value_sum = 0

            for date, quantity in product.plan_postavki.items():
                value_sum = value_sum + int(quantity.replace('шт', ''))
                for_package = self.date_for_package(date, quantity)

                if value_sum >= product.quantity:
                    break

        if not product.stock:
            self.input_excel['PACKAGE'][index] = (
                f'{product.eccn_code}/{for_package}'
            )
        else:
            self.input_excel['PACKAGE'][index] = (
                f'Сток:{product.stock}/{product.eccn_code}/{for_package}'
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
        delta_weeks = delta.days // 7 + 8

        if delta_weeks <= 18:
            delta = f'{str(delta_weeks)} недель;'
        else:
            delta_months = delta_weeks // 4.3
            delta_months = int(delta_months)
            delta = f'{str(delta_months)} месяцев;'

        date = date.strftime('%d-%m-%Y')
        return f'{date}{DELIVERY_TIME}/({quantity}/{delta})'
