import threading
from graia.application.event.mirai import *
from graia.broadcast import Broadcast, BaseEvent, ExecutionStop
from graia.application import GraiaMiraiApplication, Session, GroupMessage
from graia.application.message.chain import MessageChain
import asyncio
from graia.application.message.elements.internal import *
from graia.application.friend import *
from graia.application.group import Group
from graia.broadcast.builtin.decoraters import Depend
from graia.broadcast.entities.event import EventMeta
from config import *
from pulgin import *
from MsgObj import Msg, asSendable_creat

'''
各文件说明：
    bot.py 运行的main文件，包括消息指令入口
    config.py bot运行所需要的配置，端口号，QQ号，黑名单，白名单，超级管理员账号等，配置参见Graia文档
    MsgObj.py 独立封装的message消息类，便于对消息数据进行保存和调用
    pulgin.py bot所需要到的一些函数的封装
'''

'''
监听新人入群并欢迎
'''
@bcc.receiver("MemberJoinEvent")
async def MemberJoin(event: MemberJoinEvent):
    group = event.member.group
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
    if not message.messageChain.asSendable().asDisplay().startswith("修改迎新词"): return
    if not message.messageChain.has(Plain): return
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
async def group_message_handler(app: GraiaMiraiApplication, message: GroupMessage, group: Group):
    msg = Msg(message)
    msgChain = message.messageChain
    if msgChain.has(At) or msgChain.has(Plain):
        #首先对消息进行问答解析
        Question = msg.txt.strip()
        at = msgChain.get(At)[0].target if msgChain.has(At) else 0
        if at == BOTQQ:
            if Question == '列表':
                #获取本群问答列表
                QuestionList = ''
                if group.id in GroupQA and len(GroupQA[group.id].keys()) >= 1:
                    for i in GroupQA[group.id].keys():
                        QuestionList += f"*{i}\n"
                    await app.sendGroupMessage(group, asSendable_creat(
                        list=[Plain(QuestionList)],
                        MC=msgChain
                    ))
                else:
                    await app.sendGroupMessage(group, asSendable_creat(
                        list=[Plain("本群暂时没有问题哦")],
                        MC=msgChain
                    ))
                return
        tempQ = search(Question, group)
        if tempQ is not None:
            send_msg = tempQ.get_msg_graia(msgChain)
        else:
            if at == BOTQQ:
                send_msg=asSendable_creat(list=[
                    Plain("没有找到这个问题，请等待学长学姐来回答或回复“列表”查看已有问题")
                ],MC=msgChain)
            else:send_msg=None
        if send_msg is not None:
            await app.sendGroupMessage(group, send_msg)
            return
    if temp_talk.get(msg.user_id):
        #查看发起会话的用户是否有未结束的会话
        if temp_talk[msg.user_id]['isFirstRun']:
            temp_talk[msg.user_id]['isFirstRun'] = False
            type = temp_talk[msg.user_id]['type']
            if type == 'Add':
                await AddQA(message, group)
            elif type == 'Change':
                await change(group, message)
            temp_talk.pop(msg.user_id)
            #会话结束，将会话释放掉
            return
    if msgChain.asDisplay().startswith("添加问题 "):
        #创建添加问题的新会话
        txt = message.messageChain.get(Plain)[0].text.replace("添加问题", "").strip()
        msg.txt.replace("添加问题", "").strip()
        if not temp_talk.get(msg.user_id):
            temp_talk[msg.user_id] = {
                'type': 'Add',
                'isFirstRun': True,
                'Q': txt
            }
            await AddQA(message, group)
        return
    if msgChain.asDisplay().startswith("修改问题 "):
        #创建修改问题的新会话
        txt = message.messageChain.get(Plain)[0].text.replace("修改问题", "").strip()
        msg.txt.replace("修改问题", "").strip()
        if not temp_talk.get(msg.user_id):
            temp_talk[msg.user_id] = {
                'type': 'Change',
                'isFirstRun': True,
                'Q': txt
            }
            await change(group, message)
        return
    if msgChain.asDisplay().startswith("删除问题 "):
        #删除问题
        txt = msg.txt.replace("删除问题", "").strip()
        isdeleteOK = "删除成功" if deleteQA(txt, group) else "不存在这个问题"
        await app.sendGroupMessage(group, asSendable_creat(list=[
            Plain(isdeleteOK)
        ], MC=msgChain))
        await saveQA()
        return


if __name__ == '__main__':
    #初始化GroupQA
    # loop.run_until_complete(Compatible_old_index())
    loop.run_until_complete(ReadQA())

    app.launch_blocking()
