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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36'
    }

    result = requests.get(url, params=params, headers=headers)

    return result

if __name__ == "__main__":
    unecon_request(12837)