from graia.application import Group, GroupMessage
from init_bot import *


def is_manager(message: GroupMessage) -> bool:
    test = message.sender.permission
    if message.sender.permission.value == "ADMINISTRATOR" or message.sender.permission.value == "OWNER" or message.sender.id in Manager:
        return True
    return False


def only_group_in_list(group: Group, start_group: list) -> bool:
    if group.id in start_group:
        return True
    return False


def group_is_in_list(message: GroupMessage, group: Group, start_group: list) -> bool:
    if is_manager(message) and group.id in start_group:
        return True
    return False


def shutdown_Baidu(message: GroupMessage, group: Group) -> bool:
    if group_is_in_list(message, group, start_baiDu_group):
        start_baiDu_group.remove(group.id)
        return True
    return False


def open_manager(message: GroupMessage, group: Group) -> bool:
    if not group_is_in_list(message, group, mast_manager_group):
        mast_manager_group.append(group.id)
        return True
    return False


def close_manager(message: GroupMessage, group: Group) -> bool:
    if group_is_in_list(message, group, mast_manager_group):
        mast_manager_group.remove(group.id)
        return True
    return False


def shutdown_all(message: GroupMessage, group: Group) -> bool:
    if not group_is_in_list(message, group, shutdown_all_group):
        shutdown_all_group.append(group.id)
        return True
    return False


def start_Baidu(message: GroupMessage, group: Group) -> bool:
    if not group_is_in_list(message, group, start_baiDu_group):
        start_baiDu_group.append(group.id)
        return True
    return False


def start_all(message: GroupMessage, group: Group) -> bool:
    if group_is_in_list(message, group, shutdown_all_group):
        shutdown_all_group.remove(group.id)
        return True
    return False
