# -*- coding: utf-8 -*-
"""核心程序组件"""

import json
import os
import platform
import re
import subprocess
import sys
import time

from utils.aria2 import Aria2, Aria2File
from utils.common import size_format

SYS = platform.system()


class Resource(object):
    """所有资源类的基类

    用来定义一个资源，但不同类型的资源可能要对部分功能进行重写。

    属性
        类
            regex_sort：匹配序号的正则表达式；
            regex_file：匹配 Windows 下文件名的非法字符；
            regex_spaces：匹配连续多个空白字符。
            type：资源的类型，默认是 'Resource'；

        id：资源的唯一标识，用于在程序中标识一个资源，如 '2.3.2'；
        name：资源的名称（可含有特殊字符），和最终的文件名有关；
        meta：资源的元信息，比如资源在每个网站的 ID 和文件名等等；
        feature：其他特征（基本用不到）。
    """

    regex_sort = re.compile(r'^[第一二三四五六七八九十\d]+[\s\d._\-章课节讲]*[.\s、\-]\s*\d*')
    regex_file = re.compile(r'[\\/:*?"<>|]')
    regex_spaces = re.compile(r'\s+')
    type = 'Resource'

    def __init__(self, identify, name, meta, feature=None):
        """将 name 的序号消除，并依次为属性赋值"""
        self.id = str(identify)
        self.name = Resource.regex_spaces.sub(
            ' ', Resource.regex_sort.sub('', name)).strip()
        self.meta = meta
        self.feature = feature

    def __str__(self):
        """返回资源的名称"""

        return self.name

    @property
    def file_name(self):
        """动态生成文件名（包含前缀的 ID，不含扩展名），比如 '2.3.2 file_name'"""

        return self.id + ' ' + Resource.regex_file.sub('', self.name)

    def operation(self, *funcs):
        """传入一个或多个函数，使用函数对资源对象进行调用"""

        for func in funcs:
            func(self)

    @staticmethod
    def file_to_save(name):
        """通过一个名字生成文件名"""

        return Resource.regex_file.sub('', Resource.regex_spaces.sub(' ', Resource.regex_sort.sub('', name)).strip())


class Video(Resource):
    """视频资源类

    属性
        type：默认值是 'Video'；
    """

    type = 'Video'
    ext = '.mp4'


class Document(Resource):
    """文档资源类

    属性
        type：默认值是 'Video'；
    """

    type = 'Document'


class RichText(Resource):
    """富文本资源类

    属性
        type：默认值是 'Rich'；
    """

    type = 'Rich'


class Attachment(Resource):
    """视频资源类

    属性
        type：默认值是 'Attachment'；
    """

    type = 'Attachment'


class ClassicFile(object):
    """典型文件（UTF-8 编码的文件）类

    属性
        _f：文件指针；
        file：文件名或文件路径。
    """

    def __init__(self, file):
        """传入一个文件名或路径，然后打开文件，并保存文件指针和文件名"""

        self._f = open(file, 'w', encoding='utf_8')
        self.file = file

    def __del__(self):
        """关闭文件，并将文件号和文件名都清空"""

        self._f.close()
        del self._f
        del self.file

    def write_string(self, string):
        """向对象中打开的文件写入字符串，会自动加入换行"""

        self._f.write(string + '\n')


class Playlist(ClassicFile):
    """ 播放列表类 """

    def __init__(self, file, path_type):
        super().__init__(file)
        self.path_type = path_type

    def switch_path(self, path):
        """ 根据路径类别生成路径项 """
        path = os.path.normpath(path)
        if self.path_type == 'AP':
            path = os.path.abspath(path)
        elif self.path_type == 'RP':
            path = os.path.relpath(path, start=os.path.dirname(self.file))
        return path

    def write(self, video):
        """传入一个 Video 类的对象，将该对象的信息写入播放列表"""

        path = os.path.join("Videos", video.file_name + video.ext)
        path = self.switch_path(path)
        self.write_string(path)


class M3u(Playlist):
    """ m3u 播放列表类 """

    def __init__(self, path_type='RP'):
        super().__init__('Playlist.m3u', path_type)


