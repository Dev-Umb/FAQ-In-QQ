'''下面是bot的初始化'''
import asyncio

from graia.application import GraiaMiraiApplication, Session
from graia.broadcast import Broadcast

from config import *

loop = asyncio.get_event_loop()#获取bot运行的协程

bcc = Broadcast(loop=loop)

app = GraiaMiraiApplication(
    broadcast=bcc,
    connect_info=Session(
        host=API_ROOT,  # 填入 httpapi 服务运行的地址
        authKey=AuthKey,  # 填入 authKey
        account=BOTQQ,  # 你的机器人的 qq 号
        websocket=True  # Graia 已经可以根据所配置的消息接收的方式来保证消息接收部分的正常运作.
    )
)