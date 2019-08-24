import os


class Task():
    """ 任务对象
    接收函数对象及其参数，但并不马上执行，常用于多进程/多线程管理
    """

    def __init__(self, func, args=(), kw={}):
        """接受函数与参数以初始化对象"""

        self.func = func
        self.args = args
        self.kw = kw

    def run(self):
        """执行函数
        同步函数直接执行并返回结果，异步函数返回该函数
        """

        result = self.func(*self.args, **self.kw)
        return result


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
