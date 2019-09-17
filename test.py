from utils.aria2 import Aria2
import time

url = 'http://mov.bn.netease.com/open-movie/nos/flv/2015/03/25/SAKKBCALE_sd.flv'
aria2 = Aria2(aria2_path="aria2c")
for i in range(3):
    print(i)
    print(aria2.add_uri([url], {"out": "tmp/tmp{}.flv".format(i)}))
while True:
    num_active = int(aria2.get_global_stat()["numActive"])
    print(num_active)
    time.sleep(1)
    if num_active == 0:
        break
