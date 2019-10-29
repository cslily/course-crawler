# -*- coding: utf-8 -*-
"""学堂在线"""

import json
import sys

from bs4 import BeautifulSoup

from moocs.utils import *
from utils.crawler import Crawler

name = "xuetangx_next"
need_cookies = True
CANDY = Crawler()
CONFIG = {}
FILES = {}
VIDEOS = []
exports = {}
__all__ = ["name", "need_cookies", "start", "exports"]


def get_summary(url):
    """从课程主页面获取信息"""

    sign, cid = re.match(r"https?://next.xuetangx.com/course/"
                        "(?P<sign>.+?)/(?P<cid>.+)", url).group("sign", "cid")

    res = CANDY.get("https://next.xuetangx.com/api/v1/lms/learn/product/info?cid=%s&sign=%s" % (cid, sign))
    course_name = res.json()['data']['classroom_name']
    # 机构名称不太容易获取，暂时不获取
    dir_name = course_dir(course_name, "学堂在线")

    print(dir_name)
    CONFIG['sign'] = sign
    CONFIG['cid'] = cid
    return cid, sign, dir_name


def parse_resource(resource):

    cid, sign = CONFIG['cid'], CONFIG['sign']
    file_name = resource.file_name
    item_id, item_info_id = resource.meta
    res = CANDY.get("https://next.xuetangx.com/api/v1/lms/learn/leaf_info/%s/%s/?sign=%s" % (cid, item_id, sign),
                    headers={"xtbz": "xt"})
    if resource.type == 'Video':
        ccid = res.json()['data']['content_info']['media']['ccid']

        video_url_res = CANDY.get("https://next.xuetangx.com/api/v1/lms/service/playurl/%s/?appid=10000" % ccid)
        sources = video_url_res.json()['data']['sources']
        qualitys = ['20', '10']
        for qa in qualitys:
            if sources.get('quality' + qa):
                # 居然是个数组，暂时没发现多段的，希望以后也没有吧……
                video_url = sources['quality' + qa][0]

        ext = '.mp4'
        if WORK_DIR.need_download(file_name + ext, CONFIG["overwrite"]):
            FILES['renamer'].write(
                re.search(r'(\w+\.mp4)', video_url).group(1), file_name, ext)
            FILES['video'].write_string(video_url)
            VIDEOS.append((video_url, file_name+ext))
            resource.ext = ext

        if not CONFIG['sub']:
            return
        # 暂未支持多语言
        subtitle_res = CANDY.get("https://next.xuetangx.com/api/v1/lms/service/subtitle_parse/?c_d=%s&lg=0" % ccid)
        if subtitle_res.status_code != 200:
            return
        subtitle_json = subtitle_res.json()
        starts, ends, texts = subtitle_json['start'], subtitle_json['end'], subtitle_json['text']
        subtitle = Subtitle(WORK_DIR.file(file_name + '.srt'))
        assert len(starts) == len(ends) == len(texts)
        for i in range(len(starts)):
            subtitle.write(texts[i], starts[i], ends[i])

    elif resource.type == 'Document':
        if not WORK_DIR.need_download(file_name + '.pdf', CONFIG["overwrite"]):
            return
        # 暂时也没遇到多个文件的情况
        downloads = res.json()['data']['content_info']['download']
        if downloads:
            pdf_url = downloads[0]['file_url']
            CANDY.download_bin(pdf_url, WORK_DIR.file(file_name + '.pdf'))


def get_resource(cid, sign):
    """获取各种资源"""

    outline = Outline()
    counter = Counter()

    video_list = []
    pdf_list = []

    res = CANDY.get("https://next.xuetangx.com/api/v1/lms/learn/course/chapter?cid=%s&sign=%s" % (cid, sign),
                    headers={"xtbz": "xt"})
    for chapter in res.json()['data']['course_chapter']:
        counter.add(0)
        chapter_id, chapter_name, chapter_order = chapter['id'], chapter['name'], chapter['order']
        outline.write(chapter_name, counter, 0)

        for section in chapter['section_leaf_list']:
            counter.add(1)
            section_id, section_name, section_order = section['id'], section['name'], section['order']
            outline.write(section_name, counter, 1)

            # 暂时忽略测验，以后可能支持（在 section 中作为叶子结点， type_id = 6）
            for item in section.get('leaf_list', []):
                counter.add(2)
                item_id, item_name, item_order = item['id'], item['name'], item['order']
                item_type, item_info_id = item['leaf_type'], item['leafinfo_id']
                # Video
                if item_type == 0:
                    outline.write(item_name, counter, 2, sign='#')
                    video_list.append(Video(counter, item_name, (item_id, item_info_id)))
                # Docs
                elif item_type == 3:
                    item_name = item_name.rstrip('.pdf')
                    outline.write(item_name, counter, 2, sign='*')
                    if CONFIG['doc']:
                        pdf_list.append(Document(counter, item_name, (item_id, item_info_id)))

    if video_list:
        rename = WORK_DIR.file('Names.txt') if CONFIG['rename'] else False
        WORK_DIR.change('Videos')
        playlist = get_playlist(CONFIG["playlist_type"], CONFIG["playlist_path_type"])
        if playlist is not None:
            parse_res_list(video_list, rename, parse_resource, playlist.write)
        else:
            parse_res_list(video_list, rename, parse_resource)
    if pdf_list:
        WORK_DIR.change('PDFs')
        parse_res_list(pdf_list, None, parse_resource)


def start(url, config, cookies=None):
    """调用接口函数"""

    global WORK_DIR
    CANDY.set_cookies(cookies)
    CONFIG.update(config)

    cid, sign, course_name = get_summary(url)

    WORK_DIR = WorkingDir(CONFIG['dir'], course_name)
    WORK_DIR.change('Videos')
    FILES['renamer'] = Renamer(WORK_DIR.file('Rename.{ext}'))
    FILES['video'] = ClassicFile(WORK_DIR.file('Videos.txt'))

    get_resource(cid, sign)

    exports.update({
        "workdir": WORK_DIR,
        "spider": CANDY,
        "videos": VIDEOS
    })
