def egcd(a, b):
    x1, x2 = 1, 0
    y1, y2 = 0, 1
    while b > 0:
        tmp = a // b
        x1, x2 = x2, x1 - tmp * x2
        y1, y2 = y2, y1 - tmp * y2
        a, b = b, a % b
    return a, x1, y1


def modinv(a, b):
    return egcd(a, b)[1] % b
