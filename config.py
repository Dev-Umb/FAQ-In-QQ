import asyncio

from graia.application import GraiaMiraiApplication, Session
from graia.broadcast import Broadcast

BlackUser = []#黑名单
Manager = []#超级管理员
BlackGroup = []
#群组黑名单，可以利用这个来对bot的功能进行开关（本插件暂不支持，需要您手动写一个）
HOST='0.0.0.0'#本地地址
PORT=80#端口
BOTQQ=3394886607#Bot的QQ，一定要写，否则会报找不到无头客户端的error
API_ROOT='http://localhost:80'#本地地址

'''下面是bot的初始化'''
loop = asyncio.get_event_loop()#获取bot运行的协程

bcc = Broadcast(loop=loop)

app = GraiaMiraiApplication(
    broadcast=bcc,
    connect_info=Session(
        host=API_ROOT,  # 填入 httpapi 服务运行的地址
        authKey="graia-mirai-api-http-authkey",  # 填入 authKey
        account=BOTQQ,  # 你的机器人的 qq 号
        websocket=True  # Graia 已经可以根据所配置的消息接收的方式来保证消息接收部分的正常运作.
    )
)