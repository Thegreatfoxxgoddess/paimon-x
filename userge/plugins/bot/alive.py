"""Fun plugin"""

import asyncio
from datetime import datetime
from re import compile as comp_regex

from pyrogram import filters
from pyrogram.errors import BadRequest, FloodWait, Forbidden, MediaEmpty
from pyrogram.file_id import PHOTO_TYPES, FileId
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from userge import Config, Message, userge, versions
from userge.core.ext import RawClient
from userge.utils import get_file_id, rand_array

_ALIVE_REGEX = comp_regex(
    r"http[s]?://(i\.imgur\.com|telegra\.ph/file|t\.me)/(\w+)(?:\.|/)(gif|jpg|MP4|png|jpeg|[0-9]+)(?:/([0-9]+))?"
)
_USER_CACHED_MEDIA, _BOT_CACHED_MEDIA = None, None

LOGGER = userge.getLogger(__name__)


async def _init() -> None:
    global _USER_CACHED_MEDIA, _BOT_CACHED_MEDIA
    if Config.ALIVE_MEDIA and Config.ALIVE_MEDIA.lower() != "false":
        am_type, am_link = await Bot_Alive.check_media_link(Config.ALIVE_MEDIA.strip())
        if am_type and am_type == "tg_media":
            try:
                if Config.HU_STRING_SESSION:
                    _USER_CACHED_MEDIA = get_file_id(
                        await userge.get_messages(am_link[0], am_link[1])
                    )
            except Exception as u_rr:
                LOGGER.debug(u_rr)
            try:
                if userge.has_bot:
                    _BOT_CACHED_MEDIA = get_file_id(
                        await userge.bot.get_messages(am_link[0], am_link[1])
                    )
            except Exception as b_rr:
                LOGGER.debug(b_rr)


@userge.on_cmd("alive", about={"header": "Just For Fun"}, allow_channels=False)
async def alive_inline(message: Message):
    try:
        if message.client.is_bot:
            await send_alive_message(message)
        elif userge.has_bot:
            try:
                await send_inline_alive(message)
            except BadRequest:
                await send_alive_message(message)
        else:
            await send_alive_message(message)
    except Exception as e_all:
        await message.err(str(e_all), del_in=10, log=__name__)


async def send_inline_alive(message: Message) -> None:
    _bot = await userge.bot.get_me()
    try:
        i_res = await userge.get_inline_bot_results(_bot.username, "alive")
        i_res_id = (
            (
                await userge.send_inline_bot_result(
                    chat_id=message.chat.id,
                    query_id=i_res.query_id,
                    result_id=i_res.results[0].id,
                )
            )
            .updates[0]
            .id
        )
    except (Forbidden, BadRequest) as ex:
        await message.err(str(ex), del_in=5)
        return
    await message.delete()
    await asyncio.sleep(200)
    await userge.delete_messages(message.chat.id, i_res_id)


async def send_alive_message(message: Message) -> None:
    global _USER_CACHED_MEDIA, _BOT_CACHED_MEDIA
    chat_id = message.chat.id
    me = await userge.get_me()
    client = message.client
    caption = Bot_Alive.alive_info(me)
    if client.is_bot:
        reply_markup = Bot_Alive.alive_buttons()
        file_id = _BOT_CACHED_MEDIA
    else:
        reply_markup = None
        file_id = _USER_CACHED_MEDIA
        caption += (
            f"\n⚡️  <a href={Config.UPSTREAM_REPO}><b>REPO</b></a>"
            "    <code>|</code>    "
            " 🌿 <a href='https://t.me/my_thingsuwu'><b>SUPPORT</b></a>"
        )
    if not Config.ALIVE_MEDIA:
        await client.send_photo(
            chat_id,
            photo=Bot_Alive.alive_default_imgs(),
            caption=caption,
            reply_markup=reply_markup,
        )
        return
    url_ = Config.ALIVE_MEDIA.strip()
    if url_.lower() == "false":
        await client.send_message(
            chat_id,
            caption=caption,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
        )
    else:
        type_, media_ = await Bot_Alive.check_media_link(Config.ALIVE_MEDIA)
        if type_ == "url_gif":
            await client.send_animation(
                chat_id,
                animation=url_,
                caption=caption,
                reply_markup=reply_markup,
            )
        elif type_ == "url_image":
            await client.send_photo(
                chat_id,
                photo=url_,
                caption=caption,
                reply_markup=reply_markup,
            )
        elif type_ == "tg_media":
            try:
                await client.send_cached_media(
                    chat_id,
                    file_id=file_id,
                    caption=caption,
                    reply_markup=reply_markup,
                )
            except MediaEmpty:
                if not message.client.is_bot:
                    try:
                        refeshed_f_id = get_file_id(
                            await userge.get_messages(media_[0], media_[1])
                        )
                        await userge.send_cached_media(
                            chat_id,
                            file_id=refeshed_f_id,
                            caption=caption,
                        )
                    except Exception as u_err:
                        LOGGER.error(u_err)
                    else:
                        _USER_CACHED_MEDIA = refeshed_f_id


