# -*- coding: utf-8 -*-
"""中国大学MOOC"""

import json
import time
import sys

from moocs.utils import *
from utils.crawler import Crawler

name = "icourse163"
need_cookies = True
CANDY = Crawler()
CONFIG = {}
FILES = {}
VIDEOS = []
exports = {}
__all__ = ["name", "need_cookies", "start", "exports"]


def get_summary(url):
    """从课程主页面获取信息"""

    url = url.replace('learn/', 'course/')
    res = CANDY.get(url).text

    term_id = re.search(r'termId : "(\d+)"', res).group(1)
    names = re.findall(r'name:"(.+)"', res)

    dir_name = course_dir(*names[:2])

    print(dir_name)
    CONFIG['term_id'] = term_id
    return term_id, dir_name


def parse_resource(resource):
    """解析资源地址和下载资源"""

    post_data = {'callCount': '1', 'scriptSessionId': '${scriptSessionId}190',
                 'httpSessionId': '5531d06316b34b9486a6891710115ebc', 'c0-scriptName': 'CourseBean',
                 'c0-methodName': 'getLessonUnitLearnVo', 'c0-id': '0', 'c0-param0': 'number:' + resource.meta[0],
                 'c0-param1': 'number:' + resource.meta[1], 'c0-param2': 'number:0',
                 'c0-param3': 'number:' + resource.meta[2], 'batchId': str(int(time.time()) * 1000)}
    res = CANDY.post('https://www.icourse163.org/dwr/call/plaincall/CourseBean.getLessonUnitLearnVo.dwr',
                     data=post_data).text

    file_name = resource.file_name
    if resource.type == 'Video':
        if CONFIG["hasToken"]:
            video_token = CANDY.post('https://www.icourse163.org/web/j/resourceRpcBean.getResourceToken.rpc?csrfKey='+CONFIG['token'], data={
                'bizId': resource.meta[2],
                'bizType': 1,
                'contentType': 1,
            }).json()['result']['videoSignDto']['signature']
            data = CANDY.post('https://vod.study.163.com/eds/api/v1/vod/video', data={
                'videoId': resource.meta[0],
                'signature': video_token,
                'clientType': '1'
            }).json()

            resolutions = [3, 2, 1]
            url, ext = '', ''
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
            assert ext, "近期中国大学 MOOC 接口变动，请临时使用 https://github.com/SigureMo/mooc-dl"

            if WORK_DIR.need_download(file_name + ext, CONFIG["overwrite"]):
                FILES['renamer'].write(
                    re.search(r'(\w+\.mp4)', url).group(1), file_name, ext)
                FILES['video'].write_string(url)
                VIDEOS.append((url, file_name+ext))
                resource.ext = ext
        else:
            resolutions = ['Shd', 'Hd', 'Sd']
            url, ext = '', ''
            for sp in resolutions[CONFIG['resolution']:]:
                # TODO: 增加视频格式选择
                # video_info = re.search(r'%sUrl="(?P<url>.*?(?P<ext>\.((m3u8)|(mp4)|(flv))).*?)"' % sp, res)
                video_info = re.search(r'(?P<ext>mp4)%sUrl="(?P<url>.*?\.(?P=ext).*?)"' % sp, res)
                if video_info:
                    url, ext = video_info.group('url', 'ext')
                    ext = '.' + ext
                    break
            assert ext, "近期中国大学 MOOC 接口变动，请临时使用 https://github.com/SigureMo/mooc-dl"

            url = url.replace('v.stu.126.net', 'jdvodrvfb210d.vod.126.net')
            if CANDY.head(url, allow_redirects=True, timeout=20).status_code != 200:
                url = url.replace('mooc-video', 'jdvodrvfb210d')
            if WORK_DIR.need_download(file_name + ext, CONFIG["overwrite"]):
                FILES['renamer'].write(re.search(r'(\w+\.((m3u8)|(mp4)|(flv)))', url).group(1), file_name, ext)
                FILES['video'].write_string(url)
                VIDEOS.append((url, file_name+ext))
                resource.ext = ext

        if not CONFIG['sub']:
            return
        subtitles = re.findall(r'name="(.+)";.*url="(.*?)"', res)
        for subtitle in subtitles:
            if len(subtitles) == 1:
                sub_name = file_name + '.srt'
            else:
                subtitle_lang = subtitle[0].encode(
                    'utf_8').decode('unicode_escape')
                sub_name = file_name + '_' + subtitle_lang + '.srt'
            if not WORK_DIR.need_download(sub_name, CONFIG["overwrite"]):
                continue
            CANDY.download_bin(subtitle[1], WORK_DIR.file(sub_name))

    elif resource.type == 'Document':
        if not WORK_DIR.need_download(file_name + '.pdf', CONFIG["overwrite"]):
            return
        pdf_url = re.search(r'textOrigUrl:"(.*?)"', res).group(1)
        CANDY.download_bin(pdf_url, WORK_DIR.file(file_name + '.pdf'))

    elif resource.type == 'Rich':
        if not WORK_DIR.need_download(file_name + '.html', CONFIG["overwrite"]):
            return
        text = re.search(r'htmlContent:"(.*)",id',
                         res.encode('utf_8').decode('unicode_escape'), re.S).group(1)
        with open(WORK_DIR.file(file_name + '.html'), 'w', encoding='utf_8') as file:
            file.write(text)


