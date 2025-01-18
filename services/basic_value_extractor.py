import logging
from urllib.error import HTTPError

from bs4 import BeautifulSoup
from urllib.request import urlopen

from settings import BASIC_VALUE_IN_BYN

logger = logging.getLogger(__name__)

URL = 'https://etalonline.by/spravochnaya-informatsiya/u01405001/'


def get_soup_of_the_page(url):
    try:
        page = urlopen(url)
    except HTTPError as e:
        logger.error('HTTP error occurred: %s', e)
        return None

    html_bytes = page.read()
    html = html_bytes.decode('utf-8')

    soup = BeautifulSoup(html, "html.parser")
    return soup

def get_basic_value():
    basic_value = float(BASIC_VALUE_IN_BYN)

    soup = get_soup_of_the_page(URL)
    if soup is None:
        return basic_value

    table_cells = soup.find_all("td")
    if not table_cells:
        return basic_value

    try:
        table_cell_text = None
        for table_cell_html in table_cells:
            if table_cell_html.text.strip().isdigit():
                table_cell_text = table_cell_html.text.strip()
                break

        if table_cell_text:
            basic_value = float(table_cell_text)

    except (IndexError,AttributeError,TypeError):
        pass

    return basic_value
