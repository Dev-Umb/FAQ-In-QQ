from graia.application.event.mirai import *
from graia.broadcast.builtin.decoraters import Depend
from pulgin import *
from MsgObj import Msg
from init_bot import *

'''
各文件说明：
    init_bot.py 初始化bot对象和一些需要用到的list或者dict
    bot.py 运行的main文件，包括消息指令入口
    MsgObj.py 独立封装的message消息类，便于对消息数据进行保存和调用
    pulgin.py bot所需要到的一些函数的封装
    config.py bot运行所需要的配置，端口号，bot的QQ号等，配置参见Graia文档
    
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
    if not parser(message, "修改迎新词 "): return
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
async def close_in_group(message: GroupMessage, group: Group):
    if parser(message=message, txt="\shutdown") \
            and message.sender.id in Manager \
            and group.id in BlackGroup:
        BlackGroup.remove(group.id)
        await app.sendGroupMessage(group, message.messageChain.create(
            [Plain("已关闭百度与骚话功能")]
        ))
    elif parser(message, "\start") \
            and message.sender.id in Manager \
            and group.id not in BlackGroup:
        BlackGroup.append(group.id)
        await app.sendGroupMessage(group, message.messageChain.create(
            [Plain("已开启百度与骚话功能")]
        ))


async def indexes(message: GroupMessage, group: Group):
    id: str = message.messageChain.get(Plain)[0].text.strip().replace('#', '')
    if id.isdigit():
        temp_list: list = quick_find_question_list[group.id]
        Question: str = temp_list[int(id)]
        Answer = search(Question, group)
        send_msg = Answer.get_msg_graia(message.messageChain)
        await app.sendGroupMessage(group, send_msg)


async def FQA(app: GraiaMiraiApplication, message: GroupMessage, group: Group) -> bool:
    if not (message.messageChain.has(At) or message.messageChain.has(Plain)): return False
    msg = Msg(message)
    msgChain = message.messageChain
    # 首先对消息进行问答解析
    Question = msg.txt.strip()
    if Question == '列表' and message.messageChain.has(At):
        await app.sendGroupMessage(group, FQA_list(message, group))
        del msg
        return True
    at = msgChain.get(At)[0].target if msgChain.has(At) else 0
    tempQ = search(Question, group)
    if tempQ is not None:
        send_msg = tempQ.get_msg_graia(msgChain)
    else:
        if at == BOTQQ:
            send_msg = msgChain.create([
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
    if group.id not in BlackGroup: return
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
    elif parser(message, ".来点好听的"):
        if group.id not in BlackGroup: return
        await app.sendGroupMessage(group, message.messageChain.create([
            Plain(get_love()),
            At(message.sender.id)
        ]))


@bcc.receiver("GroupMessage")
async def group_message_handler(app: GraiaMiraiApplication, message: GroupMessage, group: Group):
    if parser(message, "百度 ") \
            or parser(message, "萌娘 "): return
    msg = Msg(message)
    Question = message.messageChain.get(Plain)[0].text if message.messageChain.has(Plain) else None
    hasSession = temp_talk.get(msg.user_id)
    if hasSession is not None:
        await session_manager(app, message, group)
        return

    if await FQA(app, message, group): return
    if parser(message, '#'):
        await indexes(message, group)
        return
    if parser(message, "添加问题 "):
        # 创建添加问题的新会话
        Question = Question.replace("添加问题 ", "").strip()
        if hasSession is None:
            add_temp_talk(msg.user_id, 'Add', True, Question)
            sendMsg = await AddQA(message, group)
            if sendMsg is not None: await app.sendGroupMessage(group, sendMsg)
        del msg
        return

    if parser(message, "修改问题 "):
        # 创建修改问题的新会话
        Question = Question.replace("修改问题", "").strip()
        if hasSession is None:
            add_temp_talk(msg.user_id, 'Change', True, Question)
            sendMsg = await change(group=group, GM=message)
            if sendMsg is not None: await app.sendGroupMessage(group, sendMsg)
        del msg
        return

    if parser(message, "删除问题 "):
        # 删除问题
        Question = Question.replace("删除问题", "").strip()
        isdeleteOK: str = "删除成功" if deleteQA(Question, group) else "不存在这个问题"
        await app.sendGroupMessage(group, message.messageChain.create([
            Plain(isdeleteOK)
        ]))
        await saveQA()
        del msg
        return


if __name__ == '__main__':
    # 初始化GroupQA
    # loop.run_until_complete(Compatible_old_index())
    nest_asyncio.apply()
    loop.run_until_complete(ReadQA())
    loop.run_until_complete(read_love())
    app.launch_blocking()