def get_resource(term_id):
    """获取各种资源"""

    outline = Outline()
    counter = Counter()

    video_list = []
    pdf_list = []
    rich_text_list = []

    post_data = {'callCount': '1', 'scriptSessionId': '${scriptSessionId}190', 'c0-scriptName': 'CourseBean',
                 'c0-methodName': 'getMocTermDto', 'c0-id': '0', 'c0-param0': 'number:' + term_id,
                 'c0-param1': 'number:0', 'c0-param2': 'boolean:true', 'batchId': str(int(time.time()) * 1000)}
    res = CANDY.post('https://www.icourse163.org/dwr/call/plaincall/CourseBean.getMocTermDto.dwr',
                     data=post_data).text.encode('utf_8').decode('unicode_escape')

    chapters = re.findall(r'homeworks=\w+;.+id=(\d+).+name="([\s\S]+?)";', res)
    for chapter in chapters:
        counter.add(0)
        outline.write(chapter[1], counter, 0)

        lessons = re.findall(
            r'chapterId=' + chapter[0] + r'.+contentId=null.+contentType=1.+id=(\d+).+name="([\s\S]+?)"', res)
        for lesson in lessons:
            counter.add(1)
            outline.write(lesson[1], counter, 1)

            videos = re.findall(r'contentId=(\d+).+contentType=(1).+id=(\d+).+lessonId=' +
                                lesson[0] + r'.+name="([\s\S]+?)"', res)
            for video in videos:
                counter.add(2)
                outline.write(video[3], counter, 2, sign='#')
                video_list.append(Video(counter, video[3], video))
            counter.reset()

            pdfs = re.findall(r'contentId=(\d+).+contentType=(3).+id=(\d+).+lessonId=' +
                              lesson[0] + r'.+name="([\s\S]+?)"', res)
            for pdf in pdfs:
                counter.add(2)
                outline.write(pdf[3], counter, 2, sign='*')
                if CONFIG['doc']:
                    pdf_list.append(Document(counter, pdf[3], pdf))
            counter.reset()

            rich_text = re.findall(r'contentId=(\d+).+contentType=(4).+id=(\d+).+jsonContent=(.+?);.+lessonId=' +
                                   lesson[0] + r'.+name="([\s\S]]+?)"', res)
            for text in rich_text:
                counter.add(2)
                outline.write(text[4], counter, 2, sign='+')
                if CONFIG['text']:
                    rich_text_list.append(RichText(counter, text[4], text))
                if CONFIG['file']:
                    if text[3] != 'null' and text[3] != '""':
                        params = {'nosKey': re.search('nosKey":"(.+?)"', text[3]).group(1),
                                  'fileName': re.search('"fileName":"(.+?)"', text[3]).group(1)}
                        file_name = Resource.file_to_save(params['fileName'])
                        outline.write(file_name, counter, 2, sign='!')

                        WORK_DIR.change('Files')
                        file_name = '%s %s' % (counter, file_name)
                        if WORK_DIR.need_download(file_name, CONFIG["overwrite"]):
                            CANDY.download_bin('https://www.icourse163.org/course/attachment.htm',
                                            WORK_DIR.file(file_name), params=params)
            counter.reset()

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
    if rich_text_list:
        WORK_DIR.change('Texts')
        parse_res_list(rich_text_list, None, parse_resource)


def start(url, config, cookies):
    """调用接口函数"""

    global WORK_DIR
    CANDY.set_cookies(cookies)
    CONFIG.update(config)

    if cookies.get('NTESSTUDYSI'):
        CONFIG['hasToken'] = True
        CONFIG['token'] = cookies.get('NTESSTUDYSI')
    else:
        CONFIG['hasToken'] = False

    term_id, dir_name = get_summary(url)
    WORK_DIR = WorkingDir(CONFIG['dir'], dir_name)
    WORK_DIR.change('Videos')
    FILES['renamer'] = Renamer(WORK_DIR.file('Rename.{ext}'))
    FILES['video'] = ClassicFile(WORK_DIR.file('Videos.txt'))

    get_resource(term_id)

    exports.update({
        "workdir": WORK_DIR,
        "spider": CANDY,
        "videos": VIDEOS
    })
