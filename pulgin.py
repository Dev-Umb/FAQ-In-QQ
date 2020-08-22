import json
import threading

from graia.broadcast import Broadcast, BaseEvent, ExecutionStop
from graia.application import GraiaMiraiApplication, Session, GroupMessage
from graia.application.message.chain import MessageChain
import asyncio
from graia.application.message.elements.internal import *
from graia.application.friend import *
from graia.application.group import Group
from config import *
from MsgObj import Msg, asSendable_creat

GroupQA = {
}
temp_talk = dict()  # 简易的会话管理器
WelcomeScence = {
}


def add_temp_talk(id: int, type: str, isFirstRun: bool, Question: str):
    temp_talk[id] = {
        'type': type,
        'isFirstRun': isFirstRun,
        'Q': Question
    }


'''进行封装的命令解析器'''


async def session_manager(message: GroupMessage, group: Group):
    if temp_talk.get(message.sender.id):
        # 查看发起会话的用户是否有未结束的会话
        if temp_talk[message.sender.id]['isFirstRun']:
            temp_talk[message.sender.id]['isFirstRun'] = False
            type = temp_talk[message.sender.id]['type']
            if type == 'Add':
                await AddQA(message, group)
            elif type == 'Change':
                await change(group, message)
            temp_talk.pop(message.sender.id)
            # 会话结束，将会话释放掉
            return True
    return False


'''获取问题列表'''


async def FQA_list(message: GroupMessage, group: Group):
    if not message.messageChain.get(At)[0].target == BOTQQ: return
    AllQuestionStr = ''
    if group.id in GroupQA and len(GroupQA[group.id].keys()) >= 1:
        for i in GroupQA[group.id].keys():
            AllQuestionStr += f"*{i}\n"
        send_txt = AllQuestionStr
    else:
        send_txt = "本群暂时没有问题哦"
    send_msg = message.messageChain.create(
        [Plain(send_txt)]
    )
    print(send_txt)
    await app.sendGroupMessage(group, send_msg)


'''
判断消息链是否合法
命令解析器
（目前有bug）
并不能很好地实现目的，因此在调用该解析器的函数中额外增加了判断语句
'''


def parser(message: GroupMessage, txt: str) -> bool:
    if message.messageChain.asSendable().asDisplay().startswith(txt):
        return True
    return False


def judge(message: MessageChain) -> bool:
    if message.has(Plain):
        if message.asSendable().asDisplay().startswith("修改迎新词"):
            return True
    return False


def judge_depend_target(message: MessageChain):
    if not judge(message):
        raise ExecutionStop()


# 删除问题
def deleteQA(Q: str, group: Group) -> bool:
    if group.id in GroupQA:
        t_QA: dict = GroupQA[group.id]
        if Q in t_QA:
            t_QA.pop(Q)
            return True
    return False


# 搜寻问题并返回msg对象
def search(Q: str, group: Group) -> Msg:
    if group.id in GroupQA:
        t_QA: dict = GroupQA[group.id]
        if Q in t_QA:
            return t_QA[Q]
    return None


# 对问题的回答进行修改
def get_change(Q: str, group: GroupQA, GM: GroupMessage) -> bool:
    if group.id in GroupQA:
        t_QA: dict = GroupQA[group.id]
        if Q in t_QA:
            t_QA[Q] = Msg(GM)
            return True
    return False


# 修改问题
async def change(group: GroupQA, GM: GroupMessage):
    isFirstRun = temp_talk[GM.sender.id]['isFirstRun']
    Question = temp_talk[GM.sender.id]['Q']
    # 在会话管理查询该会话是否正在进行
    if isFirstRun:  # 如果还没有进行
        if search(Question, group) is not None:
            reply = f"问题{Question}已找到，请问如何回答？"
        else:
            reply = f"问题{Question}不存在!"
            temp_talk.pop(GM.sender.id)
    else:  # 如果已经进行
        if get_change(Question, group, GM):
            reply="修改回答成功！"
            await saveQA()
        else:reply=None
    if reply is not None:
        already = asSendable_creat(list=[
            Plain(reply)
        ], MC=GM.messageChain)
        await app.sendGroupMessage(group, already)


async def AddQA(groupMsg: GroupMessage, group: Group):
    isFirstRun = temp_talk[groupMsg.sender.id]['isFirstRun']
    Question = temp_talk[groupMsg.sender.id]['Q']
    sendMsg=None
    if isFirstRun:
        session = Msg(groupMsg)
        if session.user_id in BlackUser:
            sendMsg = asSendable_creat(list=[
                At(session.user_id),
                Plain("你已经被拉入小黑屋")
            ], MC=session.msgChain)
            await app.sendGroupMessage(group, sendMsg)
            return
        if  not GroupQA.get(group.id):
            GroupQA[group.id] = dict()
        t_QA: dict = GroupQA[group.id]
        if Question is not None:
            if Question in t_QA.keys():
                reply="问题已存在,当前回答为:"
                sendMsg = t_QA[Question].get_msg_graia(session.msgChain).plusWith([
                    Plain(reply)
                ])
                temp_talk.pop(groupMsg.sender.id)
            else:
                sendMsg = asSendable_creat(list=[
                    Plain("问题已被录入，请问如何回答？")
                ], MC=session.msgChain)
    else:
        t_QA = GroupQA[group.id]
        answer = Msg(groupMsg)
        t_QA[Question] = answer
        sendMsg = asSendable_creat(list=[
            Plain("录入成功")
        ], MC=answer.msgChain)
        await saveQA()
    if sendMsg is not None: await app.sendGroupMessage(group, sendMsg)


async def saveQA():  # 对已有问答数据进行保存
    AllData = dict()
    with open('QAindex.json', 'w+') as f:
        for key in GroupQA:
            t_dict = GroupQA[key]
            indexDict = dict()
            for i in t_dict:
                data = json.dumps(t_dict[i].getMsgDict())
                indexDict[i] = data
            AllData[key] = indexDict.copy()
            indexDict.clear()
        f.write(json.dumps(AllData))
        f.close()
    print("已保存")


async def ReadQA():
    try:
        with open('QAindex.json', 'r') as f:
            tempDict = json.loads(f.read())
            for i in tempDict.keys():
                GroupQA[int(i)] = tempDict[i]
                for key in GroupQA[int(i)].keys():
                    t = tempDict[i][key]
                    GroupQA[int(i)][key] = Msg()
                    GroupQA[int(i)][key].set_dict_from_json(t)
            f.close()
            print("读取结束")
    except:
        with open('QAIndex.json', 'w+') as f:
            f.close()


async def Compatible_old_index():  # 对旧有数据的转化
    with open('QAindex.json', 'r') as f:
        tempDick = json.loads(f.read())
        for i in tempDick.keys():
            tempDick[i] = json.loads(tempDick[i])
            GroupQA[int(i)] = tempDick[i].copy()
            for key in tempDick[i]:
                txt = tempDick[i][key]
                GroupQA[int(i)][key] = Msg()
                TransformDict = {
                    'user_id': None,
                    'at': None,
                    'msg_txt': txt,
                    'img_url': None
                }
                GroupQA[int(i)][key].set_dict(TransformDict)
        f.close()
        await  saveQA()
