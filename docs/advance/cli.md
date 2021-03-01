# 命令行参数

<bilibili-player avid=65418448 cid=113566361 page=2></bilibili-player>

## 显示帮助信息

> `-h` `--help` 用于显示帮助信息。

输入 `python mooc.py -h` 或 `python mooc.py --help`。

## 指定下载目录

> `-d <path>` `--dir=<path>` 用于指定下载目录为 `<path>`。

课程文件夹将在创建在 `<path>` 中。默认创建在当前目录，即 `-d ""`。

示例

```bash
python mooc.py -d "G:\MOOCs" https://www.icourse163.org/course/TONGJI-53004
```

::: tip
`<path>` 不能以 \ 结尾；当 `<path>` 存在空格的时候，必须使用 `"` 将路径包裹起来。
:::

## 重新录入 Cookies

> `-c` `--restore-cookies` 用于在程序运行时录入新的 Cookies，以覆盖旧的 Cookies

由于 Cookies 经常存在过期的情况，手动去删除会很麻烦，这时只需要运行时加上这样一个参数就可以将旧的 Cookies 覆盖掉

## 指定视频清晰度

> `-r <quality>` `--quality <quality>` 用于指定视频清晰度为 `<quality>`

`<quality>` 可选列表为 `shd` `hd` `sd` ，分别对应超高清、高清、标清，默认为超高清

示例

```bash
python mooc.py -r hd https://www.icourse163.org/course/TONGJI-53004
```

::: tip
在支持清晰度调节的课程中，如果指定的清晰度不存在，则先自动降低清晰度，若仍无匹配的清晰度，则后升高清晰度，比如指定为 hd ，则会以 hd sd shd 序列对清晰度进行匹配
:::

## 强制覆盖已下载文件 <Badge text="danger" type="error"/>

> `-w`, `--overwrite` 用于启用强制覆盖已经下载过的文件

示例

```bash
python mooc.py https://www.icourse163.org/course/TONGJI-53004 -w
```

## aria2 的调用 <Badge text="beta" type="warn"/>

为了方便后续视频的下载，增加了直接调用 `aria2` 进行下载的支持

::: tip aria2 相关下载：

-  [aria2](https://github.com/aria2/aria2/releases)
-  [aria2 webui](https://github.com/ziahamza/webui-aria2/archive/master.zip)
-  [AriaNg（一个比较好看的 webui）](https://github.com/mayswind/AriaNg/releases)

:::

> `--aria2` 用于启用 `aria2` 直接下载视频

当配置好 aria2 路径后，在课件解析完成时程序不退出，直接调用 `aria2` 下载视频

::: tip

请事先确保 `aria2c` 已经是可执行程序，即已经添加到环境变量

:::

示例

```bash
python mooc.py --aria2 https://www.icourse163.org/course/TONGJI-53004
```

## 播放列表设置

由于不同播放器对播放列表格式的要求并不相同，通过修改参数可以获得更通用的播放列表

::: tip 一些推荐的播放器

-  Windows
   -  PotPlayer
-  Linux
   -  SMPlayer
-  MacOS
   -  IINA

:::

### 播放列表类型

> `--playlist-type=<playlist_type>` 用于指定播放列表类型

可选列表 `dpl` `m3u` `no` ，默认为 `dpl` ，若指定 `no` 则不生成播放列表

::: tip

默认生成的 `Playlist.dpl` 仅仅对 PotPlayer 有效，如果无法使用 PotPlayer （比如 Linux 下），请生成更通用的 `m3u` 格式

:::

示例

```bash
python mooc.py --playlist-type=m3u https://www.icourse163.org/course/TONGJI-53004
```

### 播放列表路径类型

> `--abs-path` 用于指定播放列表内的路径为绝对路径

::: tip

有些播放器并不支持相对路径的播放列表，如果你的播放器无法打开该文件，请尝试生成绝对路径的播放列表

:::

示例

```bash
python mooc.py --playlist-type=m3u --abs-path https://www.icourse163.org/course/TONGJI-53004
```

::: warning

绝对路径的播放列表会在课程文件夹移动后失效，如果开启该选项，请不要在课程下载后进行移动

:::

## 不下载 ...

### 不下载文档

> `--no-doc` 用于阻止下载 PDF、Word、PowerPoint 等文档。

默认会下载所有文档。

当指定了这个选项之后，不会下载任何文档（包括 PPT 和书籍等）。

示例

```bash
python mooc.py https://www.icourse163.org/course/TONGJI-53004 --no-doc
```

### 不下载字幕

> `--no-sub` 用于阻止下载字幕。

### 不下载富文本

> `--no-text` 用于阻止下载富文本。

### 不下载附件

> `--no-file` 用于阻止下载附件。

### 不下载播放列表

> `--playlist-type=no` 用于阻止下载播放列表。详情见 [播放列表类型](#播放列表类型)

## 修正视频/文档名

> `--inter` 用于修改文件名。

会调出文件编辑器，编辑好视频的名字之后保存。默认没有启用。

::: tip
请严格按照原来文本长度进行设置，否则可能会发生没有标题的情况。
:::
