"""Fun plugin"""

import asyncio
from datetime import datetime
from re import compile as comp_regex

from pyrogram import filters
from pyrogram.errors import BadRequest, FloodWait, Forbidden, MediaEmpty
from pyrogram.file_id import PHOTO_TYPES, FileId
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from userge import Config, Message, get_version, userge
from userge.core.ext import RawClient
from userge.utils import get_file_id, rand_array

_ALIVE_REGEX = comp_regex(
    r"http[s]?://(i\.imgur\.com|telegra\.ph/file|t\.me)/(\w+)(?:\.|/)(gif|mp4|jpg|png|jpeg|[0-9]+)(?:/([0-9]+))?"
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
    client = message.client
    caption = Bot_Alive.alive_info()
    if client.is_bot:
        reply_markup = Bot_Alive.alive_buttons()
        file_id = _BOT_CACHED_MEDIA
    else:
        reply_markup = None
        file_id = _USER_CACHED_MEDIA
        caption += (
            f"\n⚡️  <a href={Config.UPSTREAM_REPO}><b>ʀᴇᴘᴏꜱɪᴛᴏʀɪᴏ</b></a>"
            "    <code>|</code>    "
            "👥  <a href='https://t.me/fnixdev'><b>ꜱᴜᴘᴏʀᴛᴇ</b></a>"
        )
    if not Config.ALIVE_MEDIA:
        await client.send_animation(
            chat_id,
            animation=Bot_Alive.alive_default_imgs(),
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

    @userge.bot.on_callback_query(filters.regex(pattern=r"^status_alive$"))
    async def status_alive_(_, c_q: CallbackQuery):
        c_q.from_user.id
        await c_q.answer(
            f"▫️ ᴍᴏᴅᴏ :  {Bot_Alive._get_mode()}\n▫️ ᴠᴇʀsɪᴏɴ  :  v{get_version()}\n▫️ ᴜᴘᴛɪᴍᴇ  :  {userge.uptime}\n\n{rand_array(FRASES)}",
            show_alert=True,
        )
        return status_alive_

    @userge.bot.on_callback_query(filters.regex(pattern=r"^settings_btn$"))
    async def alive_cb(_, c_q: CallbackQuery):
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
                    Bot_Alive.alive_info(),
                    reply_markup=Bot_Alive.alive_buttons(),
                    disable_web_page_preview=True,
                )
            except FloodWait as e:
                await asyncio.sleep(e.x)
            except BadRequest:
                pass
            ping = "🏓 ᴘɪɴɢ : {} ᴍs\n"
        alive_s = "➕ ᴘʟᴜɢɪɴs + : {}\n".format(
            _parse_arg(Config.LOAD_UNOFFICIAL_PLUGINS)
        )
        alive_s += f"👥 ᴀɴᴛɪsᴘᴀᴍ : {_parse_arg(Config.SUDO_ENABLED)}\n"
        alive_s += f"🚨 ᴀɴᴛɪsᴘᴀᴍ : {_parse_arg(Config.ANTISPAM_SENTRY)}\n"
        if Config.HEROKU_APP and Config.RUN_DYNO_SAVER:
            alive_s += "⛽️ ᴅʏɴᴏ :  ✅ ᴀᴛɪᴠᴀᴅᴏ\n"
        alive_s += f"💬 ʙᴏᴛ ꜰᴡᴅ : {_parse_arg(Config.BOT_FORWARDS)}\n"
        alive_s += f"🛡 ᴘᴍ ʙʟᴏᴄᴋ : {_parse_arg(not Config.ALLOW_ALL_PMS)}\n"
        alive_s += f"📝 ʟᴏɢ ᴘᴍ : {_parse_arg(Config.PM_LOGGING)}"
        if allow:
            end = datetime.now()
            m_s = (end - start).microseconds / 1000
            await c_q.answer(ping.format(m_s) + alive_s, show_alert=True)
        else:
            await c_q.answer(alive_s, show_alert=True)
        await asyncio.sleep(0.5)


def _parse_arg(arg: bool) -> str:
    return " ᴀᴛɪᴠᴀᴅᴏ" if arg else " ᴅᴇsᴀᴛɪᴠᴀᴅᴏ"


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
            link_type = "url_gif" if match.group(3) == "gif" else "url_image"
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
    def alive_info() -> str:
        alive_info_ = f"""

ㅤㅤㅤㅤㅤㅤㅤ
  💕   <b> [paimon](https://t.me/my_thingsuwu) </b>
  🦋   <b> User      :</b>    `Alicia`
                       <b>{userge.uptime}</b>

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
                InlineKeyboardButton(text="⚙️  ᴄᴏɴꜰɪɢ", callback_data="settings_btn"),
                InlineKeyboardButton(text="💭  sᴛᴀᴛᴜs", callback_data="status_alive"),
            ],
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
        ]
        return rand_array(alive_imgs)

    @staticmethod
    def get_bot_cached_fid() -> str:
        return _BOT_CACHED_MEDIA

    @staticmethod
    def is_photo(file_id: str) -> bool:
        return bool(FileId.decode(file_id).file_type in PHOTO_TYPES)


FRASES = (
    "Hey how are you doing today",
    "you're looking beautiful",
)
