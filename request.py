import requests
from typing import Optional


def unecon_request(group: int, week: Optional[int] = None):
    """
    Эта функция делает запрос на сайт СПбГЭУ и возвращает страницу расписания.
    Если не указан параметр week, то сайт СПбГЭУ возращает страницу расписания на данную неделю

    :param group: id группы
    :param week: номер недели от начала учебного года
    :return: страница расписания
    """

    url = "https://rasp.unecon.ru/raspisanie_grp.php"

    params = {
        "g": group,
        "w": week
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
    }

    result = requests.get(url, params=params, headers=headers)

    return result
