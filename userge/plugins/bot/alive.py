"""Fun plugin"""

import asyncio
from datetime import datetime
from re import compile as comp_regex

from pyrogram import filters
from pyrogram.errors import BadRequest, FloodWait, Forbidden, MediaEmpty
from pyrogram.file_id import PHOTO_TYPES, FileId
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from userge import Config, Message, get_version, userge, versions
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
            "👥  <a href='https://t.me/useless_x'><b>SUPPORT</b></a>"
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
        alive_s = "➕ 𝗘𝘅𝘁𝗿𝗮 𝗣𝗹𝘂𝗴𝗶𝗻𝘀 : {}\n".format(
            _parse_arg(Config.LOAD_UNOFFICIAL_PLUGINS)
        )
        alive_s += f"👥 𝗦𝘂𝗱𝗼 : {_parse_arg(Config.SUDO_ENABLED)}\n"
        alive_s += f"🚨 𝗔𝗻𝘁𝗶𝘀𝗽𝗮𝗺 : {_parse_arg(Config.ANTISPAM_SENTRY)}\n"
        if Config.HEROKU_APP and Config.RUN_DYNO_SAVER:
            alive_s += "⛽️ 𝗗𝘆𝗻𝗼 𝗦𝗮𝘃𝗲𝗿 :  𝙴𝚗𝚊𝚋𝚕𝚎𝚍\n"
        alive_s += f"💬 𝗕𝗼𝘁 𝗙𝗼𝗿𝘄𝗮𝗿𝗱𝘀 : {_parse_arg(Config.BOT_FORWARDS)}\n"
        alive_s += f"🛡 𝗣𝗠 𝗚𝘂𝗮𝗿𝗱 : {_parse_arg(not Config.ALLOW_ALL_PMS)}\n"
        alive_s += f"📝 𝗣𝗠 𝗟𝗼𝗴𝗴𝗲𝗿 : {_parse_arg(Config.PM_LOGGING)}"
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
  🧬  <b> [paimon](https://t.me/aliciadarkxd_bot) :ㅤㅤㅤ</b><code>v0.5.1</code>
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
            "https://telegra.ph/file/6f8aa08193c4a26d32c8f.jpg",
            "https://telegra.ph/file/f31cf4721636102bba528.jpg",
            "https://telegra.ph/file/7b93eb9f3a71d4a009961.jpg",
            "https://telegra.ph/file/59aefb8f199af9e4ce214.jpg",
            "https://telegra.ph/file/e7b569283c9484c280242.jpg",
            "https://telegra.ph/file/fccccf1269bd28a22dd24.jpg",
            "https://telegra.ph/file/ea4adcad104ec3421f9cc.jpg",
            "https://telegra.ph/file/377e047a87f9fd7e8b4fc.jpg",
            "https://telegra.ph/file/6f63195d08df591bc4388.jpg",
            "https://telegra.ph/file/87911231dfc1137c145ef.jpg",
            "https://telegra.ph/file/0cdff991a8c31dc6eb5e2.jpg",
            "https://telegra.ph/file/43c24db2b9f7211cdc559.jpg",
            "https://telegra.ph/file/df2e8a2c5532df9db458d.jpg",
            "https://telegra.ph/file/c46511ea3f56d287e8c82.jpg",
            "https://telegra.ph/file/f93b692f0ff3719abe497.jpg",
            "https://telegra.ph/file/c13c205edd80e06abf440.jpg",
            "https://telegra.ph/file/5536eee05b34240538491.jpg",
            "https://telegra.ph/file/9e2f4efa63ffede41528a.jpg",
            "https://telegra.ph/file/92da4c48a812dff03d338.jpg",
            "https://telegra.ph/file/92da4c48a812dff03d338.jpg",
            "https://telegra.ph/file/24062dabe6904a3be2c6f.jpg",
            "https://telegra.ph/file/ad0489b333dfff59c7d90.jpg",
            "https://telegra.ph/file/226c91584f99d2850d4c5.jpg",
            "https://telegra.ph/file/e1bcdeaa8b65f93a2b2c7.jpg",
            "https://telegra.ph/file/05bec6e7375a8a4eb33f9.jpg",
            "https://telegra.ph/file/4443de8b0fcfd6dccd65e.jpg",
            "https://telegra.ph/file/26252450e097240040285.jpg",
            "https://telegra.ph/file/03ec8ed814ee02625b896.jpg",
            "https://telegra.ph/file/9a3f71393836a752c6b41.jpg",
            "https://telegra.ph/file/a480d0a9f97a4e8891688.jpg",
            "https://telegra.ph/file/75990831f9befadf43862.jpg",
            "https://telegra.ph/file/f4e9726bc287f3a746c90.jpg",
        ]
        return rand_array(alive_imgs)

    @staticmethod
    def get_bot_cached_fid() -> str:
        return _BOT_CACHED_MEDIA

    @staticmethod
    def is_photo(file_id: str) -> bool:
        return bool(FileId.decode(file_id).file_type in PHOTO_TYPES)
