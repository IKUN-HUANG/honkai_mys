import re
from .modules.database import DB
from .modules.image_handle import (DrawCharacter, DrawFinance, DrawIndex,
                                   ItemTrans)
from .modules.mytyping import Index
from .modules.query import Finance, GetInfo, InfoError
from .modules.util import NotBindError
from core import Handler, Request, Response

from .autosign import switch_autosign, reload_sign
from .config import CONFIG

is_cookie = not CONFIG["cookies"][0].startswith("这里")

package = "bh3"


def handle_id(request: Request):
    msg = request.message

    if atList := request.event.atList:
        qid = atList[0].qq
    else:
        qid = request.event.sender.qq

    role_id = re.search(r"\d+", msg)
    region_name = re.search(r"\D+\d?", msg)

    region_db = DB("uid.sqlite", tablename="uid_region")
    qid_db = DB("uid.sqlite", tablename="qid_uid")

    if re.search(r"[mM][yY][sS]|米游社", msg):
        spider = GetInfo(mysid=role_id.group())
        region_id, role_id = spider.mys2role(spider.getrole)

    elif role_id is None:
        try:
            role_id = qid_db.get_uid_by_qid(qid)
            region_id = region_db.get_region(role_id)
        except KeyError:
            raise InfoError(
                "请在原有指令后面输入游戏uid及服务器,只需要输入一次就会记住下次直接使用bh#获取就好\n例如:bh#100074751官服"
            )

    elif role_id is not None and region_name is None:
        region_id = region_db.get_region(role_id.group())

        if not region_id:
            raise InfoError(
                f"{role_id.group()}为首次查询,请输入服务器名称.如:bh#100074751官服")

    else:
        try:
            region_id = ItemTrans.server2id(region_name.group())
        except InfoError as e:
            raise InfoError(str(e))

        now_region_id = region_db.get_region(role_id.group())

        if now_region_id is not None and now_region_id != region_id:
            raise InfoError(
                f"服务器信息与uid不匹配,可联系管理员修改."
            )  # 输入的服务器与数据库中保存的不一致，可手动delete该条数据

    role_id = role_id if isinstance(role_id, str) else role_id.group()
    return role_id, region_id, qid


@Handler.FrameToStream
async def bh3_player_card(request: Request):
    if not is_cookie:
        yield Response(message="需要机器人主人再config.py添加cookie才能使用该功能")
        return

    region_db = DB("uid.sqlite", tablename="uid_region")
    qid_db = DB("uid.sqlite", tablename="qid_uid")
    try:
        role_id, region_id, qid = handle_id(request)
    except InfoError as e:
        yield Response(message=f"出错了：{str(e)}", messageDict={"at": request.event.sender.qq})
        return

    spider = GetInfo(server_id=region_id, role_id=role_id)

    try:
        ind = await spider.part()
    except InfoError as e:
        yield Response(message=f"出错了：{str(e)}", messageDict={"at": request.event.sender.qq})
        return

    yield Response(message="制图中，请稍后", messageDict={"at": request.event.sender.qq})

    region_db.set_region(role_id, region_id)
    qid_db.set_uid_by_qid(qid, role_id)
    ind = DrawIndex(**ind)
    im = await ind.draw_card(qid)
    yield Response(image=im, messageDict={"at": request.event.sender.qq})


@Handler.FrameToStream
async def bh3_chara_card(request: Request):
    if not is_cookie:
        yield Response(message="需要机器人主人再config.py添加cookie才能使用该功能")
        return

    region_db = DB("uid.sqlite", tablename="uid_region")
    qid_db = DB("uid.sqlite", tablename="qid_uid")

    try:
        role_id, region_id, qid = handle_id(request)
    except InfoError as e:
        yield Response(message=f"出错了：{str(e)}", messageDict={"at": request.event.sender.qq})
        return

    spider = GetInfo(role_id=role_id, server_id=region_id)

    try:
        _, data = await spider.fetch(spider.valkyrie)
        _, index_data = await spider.fetch(spider.index)
    except InfoError as e:
        yield Response(message=f"出错了：{str(e)}", messageDict={"at": request.event.sender.qq})
        return

    yield Response(message="制图中，请稍后", messageDict={"at": request.event.sender.qq})

    region_db.set_region(role_id, region_id)
    qid_db.set_uid_by_qid(qid, role_id)
    index = Index(**index_data["data"])
    dr = DrawCharacter(**data["data"])
    im = await dr.draw_chara(index, qid)
    yield Response(image=im, messageDict={"at": request.event.sender.qq})


@Handler.FrameToFrame
async def show_finance(request: Request):
    qid = request.event.sender.qq
    try:
        spider = Finance(str(qid))
    except InfoError as e:
        return Response(message=f"出错了：{str(e)}")

    fi = await spider.get_finance()
    fid = DrawFinance(**fi)
    im = fid.draw()
    return Response(image=im)


@Handler.FrameToFrame
async def bind(request: Request):
    qid = request.event.sender.qq
    msg = request.message
    role_id = re.search(r"\d+", msg)
    region_name = re.search(r"\D+\d?", msg)

    if not role_id or not region_name:
        return Response(message="请按以下格式绑定：#崩坏三绑定114514官服")
    try:
        region_id = ItemTrans.server2id(region_name.group())
    except InfoError as e:
        return Response(message=str(e))

    region_db = DB("uid.sqlite", tablename="uid_region")
    qid_db = DB("uid.sqlite", tablename="qid_uid")

    region_db.set_region(role_id.group(), region_id)
    qid_db.set_uid_by_qid(qid, role_id.group())

    return Response(message="已绑定")


@Handler.FrameToFrame
async def cookie(request: Request):
    qid_db = DB("uid.sqlite", tablename="qid_uid")
    qid = request.event.sender.qq

    try:
        qid_db.get_uid_by_qid(qid)
    except:
        return Response(message="请先绑定uid，如#崩坏三绑定114514官服")

    try:
        cookieraw = request.messageDict
        spider = Finance(qid=qid, cookieraw=cookieraw["account_id"] + "," + cookieraw["cookie_token"])
    except InfoError as e:
        return Response(message=str(e))
    try:
        fi = await spider.get_finance()
    except InfoError as e:
        return Response(message=str(e))

    fid = DrawFinance(**fi)
    im = fid.draw()

    return Response(message="已绑定", image=im)
