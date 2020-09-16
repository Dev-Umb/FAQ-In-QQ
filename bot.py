import functools
import gc
import os
import signal
import subprocess
import sys
import threading
import psutil
import time
from apscheduler.schedulers.blocking import BlockingScheduler
from graia.application import FriendMessage, Friend
from graia.application.event.mirai import *
from graia.broadcast.builtin.decoraters import Depend
from pulgin import *
from MsgObj import Msg
from init_bot import *
from command_session import *
import sched

'''
各文件说明：
    init_bot.py 初始化bot对象和一些需要用到的list或者dict
    bot.py 运行的main文件，包括消息指令入口
    MsgObj.py 独立封装的message消息类，便于对消息数据进行保存和调用
    pulgin.py bot所需要到的一些函数的封装
    config.py bot运行所需要的配置，端口号，bot的QQ号等，配置参见Graia文档
    command_session.py 命令解析器相关函数
'''

commands = {  # 命令解析器
    'startBaidu': start_Baidu,
    'shutdownBaidu': shutdown_Baidu,
    'startQA': start_all,
    'shutdownQA': shutdown_all,
    'manage': open_manager,
    'closeManage': close_manager,
    'welcome': open_welcome,
    'closeWelcome': close_welcome
}

'''
监听新人入群并欢迎
'''


@bcc.receiver("MemberJoinEvent")
async def MemberJoin(event: MemberJoinEvent):
    group = event.member.group
    if group.id not in WelComeGroup:
        return
    if group.id in WelcomeScence:
        talk = WelcomeScence[group.id]
    else:
        talk = "欢迎小可爱来到本群"
    await app.sendGroupMessage(group, MessageChain.create([
        Plain(talk),
        At(event.member.id)
    ]))


'''
修改群迎新词
'''


@bcc.receiver('GroupMessage', headless_decoraters=[
    Depend(judge_depend_target)
])
async def changeWelcome(message: GroupMessage, group: Group):
    if not parser(message, "修改迎新词 "):
        return
    if not message.messageChain.has(Plain):
        return
    plain = message.messageChain.get(Plain)
    txt = plain[0].text.replace("修改迎新词 ", "")
    if len(txt) > 0:
        WelcomeScence[group.id] = txt
        status = "修改成功"
    else:
        status = "修改失败，不合法！"
    await app.sendGroupMessage(group, MessageChain.create([Plain(status)]))


'''
问答模块，集合了
    添加问题
    修改问题
    会话管理
    删除问题
    问答功能
（注：这部分代码十分恶心，请谨慎阅读，之后会重构）
'''


@bcc.receiver("GroupMessage")
async def close_in_group(commandApp: GraiaMiraiApplication, message: GroupMessage, group: Group):
    if parser(message, ".command "):
        if not is_manager(message):
            return
        command = message.messageChain.get(Plain)[0].text.replace('.command ', '')
        send_msg = f"未知的指令{command},目前可执行指令：\n"
        if commands.get(command):
            flag: bool = commands[command](message, group)
            if flag is None:
                return
            if flag:
                send_msg = f"已执行命令{command}"
            else:
                send_msg = f"此群尚不具备{command}指令的条件！"
        else:
            for i in commands.keys():
                send_msg += f"{i}"
        await commandApp.sendGroupMessage(group, message.messageChain.create(
            [Plain(send_msg)]
        ))


async def indexes(message: GroupMessage, group: Group):
    id : str = message.messageChain.get(Plain)[0].text.strip().replace('#', '')
    if id.isdigit():
        temp_list: list = quick_find_question_list[group.id]
        question: str = temp_list[int(id)]
        answer: Msg = search(question, group)
        send_msg = answer.get_msg_graia(message.messageChain)
        await app.sendGroupMessage(group, send_msg)


async def FQA(message: GroupMessage, group: Group) -> bool:
    if not message.messageChain.has(Plain):
        return False
    msg = Msg(message)
    msg_chain = message.messageChain
    # 首先对消息进行问答解析
    Question = msg.txt.strip()
    if Question == '列表':
        await app.sendGroupMessage(group, FQA_list(message, group))
        del msg
        return True
    at = msg_chain.get(At)[0].target if msg_chain.has(At) else 0
    tempQ = search(Question, group)
    if tempQ is not None:
        send_msg = tempQ.get_msg_graia(msg_chain)
    else:
        if at == BOTQQ:
            send_msg = msg_chain.create([
                Plain("没有找到这个问题，请等待学长学姐来回答或回复“列表”查看已有问题")
            ])
        else:
            send_msg = None
    if send_msg is not None:
        await app.sendGroupMessage(group, send_msg)
        del msg
        return True
    del msg
    return False


