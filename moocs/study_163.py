# -*- coding: utf-8 -*-
"""网易云课堂"""

import time
from urllib import parse

import requests

from moocs.utils import *
from utils.crawler import Crawler

name = "study_163"
need_cookies = False
CANDY = Crawler()
CONFIG = {}
FILES = {}
VIDEOS = []
exports = {}
__all__ = ["name", "need_cookies", "start", "exports"]


def get_summary(url):
    """从课程主页面获取信息"""

    res = requests.get(url).text

    if re.search(r'courseId=(\d+)', url):
        course_id = re.search(r'courseId=(\d+)', url).group(1)
    else:
        course_id = re.search(r'introduction/(\d+)\.htm', url).group(1)
    name = re.search(r'<title>(.+) - 网易云课堂</title>', res).group(1)

    dir_name = course_dir(name, '网易云课堂')

    print(dir_name)

    CONFIG['course_id'] = course_id
    return course_id, dir_name


def parse_resource(resource):
    """解析资源地址和下载资源"""

    file_name = resource.file_name
    if resource.type == 'Video':
        post_data = {'callCount': '1', 'scriptSessionId': '${scriptSessionId}190',
                     'httpSessionId': 'b1a6d411df364e51833ac11570fc3f07', 'c0-scriptName': 'LessonLearnBean',
                     'c0-methodName': 'getVideoLearnInfo', 'c0-id': '0', 'c0-param0': 'string:' + resource.meta[1],
                     'c0-param1': 'string:' + CONFIG['course_id'],
                     'batchId': str(int(time.time() * 1000))}
        res = CANDY.post('https://study.163.com/dwr/call/plaincall/LessonLearnBean.getVideoLearnInfo.dwr',
                         data=post_data).text.encode('utf_8').decode('unicode_escape')
        video_info = re.search(
            r'signature="(\w+)";.+videoId=(\d+);[\s\S]+name:"(.+?)",', res).group(1, 2, 3)
        data = CANDY.post('https://vod.study.163.com/eds/api/v1/vod/video', data={
            'videoId': video_info[1],
            'signature': video_info[0],
            'clientType': '1'
        }).json()

        resolutions = [3, 2, 1]
        for sp in resolutions[CONFIG['resolution']:]:
            # TODO: 增加视频格式选择
            for video in data['result']['videos']:
                if video['quality'] == sp and video['format'] == 'mp4':
                    url = video['videoUrl']
                    ext = '.mp4'
                    break
            else:
                continue
            break
        if WORK_DIR.need_download(file_name + ext, CONFIG["overwrite"]):
            FILES['renamer'].write(
                re.search(r'(\w+\.mp4)', url).group(1), file_name, ext)
            FILES['video'].write_string(url)
            VIDEOS.append((url, file_name+ext))
            resource.ext = ext

        if not CONFIG['sub']:
            return
        # 暂未发现字幕 api应该在data['result']['srtCaptions']

    elif resource.type == 'Document':
        if not WORK_DIR.need_download(file_name+".pdf", CONFIG["overwrite"]):
            return
        post_data = {
            'callCount': '1',
            'scriptSessionId': '${scriptSessionId}190',
            'httpSessionId': 'c4927103a1c042ee95faed758d0db8f8',
            'c0-scriptName': 'LessonLearnBean',
            'c0-methodName': 'getTextLearnInfo',
            'c0-id': '0',
            'c0-param0': 'string:' + resource.meta[1],
            'c0-param1': 'string:' + CONFIG['course_id'],
            'batchId': str(int(time.time() * 1000)),
        }
        res = CANDY.post('https://study.163.com/dwr/call/plaincall/LessonLearnBean.getTextLearnInfo.dwr',
                         data=post_data).text.encode('utf_8').decode('unicode_escape')
        pdf_url = re.search(r'pdfUrl:"(http://.+?)",', res).group(1)
        CANDY.download_bin(pdf_url, WORK_DIR.file(file_name + '.pdf'))
    else:
        if not WORK_DIR.need_download(file_name+resource.meta[2], CONFIG["overwrite"]):
            return
        CANDY.download_bin(resource.meta[3], WORK_DIR.file(
            file_name + resource.meta[2]))


