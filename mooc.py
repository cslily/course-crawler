# -*- coding: utf-8 -*-
"""MOOC 课程下载"""

import os
import sys
import re
import json
import argparse

from moocs.utils import aria2_download, segment_download


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


def main():
    """解析命令行参数并调用相关模块进行下载"""

    parser = argparse.ArgumentParser(description='Course Crawler')
    parser.add_argument('url', help='课程地址')
    parser.add_argument('-c', '--restore-cookies', action='store_true',
                        help='执行任务的时候重新输入 cookies')
    parser.add_argument('-d', '--dir', default=r'', help='下载目录')
    parser.add_argument('-r', '--quality', default='shd', help='视频清晰度')
    parser.add_argument('-w', '--override',
                        action='store_true', help='强制覆盖重新下载')
    parser.add_argument('--inter', action='store_true', help='交互式修改文件名')
    parser.add_argument('--no-doc', action='store_false',
                        help='不下载 PDF、Word 等文档')
    parser.add_argument('--no-sub', action='store_false', help='不下载字幕')
    parser.add_argument('--no-file', action='store_false', help='不下载附件')
    parser.add_argument('--no-text', action='store_false', help='不下载富文本')
    parser.add_argument("--playlist-type", default="dpl",
                        choices=["dpl", "m3u", "no"], help="播放列表类型，支持 dpl 和 m3u，输入 no 不生成播放列表")
    parser.add_argument("--abs-path", action='store_true',
                        help="播放列表路径使用绝对路径，默认为相对路径")
    parser.add_argument('--download-video',
                        action='store_true', help='使用分段下载器直接下载视频')
    parser.add_argument('--num-thread', type=int, default=30, help='分段下载器线程数')
    parser.add_argument('--aria2', default=None,
                        help='aria2路径，配置后自动调用aria2下载视频')
    parser.add_argument('--aria2-webui', default=None,
                        help='aria2-webui路径，配置后自动开启webui')
    parser.add_argument('--aria2-session', default=None,
                        help='aria2-session路径，配置后将未完成任务保存至session中')

    args = parser.parse_args()
    resolutions = ['shd', 'hd', 'sd']
    playlist_path_type = 'AP' if args.abs_path else 'RP'

    config = {'doc': args.no_doc, 'sub': args.no_sub, 'file': args.no_file, 'text': args.no_text,
              'rename': args.inter, 'dir': args.dir, 'resolution': resolutions.index(args.quality.lower()),
              'override': args.override, 'playlist_type': args.playlist_type, 'playlist_path_type': playlist_path_type,
              'aria2': args.aria2, 'aria2-webui': args.aria2_webui, 'aria2-session': args.aria2_session,
              'download_video': args.download_video, 'num_thread': args.num_thread}

    if re.match(r'https?://www.icourse163.org/(spoc/)?(course|learn)/', args.url):
        from moocs import icourse163 as mooc
    elif re.match(r'https?://www.xuetangx.com/courses/.+/about', args.url):
        from moocs import xuetangx as mooc
    elif re.match(r'https?://mooc.study.163.com/(course|learn)/', args.url):
        from moocs import study_mooc as mooc
    elif re.match(r'https?://study.163.com/course/', args.url):
        from moocs import study_163 as mooc
    elif re.match(r'https?://open.163.com/(special|movie)/', args.url):
        from moocs import open_163 as mooc
    elif re.match(r'https?://www.cnmooc.org/portal/course/', args.url):
        from moocs import cnmooc as mooc
    elif re.match(r'https?://www.icourses.cn/web/sword/portal/videoDetail', args.url):
        from moocs import icourses as mooc
    elif re.match(r'https?://www.icourses.cn/sCourse/course_\d+.html', args.url) or \
            re.match(r'https?://www.icourses.cn/web/sword/portal/shareDetails\?cId=', args.url):
        from moocs import icourses_share as mooc
    elif re.match(r'https?://www.livedu.com.cn/ispace4.0/moocxjkc/toKcView.do\?kcid=', args.url):
        from moocs import livedu as mooc
    else:
        print('课程地址有误！')
        sys.exit(1)

    if mooc.need_cookies:
        cookies = store_cookies(mooc.name, restore=args.restore_cookies)
    else:
        cookies = None

    mooc.start(args.url, config, cookies)

    # 视频下载
    if config['aria2'] or config['download_video']:
        workdir = mooc.exports["workdir"]
        workdir.change('Videos')
        if config['aria2']:
            aria2_download(config['aria2'], workdir.path,
                           webui=config['aria2-webui'], session=config['aria2-session'])
        elif config['download_video']:
            spider, videos = mooc.exports["spider"], mooc.exports["videos"]
            segment_download(videos, workdir.path, spider, override=config["override"],
                             num_thread=config["num_thread"])


if __name__ == '__main__':
    main()
