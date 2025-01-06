import math

import exceptions
from api.constants.commission_table import start_end_cost_commission_table_in_BASIC_VALUE
from api.services.currency import CurrencyService
from services.basic_value_extractor import get_basic_value


class CostTaxService:
    COMMISSION_TABLE = start_end_cost_commission_table_in_BASIC_VALUE

    def get_commission(self, BASIC_VALUE_cost):
        for commission_row in self.COMMISSION_TABLE:
            start, end, commission = commission_row

            if end is None:
                return commission

            if start < BASIC_VALUE_cost <= end:
                return commission


class CommissionCalculator:
    def __init__(self, object_cost):
        self._validation(object_cost)

        self.object_cost_in_USD = int(object_cost)
        self.basic_value_in_BYN = get_basic_value()
        self._calculate()

    @staticmethod
    def _validation(query_string):
        if query_string.isnumeric():
            return

        raise exceptions.InputError

    def _calculate(self):
        self.USD_rate = CurrencyService().get_dollar_rate_for_today()
        self.object_cost_in_BYN = self.object_cost_in_USD * self.USD_rate
        self.object_cost_in_basic_value = math.ceil(self.object_cost_in_BYN / self.basic_value_in_BYN)
        self.commission = CostTaxService().get_commission(self.object_cost_in_basic_value)
        self.tax_cost_in_BYN = self.object_cost_in_BYN * self.commission / 100
        self.tax_cost_in_USD = self.object_cost_in_USD * self.commission / 100