def get_resource(course_id):
    """获取各种资源"""

    outline = Outline()
    counter = Counter()

    video_list = []
    pdf_list = []
    file_list = []

    post_data = {
        'callCount': '1',
        'scriptSessionId': '${scriptSessionId}190',
        'httpSessionId': '89a04ce41c7d42759b0a62efe392e153',
        'c0-scriptName': 'PlanNewBean',
        'c0-methodName': 'getPlanCourseDetail',
        'c0-id': '0',
        'c0-param0': 'string:' + course_id,
        'c0-param1': 'number:0',
        'c0-param2': 'null:null',
        'batchId': str(int(time.time() * 1000)),
    }
    res = CANDY.post('https://study.163.com/dwr/call/plaincall/PlanNewBean.getPlanCourseDetail.dwr',
                     data=post_data).text.encode('utf_8').decode('unicode_escape')

    chapters = re.findall(r'courseId=\d+;.+id=(\d+);.+name="(.+)";', res)
    for chapter in chapters:
        counter.add(0)
        outline.write(chapter[1], counter, 0)

        lessons = re.findall(
            r'chapterId=%s;.+?hasReferences=(\w+);.+?id=(\d+).+?lessonName="(.*?)";.+?type=(\d+);' % chapter[0], res, re.DOTALL)
        for lesson in lessons:
            counter.add(1)
            outline.write(lesson[2], counter, 1)

            # Video
            if lesson[3] == '2' or lesson[3] == '50':
                counter.add(2)
                outline.write(lesson[2], counter, 2, sign='#')
                video_list.append(Video(counter, lesson[2], lesson))
                counter.reset()

            # Pdf
            elif lesson[3] == '3':
                counter.add(2)
                outline.write(lesson[2], counter, 2, sign='*')
                pdf_list.append(Document(counter, lesson[2], lesson))

            # References
            files = []
            if eval(lesson[0][0].upper() + lesson[0][1:]):
                post_data = {'callCount': '1', 'scriptSessionId': '${scriptSessionId}190',
                             'httpSessionId': 'b1a6d411df364e51833ac11570fc3f07', 'c0-scriptName': 'LessonReferenceBean',
                             'c0-methodName': 'getLessonReferenceVoByLessonId', 'c0-id': '0', 'c0-param0': 'number:' + lesson[1],
                             'batchId': str(int(time.time() * 1000))}
                ref_info = CANDY.post('https://study.163.com/dwr/call/plaincall/LessonReferenceBean.getLessonReferenceVoByLessonId.dwr',
                                      data=post_data).text.encode('utf_8').decode('unicode_escape')
                refs = re.findall(
                    r'id=(\d+);.+name="(.+)";.+suffix="(\.\w+)";.+url="(.+?)";', ref_info)

                for ref in refs:
                    ref = (ref[0], parse.unquote(ref[1]), ref[2], ref[3])
                    files.append(ref)

            for file in files:
                counter.add(2)
                outline.write(file[1], counter, 2, sign='!')
                if CONFIG['file']:
                    file_list.append(Resource(counter, file[1], file))
            counter.reset()

    if video_list:
        rename = WORK_DIR.file('Names.txt') if CONFIG['rename'] else False
        WORK_DIR.change('Videos')
        playlist = get_playlist(CONFIG["playlist_type"], CONFIG["playlist_path_type"])
        if playlist:
            parse_res_list(video_list, rename, playlist.write, parse_resource)
        else:
            parse_res_list(video_list, rename, parse_resource)
    if pdf_list:
        WORK_DIR.change('PDFs')
        parse_res_list(pdf_list, None, parse_resource)
    if file_list:
        WORK_DIR.change('Files')
        parse_res_list(file_list, None, parse_resource)


def start(url, config, cookies=None):
    """调用接口函数"""

    # 初始化设置
    global WORK_DIR
    CONFIG.update(config)

    # 课程信息
    course_info = get_summary(url)

    # 创建课程目录
    WORK_DIR = WorkingDir(CONFIG['dir'], course_info[1])

    WORK_DIR.change('Videos')
    FILES['renamer'] = Renamer(WORK_DIR.file('Rename.{ext}'))
    FILES['video'] = ClassicFile(WORK_DIR.file('Videos.txt'))

    # 获得资源
    get_resource(course_info[0])

    exports.update({
        "workdir": WORK_DIR,
        "spider": CANDY,
        "videos": VIDEOS
    })
