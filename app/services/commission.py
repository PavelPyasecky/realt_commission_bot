import math

from app.core.config import config
from app.services.basic_value_extractor import get_basic_value
from app.services.commission_table import get_commission_percent
from app.services.currency import CurrencyService
from app.services.input_parser import parse_amount_usd
from app.services.rounding import round_number
from app.i18n import get_translator


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
        object_cost_in_USD = parse_amount_usd(query_string)
        return await cls.from_amount(object_cost_in_USD)

    @classmethod
    async def from_amount(cls, object_cost_in_USD):
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

    def format_compact_html(self):
        _ = get_translator()
        tax_usd = self.tax_usd_text
        tax_byn = self.tax_byn_text
        commission = self.commission_text
        return (
            f"💰 <b>{_('Calculation result')}</b>\n"
            f"{_('Tax (USD):')} <b>{tax_usd}</b>\n"
            f"{_('Tax (BYN):')} <b>{tax_byn}</b>\n"
            f"{_('Commission rate:')} <b>{commission}%</b>\n"
            f"\n{_('Enter new amount hint')}"
        )

    def format_detailed_html(self):
        _ = get_translator()
        tax_usd = self.tax_usd_text
        tax_byn = self.tax_byn_text
        object_usd = self.object_usd_text
        usd_rate = self.usd_rate_text
        object_byn = self.object_byn_text
        basic_value = self.basic_value_text
        object_in_basic = self.object_in_basic_text
        commission = self.commission_text
        return (
            f"💰 <b>{_('Calculation result')}</b>\n"
            f"{_('Tax (USD):')} <b>{tax_usd}</b>\n"
            f"{_('Tax (BYN):')} <b>{tax_byn}</b>\n"
            "\n"
            f"📊 <b>{_('Calculation details')}</b>\n"
            f"{_('Object cost (USD):')} <b>{object_usd}</b>\n"
            f"{_('USD rate:')} <b>{usd_rate}</b>\n"
            f"{_('Object cost (BYN):')} <b>{object_byn}</b>\n"
            f"{_('Basic Value (BYN):')} <b>{basic_value}</b>\n"
            f"{_('Object cost in basic values:')} <b>{object_in_basic}</b>\n"
            f"{_('Commission rate:')} <b>{commission}%</b>\n"
            "\n"
            f"🧮 <i>{_('Formula')}: {tax_usd} = {object_usd} x {commission}%</i>\n"
            f"\n{_('Enter new amount hint')}"
        )

    def format_html(self):
        return self.format_detailed_html()

    @property
    def tax_usd_text(self):
        return _format_amount(self.tax_cost_in_USD) + "$"

    @property
    def tax_byn_text(self):
        return _format_amount(self.tax_cost_in_BYN)

    @property
    def object_usd_text(self):
        return _format_amount(self.object_cost_in_USD) + "$"

    @property
    def usd_rate_text(self):
        return _format_amount(self.USD_rate)

    @property
    def object_byn_text(self):
        return _format_amount(self.object_cost_in_BYN)

    @property
    def basic_value_text(self):
        return _format_amount(self.basic_value_in_BYN)

    @property
    def object_in_basic_text(self):
        return _format_amount(self.object_cost_in_basic_value, digits=0)

    @property
    def commission_text(self):
        return _format_amount(self.commission)


def _format_amount(value, digits=2):
    text = round_number(value, digits=digits)
    if "." in text:
        integer, fraction = text.split(".", maxsplit=1)
        return f"{int(integer):,}".replace(",", " ") + f".{fraction}"
    return f"{int(text):,}".replace(",", " ")
