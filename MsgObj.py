import json
from graia.application import  GroupMessage
from graia.application.message.elements.internal import *


'''封装好的message对象'''


class Msg():
    def __init__(self, *msg: GroupMessage):
        if len(msg) <= 0:
            self.msgChain =\
                self.msgChain=\
                self.user_id =\
                self.img_url = \
                self.at =\
                self.txt =\
                self.sendChain= None
        else:
            msg = msg[0]
            self.msgChain = msg.messageChain
            self.user_id = msg.sender.id
            self.img_url = self.msgChain.get(Image) if self.msgChain.has(Image) else None
            # 提取img对象中的url组成list
            if self.img_url is not None:
                self.img_url = [urls.url for urls in self.img_url]
            self.at = self.msgChain.get(At) if self.msgChain.has(At) else None
            # 提取At对象中的用户ID，组成list
            if self.at is not None:
                self.at = [ats.target for ats in self.at]
            self.txt = ''
            Plains = self.msgChain.get(Plain)
            if self.msgChain.has(Plain):
                for i in Plains:
                    self.txt += i.text
            else:
                self.txt = None
            self.init_msg_chain()

    def init_msg_chain(self):
        self.msg_list = list()
        if self.img_url is not None:
            [self.msg_list.append(Image.fromNetworkAddress(i)) for i in self.img_url]
        if self.at is not None:
            [self.msg_list.append(At(i)) for i in self.at]
        if self.txt is not None: self.msg_list.append(Plain(self.txt))
        if self.msgChain is not None:self.sendChain=self.msgChain.create(self.msg_list)

    def getMsgDict(self) -> dict:  # 获取msg的dict对象
        self.msg_dict = {
            'user_id': self.user_id,
            'img_url': self.img_url,
            'at': self.at,
            'msg_txt': self.txt
        }
        return self.msg_dict

    def get_json(self) -> str:  # 返回该消息对象的json字符串，用于保存数据
        return json.dumps(self.getMsgDict())

    def set_dict_from_json(self, jsons: str):  # 根据json字符串初始化对象
        self.set_dict(json.loads(jsons))

    def set_dict(self, set_dict: dict):  # 传入dict来初始化对象
        self.msg_dict = set_dict
        self.user_id = self.msg_dict['user_id'] if 'user_id' in self.msg_dict.keys() else None
        self.at = self.msg_dict['at'] if 'at' in self.msg_dict.keys() else None
        self.txt = self.msg_dict['msg_txt'] if 'msg_txt' in self.msg_dict.keys() else None
        self.img_url = self.msg_dict['img_url'] if 'img_url' in self.msg_dict.keys() else None
        self.init_msg_chain()

    def get_msg_list(self):
        return self.msg_list

    def get_msg_graia(self, MC: MessageChain) -> MessageChain:  # 获取该消息的消息链（懒加载）
        if self.sendChain is None:
            self.sendChain=MC.create(self.msg_list)
        return self.sendChain
