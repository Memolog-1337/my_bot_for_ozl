class Product:
    parametrica: list
    korpus: str
    nominal: str
    pogreshnost: str
    partnumber: str
    manufacturer: str
    manufacturers: list = ['YAG', 'MUR', 'SAMSUNG', 'BOURNS']
    dop_info: str
    korpuses: list = [
        '0101', '0201', '0202', '0303', '0402', '0502', '0504', '0505', '0602',
        '0603', '0704', '0805', '1005', '1111', '1206', '1210', '1515', '1805',
        '1808', '1812', '2020', '2220', '2320', '2520', '2525', '2824', '2924',
        '3020', '3025', '3333', '3530', '3838', '4040', '4540', '5550'
    ]
    nominals_variants: dict
    pogreshnost_values: list

    def __init__(self, parametrica_from_table: str, manufacturer: str) -> None:
        parametrica_from_table = parametrica_from_table.replace('\n', '')
        parametrica_from_table = parametrica_from_table.replace(' ', '')
        parametrica_from_table = parametrica_from_table.lower()

        if ',' in parametrica_from_table:
            parametrica_from_table = parametrica_from_table.replace(',', '.')

        self.parametrica = parametrica_from_table.split('-')
        self.check_manufacturer(manufacturer)

    def is_nan(self, num: str) -> bool:
        return num != num

    def check_korpus(self, parametr: str) -> bool:
        for korpus in self.korpuses:
            if korpus in parametr:
                self.korpus = korpus
                return True

        return False

    def check_manufacturer(self, manufacturer: str) -> None:
        if self.is_nan(manufacturer):
            return
        else:
            manufacturer = manufacturer.upper()

        for manufacturer_unit in self.manufacturers:
            if manufacturer_unit in manufacturer:
                self.manufacturer = manufacturer_unit
                return

        self.add_to_dop_info('др производитель')
        return

    def check_nominal(self, parametr: str) -> bool:
        for key, value in self.nominals_variants.items():
            if key in parametr:
                self.nominal = parametr.replace(key, value)
                return True

        return False

    def add_to_dop_info(self, dop_info: str) -> None:
        if self.dop_info:
            self.dop_info = f'{dop_info}/{self.dop_info}'
        else:
            self.dop_info = dop_info

    def take_analog_pogreshnost(self, data_base) -> bool:
        if self.pogreshnost == self.pogreshnost_values[-1]:
            return False

        start_index = self.pogreshnost_values.index(self.pogreshnost)
        start_pogreshnost = self.pogreshnost

        for pogreshnost in self.pogreshnost_values[start_index:]:
            self.pogreshnost = pogreshnost
            if self.take_normal_partnumber(data_base):
                self.add_to_dop_info(f'др погрешность - {self.pogreshnost}%')
                return True

        self.pogreshnost = start_pogreshnost
        return False

    def take_normal_partnumber(self, data_base):
        pass


class Resistor(Product):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.nominals_variants = {
            'ом': 'ом',
            'ком': 'ком',
            'ohm': 'ом',
            'kohm': 'ком',
            'r': 'ом',
            'k': 'ком'
        }
        self.pogreshnost_values = ['20', '10', '5', '1']
        # Тут бы сделать как-то, чтобы не проверять
        # на каждом параметре каждый признак
        for parametr in self.parametrica:
            if self.check_pogreshnost(parametr):
                break
            elif self.check_korpus(parametr):
                break
            elif self.check_nominal(parametr):
                break

    def check_pogreshnost(self, parametr: str) -> bool:
        if '%' in parametr:
            self.pogreshnost = parametr.replace('%', '')
            return True

        return False

    def take_normal_partnumber(self, data_base) -> bool:  # Нужен typing
        try:
            result = data_base[self.korpus][self.nominal][self.pogreshnost]
        except KeyError:
            return False

        if self.manufacturer:
            if self.manufacturer in result.keys():
                result = result[self.manufacturer]
                if self.partnumber_from_data(result, self.manufacturer):
                    return True
            else:
                self.add_to_dop_info('др производитель')

        for manufacturer in self.manufacturers:
            if manufacturer not in result.keys():
                continue
            if self.partnumber_from_data(result[manufacturer], manufacturer):
                self.manufacturer = manufacturer
                return True

        return False

    def partnumber_from_data(self, result: list, manufacturer: str) -> bool:
        if manufacturer == 'YAG':
            for part in result:
                if 'RC' and '-07' in part:
                    self.partnumber = part
                    return True
        elif manufacturer == 'BOURNS':
            for part in result:
                if 'ELF' in part:
                    self.partnumber = part
                    return True
        elif manufacturer == 'SAMSUNG':
            self.partnumber = result[0]
            return True

        return False


