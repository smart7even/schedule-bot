import requests
from typing import Optional


def unecon_request(group_id: int, week: Optional[int] = None):
    """
    Does request to unecon schedule site and returns response
    :param group_id:
    :param week: study week since the start of the year
    :return: site response
    """

    url = "https://rasp.unecon.ru/raspisanie_grp.php"

    params = {
        "g": group_id,
        "w": week
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/39.0.2171.95 Safari/537.36 '
    }

    result = requests.get(url, params=params, headers=headers)

    return result
