import json
import re

import nonebot
from nonebot import *

# 欢饮新成员
QA = dict()
Manager = [1149558764]


@on_notice('group_increase')
async def WelcomeNewMember(session: NoticeSession):
    await session.send('欢迎小可爱来到中北大学大数据学院迎新群，有想要了解的相关信息可以问我或者群内的学长学姐哦', at_sender=True)


def ReadQA():
    global QA
    try:
        with open('QAIndex.json', 'r') as f:
            QA = json.loads(f.read())
            t=QA
            f.close()
    except:
        with open('QAIndex.json', 'a') as f:
            f.close()


@on_startup(func=ReadQA)
@on_command('Question', aliases=('添加问题',), only_to_me=False)
async def setQA(session: CommandSession):
    global Question
    if session.is_first_run:
        Question = session.current_arg_text.strip().replace(' ','')
        if len(Question)<2:
            await session.send("不合法,请重新添加问题！")
            return
    try:
        a = QA[Question]
        await session.send('问题已存在，当前回答：\n' + a)
    except:
        answer = session.get('answer', prompt='问题已被纳入，请问如何回答？')
        QA[Question] = answer
        await session.send('录入成功')
    await saveQA()


async def saveQA():
    with open('QAIndex.json', 'w+') as f:
        data = json.dumps(QA)
        f.write(data)
        f.close()


@on_command('ChangeAnswer', aliases=('修改问题'), only_to_me=False)
async def ChangeQA(session: CommandSession):
    global QA
    global Q
    if session.is_first_run:
        Q = session.current_arg_text.strip()
    try:
        a = QA[Q]
    except:
        await session.send('不存在这个问题')
        return
    QA[Q] = session.get('ansewer', prompt='请问如何更改？')
    await session.send('修改成功')
    await saveQA()


@on_natural_language(only_to_me=True)
async def Reply_question(session: NLPSession):
    global QA
    text = session.msg_text.strip().replace(' ','')
    for key, values in QA.items():
        if text == key or re.search(key, text):
            await session.send(at_sender=True, message=QA[key])
            break
    else:
        await session.send(at_sender=True, message=('我还不会回答你说的这个问题呢，可以等待学姐学长来回答哦，被回答以后请不要吝啬感谢哦(●ˇ∀ˇ●)'))