class Dpl(Playlist):
    """ Potplayer 播放列表类

    属性
        _count：已经写入的播放列表的文件数；
    """

    def __init__(self, path_type='RP'):
        super().__init__('Playlist.dpl', path_type)
        self.write_string('DAUMPLAYLIST\n')
        self._count = 0

    def write(self, video):
        """传入一个 Video 类的对象，将该对象的信息写入播放列表"""

        self._count += 1
        path = os.path.join("Videos", video.file_name + video.ext)
        path = self.switch_path(path)
        self.write_string('{}*file*{}'.format(self._count, path))
        self.write_string('{}*title*{} {}\n'.format(self._count,
                                                    '.'.join(video.id.split('.')[:-1]), video.name))


class Renamer(ClassicFile):
    """重命名批处理文件类"""

    ext = 'bat' if SYS == 'Windows' else 'sh'

    def __init__(self, file):
        """初始化文件，并写入调用 UTF-8 代码页的命令"""

        file = file.format(ext=Renamer.ext)
        super().__init__(file)
        if SYS == 'Windows':
            self.write_string('CHCP 65001\n')

    def write(self, origin_name, file_name, ext='.mp4'):
        """传入一个文件的原始名字（URL 中的文件名）和一个新的文件名"""

        if SYS == 'Windows':
            self.write_string('REN "%s" "%s%s"' %
                              (origin_name, file_name, ext))
        else:
            self.write_string('mv "%s" "%s%s"' % (origin_name, file_name, ext))


class Outline(ClassicFile):
    """课程大纲类

    属性
        res_type：通过一个符号代表一种文件类型。
    """

    res_type = {'#': '【视频】', '!': '【附件】', '*': '【文档】',
                '+': '【富文本】', '&': '【字幕】', '': ''}

    def __init__(self):
        """创建 Outline.txt 文件"""

        super().__init__('Outline.txt')

    def write(self, string, counter, level=2, sign=''):
        """传入一个字符串，一个计数器，一个级别（从 0 开始）和一个符号，然后写入大纲。首先会打印出相关信息。"""

        print('%s%s%s' % ('  ' * level, Outline.res_type[sign], string))
        name = '%s%s {%s}%s' % ('  ' * level, string, counter[level], sign)
        self.write_string(name)


class WorkingDir(object):
    """工作目录类

    用于切换下载目录和创建目录等。

    属性
        base_dir：工作目录的根目录，任何时候都基于这个目录；
        path：相对于根目录的路径。
    """

    def __init__(self, *base_dirs):
        """传递一些字符串，创建一个目录，并切换到这个目录"""

        base_dir = os.path.join(*base_dirs)
        if not os.path.isdir(base_dir):
            os.makedirs(base_dir)
        os.chdir(base_dir)
        self.base_dir = os.getcwd()
        self.path = ''

    def change(self, *relative):
        """切换工作目录（假），可以接受连续多个目录名，如果不存在该目录就创建它

        切换的功能需要配合 file() 才能实现。
        """

        self.path = os.path.join(self.base_dir, *relative)
        if not os.path.isdir(self.path):
            os.makedirs(self.path)

    def file(self, file_name):
        """根据文件名返回一个完整的路径，会根据 path 生成一个路径"""

        return os.path.join(self.path, file_name)

    def exist(self, file_name):
        """判断当前路径（雾）是否存在一个文件"""

        return os.path.exists(os.path.join(self.path, file_name))

    def need_download(self, file_name, overwrite=False):
        """判断当前文件是否需要下载，并且打印输出"""

        need = overwrite or not self.exist(file_name)
        sign = ">" if need else "!"
        res_print(file_name, sign=sign)
        return need


