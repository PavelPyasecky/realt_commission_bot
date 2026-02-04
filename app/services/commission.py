import math

from app.core.config import config
from app.services import exceptions
from app.services.basic_value_extractor import get_basic_value
from app.services.commission_table import get_commission_percent
from app.services.currency import CurrencyService
from app.services.rounding import round_number


class CommissionCalculator:
    def __init__(
        self,
        object_cost_in_USD,
        basic_value_in_BYN,
        USD_rate,
        object_cost_in_BYN,
        object_cost_in_basic_value,
        commission,
        tax_cost_in_BYN,
        tax_cost_in_USD,
    ):
        self.object_cost_in_USD = object_cost_in_USD
        self.basic_value_in_BYN = basic_value_in_BYN
        self.USD_rate = USD_rate
        self.object_cost_in_BYN = object_cost_in_BYN
        self.object_cost_in_basic_value = object_cost_in_basic_value
        self.commission = commission
        self.tax_cost_in_BYN = tax_cost_in_BYN
        self.tax_cost_in_USD = tax_cost_in_USD

    @classmethod
    async def from_query(cls, query_string):
        _validation(query_string)
        object_cost_in_USD = float(query_string)
        basic_value_in_BYN = await get_basic_value(float(config.BASIC_VALUE_BYN))
        USD_rate = await CurrencyService().get_dollar_rate_for_today()
        object_cost_in_BYN = object_cost_in_USD * USD_rate
        object_cost_in_basic_value = math.ceil(object_cost_in_BYN / basic_value_in_BYN)
        commission = get_commission_percent(object_cost_in_basic_value)
        tax_cost_in_BYN = object_cost_in_BYN * commission / 100
        tax_cost_in_USD = object_cost_in_USD * commission / 100
        return cls(
            object_cost_in_USD=object_cost_in_USD,
            basic_value_in_BYN=basic_value_in_BYN,
            USD_rate=USD_rate,
            object_cost_in_BYN=object_cost_in_BYN,
            object_cost_in_basic_value=object_cost_in_basic_value,
            commission=commission,
            tax_cost_in_BYN=tax_cost_in_BYN,
            tax_cost_in_USD=tax_cost_in_USD,
        )

    def format_html(self):
        return (
            "Object cost (USD):\t<b>"
            f"{round_number(self.object_cost_in_USD)}$</b>\n"
            "USD rate:\t<b>"
            f"{round_number(self.USD_rate)}$</b>\n"
            "Object cost (BYN):\t<b>"
            f"{round_number(self.object_cost_in_BYN)}</b>\n"
            "Basic Value (BYN):\t<b>"
            f"{round_number(self.basic_value_in_BYN)}</b>\n"
            "Object cost in Basic Value (BV):\t<b>"
            f"{round_number(self.object_cost_in_basic_value)}</b>\n"
            "Commission (%):\t<b>"
            f"{round_number(self.commission)}%</b>\n"
            "Tax cost (BYN):\t<b>"
            f"{round_number(self.tax_cost_in_BYN)}</b>\n"
            "Tax cost (USD):\t<b>"
            f"{round_number(self.tax_cost_in_USD)}$</b>\n"
        )


def _validation(query_string):
    if query_string.isnumeric():
        return
    raise exceptions.InputError
