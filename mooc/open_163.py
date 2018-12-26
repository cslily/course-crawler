# -*- coding: utf-8 -*-
"""网易公开课"""

import time

from .utils import *
from bs4 import BeautifulSoup
from Crypto.Cipher import AES

CANDY = Crawler()
CONFIG = {}
FILES = {}


def get_summary(url):
    """从课程主页面获取信息"""

    res = CANDY.get(url).text
    soup = BeautifulSoup(res,'html.parser')
    links = []
    if re.match(r'https?://open.163.com/special/', url):
        # 从课程主页解析各课程链接
        names = soup.find_all('div', class_='g-container')[1]
        organization = names.find('a').string.strip()
        course = names.find('span', class_='pos').string.strip()
        list1 = soup.find('table', id='list2')
        tds = list1.find_all('td', class_="u-ctitle")

        for td in tds:
            a = td.find('a')
            links.append((a.get('href'), a.string))

    else:
        # 从学习页面解析各课程链接（有的课程不含课程主页）
        names = soup.find('p', class_='bread').find_all('a', class_='f-c9')
        organization = names[0].string.strip()
        course = names[1].string.strip()
        listrow = soup.find('div', class_='listrow')
        for item in listrow.find_all('div',class_='item'):
            p = item.find('p', class_='f-thide')
            if p.find('a'):
                a = p.find('a')
                links.append((a.get('href'), a.string))
            else:
                links.append((url, p.string.split(']')[-1]))

    dir_name = course_dir(course, organization)

    print(dir_name)

    CONFIG['links'] = links
    return links, dir_name

def parse_resource(resource):
    """解析资源地址和下载资源"""

    def open_decrypt(hex_string, t):
        """将加密16进制字符串转化为真实url"""
        CRYKey = {1: b"4fxGZqoGmesXqg2o", 2: b"3fxVNqoPmesAqg2o"}
        aes = AES.new(CRYKey[t], AES.MODE_ECB)
        return str(aes.decrypt(bytes.fromhex(hex_string)),encoding='gbk',errors="ignore").replace('\x08','').replace('\x06', '')

    def update_hex_urls(node, hex_urls):
        """从node中解析出来url信息，并更新hex_url"""
        for child in node.children:
            sp = child.name
            if not hex_urls.get(sp):
                hex_urls[sp] = {}
            for hex_url_tag in child.children:
                hex_urls[sp][hex_url_tag.name] = hex_url_tag.string

    link = resource.meta
    file_name = resource.file_name
    video_info = link.replace('.html', '').split('/')[-1]
    xml_url = 'http://live.ws.126.net/movie/' + video_info[-2] + '/' + video_info[-1] + '/2_' + video_info + '.xml'
    res = CANDY.get(xml_url)
    res.encoding = 'gbk'

    # 解析xml数据
    soup = BeautifulSoup(res.text,'lxml')
    name = soup.find('title').string
    encrypt = int(soup.find('encrypt').string)
    hex_urls = {}
    update_hex_urls(soup.find('flvurl'), hex_urls)
    update_hex_urls(soup.find('flvurlorigin'), hex_urls)
    update_hex_urls(soup.find('playurl'), hex_urls)
    update_hex_urls(soup.find('playurl_origin'), hex_urls)
    subs = {}
    for sub in soup.find('subs'):
        subs[sub.find('name').string] = sub.find('url').string

    formats = ['mp4', 'flv']
    resolutions = ['shd', 'hd', 'sd']
    resolutions = resolutions[CONFIG['resolution']:] + list(reversed(resolutions[:CONFIG['resolution']]))
    modes = ((sp, ext) for sp in resolutions for ext in formats)
    for sp, ext in modes:
        if hex_urls.get(sp):
            if hex_urls[sp].get(ext):
                hex_url = hex_urls[sp][ext]
                video_url = open_decrypt(hex_url, encrypt)
                ext = video_url.split('.')[-1] # 对扩展名进行修正，有的课程从mp4中解析出来的仍为flv
                if ext in formats:
                    ext = '.' + ext
                    resource.ext = ext
                    break

    res_print(file_name + ext)
    FILES['renamer'].write(re.search(r'(\w+\%s)'% ext, video_url).group(1), file_name, ext)
    FILES['video'].write_string(video_url)
    if not CONFIG['sub']:
        return
    WORK_DIR.change('Videos')
    for subtitle_lang, subtitle_url in subs.items():
        if len(subs) == 1:
            sub_name = file_name + '.srt'
        else:
            sub_name = file_name + '_' + subtitle_lang + '.srt'
        res_print(sub_name)
        CANDY.download_bin(subtitle_url, WORK_DIR.file(sub_name))

def get_resource(links):
    """获取各种资源"""

    outline = Outline()
    counter = Counter(1)

    video_list = []

    for link, name in links:
        counter.add(0)
        outline.write(name, counter, 0, sign='#')
        video_list.append(Video(counter, name, link))

    if video_list:
        rename = WORK_DIR.file('Names.txt') if CONFIG['rename'] else False
        WORK_DIR.change('Videos')
        if CONFIG['dpl']:
            playlist = Playlist()
            parse_res_list(video_list, rename, parse_resource, playlist.write)
        else:
            parse_res_list(video_list, rename, parse_resource)

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
        for file in ['video', 'renamer']:
            del FILES[file]
        WORK_DIR.change('Videos')
        aria2_download(CONFIG['aria2'], WORK_DIR.path, webui=CONFIG['aria2-webui'], session=CONFIG['aria2-session'])