if userge.has_bot:

    @userge.bot.on_callback_query(filters.regex(pattern=r"^settings_btn$"))
    async def alive_cb(_, c_q: CallbackQuery):
        me = await userge.get_me()
        allow = bool(
            c_q.from_user
            and (
                c_q.from_user.id in Config.OWNER_ID
                or c_q.from_user.id in Config.SUDO_USERS
            )
        )
        if allow:
            start = datetime.now()
            try:
                await c_q.edit_message_text(
                    Bot_Alive.alive_info(me),
                    reply_markup=Bot_Alive.alive_buttons(),
                    disable_web_page_preview=True,
                )
            except FloodWait as e:
                await asyncio.sleep(e.x)
            except BadRequest:
                pass
            ping = "𝗣𝗶𝗻𝗴:  {} sec\n"
        alive_s = "𝗘𝘅𝘁𝗿𝗮 𝗣𝗹𝘂𝗴𝗶𝗻𝘀 : {}\n".format(
            _parse_arg(Config.LOAD_UNOFFICIAL_PLUGINS)
        )
        alive_s += f"𝗦𝘂𝗱𝗼 : {_parse_arg(Config.SUDO_ENABLED)}\n"
        alive_s += f"𝗔𝗻𝘁𝗶𝘀𝗽𝗮𝗺 : {_parse_arg(Config.ANTISPAM_SENTRY)}\n"
        if Config.HEROKU_APP and Config.RUN_DYNO_SAVER:
            alive_s += "𝗗𝘆𝗻𝗼 𝗦𝗮𝘃𝗲𝗿 :  𝙴𝚗𝚊𝚋𝚕𝚎𝚍\n"
        alive_s += f"𝗕𝗼𝘁 𝗙𝗼𝗿𝘄𝗮𝗿𝗱𝘀 : {_parse_arg(Config.BOT_FORWARDS)}\n"
        alive_s += f"𝗣𝗠 𝗚𝘂𝗮𝗿𝗱 : {_parse_arg(not Config.ALLOW_ALL_PMS)}\n"
        alive_s += f"𝗣𝗠 𝗟𝗼𝗴𝗴𝗲𝗿 : {_parse_arg(Config.PM_LOGGING)}"
        if allow:
            end = datetime.now()
            m_s = (end - start).microseconds / 1000
            await c_q.answer(ping.format(m_s) + alive_s, show_alert=True)
        else:
            await c_q.answer(alive_s, show_alert=True)
        await asyncio.sleep(0.5)


def _parse_arg(arg: bool) -> str:
    return "𝙴𝚗𝚊𝚋𝚕𝚎𝚍" if arg else "𝙳𝚒𝚜𝚊𝚋𝚕𝚎𝚍"


