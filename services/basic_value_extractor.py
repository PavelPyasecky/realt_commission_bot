from bs4 import BeautifulSoup
from urllib.request import urlopen

from settings import BASIC_VALUE_IN_BYN

url = 'https://etalonline.by/spravochnaya-informatsiya/u01405001/'
page = urlopen(url)

html_bytes = page.read()
html = html_bytes.decode('utf-8')

soup = BeautifulSoup(html, "html.parser")

def get_basic_value():
    table_cells = soup.find_all("td")

    if not table_cells:
        return BASIC_VALUE_IN_BYN

    basic_value = BASIC_VALUE_IN_BYN
    try:
        table_cell_text = None
        for table_cell_html in table_cells:
            if table_cell_html.text.strip().isdigit():
                table_cell_text = table_cell_html.text.strip()
                break

        if table_cell_text:
            basic_value = table_cell_text

    except (IndexError,AttributeError,TypeError):
        pass

    return float(basic_value)
