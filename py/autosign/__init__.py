import asyncio
import json
import os
from pathlib import Path
from datetime import datetime

from genshinhelper import Honkai3rd
from genshinhelper.exceptions import GenshinHelperException
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ..modules.database import DB
from ..modules.mytyping import config, result
from core import Handler, Request, Response


def autosign(hk3: Honkai3rd, qid: str):
    sign_data = load_data()
    today = datetime.today().day
    try:
        result_list = hk3.sign()
    except Exception as e:
        sign_data.update({qid: {"date": today, "status": False, "result": None}})
        return f"{e}\n自动签到失败."
    ret_list = f"〓米游社崩坏3签到〓\n####{datetime.date(datetime.today())}####\n"
    for n, res in enumerate(result_list):
        res = result(**res)
        ret = f"🎉No.{n + 1}\n{res.region_name}-{res.nickname}\n今日奖励:{res.reward_name}*{res.reward_cnt}\n本月累签:{res.total_sign_day}天\n签到结果:"
        if res.status == "OK":
            ret += f"OK✨"
        else:
            ret += f"舰长,你今天已经签到过了哦👻"
        ret += "\n###############\n"
        ret_list += ret
    sign_data.update({qid: {"date": today, "status": True, "result": ret_list}})
    save_data(sign_data)
    return ret_list.strip()


SIGN_PATH = Path(os.path.dirname(os.path.abspath(__file__))) / "sign_on.json"


def load_data():
    if not os.path.exists(SIGN_PATH):
        with open(SIGN_PATH, "w", encoding="utf8") as f:
            json.dump({}, f)
            return {}
    with open(SIGN_PATH, "r", encoding="utf8") as f:
        data: dict = json.load(f)
        return data


def save_data(data):
    with open(SIGN_PATH, "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def check_cookie(qid: str):
    db = DB("uid.sqlite", tablename="qid_uid")
    cookie = db.get_cookie(qid)
    if not cookie:
        return f"自动签到需要绑定cookie,发送'bhf?'查看如何绑定."
    hk3 = Honkai3rd(cookie=cookie)
    try:
        role_info = hk3.roles_info
    except GenshinHelperException as e:
        return f"{e}\ncookie不可用,请重新绑定."
    if not role_info:
        return f"未找到崩坏3角色信息,请确认cookie对应账号是否已绑定崩坏3角色."
    return hk3


@Handler.FrameToFrame
async def switch_autosign(request: Request):
    """自动签到开关"""
    qid = request.event.sender.qq
    cmd = request.message
    sign_data = load_data()
    if cmd in ["off", "关闭"]:
        if qid not in sign_data:
            return
        sign_data.pop(qid)
        save_data(sign_data)
        return Response(message="已关闭", messageDict={"at": qid})

    hk3 = check_cookie(qid)
    if isinstance(hk3, str):
        return Response(message=hk3, messageDict={"at": qid})

    result = autosign(hk3, qid)

    return Response(message=result, messageDict={"at": qid})


async def schedule_sign():
    today = datetime.today().day
    sign_data = load_data()
    cnt = 0
    sum = len(sign_data)
    for qid in sign_data:
        await asyncio.sleep(5)
        if sign_data[qid].get("date") != today or not sign_data[qid].get("status"):
            hk3 = check_cookie(qid)
            if isinstance(hk3, Honkai3rd):
                hk3 = autosign(hk3, qid)
                cnt += 1
    return cnt, sum


@Handler.FrameToStream
async def reload_sign(request: Request):
    yield Response(message="开始手动全部签到")
    cnt, total = await schedule_sign()
    yield Response(message=f"重执行完成，状态刷新{cnt}条，共{total}条")


scheduler = AsyncIOScheduler()


@scheduler.scheduled_job('cron', day_of_week='*', hour=1, minute='00', second='00')
async def task():
    print(await schedule_sign())


scheduler.start()