class Bot_Alive:
    @staticmethod
    async def check_media_link(media_link: str):
        match = _ALIVE_REGEX.search(media_link.strip())
        if not match:
            return None, None
        if match.group(1) == "i.imgur.com":
            link = match.group(0)
            link_type = "url_gif" if match.group(3) == "gif" else "url_image"
        elif match.group(1) == "telegra.ph/file":
            link = match.group(0)
            link_type = "url_image"
        else:
            link_type = "tg_media"
            if match.group(2) == "c":
                chat_id = int("-100" + str(match.group(3)))
                message_id = match.group(4)
            else:
                chat_id = match.group(2)
                message_id = match.group(3)
            link = [chat_id, int(message_id)]
        return link_type, link

    @staticmethod
    def alive_info(me) -> str:
        user = " ".join([me.first_name, me.last_name or ""])
        alive_info_ = f"""
ㅤㅤㅤㅤㅤㅤㅤ
  🧬  <b> [paimon](https://t.me/aliciadarkxd_bot) :ㅤ</b><code>v0.5.1</code>
  🐍  <b> Python  :</b>    <code>v{versions.__python_version__}</code>
  🔥  <b> Pyro      :</b>    <code>v{versions.__pyro_version__}</code>
  🦋  <b> User      :</b>    `{user}`

  <b>{Bot_Alive._get_mode()}   |   {userge.uptime}</b>
"""
        return alive_info_

    @staticmethod
    def _get_mode() -> str:
        if RawClient.DUAL_MODE:
            return "DUAL"
        if Config.BOT_TOKEN:
            return "BOT"
        return "USER"

    @staticmethod
    def alive_buttons() -> InlineKeyboardMarkup:
        buttons = [
            [
                InlineKeyboardButton(text="SETTINGS", callback_data="settings_btn"),
                InlineKeyboardButton(text="REPO", url=Config.UPSTREAM_REPO),
            ]
        ]
        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def alive_default_imgs() -> str:
        alive_imgs = [
            "https://upload-os-bbs.mihoyo.com/upload/2021/03/04/19193793/34294e69072a60066952110c86c6b6b2_463911016668843253.gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/04/07/1491959/6063780e44469bf84f264293fa0486d6_8207551150153056185.gif",
            "https://upload-os-bbs.mihoyo.com/upload/2021/03/28/42423345/7b9ca45750cdbe2606ba71fc92f7d4c7_2902273258542606860.gif",
            "https://64.media.tumblr.com/16688f1cc1f70a5c2713c45ddd131c2c/ec59085d6587885a-28/s1280x1920/f9202ad241714e010acd2d5ae7d4b12c706d5340.gifv",
            "https://upload-os-bbs.mihoyo.com/upload/2021/03/17/117389507/c74d9f77e6d283535f5bf2a0cbf82823_2372392945340857741.gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/01/17/1016483/3a2dceb82908a030448caa6e2a304377_4296988101512302124.gif?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/07/03/1072831/7d85c0f56d1862f9817f6f531a3fcd47_6798977206853753290.gif?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/01/17/1016483/aa770f3cbad0452b7998eeb7bef91bb2_5261425591952038188.gif?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/01/17/1016483/e264666adf0d19b912319b59e9bd5db5_6056298681795866978.gif?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/01/17/1016483/bbd3418a348b827f90364411ab62edf6_3912268420182416957.gif?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/01/17/1016483/7e5a3f6b906308dd28ac77838023ab33_2042358574287811481.gif?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/11/22/13439427/f7c90d1bbe8ebaa7d3077b4aadac2d44_2582140516342929168.gif?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://upload-os-bbs.mihoyo.com/upload/2021/01/06/13439427/e6721bfa5af6c0708797f13258b02ea9_3814557792262964079.gif",
            "https://upload-os-bbs.hoyolab.com/upload/2020/11/20/13439427/bafc2f2b30e7063b49371f6261775cc4_2938495712919911575.gif",
            "https://upload-os-bbs.mihoyo.com/upload/2021/01/14/13439427/72329d3340b7fe19b5a139cd3a937655_1506433168291848345.gif?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://giffiles.alphacoders.com/214/214203.gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/01/17/1016483/973eae6861b9eda831a25b7f0b12930c_4235691643004612761.gif?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/06/17/6682430/9ba34e53b939b8c76a88ee5e3e88d51f_6064201769440250870.gif?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://lh5.googleusercontent.com/t_aWO7FNrfpS4QGIK4RrEk0iuPMh-CSzjLgFEIUdXsX_CwvKsF2mMr9diJ6XbpNX7K6LAkjfbCXyKePFdKd90H_A1LbxUDZRl5Lwtf0yox2ChRCkaF2QQltSqAMlYiXCSZnccDim",
            "https://upload-os-bbs.mihoyo.com/upload/2020/11/10/23488793/bda96b8a8b6854f1b6b39ac9c9d70aa9_4783927684494221244.gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/03/21/2072149/b9e314d799c726f742e43cbd1acccb2d_3787993478380514609.gif?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://i.pinimg.com/originals/25/ac/be/25acbecce5df023f08998ec95ac93f4c.gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/06/29/1010453/5f776c137d552c472c6bb827f6c1131e_2410678658087317335.gif?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/01/17/1016483/475f9c61629439c6ba19fb8709dc4f10_4698642964844992833.gif?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/0bdf5aaf-0179-432a-bf9a-1b079c5fe990/dednkyx-dce1bf0a-7483-4e3f-90d3-aaa04c976c60.gif?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7InBhdGgiOiJcL2ZcLzBiZGY1YWFmLTAxNzktNDMyYS1iZjlhLTFiMDc5YzVmZTk5MFwvZGVkbmt5eC1kY2UxYmYwYS03NDgzLTRlM2YtOTBkMy1hYWEwNGM5NzZjNjAuZ2lmIn1dXSwiYXVkIjpbInVybjpzZXJ2aWNlOmZpbGUuZG93bmxvYWQiXX0.RJE_UNo1M92mLNolnXziHCLhRQg6038LqjphSgSArNw",
            "https://upload-os-bbs.mihoyo.com/upload/2020/01/17/1016483/769e08790ec1b0a5fe5df46dfb94fec6_5307657477810149185.gif?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://64.media.tumblr.com/e2534e0bdeed36978ecec8251ac925b2/62cbf967ceccbb8d-a1/s1280x1920/3ebc9a37d0c982d88bfe8679d6260a74e2af5634.gifv",
            "https://upload-os-bbs.mihoyo.com/upload/2020/11/16/43854381/b5e15fc9756860e4c52dc6b48b0ac86f_4286870611331683423.gif?x-oss-process=image/resize,s_500/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://steamuserimages-a.akamaihd.net/ugc/1661230683494635119/A93C2D11FDC15A4348F836B0D3E7885E4847F314/",
            "https://upload-os-bbs.mihoyo.com/upload/2020/02/29/1016483/6aa0b61c05cd35631b093199ce6a80c0_6450221338136152897.gif?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://64.media.tumblr.com/05f1c2f995848970861d444555b1daa6/85d01fd49e617ccd-09/s500x750/f63a1606fef105c80acc2cffb71da94a4f1fbecf.gifv",
            "https://uploadstatic-sea.mihoyo.com/contentweb/20201217/2020121710180745311.gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/01/27/1010837/a924ccd849fcd61f837416af91035ebd_2019330514823751552.gif?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://media1.tenor.com/images/0e063907a4d819f0c766ee7cce69a569/tenor.gif?itemid=18694033",
            "https://gamezo.co.uk/wp-content/uploads/2020/12/2020122110503016687.gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/06/20/6443925/06c2ada7b68f9d72a47aa14442d3ed97_391016525958412150.gif",
            "https://img1.picmix.com/output/pic/normal/4/2/1/0/9780124_b28fe.gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/01/17/1045285/03d2efdbcac3afafdae5817fa26fbdc8_2333359832013865104.gif",
            "https://upload-os-bbs.hoyolab.com/upload/2020/04/04/1015719/16e8197c8f3fffd6dbbfa41bf644abfa_7880796540095760391.gif",
            "https://upload-os-bbs.hoyolab.com/upload/2020/12/17/57202246/324299c68f3b4814a69b692003ebd1e4_3771835207628391357.gif",
            "https://1.bp.blogspot.com/-FNjlGvIFdDc/X7D5Rohf9vI/AAAAAAAAMx8/3VCCEr4EImMqgXvd4Wr7cAX4_-Py64u2gCLcBGAsYHQ/s640/D3r8cCa.gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/05/08/1012739/a62ec3a9f038f0a65f9fa99a7203122d_4135273782360737372.gif?x-oss-process=image/resize,s_500/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/11/26/74598429/7bd494f99885da8d42b4e88f08f23937_5631596833611915512.gif?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/12/02/64089391/457510710816a5c81697e3787c188d63_3669156310917834036.gif",
            "https://upload-os-bbs.hoyolab.com/upload/2020/12/02/64089391/ece35609c4c35a1445f354dcc87e8681_2563365341162300701.gif?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://steamuserimages-a.akamaihd.net/ugc/1750183521580244801/8BCBB68B0D27D845284464F0D3A8A442CB5D3914/?imw=637&imh=358&ima=fit&impolicy=Letterbox&imcolor=%23000000&letterbox=true",
            "https://steamuserimages-a.akamaihd.net/ugc/1475442891916412819/608C923FA0ABF7B6867EF6E309932D946DB865A8/?imw=637&imh=358&ima=fit&impolicy=Letterbox&imcolor=%23000000&letterbox=true",
            "https://upload-os-bbs.mihoyo.com/upload/2020/06/05/6682430/e0dff66cd6b6d8082de3f20fe482f016_4055159949292897772.gif?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/11/29/44380181/4df6ec39db08448842aa48faa1af79d9_5381631273145060381.gif?x-oss-process=image/resize,s_500/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/03/06/1017906/07979aa09b0de13e51f2a7cb3e1811c5_8996630850272803835.gif?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://upload-os-bbs.mihoyo.com/upload/2021/02/20/90525284/3903a19f5f57c55bd9308128382682ac_3809238191905617885.gif",
            "https://cdn.i-scmp.com/sites/default/files/d8/images/2020/01/22/image2.gif",
            "https://uploadstatic-sea.mihoyo.com/contentweb/20191114/2019111411194459845.gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/01/23/1010453/5fc79df4dcad5d65e663e2018194e2ac_5150452034013479792.gif",
            "https://upload-os-bbs.hoyolab.com/upload/2020/07/27/1096276/874f66c0e960ef35cbb91301309e0846_6095363573915483714.gif",
            "https://upload-os-bbs.mihoyo.com/upload/2021/01/11/85232730/68cee559c8aa8d5ed02fb0e786bec664_8461358318534623244.gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/09/23/6511331/5d55575548a30ca21fcdb50285b9c694_6773655007084040456.gif?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://media.giphy.com/media/2HT9Vir1e6nXnFcGqX/giphy.gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/05/08/3237367/735bad85b9b659a9b72254f8cc4c9010_3928418311493742243.gif?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://upload-os-bbs.mihoyo.com/upload/2021/02/06/6681382/1fcb3f632dd49b06ac14a67890f99bc5_4216942634457753006.gif",
            "https://static1-www.millenium.gg/articles/2/21/21/2/@/203549-2020110614181218388-orig-1-article_m-1.gif",
            "https://upload-os-bbs.hoyolab.com/upload/2021/01/15/6789672/b0cdb5cae0145fb04891ec57829665a6_1819290475455676688.gif?x-oss-process=image/resize,s_500/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://64.media.tumblr.com/4d195d1f85dad2a7243649e6e2f9ddde/63b55500bed3fde6-0d/s640x960/9e5cd75536606c003d2927b1f047d955c68293db.gif",
            "https://upload-os-bbs.mihoyo.com/upload/2021/04/30/55543605/cf484a128e2471c1b1d385e0d7882799_8946186364656477160.gif",
            "http://1900hotdog.com/wp-content/uploads/2020/11/10standing.gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/01/18/1014120/64f2d2a58cad5a74ed5180a2b2d5bc48_1580198778834377248.gif?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://upload-os-bbs.mihoyo.com/upload/2021/01/18/99381702/2e84dc86777adc13efd14a12174795a1_3414418011656696734.png",
            "https://upload-os-bbs.mihoyo.com/upload/2020/06/15/1044038/5bea4b057363025865313036b521e0a6_1070446406643189125.gif",
            "https://www.gensh.in/fileadmin/News/2020/2020-02/81fbe167-9b6d-468b-ae2d-7608a3eee098.gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/01/16/1019934/3b1017d62ff5e3849483fb4a2c49f7b7_8236000563283034457.gif?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,gif",
            "https://i.pinimg.com/originals/6d/35/4c/6d354cf270ab30955fd27242d541f98d.gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/01/18/1014632/e73c54dac76c8e12f76946d9eacdc471_8307670463032709204.gif",
            "https://img.game8.co/3295820/54aca8db72f08890150dc74426c06ffc.gif/show",
            "https://uploadstatic-sea.mihoyo.com/contentweb/20201111/2020111109012666209.gif",
            "https://i.pinimg.com/originals/df/fc/9d/dffc9d812ed545d227bf1752aae93d8a.gif",
            "https://j.gifs.com/GvQGz8.gif",
            "https://upload-os-bbs.mihoyo.com/upload/2020/09/22/1117081/a91641a5dda22dace92e36b05d358700_1380604886138984489.gif",
            "https://steamuserimages-a.akamaihd.net/ugc/1644335490328668704/D256808B083779F126F7EEB6ECE3B1AACCA34366/?imw=268&imh=268&ima=fit&impolicy=Letterbox&imcolor=%23000000&letterbox=true",
            "https://gamezo.co.uk/wp-content/uploads/2020/12/Genshin-Razor-GIF-1.gif",
            "https://media.tenor.com/images/90d518e185425b7532683a862a28cbff/tenor.gif",
            "https://media.tenor.com/images/48712527acd9eaa3c50637fb3d315236/tenor.gif",
            "https://media.tenor.com/images/a6c75e87cce3af61b10e4782c6a4598d/tenor.gif",
            "https://media.tenor.com/images/05ea56308c09bce5e03b89a8135bef93/tenor.gif",
            "https://thumbs.gfycat.com/UnacceptableHandyHadrosaurus-small.gif",
            "https://media.tenor.com/images/8a3e5b0a1e4c0a8d801210cab077e813/tenor.gif",
        ]
        return rand_array(alive_imgs)

    @staticmethod
    def get_bot_cached_fid() -> str:
        return _BOT_CACHED_MEDIA

    @staticmethod
    def is_photo(file_id: str) -> bool:
        return bool(FileId.decode(file_id).file_type in PHOTO_TYPES)
