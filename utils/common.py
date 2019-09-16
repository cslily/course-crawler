import os


def size_format(size):
    """ 输入数据字节数，返回数据字符串 """
    flag = '-' if size < 0 else ''
    size = abs(size)
    if size >= 2 ** 90:
        return '{}{:.2f} BB'.format(flag, size / 2**90)
    elif size >= 2 ** 80:
        return '{}{:.2f} YB'.format(flag, size / 2**80)
    elif size >= 2 ** 70:
        return '{}{:.2f} ZB'.format(flag, size / 2**70)
    elif size >= 2 ** 60:
        return '{}{:.2f} EB'.format(flag, size / 2**60)
    elif size >= 2 ** 50:
        return '{}{:.2f} PB'.format(flag, size / 2**50)
    elif size >= 2 ** 40:
        return '{}{:.2f} TB'.format(flag, size / 2**40)
    elif size >= 2 ** 30:
        return '{}{:.2f} GB'.format(flag, size / 2**30)
    elif size >= 2 ** 20:
        return '{}{:.2f} MB'.format(flag, size / 2**20)
    elif size >= 2 ** 10:
        return '{}{:.2f} kB'.format(flag, size / 2**10)
    else:
        return '{}{:.2f} Bytes'.format(flag, size)