class Counter(object):
    """计数器类

    属性
        counter：计数器的列表。
    """

    def __init__(self, num_level=3):
        """初始化一个列表"""

        self.counter = [0] * num_level
        self.num_level = num_level

    def add(self, level):
        """给第 level 级别的计数器 +1"""

        for i in range(level + 1, self.num_level):
            self.counter[i] = 0
        self.counter[level] += 1

    def __str__(self):
        """返回一个完整的计数器"""

        return '.'.join(map(str, self.counter))

    def __getitem__(self, index):
        """返回到第 level 级别为止的计数器"""

        return '.'.join(map(str, self.counter[:index + 1]))

    def reset(self):
        """将第 2 级别的计数置为 0"""

        self.counter[-1] = 0


def res_print(file_name, sign=">"):
    """打印一个将要输出的文件"""

    print('------{}'.format(sign), file_name)


def course_dir(course_name, institution):
    """通过课程名和机构名返回一个完整的目录名字"""

    return Resource.regex_file.sub('', '%s - %s' % (course_name, institution))


def parse_res_list(res_list, file, *operator):
    """传入一个 Resource 实例的列表，并传入一个临时文件名，将调出默认程序修改名字，并调用对象的 operation 方法"""

    if file:
        with open(file, 'w', encoding='utf_8') as f:
            for res in res_list:
                f.write(str(res) + '\n')
        if SYS == 'Windows':
            os.startfile(file)
        elif SYS == 'Linux':
            subprocess.run('gedit "%s"' %
                           file, shell=True, stdout=subprocess.PIPE)
        elif SYS == 'Darwin':
            subprocess.run('open -t "%s"' %
                           file, shell=True, stdout=subprocess.PIPE)
        input('修改完文件名后按回车继续。')
        with open(file, encoding='utf_8') as f:
            for res in res_list:
                res.name = f.readline().rstrip('\n')
                res.operation(*operator)
    else:
        for res in res_list:
            res.operation(*operator)


def store_cookies(mooc_type, restore=False):
    """存储并返回 Cookie 字典"""

    def cookie_to_json():
        """将分号分隔的 Cookie 转为字典"""

        cookies_dict = {}
        raw_cookies = input('> ')
        if not raw_cookies:
            return {}
        if raw_cookies[:7].lower() == 'cookie:':
            raw_cookies = raw_cookies[7:]

        for cookie in raw_cookies.split(';'):
            key, value = cookie.lstrip().split("=", 1)
            cookies_dict[key] = value

        return cookies_dict

    file_path = os.path.join(sys.path[0], "cookies.json")
    if not os.path.isfile(file_path):
        cookies = {}
    else:
        with open(file_path, 'r') as cookies_file:
            cookies = json.load(cookies_file)

    if restore or not cookies.get(mooc_type):
        print("输入 Cookie：")
        cookies[mooc_type] = cookie_to_json()
        with open(file_path, 'w') as f:
            json.dump(cookies, f, indent=2)

    return cookies[mooc_type]


def get_playlist(playlist_type, path_type):
    """传入播放列表类型及路径类型，返回播放列表对象"""

    if playlist_type == 'no':
        playlist = None
    elif playlist_type == 'dpl':
        playlist = Dpl(path_type=path_type)
    elif playlist_type == 'm3u':
        playlist = M3u(path_type=path_type)
    return playlist


def aria2_download(videos, workdir, overwrite=False):
    """调用 aria2 下载视频"""

    aria2 = Aria2()
    files = []

    for url, file_name in videos:
        file = Aria2File(aria2, url, file_name, workdir, overwrite=overwrite)
        files.append(file)

    # 显示进度
    process_bar_length = 50
    total_length = sum([file.get_length() for file in files])
    while True:
        speed = sum([file.get_speed() for file in files])
        completed_length = sum([file.get_complete_length() for file in files])
        len_done = process_bar_length * \
            completed_length // total_length
        len_undone = process_bar_length - len_done
        log_string = '{}{} {}/{} {:12}'.format(
            "#" * len_done, "_" * len_undone, size_format(completed_length),
            size_format(total_length), size_format(speed)+"/s")
        print(log_string, end="\r")

        # 重命名文件
        for file in files:
            if file.get_status() == "complete" and not file.exists():
                file.rename()

        time.sleep(1)
        if all([file.get_status() == "complete" for file in files]):
            break

    print("视频已下载全部完成~")
