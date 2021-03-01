# -*- coding: utf-8 -*-
"""爱课程"""

from moocs.utils import *
from bs4 import BeautifulSoup
import re
import json
from utils.crawler import Crawler

name = "icourses"
need_cookies = False
CANDY = Crawler()
CONFIG = {}
FILES = {}
VIDEOS = []
exports = {}
__all__ = ["name", "need_cookies", "start", "exports"]


def get_content(url):
    """获得课程信息"""

    res = CANDY.get(url).text
    soup = BeautifulSoup(res, 'lxml')
    script = soup.find_all('script')[-2].string
    js = re.search(r'_sourceArrStr = (.*);', script)
    school = soup.find(class_='teacher-infor-from').string
    name = soup.find(class_='coursetitle pull-left').a.string
    dir_name = course_dir(name, school)
    res_info = json.loads(js.group(1))
    print(dir_name)
    return dir_name, res_info


def parse_res(js):
    """获得视频名称和地址"""
    outline = Outline()
    length = len(str(len(js)))
    counter = 0
    video_list = []
    for lesson in js:
        counter += 1
        counter_str = str(counter).zfill(length)
        title = lesson['title']
        url = lesson['fullLinkUrl']
        outline.write_string('%s {%s}#' % (title, counter_str))
        video = Video(counter_str, title, url)
        video_list.append(video)

    return video_list


def parse_video(video):
    """将视频信息添加到相关列表中"""

    if WORK_DIR.need_download(video.file_name+".mp4", CONFIG["overwrite"]):
        FILES['videos'].write_string(video.meta)
        FILES['renamer'].write(video.meta.split('/')[-1], video.file_name)
        VIDEOS.append((video.meta, video.file_name+".mp4"))


def start(url, config, cookies=None):
    """调用接口函数"""

    global WORK_DIR
    CONFIG.update(config)

    course_info = get_content(url)
    WORK_DIR = WorkingDir(CONFIG['dir'], course_info[0])

    WORK_DIR.change('Videos')
    FILES['renamer'] = Renamer(WORK_DIR.file('Rename.{ext}'))
    FILES['videos'] = ClassicFile(WORK_DIR.file('Videos.txt'))
    playlist = get_playlist(CONFIG["playlist_type"], CONFIG["playlist_path_type"])
    if playlist:
        FILES['playlist'] = playlist

    video_list = parse_res(course_info[1])

    rename = WORK_DIR.file('Names.txt') if CONFIG['rename'] else False

    if playlist:
        parse_res_list(video_list, rename,
                       FILES['playlist'].write, parse_video)
    else:
        parse_res_list(video_list, rename, parse_video)

    exports.update({
        "workdir": WORK_DIR,
        "spider": CANDY,
        "videos": VIDEOS
    })
