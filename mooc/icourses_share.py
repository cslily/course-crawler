# -*- coding: utf-8 -*-
"""爱课程 资源共享课"""
import re

from .utils import *
from bs4 import BeautifulSoup

CANDY = Crawler()
CONFIG = {}
FILES = {}

def get_summary(url):
    """从课程主页面获取信息"""
    if re.match(r'https?://www.icourses.cn/web/sword/portal/shareDetails\?cId=(\d+)', url):
        course_id = re.match(r'https?://www.icourses.cn/web/sword/portal/shareDetails\?cId=(\d+)', url).group(1)
        url = 'http://www.icourses.cn/sCourse/course_{}.html'.format(course_id)
    res = CANDY.get(url)
    res.encoding = 'utf8'
    soup = BeautifulSoup(res.text, 'lxml')
    print(soup)
    name = soup.find('div', class_='course-introduction-infor').find('div', class_='course-title').p.string

    dir_name = course_dir(name, '爱课程资源共享课')

    print(dir_name)

    return course_id, dir_name


def parse_resource(resource):
    """解析资源地址和下载资源"""

    file_name = resource.file_name
    if resource.type == 'Video':
        video_urls = {}
        video_urls['sd'] = resource.meta['fullResUrl']
        if resource.meta.get('fullResUrl2'):
            video_urls['hd'] = resource.meta['fullResUrl2']
        
        resolutions = ['shd', 'hd', 'sd']
        for sp in resolutions[CONFIG['resolution']:]:
            if video_urls.get(sp):
                url = video_urls[sp]
                break

        res_print(file_name + '.mp4')
        FILES['renamer'].write(re.search(r'(\w+\.mp4)', url).group(1), file_name)
        FILES['video'].write_string(url)
        #resource.ext = ext

        if not CONFIG['sub']:
            return
        # 暂未发现字幕

    elif resource.type == 'Document':
        if WORK_DIR.exist(file_name + '.pdf'):
            return
        pdf_url = resource.meta['fullResUrl']
        res_print(file_name + '.pdf')
        CANDY.download_bin(pdf_url, WORK_DIR.file(file_name + '.pdf'))


def get_resource(course_id):
    """获取各种资源"""

    outline = Outline()
    counter = Counter()

    video_list = []
    pdf_list = []

    res = CANDY.get('http://www.icourses.cn/web/sword/portal/shareChapter?cid={}'.format(course_id))
    soup = BeautifulSoup(res.text, 'lxml')
    chapters = soup.find('ul', id = 'chapters').children
    for chapter in chapters:
        if chapter.name is None:
            continue
        counter.add(0)
        chapter_id = chapter.attrs['data-id']
        chapter_name = chapter.find('a', class_ = 'chapter-title-text').string.replace('\n\t\t\t\t\t\t\t', ' ')
        outline.write(chapter_name, counter, 0)

        # 章前导读
        important = chapter.find('a', attrs = {'title': '重点难点'}).attrs['data-url']
        instructional_design = chapter.find('a', attrs = {'title': '教学设计'}).attrs['data-url']
        exam_id = chapter.find('a', attrs = {'title': '评价考核'}).attrs['data-id']
        exam_contents = requests.post('http://www.icourses.cn/web//sword/common/getTextBody', data = {'id': exam_id}).text
        textbook_id = chapter.find('a', attrs = {'title': '教材内容'}).attrs['data-id']
        textbook_contents = requests.post('http://www.icourses.cn/web//sword/common/getTextBody', data = {'id': textbook_id}).text
        WORK_DIR.change('Introduction')
        outline.write('重点难点', counter, 2, sign='*')
        CANDY.download_bin(important, WORK_DIR.file('%s 重点难点.html') % counter)
        outline.write('教学设计', counter, 2, sign='*')
        CANDY.download_bin(instructional_design, WORK_DIR.file('%s 教学设计.html') % counter)
        outline.write('评价考核', counter, 2, sign='+')
        with open(WORK_DIR.file('%s 评价考核.html' % counter), 'w', encoding='utf_8') as file:
            file.write(exam_contents)
        outline.write('教材内容', counter, 2, sign='+')
        with open(WORK_DIR.file('%s 教材内容.html' % counter), 'w', encoding='utf_8') as file:
            file.write(textbook_contents)

        lessons = chapter.find('ul', class_='chapter-body-l').contents
        for lesson in lessons:
            if len(lessons) == 1:
                counter.add(1)
                lesson_id = chapter_id
                lesson_name = chapter_name
            else:
                if lesson.name is None:
                    continue
                counter.add(1)
                lesson_info = lesson.find('a', class_='chapter-body-content-text')
                lesson_id = lesson_info.attrs['data-secid']
                lesson_name = lesson_info.text.replace('\n', '')
            rej = requests.post('http://www.icourses.cn/web//sword/portal/getRess', data = {'sectionId': lesson_id}).json()
            
            outline.write(lesson_name, counter, 1)

            for resource in rej['model']['listRes']:
                if resource['mediaType'] == 'mp4':
                    counter.add(2)
                    outline.write(resource['title'], counter, 2, sign='#')
                    video_list.append(Video(counter, resource['title'], resource))
            counter.reset()

            for resource in rej['model']['listRes']:
                if resource['mediaType'] in ['pdf', 'ppt']:
                    counter.add(2)
                    outline.write(resource['title'], counter, 2, sign='*')
                    if CONFIG['doc']:
                        pdf_list.append(Document(counter, resource['title'], resource))
            counter.reset()

    if video_list:
        rename = WORK_DIR.file('Names.txt') if CONFIG['rename'] else False
        WORK_DIR.change('Videos')
        if CONFIG['dpl']:
            playlist = Playlist()
            parse_res_list(video_list, rename, playlist.write, parse_resource)
        else:
            parse_res_list(video_list, rename, parse_resource)
    if pdf_list:
        WORK_DIR.change('PDFs')
        parse_res_list(pdf_list, None, parse_resource)


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

    if CONFIG['aria2']:
        del FILES['video']
        WORK_DIR.change('Videos')
        aria2_download(CONFIG['aria2'], WORK_DIR.path, webui=CONFIG['aria2-webui'], session=CONFIG['aria2-session'])
