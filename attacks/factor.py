import multiprocessing

import gmpy2


ATTACKS = {}


def printlog(msg, verbose=True):
    if verbose:
        print msg


### Synchronisation / multiprocessing functions

LOG = "LOG"
SUCCESS = "SUCCESS"
FAIL = "FAIL"


def parentlog(msg, **kwargs):
    if kwargs.get('verbose'):
        kwargs['queue'].put((LOG, kwargs['name'], msg))


def success(n, factor, **kwargs):
    if n % factor != 0:
        return fail(**kwargs)
    factors = (int(factor), int(n / factor))
    kwargs['queue'].put((SUCCESS, kwargs['name'], factors))


def fail(**kwargs):
    kwargs['queue'].put((FAIL, kwargs['name'], None))


def run_attacks(n, funs=None, verbose=False):
    if funs is None:
        funs = ATTACKS.keys()
    processes = {}
    queue = multiprocessing.Queue()
    for name, (fun, msg) in ATTACKS.iteritems():
        processes[name] = multiprocessing.Process(
            target=fun,
            args=(n,),
            kwargs={'queue': queue, 'name': name, 'verbose': verbose})
        processes[name].start()
        printlog("==Starting python attack: {} ({})".format(name, msg))
    while processes:
        action, name, payload = queue.get()
        if action == LOG:
            printlog('====[{}]: {}'.format(name, payload), verbose)
        elif action == FAIL:
            del processes[name]
            printlog("==Attack {} FAILED (still running: {})"
                     .format(name, ', '.join(processes.keys())))
        else:
            printlog("==Attack {} SUCCEDED. Found factors: {}"
                     .format(name, payload))
            del processes[name]
            for p in processes.itervalues():
                # that could be done cleaner by sending message, but I'm lazy
                p.terminate()
            return payload, ATTACKS[name][1]
    return None


### Attacks

def mersenne(n, **kwargs):
    n = gmpy2.mpz(n)
    i = gmpy2.mpz(2)
    guess = pow(2, i) - 1
    end = gmpy2.isqrt(n)
    while guess < end:
        if n % guess == 0:
            return success(n, guess, **kwargs)
        i += 1
        guess = pow(2, i) - 1
    return fail(**kwargs)


ATTACKS['mersenne'] = mersenne, "check all mersenne primes"


def dumb_brute(n, **kwargs):
    n = gmpy2.mpz(n)
    i = 2
    last_power = 10000
    while True:
        if n % i == 0:
            return success(n, i, **kwargs)
        i += 1
        if i == last_power:
            parentlog("checked {} numbers".format(i), **kwargs)
            last_power *= 10


ATTACKS['brute'] = dumb_brute, "dumb brute force attack"


def brute_from_sqrt(n, **kwargs):
    n = gmpy2.mpz(n)
    start = gmpy2.isqrt(n)
    i = start
    last_power = 10000
    while True:
        if n % i == 0:
            return success(n, i, **kwargs)
        i -= 1
        if (start - i) == last_power:
            parentlog("checked {} numbers".format(start - i), **kwargs)
            last_power *= 10

ATTACKS['brute_from_sqrt'] = (brute_from_sqrt,
                              "brute attack starting from sqrt and going down")
