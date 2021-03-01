# -*- coding: utf-8 -*-
"""好大学在线"""

from bs4 import BeautifulSoup

from moocs.utils import *
from utils.crawler import Crawler

name = "cnmooc"
need_cookies = True
CANDY = Crawler()
CONFIG = {}
FILES = {}
VIDEOS = []
exports = {}
__all__ = ["name", "need_cookies", "start", "exports"]


def get_summary(url):
    """获得课程信息"""

    res = CANDY.get(url).text
    soup = BeautifulSoup(res, 'lxml')
    title = soup.find(class_='view-title substr').get_text(strip=True)
    university = soup.find(class_='person-attach substr').get_text(strip=True)

    dir_name = course_dir(title, university)
    print(dir_name)
    return dir_name


def get_resource(course_nav):
    """获得视频资源"""

    counter = Counter()
    outline = Outline()
    video_list = []
    document_list = []

    res = CANDY.get(course_nav).text
    soup = BeautifulSoup(res, 'lxml')
    nav = soup.find(id='unitNavigation')
    chapters = nav.find_all(class_='view-chapter')
    for chapter in chapters:
        chapter_name = chapter.find(
            class_='chapter-text substr').get_text(strip=True)
        counter.add(0)
        outline.write(chapter_name, counter, 0)

        lectures = chapter.find_all(class_='view-lecture')
        for lecture in lectures:
            actions = lecture.find(class_='lecture-title')
            lecture_name = actions.get_text(strip=True)
            counter.add(1)
            outline.write(lecture_name, counter, 1)
            # unitid = actions.a['unitid']
            # print(unitid)
            group = actions.div.find_all('a')
            # for action in group:
            #     print(action.i['class'])
            videos = list(
                filter(lambda action: 'icon-play' in action.i['class'][0], group))
            # videos = [action for action in group if lambda :'icon-play' in action.i['class'][0]]
            docs = list(
                filter(lambda action: 'icon-doc' in action.i['class'][0], group))
            for video in videos:
                counter.add(2)
                outline.write(video['title'], counter, 2, sign='#')
                if len(videos) == 1:
                    extra_num = ''
                else:
                    extra_num = '-%s' % str(counter)[-1:]
                video_list.append(
                    Video(counter, lecture_name + extra_num, video['itemid']))
            counter.reset()
            for doc in docs:
                counter.add(2)
                outline.write(doc['title'], counter, 2, sign='*')
                document_list.append(
                    Document(counter, lecture_name, doc['itemid']))
    return video_list, document_list


def parse_resource(video):
    """解析视频地址"""

    res = CANDY.post('https://www.cnmooc.org/study/play.mooc',
                    data={'itemId': video.meta, 'itemType': '10', 'testPaperId': ''}).text
    soup = BeautifulSoup(res, 'lxml')
    node_id = soup.find(id='nodeId')['value']

    res = CANDY.post('https://www.cnmooc.org/item/detail.mooc',
                    data={'nodeId': node_id, 'itemId': video.meta}).json()
    if WORK_DIR.need_download(video.file_name+".mp4", CONFIG["overwrite"]):
        url = res['node']['flvUrl']
        FILES['videos'].write_string(url)
        FILES['renamer'].write(url.split('/')[-1], video.file_name)
        VIDEOS.append((url, video.file_name+".mp4"))

    if CONFIG['sub']:
        exts = res['node']['nodeExts']
        for ext in exts:
            file_name = '%s%s.srt' % (video.file_name, '' if len(
                exts) == 1 else '_' + ext['languageCode'])
            if WORK_DIR.need_download(file_name, CONFIG["overwrite"]):
                CANDY.download_bin('https://static.cnmooc.org' +
                                ext['node']['rsUrl'], WORK_DIR.file(file_name))


def get_doc(doc_list):
    """获得文档"""

    WORK_DIR.change('Docs')
    for doc in doc_list:
        post_data = {'itemId': doc.meta, 'itemType': '20', 'testPaperId': ''}
        res = CANDY.post(
            'https://www.cnmooc.org/study/play.mooc', data=post_data).text
        try:
            url = re.search(r'isSlideShow\("(.+)?"\);', res).group(1)
        except AttributeError:
            continue
        ext = url.split('.')[-1]
        file_name = doc.file_name
        if WORK_DIR.need_download(file_name + '.' + ext, CONFIG["overwrite"]):
            CANDY.download_bin('https://static.cnmooc.org' + url, WORK_DIR.file(file_name + '.' + ext))


def start(url, config, cookies=None):
    """调用接口函数"""

    global WORK_DIR
    CONFIG.update(config)

    CANDY.set_cookies(cookies)

    course_info = get_summary(url)
    WORK_DIR = WorkingDir(CONFIG['dir'], course_info)
    WORK_DIR.change('Videos')

    FILES['renamer'] = Renamer(WORK_DIR.file('Rename.{ext}'))
    FILES['videos'] = ClassicFile(WORK_DIR.file('Videos.txt'))

    course = 'https://www.cnmooc.org/portal/session/unitNavigation/'
    course_nav = course + url.split('/')[-1]
    resource = get_resource(course_nav)

    rename = WORK_DIR.file('Names.txt') if CONFIG['rename'] else False

    playlist = get_playlist(CONFIG["playlist_type"], CONFIG["playlist_path_type"])
    if playlist:
        parse_res_list(resource[0], rename, playlist.write, parse_resource)
    else:
        parse_res_list(resource[0], rename, parse_resource)

    if CONFIG['doc']:
        get_doc(resource[1])

    exports.update({
        "workdir": WORK_DIR,
        "spider": CANDY,
        "videos": VIDEOS
    })
