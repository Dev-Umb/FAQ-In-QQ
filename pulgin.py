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
temp_talk = dict()#简易的会话管理器
WelcomeScence = {
    1147322663: '欢迎小可爱来到大数据学院迎新群',
    1129408240: '欢迎小可爱来到大数据学院迎新群',
    912306370: '欢迎来到中北最大的游戏养鸽场',
    820740615: '欢迎大佬来到中北大学AI+移动互联实验室'
}
'''判断消息链是否合法
（目前有bug）
并不能很好地实现目的，因此在调用该解析器的函数中额外增加了判断语句
'''
def judge(message: MessageChain) -> bool:
    if message.has(Plain):
        if message.asSendable().asDisplay().startswith("修改迎新词"):
            return True
    return False
def judge_depend_target(message: MessageChain):
    if not judge(message):
        raise ExecutionStop()

#删除问题
def deleteQA(Q: str, group: Group) -> bool:
    if group.id in GroupQA:
        t_QA: dict = GroupQA[group.id]
        if Q in t_QA:
            t_QA.pop(Q)
            return True
        return False

#搜寻问题并返回msg对象
def search(Q: str, group: Group) -> Msg:
    if group.id in GroupQA:
        t_QA: dict = GroupQA[group.id]
        if Q in t_QA:
            return t_QA[Q]
    return None

#对问题的回答进行修改
def get_change(Q: str, group: GroupQA, GM: GroupMessage) -> bool:
    if group.id in GroupQA:
        t_QA: dict = GroupQA[group.id]
        if Q in t_QA:
            t_QA[Q] = Msg(GM)
            return True
    return False

#修改问题的入口函数
async def change(group: GroupQA, GM: GroupMessage):
    global app
    isFirstRun = temp_talk[GM.sender.id]['isFirstRun']
    #在会话管理查询该会话是否正在进行
    Question = temp_talk[GM.sender.id]['Q']
    if isFirstRun:#如果还没有进行
        if search(Question, group) is not None:
            reply = f"问题{Question}已找到，请问如何回答？"
        else:
            reply = f"问题{Question}不存在!"
            temp_talk.pop(GM.sender.id)
        already = asSendable_creat(list=[
            Plain(reply)
        ], MC=GM.messageChain)
        await app.sendGroupMessage(group, already)
    else:#如果已经进行
        if get_change(Question, group, GM):
            already = asSendable_creat(list=[
                Plain("修改回答成功！")
            ], MC=GM.messageChain)
            await app.sendGroupMessage(group, already)
        await saveQA()


async def AddQA(groupMsg: GroupMessage, group: Group):
    global app
    #会话管理器，同上
    isFirstRun = temp_talk[groupMsg.sender.id]['isFirstRun']
    Question = temp_talk[groupMsg.sender.id]['Q']
    if isFirstRun:
        session = Msg(groupMsg)
        if session.user_id in BlackUser:
            msg = asSendable_creat(list=[
                At(session.user_id),
                Plain("你已经被拉入小黑屋")
            ], MC=session.msgChain)
            await  app.sendGroupMessage(group, msg)
            return
        if group.id in GroupQA:
            t_QA: dict = GroupQA[group.id]
        else:
            GroupQA[group.id] = dict()
            t_QA: dict = GroupQA[group.id]
        if Question is not None:
            if Question in t_QA.keys():
                await app.sendGroupMessage(group, asSendable_creat([
                    Plain("问题已存在,当前回答为:")
                ], session.msgChain))
                sendMsg = t_QA[Question].get_msg_graia(session.msgChain)
                await app.sendGroupMessage(group, sendMsg)
                temp_talk.pop(groupMsg.sender.id)
            else:
                already = asSendable_creat(list=[
                    Plain("问题已被录入，请问如何回答？")
                ], MC=session.msgChain)
                await app.sendGroupMessage(group, already)
    else:
        t_QA = GroupQA[group.id]
        answer = Msg(groupMsg)
        t_QA[Question] = answer
        temp = asSendable_creat(list=[
            Plain("录入成功")
        ], MC=answer.msgChain)
        await app.sendGroupMessage(group, temp)
        await saveQA()


async def saveQA():#对已有问答数据进行保存
    allData = dict()
    with open('QAindex.json', 'w+') as f:
        for key in GroupQA:
            t_dict = GroupQA[key]
            indexDict=dict()
            for i in t_dict:
                data = json.dumps(t_dict[i].getMsgDict())
                indexDict[i] = data
            allData[key] = indexDict.copy()
            indexDict.clear()
        f.write(json.dumps(allData))
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
            t=GroupQA
            f.close()
            print("读取结束")
    except:
         with open('QAIndex.json', 'w+') as f:
             f.close()


async def Compatible_old_index():#对旧有数据的转化
    with open('QAindex.json', 'r') as f:
        tempDick = json.loads(f.read())
        for i in tempDick.keys():
            tempDick[i]=json.loads(tempDick[i])
            GroupQA[int(i)] = tempDick[i].copy()
            for key in tempDick[i]:
                txt=tempDick[i][key]
                GroupQA[int(i)][key] = Msg()
                TransformDict = {
                    'user_id': None,
                    'at': None,
                    'msg_txt': txt,
                    'img_url': None
                }
                GroupQA[int(i)][key].set_dict(TransformDict)
        f.close()
        await saveQA()
