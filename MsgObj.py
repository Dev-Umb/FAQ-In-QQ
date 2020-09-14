import json
from graia.application import GroupMessage
from graia.application.message.elements.internal import *

'''封装好的message对象'''


class Msg:
    __slots__ = ['msg_chain', 'user_id', 'at', 'txt', 'sendChain', 'img_url', 'msg_list']

    def __del__(self):
        del self

    def __init__(self, *msg: GroupMessage):
        self.msg_list = list()
        if len(msg) <= 0:
            self.msg_chain = \
                self.user_id = \
                self.img_url = \
                self.at = \
                self.txt = \
                self.sendChain = None
        else:
            msg = msg[0]
            self.msg_chain = msg.messageChain
            self.user_id = msg.sender.id
            self.img_url = self.msg_chain.get(Image) if self.msg_chain.has(Image) else None
            # 提取img对象中的url组成list
            if self.img_url is not None:
                self.img_url = [urls.url for urls in self.img_url]
            self.at = self.msg_chain.get(At) if self.msg_chain.has(At) else None
            # 提取At对象中的用户ID，组成list
            if self.at is not None:
                self.at = [ats.target for ats in self.at]
            self.txt = ''
            if self.msg_chain.has(Plain):
                self.txt = [i.text for i in self.msg_chain.get(Plain)]
                txt: str = ''
                for i in self.txt:
                    txt += i
                self.txt = txt
            else:
                self.txt = None
            self.init_msg_chain()

    def init_msg_chain(self):
        if self.img_url is not None:
            [self.msg_list.append(Image.fromNetworkAddress(i)) for i in self.img_url]
        if self.at is not None:
            [self.msg_list.append(At(i)) for i in self.at]
        if self.txt is not None:
            self.msg_list.append(Plain(self.txt))
        if self.msg_chain is not None:
            self.sendChain = self.msg_chain.create(self.msg_list)

    def getMsgDict(self) -> dict:  # 获取msg的dict对象
        return {
            'user_id': self.user_id,
            'img_url': self.img_url,
            'at': self.at,
            'msg_txt': self.txt
        }

    def set_dict_from_json(self, jsons: str):  # 根据json字符串初始化对象
        self.set_dict(json.loads(jsons))

    def set_dict(self, set_dict: dict):  # 传入dict来初始化对象
        self.user_id = set_dict['user_id'] if 'user_id' in set_dict.keys() else None
        self.at = set_dict['at'] if 'at' in set_dict.keys() else None
        self.txt = set_dict['msg_txt'] if 'msg_txt' in set_dict.keys() else None
        self.img_url = set_dict['img_url'] if 'img_url' in set_dict.keys() else None
        self.init_msg_chain()

    def get_msg_list(self):
        return self.msg_list

    def get_msg_graia(self, MC: MessageChain) -> MessageChain:  # 获取该消息的消息链（懒加载）
        if self.sendChain is None:
            self.sendChain = MC.create(self.msg_list)
        return self.sendChain
