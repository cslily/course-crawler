# -*- coding: utf-8 -*-
"""MOOC 课程下载"""

import os
import sys
import re
import argparse

from moocs.utils import aria2_download, store_cookies


def main():
    """解析命令行参数并调用相关模块进行下载"""

    parser = argparse.ArgumentParser(description='Course Crawler')
    parser.add_argument('url', help='课程地址')
    parser.add_argument('-c', '--restore-cookies', action='store_true',
                        help='执行任务的时候重新输入 cookies')
    parser.add_argument('-d', '--dir', default=r'', help='下载目录')
    parser.add_argument('-r', '--quality', default='shd', help='视频清晰度')
    parser.add_argument('-w', '--overwrite',
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
    parser.add_argument('--aria2', default=None,
                        help='aria2路径，配置后自动调用aria2下载视频')

    args = parser.parse_args()
    resolutions = ['shd', 'hd', 'sd']
    playlist_path_type = 'AP' if args.abs_path else 'RP'

    config = {'doc': args.no_doc, 'sub': args.no_sub, 'file': args.no_file, 'text': args.no_text,
              'rename': args.inter, 'dir': args.dir, 'resolution': resolutions.index(args.quality.lower()),
              'overwrite': args.overwrite, 'playlist_type': args.playlist_type, 'playlist_path_type': playlist_path_type,
              'aria2': args.aria2}

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
    if config['aria2']:
        workdir = mooc.exports["workdir"]
        workdir.change('Videos')
        videos = mooc.exports["videos"]
        aria2_download(config['aria2'], videos, workdir.path)


if __name__ == '__main__':
    main()