@bcc.receiver("GroupMessage")
async def BaiDu(message: GroupMessage, group: Group):
    if only_group_in_list(group, shutdown_all_group) \
            or not only_group_in_list(group, start_baiDu_group): return
    if parser(message, "百度 "):
        entry = message.messageChain.get(Plain)[0].text.strip().replace("百度 ", "")
        await app.sendGroupMessage(group=group, message=message.messageChain.create([
            Plain(getBaiduKnowledge(entry))
        ]))
    elif parser(message, "萌娘 "):
        entry = message.messageChain.get(Plain)[0].text.strip().replace("萌娘 ", "")
        await app.sendGroupMessage(group=group, message=message.messageChain.create([
            Plain(getACGKnowledge(entry))
        ]))
    elif parser(message, '。来点好听的'):
        say_loving(message, group)


@bcc.receiver("GroupMessage")
async def group_message_handler(message: GroupMessage, group: Group):
    if message.sender.id in FuckUser:
        await app.sendGroupMessage(group, message.messageChain.create(
            [
                Plain("此用户信用度极低，请勿相信其发布的任何小程序或广告链接，谨防上当受骗！"),
                At(message.sender.id)
            ]
        ))
        return
    if group_is_in_list(message, group, shutdown_all_group):
        return
    if parser(message, "百度 ") \
            or parser(message, "萌娘 "):
        return
    msg = Msg(message)
    question = message.messageChain.get(Plain)[0].text if message.messageChain.has(Plain) else None
    has_session = temp_talk.get(msg.user_id)
    if has_session is not None:
        await session_manager(message,group)
        return
    if await FQA(message, group):
        return

    if parser(message, '#'):
        await indexes(message, group)
        return
    if group.id in mast_manager_group:
        if not is_manager(message):
            return
    if parser(message, "添加问题 "):
        # 创建添加问题的新会话
        question = question.replace("添加问题 ", "").strip()
        if has_session is None:
            add_temp_talk(msg.user_id, 'Add', True, question)
            sendMsg = await AddQA(message, group)
            if sendMsg is not None:
                await app.sendGroupMessage(group, sendMsg)
        del msg
        return

    if parser(message, "修改问题 "):
        # 创建修改问题的新会话
        question = question.replace("修改问题", "").strip()
        question = question if not re.search("#",question) \
            else quick_find_question_list[group.id][int(question.replace('#',''))]
        if has_session is None:
            add_temp_talk(msg.user_id, 'Change', True, question)
            sendMsg = await change(group=group, GM=message)
            if sendMsg is not None:
                await app.sendGroupMessage(group, sendMsg)
        del msg
        return

    if parser(message, "删除问题 "):
        # 删除问题
        question = question.replace("删除问题", "").strip()
        question = question if not re.search("#", question) \
            else quick_find_question_list[group.id][int(question.replace('#', ''))]
        isdeleteOK: str = f"删除问题{question}成功" if deleteQA(question, group) else "不存在这个问题"
        await app.sendGroupMessage(group, message.messageChain.create([
            Plain(isdeleteOK)
        ]))
        await saveQA()
        del msg
        gc.collect()
        return

    if parser(message, ".Fuck") and message.messageChain.has(At) and is_manager(message):
        id = message.messageChain.get(At)[0].target
        if id not in FuckUser:
            FuckUser.append(id)
            await app.sendGroupMessage(group, message.messageChain.create([
                Plain("已经将此人拉入危险用户名单")
            ]))
        else:
            await app.sendGroupMessage(group, message.messageChain.create([
                Plain("此人已被认定为危险用户")
            ]))
        return


def apscheduler(*args, **kwargs):
    def decorator(func):
        @functools.wraps(func)
        def wrapper():
            scheduler = BlockingScheduler()
            scheduler.add_job(func, args[0],
                              hours=kwargs['hour'])
            scheduler.start()
            return func(args=args, kwargs=kwargs)

        return wrapper

    return decorator


@apscheduler('interval', hour=6)
def test():
    print("程序重新开始")
    python = sys.executable
    os.execl(python, python, *sys.argv)


@bcc.receiver("FriendMessage")
async def restart(message: FriendMessage, friend: Friend):
    if friend.id in Manager and message.messageChain.asDisplay().startswith("重启"):
        test()


if __name__ == '__main__':
    # 初始化GroupQA
    # loop.run_until_complete(Compatible_old_index())
    nest_asyncio.apply()
    threading.Thread(target=test, args=()).start()
    loop.run_until_complete(ReadQA())
    loop.run_until_complete(read_love())
    app.launch_blocking()
