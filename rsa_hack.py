import argparse
import string
import sys

from attacks.factordb import NumberStatus, FactorDBError, check_factordb
from attacks import factor
from util.math import modinv


DESCRIPTION = ('Try simple attacks on PGP public keys. This is mainly meant '
               'as a first check on CTF competitions.')

ALLOWED_SYMBOLS = ('n', 'e', 'phi', 'd', 'c')


### Utility functions

def printlog(msg, verbose=True):
    if verbose:
        print msg


### Final processing (after finding solution)

def try_decrypting(data_dict, factors, verbose=False):
    if 'c' not in data_dict:
        return None
    printlog('TRYING TO DECRYPT MESSAGE...', verbose)
    c = data_dict['c']
    n = data_dict['n']
    d = data_dict.get('d')
    e = data_dict.get('e')
    phi = data_dict.get('phi')
    if d is None:
        if phi is None:
            if e is None:
                return None
            if factors and len(factors) == 2:
                phi = (factors[0] - 1) * (factors[1] - 1)
            else:
                return None
        d = modinv(e, phi)
        printlog('==Calculated d={}'.format(d), verbose)
    data = pow(c, d, n)
    printlog('==Calculated m={}'.format(data), verbose)
    return data


def try_stringifying(data, verbose=False):
    try:
        text = '{:x}'.format(data).decode('hex')
    except:
        return None
    if all(t in string.printable for t in text):
        return text
    return None


def solved(msg, data_dict, factors=None, decrypted=None, verbose=False):
    header = '=== SOLVED: {} ==='.format(msg)
    sep = '=' * len(header)
    output = [sep, header, sep]
    if factors:
        output.append('N factors:')
        for f in factors:
            output.append(' - {}'.format(f))
    if decrypted is None and 'c' in data_dict:
        decrypted = try_decrypting(data_dict, factors, verbose)
    if decrypted:
        text = try_stringifying(decrypted, verbose)
        if text:
            output.append('=== Decrypted message: {} ==='.format(text))
        else:
            output.append('=== Decrypted m (failed to translate to ASCII - non'
                          ' printable characters produced): {} ==='
                          .format(decrypted))
    print '\n'.join(output)
    sys.exit(0)


### Input reading

def parse_file(filename, verbose=False):
    result = {}
    with open(filename, 'r') as f:
        printlog('PARSING FILE {}...'.format(filename))
        for line in f:
            line = line.strip()
            if not line or line[0] == '#' or '=' not in line:
                continue
            parts = line.split('=')
            try:
                val = int(parts[1])
            except ValueError:
                val = int(parts[1], 16)
            sym = parts[0].lower()
            if sym not in ALLOWED_SYMBOLS:
                raise ValueError("Unknown symbol {} in datafile"
                                 .format(parts[0]))
            if sym in result:
                raise ValueError("Symbol {} defined multiple times in data"
                                 .format(sym))
            result[sym] = val
    printlog(
        '==Read following values from file: {}'.format(
            ','.join(result.iterkeys())),
        verbose)
    return result


# Attacks

def handle_e_1(data_dict, verbose=False):
    decrypted = None
    if 'c' in data_dict and 'n' in data_dict:
        decrypted = data_dict['c'] % data_dict['n']
    solved('e == 1 - trivial', data_dict, decrypted=decrypted, verbose=verbose)


# Main functions

def process_data(data_dict, verbose=False, skip_factordb=False):
    printlog("TRIVIAL CHECKS...")
    if 'n' not in data_dict:
        raise ValueError("Unknown N")
    if 'phi' in data_dict or 'd' in data_dict:
        solved('phi or d given', data_dict, verbose=verbose)
    if 'e' not in data_dict:
        raise ValueError("Unknown e")
    if data_dict['e'] == 1:
        handle_e_1(data_dict, verbose=verbose)

    if not skip_factordb:
        printlog("CHECKING FACTORDB...")
        for x in xrange(3):
            try:
                fdb = check_factordb(data_dict['n'], verbose)
                break
            except FactorDBError:
                printlog('==Query failed - retries left {}'
                         .format(3 - x), verbose)
        if fdb[1] == NumberStatus.FACTORS_KNOWN:
            solved('found N in factordb', data_dict,
                   factors=fdb[2], verbose=verbose)

    printlog("STARTING FACTORIZATION ATTEMPTS...")
    result = factor.run_attacks(data_dict['n'], verbose=verbose)
    if result is not None:
        solved(result[1], data_dict, factors=result[0], verbose=verbose)


def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('datafile', help="Input file")
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--no-factordb', action='store_true')
    args = parser.parse_args()
    data_dict = parse_file(args.datafile, args.verbose)
    process_data(data_dict, args.verbose, skip_factordb=args.no_factordb)


if __name__ == '__main__':
    main()
