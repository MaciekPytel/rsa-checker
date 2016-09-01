# Apparently there is no API available for factordb.com, so this module
# just parses it. It makes assumptions about how the page looks like and
# will stop working if it is changed at any point...

import itertools

from bs4 import BeautifulSoup
import requests


class FactorDBError(Exception):
    pass


class NumberStatus(object):
    PRIME = 1
    FACTORS_KNOWN = 2
    FACTORS_UNKNOWN = 3


_status_map = {
    'C': NumberStatus.FACTORS_UNKNOWN,
    'CF': NumberStatus.FACTORS_KNOWN,
    'FF': NumberStatus.FACTORS_KNOWN,
    'P': NumberStatus.PRIME,
    'Prp': NumberStatus.PRIME,
    'U': NumberStatus.FACTORS_UNKNOWN,
    'N': NumberStatus.FACTORS_UNKNOWN,
}


def _parse_factordb_html(source, verbose=False):
    soup = BeautifulSoup(source, 'html.parser')
    val = soup.find('input', attrs={'name': 'query'}).attrs['value']
    val = int(val)
    table = soup.find_all('table')[1]
    row = next(itertools.islice(table, 2, None))
    status = row.children.next().children.next()  # this is a lil' bit ugly
    status = _status_map.get(status, NumberStatus.FACTORS_UNKNOWN)
    factors = []
    if status == NumberStatus.FACTORS_KNOWN:
        equation = next(itertools.islice(row, 4, None))
        links = equation.find_all('a')
        for i, link in enumerate(links):
            if i > 0:
                url = 'http://factordb.com/' + link.attrs['href']
                lsource = _fetch_factordb_link(url, verbose)
                lv, ls, lf = _parse_factordb_html(lsource, verbose)
                if ls == NumberStatus.FACTORS_KNOWN:
                    factors += lf
                else:
                    factors.append(lv)
    return val, status, factors


def _fetch_factordb_link(url, verbose=False):
    if verbose:
        print '==FACTORDB: Will fetch {}'.format(url)
    try:
        response = requests.get(url)
    except:
        raise FactorDBError()
    if response.status_code != 200:
        raise FactorDBError()
    return response.text


def check_factordb(n, verbose=False):
    url = 'http://factordb.com/index.php?query={}'.format(n)
    return _parse_factordb_html(_fetch_factordb_link(url, verbose), verbose)


if __name__ == '__main__':
    #print check_factordb(30064958471180141352963255964320727764941087854957385562672821662319854021395100968823341108075020928542437446993994119863902565874355296188498304761389336438421889636409561936141985786801002923752627293790265351723795968412774268086467114263767947693310444934316205390814185802517514694528501333851255084653925181726978734804806707740444755908398751964899143494522781405457103697373868972836201511424363601490903086488506985489526910314474245106338585623571369549388434865567951986866445306840505397268281889886738015891982162371413136885989746931929787765617838750381226036784122498143172854419447324975505933540511, verbose=True)
    print check_factordb(120, True)
