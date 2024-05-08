from api.nbrb.api import CurrencyAPI


class CurrencyService:
    API_SERVICE = CurrencyAPI()

    def get_dollar_rate_for_today(self):
        dollar_data = self.API_SERVICE.get_dollar_rate_data()
        return dollar_data['Cur_OfficialRate']