class Capasitor(Product):
    term_coef: str
    voltage: str

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.nominals_variants = {
            'пф': 'пф',
            'мкф': 'мкф',
            'pf': 'пф',
            'uf': 'мкф',
            'нф': 'нф',
            'nf': 'нф'
        }
        self.pogreshnost_values = [
            '20', '10', '5', '1', '0.5пф', '0.25пф', '0.1пф', '0.05пф'
        ]
        # Тут бы сделать как-то, чтобы не проверять
        # на каждом параметре каждый признак
        # список методов у родителя? проходить по каждому методу и удалять,
        # если он сработал?
        for parametr in self.parametrica:
            if self.check_korpus(parametr):
                break
            elif self.check_nominal(parametr):
                break
            elif self.check_pogreshnost(parametr):
                break
            elif self.check_term_coef(parametr):
                break
            elif self.check_voltage(parametr):
                break

    def check_nominal(self, parametr: str) -> bool:
        for key, value in self.nominals_variants.items():
            if key in parametr:
                self.nominal = parametr.replace(key, value)
                if 'нф' in self.nominal:
                    self.nominal = self.convert_nf(self.nominal)
                return True

        return False

    def convert_nf(self, nominal: str) -> str:
        nominal = float(nominal.replace('нф', ''))
        if nominal > 10:
            return f'{nominal / 1000}мкф'
        else:
            return f'{nominal * 1000}пф'

    def check_pogreshnost(self, parametr: str) -> bool:
        if 'pf' in parametr:
            parametr = parametr.replace('pf', 'пф')

        if '%' in parametr:
            self.pogreshnost = parametr.replace('%', '')
            return True

        return False

    def check_term_coef(self, parametr: str) -> bool:
        term_coef_list = ['c0g', 'x5r', 'x7r', 'y5v']

        if parametr == 'np0' or parametr == 'npo':
            self.term_coef = 'c0g'
            return True

        for term_coef in term_coef_list:
            if parametr == term_coef:
                self.term_coef = parametr
                return True

        return False

    def check_voltage(self, parametr: str) -> bool:
        if 'v' in parametr:
            self.voltage = parametr.replace('v', 'в')
            return True

        elif 'в' in parametr:
            self.voltage = parametr
            return True

        return False

    def take_normal_partnumber(self, data_base) -> bool:  # Нужен typing
        try:
            result = (data_base[self.korpus][self.voltage][self.term_coef]
                                            [self.nominal][self.pogreshnost])
        except KeyError:
            return False

        if self.manufacturer:
            if self.manufacturer in result.keys():
                self.partnumber = result[self.manufacturer][0]
                return True
            else:
                self.add_to_dop_info('др производитель')

        for manufacturer in self.manufacturers:
            if manufacturer not in result.keys():
                continue
            self.partnumber = result[manufacturer][0]
            self.manufacturer = manufacturer
            return True

        return False

    def take_analog_partnumber(self, data_base) -> bool:  # Нужен typing
        if self.take_analog_pogreshnost(data_base):
            return True

        elif self.take_analog_term_coef(data_base):
            return True

        return False

    def take_analog_term_coef(self, data_base) -> bool:  # Нужен typing
        if self.term_coef == 'c0g':
            return False

        term_coef_values = ['y5v', 'x5r', 'x7r', 'c0g']
        start_index = term_coef_values.index(self.term_coef)
        start_term_coef = self.term_coef

        for term_coef in term_coef_values[start_index:]:
            self.term_coef = term_coef

            if self.take_normal_partnumber(data_base):
                return True
            elif self.take_analog_pogreshnost(data_base):
                return True

        self.term_coef = start_term_coef
        return False
