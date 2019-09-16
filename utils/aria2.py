import requests
import subprocess
import json
import time
import os

from urllib.request import urlopen

rpc_url = "http://localhost:{port}/jsonrpc"


class Aria2():

    def __init__(self, aria2_path="aria2c", port=6800):
        self.port = port
        self.rpc_url = rpc_url.format(port=port)
        self.aria2_path = aria2_path
        self.process_file = open("process.out", "w")
        assert self.is_installed(), "请配置正确的 aria2 路径"
        if not self.is_connected():
            self.process = self.init_rpc()

    def __del__(self):
        """ 析构时确保 aria2 关闭 """
        if self.is_connected():
            self.shutdown()
        self.process_file.close()
        self.process.terminate()
        # os.remove(self.process_file.name)

    def rpc_api(method):
        """ RPC 装饰器 """
        def rpc_method(func):
            def new_func(self, *args):
                data = {
                    'jsonrpc': '2.0',
                    'id': 'qwer',
                    'method': method,
                    'params': list(filter(lambda arg: arg is not None, args)),
                }
                res = requests.post(
                    self.rpc_url, data=json.dumps(data), timeout=2)
                return res.json()["result"]
            return new_func
        return rpc_method

    @rpc_api(method="aria2.addUri")
    def add_uri(self, uris, options=None, position=None):
        """ 添加 URI 任务 """
        pass

    @rpc_api(method="aria2.getGlobalStat")
    def get_global_stat(self):
        """ 获取全局统计信息 """
        pass

    @rpc_api(method="aria2.shutdown")
    def shutdown(self):
        """ 关闭 aria2 """
        pass

    def init_rpc(self):
        """ 启动 aria2 RPC """
        cmd = self.aria2_path + \
            ' --enable-rpc' \
            ' --rpc-listen-port %d' \
            ' --continue' \
            ' --max-concurrent-downloads=20' \
            ' --max-connection-per-server=10' \
            ' --rpc-max-request-size=1024M' % self.port

        return subprocess.Popen(cmd, shell=True, stdout=self.process_file)

    def is_connected(self):
        """ 是否可以连接 aria2 """
        try:
            requests.post(self.rpc_url)
            return True
        except requests.exceptions.ConnectionError:
            return False

    def is_installed(self):
        """ 是否已经下载 aria2 """
        try:
            return subprocess.run([self.aria2_path], stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE).returncode == 1
        except FileNotFoundError:
            return False
