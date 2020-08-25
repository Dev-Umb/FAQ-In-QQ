import json
import random
import re
import graia
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
from graia.broadcast import ExecutionStop
from graia.application import GroupMessage
from graia.application.message.elements.internal import *
from graia.application.group import Group
from MsgObj import Msg
from init_bot import *
import nest_asyncio

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36 Edg/81.0.416.77'
}  # 请求header
BaiDuWiKi = 'https://baike.baidu.com/item/'


def get_love() -> str:
    return LoveTalkList[random.randint(0, len(LoveTalkList) - 1)]


async def read_love():
    try:
        f = open('love.txt', 'r')
        a = f.readline()
        while a:
            if not a in LoveTalkList:
                LoveTalkList.append(a)
            a = f.readline()
    except:
        pass
        # f = open('love.txt', 'w+')
        # f.close()


def getACGKnowledge(txt: str) -> str:
    Entry = txt
    txt = quote(txt)
    moeGirlWiki = f'https://zh.moegirl.org.cn/{txt}'
    data = requests.get(moeGirlWiki, headers=headers).text
    content = BeautifulSoup(data, 'html.parser')
    [s.extract() for s in content('script')]
    [s.extract() for s in content('style')]
    try:
        try:
            datas = content.find_all(class_='mw-parser-output')[1]
        except:
            datas = content.find_all(class_='mw-parser-output')[0]
        try:
            bs = re.sub('\n+', '\n', datas.text)
            bs = re.sub(' +', ' ', bs)
            bs = ''.join([s for s in bs.splitlines(True) if s.strip()])
            bs = bs. \
                replace("萌娘百科欢迎您参与完善本条目☆欢迎有兴趣编辑讨论的朋友加入萌百Bilibili UP主专题编辑团队：338917445 欢迎正在阅读这个条目的您协助.", '') \
                .replace("编辑前请阅读Wiki入门或条目编辑规范，并查找相关资料。萌娘百科祝您在本站度过愉快的时光。", '')
            try:
                firstIntroduce: str = re.findall(f'{Entry}([\s\S]*?)目录', bs)[0]
            except:
                firstIntroduce = ''
            if len(firstIntroduce) < 200:
                introduce = datas.find_all(class_='toclevel-1 tocsection-1')[0].find_all(class_='toctext')[0].get_text()
                end = datas.find_all(class_='toclevel-1 tocsection-2')[0].find_all(class_='toctext')[0].text
                firstIntroduce += re.findall(f"{introduce}([\s\S]*?){end}", bs)[1]
            return firstIntroduce + moeGirlWiki
        except:
            return datas.find_all('p')[0].get_text() + '\n' + moeGirlWiki
    except:
        return "很抱歉没有找到相关信息或找到多个词条" + '\n' + moeGirlWiki


def getBaiduKnowledge(text: str) -> str:
    txt = quote(text)
    url = BaiDuWiKi + txt
    try:
        data = requests.get(url, headers=headers).text
        bs = BeautifulSoup(data, 'html.parser').find_all(class_='para')[0].get_text() + url
        return bs
    except:
        return "很抱歉没有找到相关结果"


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


def list_refresh(group_id: int):
    quick_find_question_list[group_id] = sorted(GroupQA[group_id].keys(), key=lambda i: len(i), reverse=False)


'''获取问题列表'''


def FQA_list(message: GroupMessage, group: Group):
    if not message.messageChain.get(At)[0].target == BOTQQ: return
    AllQuestionStr = ''
    if group.id in GroupQA and len(GroupQA[group.id].keys()) >= 1:
        keyList = quick_find_question_list[group.id] if group.id in quick_find_question_list else ['']
        num = 0
        for i in keyList:
            AllQuestionStr += f"#{num}.{i}\n"
            num += 1
        AllQuestionStr+="使用快速索引：#+问题序号"
        send_txt = AllQuestionStr
    else:
        send_txt = "本群暂时没有问题哦"
    send_msg = message.messageChain.create(
        [Plain(send_txt)]
    )
    print(send_txt)
    loop.run_until_complete(app.sendGroupMessage(group, send_msg))


'''
判断消息链是否合法
命令解析器
（目前有bug）
并不能很好地实现目的，因此在调用该解析器的函数中额外增加了判断语句
'''


def parser(message: GroupMessage, txt: str) -> bool:
    if message.messageChain.asDisplay().startswith(txt):
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
            reply = "修改回答成功！"
            await saveQA()
        else:
            reply = None
    if reply is not None:
        already = GM.messageChain.create([
            Plain(reply)
        ])
        await app.sendGroupMessage(group, already)


async def AddQA(groupMsg: GroupMessage, group: Group):
    global app
    isFirstRun = temp_talk[groupMsg.sender.id]['isFirstRun']
    Question = temp_talk[groupMsg.sender.id]['Q']
    sendMsg = None
    session = Msg(groupMsg)
    if isFirstRun:
        if session.user_id in BlackUser:
            sendMsg = session.msgChain.create([
                At(session.user_id),
                Plain("你已经被拉入小黑屋")
            ])
            await app.sendGroupMessage(group, sendMsg)
            return
        if not GroupQA.get(group.id):
            GroupQA[group.id] = dict()
        t_QA: dict = GroupQA[group.id]
        if Question is not None:
            if Question in t_QA.keys():
                reply = "问题已存在,当前回答为:"
                sendMsg = groupMsg.messageChain.create([
                    Plain(reply)
                ]).plusWith(t_QA[Question].get_msg_list())
                temp_talk.pop(groupMsg.sender.id)
            else:
                sendMsg = session.msgChain.create([
                    Plain("问题已被录入，请问如何回答？")
                ])
    else:
        t_QA = GroupQA[group.id]
        answer = Msg(groupMsg)
        t_QA[Question] = answer
        temp_talk.pop(groupMsg.sender.id)
        sendMsg = session.msgChain.create([
            Plain("录入成功")
        ])
        list_refresh(group.id)
        await saveQA()
    del session
    if sendMsg is not None: await app.sendGroupMessage(group, sendMsg)
