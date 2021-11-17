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
            "https://cdn.discordapp.com/attachments/871469925364039721/904353913707327558/IMG_20211031_182917_143.jpg",
            "https://media.discordapp.net/attachments/871469925364039721/904353914101579777/IMG_20211031_182911_035.jpg",
            "https://media.discordapp.net/attachments/871469925364039721/904353914567163954/IMG_20211031_182855_657.jpg",
            "https://media.discordapp.net/attachments/871469925364039721/904353914869149756/IMG_20211031_182816_108.jpg",
            "https://media.discordapp.net/attachments/871469925364039721/904353915133378630/IMG_20211031_182803_562.jpg",
            "https://media.discordapp.net/attachments/871469925364039721/904353915481493554/IMG_20211031_182757_699.jpg",
            "https://media.discordapp.net/attachments/871469925364039721/904353916265853028/IMG_20211031_182648_078.jpg",
            "https://media.discordapp.net/attachments/871469925364039721/904353916538470400/IMG_20211031_182651_842.jpg",
            "https://static.zerochan.net/Genshin.Impact.full.3114614.jpg",
            "https://upload-os-bbs.mihoyo.com/upload/2020/09/01/7793492/b6d4c59195d2d9aeeb443ec18b83f6ca_6891885956397011448.png",
            "https://static.zerochan.net/Genshin.Impact.full.3114617.jpg",
            "https://i.redd.it/inzuhy5lgke61.jpg",
            "https://art.ngfiles.com/images/1475000/1475667_payaazz_genshin-impact-fanart.jpg?f1603489327",
            "https://upload-os-bbs.hoyolab.com/upload/2020/12/08/67936930/467197bd6cc61eba66a7966c22e0c7d4_623833578884025245.jpg",
            "https://static.zerochan.net/Xiao.(Genshin.Impact).full.3143939.jpg",
            "https://upload-os-bbs.mihoyo.com/upload/2021/03/06/19690622/9bc800c85088477face6e2a6b3a71463_4252434937019684979.jpg",
            "https://w.wallha.com/ws/12/6dt1A9oI.png",
            "https://images.wallpapersden.com/image/download/genshin-impact-sucrose-fanart_bGlsamuUmZqaraWkpJRpZWVlrWhmbGw.jpg",
            "https://images.wallpapersden.com/image/download/genshin-impact-mona-fanart_bGlsamyUmZqaraWkpJRpZWVlrWhlZWU.jpg",
            "https://upload-os-bbs.mihoyo.com/upload/2020/09/03/1072594/f1dbafc59864694b989899922de521ed_8372537966490933481.png",
            "https://static.zerochan.net/Mona.(Genshin.Impact).full.3119386.png",
            "https://upload-os-bbs.mihoyo.com/upload/2020/05/21/6600252/3dbbe95ce534c70905801c8084599306_5765230530578945359.png",
            "https://static.zerochan.net/Genshin.Impact.full.3115999.jpg",
            "https://upload-os-bbs.mihoyo.com/upload/2020/07/29/6629765/4d075e2b7ef3cd6d9406c4cb0543e8ef_308469974232994649.png",
            "https://static.zerochan.net/Fischl.full.3130463.jpg",
            "https://upload-os-bbs.mihoyo.com/upload/2020/11/21/12293768/c13374d62e531b8b028a811633872a46_5610468602736387097.jpg",
            "https://upload-os-bbs.mihoyo.com/upload/2020/11/22/12293768/6466d106aaa6baf06b6be954e2bf54ee_1984691076488541398.jpg",
            "https://i.redd.it/9ezdzvvbvw061.jpg",
            "https://preview.redd.it/26d1rm0xq5861.jpg?auto=webp&s=22ff0b8cebb412e3e1e5487c0e925a9d8c43dd6d",
            "https://upload-os-bbs.mihoyo.com/upload/2021/04/06/69760498/69ff7776a43896480a3a1bcd58382a19_6333108024837865022.jpg",
            "https://upload-os-bbs.mihoyo.com/upload/2020/11/14/13732917/627686133a1a2a272123f4427f5017f6_6150275195801671010.png",
            "https://preview.redd.it/ujzp3gvo6hr51.jpg?auto=webp&s=834b531e2aeaeb299a5042b876c3a4acbbc90dbd",
            "https://upload-os-bbs.hoyolab.com/upload/2020/12/07/17195475/9ba8ed2fcfd55c0b58297a59c3ca461a_3718175974472214771.jpg",
            "https://images.wallpapersden.com/image/download/genshin-impact-barbara-fanart_bGltamyUmZqaraWkpJRnaW1lrWZuaGw.jpg",
            "https://i.redd.it/17tpn67pcbz51.jpg",
            "https://images.wallpapersden.com/image/download/genshin-impact-mona-fanart_bGlsamyUmZqaraWkpJRmaWllrWhlaWU.jpg",
            "https://images.wallpapersden.com/image/download/zhongli-fanart-genshin-impact_bGlrZm6UmZqaraWkpJRnZWltrWdlaW0.jpg",
            "https://www.dualshockers.com/static/uploads/2021/02/Genshin-Impact-Bennett-birthday-official-artwork-mihoyo-ps4-ps5-pc-switch-mobile-.jpg",
            "https://i.redd.it/zwa6gkc8mtr51.png",
            "https://lh6.googleusercontent.com/proxy/BHtD3kNvkPVUCecsHR84m0sYEOzhpx54vS4j0VuNsp2dqRVdUV0wc2_bjeSK1ctRcPSf8SMCHzLT2bv7RDe1Jgn7VL1LfqU0BPostGO6iB6yZZ5RYBU=w1600",
            "https://i.redd.it/f87n7ph3xk861.png",
            "https://upload-os-bbs.mihoyo.com/upload/2021/01/04/1124531/1f816ff6949726aaccac295f9c583cd6_3902537051958411446.jpg",
            "https://i.redd.it/b6a9ihdo0e061.jpg",
            "http://pm1.narvii.com/7827/a99d986f46b93634351241f23b6bbd33ddfded90r1-1548-2048v2_uhq.jpg",
            "https://upload-os-bbs.mihoyo.com/upload/2021/01/26/1014585/77439b10f353ccf9c3919af1a0cfda42_2730526612135052900.jpg",
            "https://dthezntil550i.cloudfront.net/mf/latest/mf2011141801476500000811437/f0033a6b-8608-4183-9421-396f28060c24.png",
            "https://images.wallpapersden.com/image/download/genshin-impact-mona-fanart_bGlsamyUmZqaraWkpJRmZmxrrWdpZWU.jpg",
            "https://static.zerochan.net/Zhongli.full.3133085.png",
            "https://images.wallpapersden.com/image/download/genshin-impact-sucrose-fanart_bGlsamuUmZqaraWkpJRnamtlrWZlbWU.jpg",
            "https://upload-os-bbs.hoyolab.com/upload/2020/11/30/7943498/9aafb97ae5df095f03b710a924153b89_4055158283853689405.png",
            "https://upload-os-bbs.mihoyo.com/upload/2021/03/05/105760636/4f4990ffb045980f77428d3e1d3ebd5f_4424481153483373271.png",
            "https://upload-os-bbs.mihoyo.com/upload/2020/07/11/1017267/78ed887fee7a48772666ca65419986f4_3273963756580939990.png",
            "https://www.enwallpaper.com/wp-content/uploads/genshin-impact-ningguang-by-10juu-de5t826-fullview.jpg",
            "https://upload-os-bbs.mihoyo.com/upload/2021/01/11/86691207/9b3c1722f5931f896f26b70ad73bf9db_8914014846236083575.jpg",
            "https://static.zerochan.net/Mona.(Genshin.Impact).full.3118629.jpg",
            "https://i.pinimg.com/originals/5c/9c/19/5c9c190dfcd33f9fb7fee28ef9c6f2ec.jpg",
            "https://i.redd.it/3ibopzhcext51.png",
            "https://static.zerochan.net/Mona.(Genshin.Impact).full.3122471.png",
            "https://d.wattpad.com/story_parts/249/images/163d4cdd6913b5fd942913551668.jpg",
            "https://static.zerochan.net/Qiqi.full.3106064.jpg",
            "https://images.wallpapersden.com/image/download/genshin-impact-barbara-fanart_bGltamyUmZqaraWkpJRmZ21lrWZlZ2k.jpg",
            "https://64.media.tumblr.com/5f517c16d4bb951273df749a3fda30de/8294639a455bb7b2-09/s1280x1920/955255204b1e6eb301d84ddbfb4499ae30750627.png",
            "https://upload-os-bbs.mihoyo.com/upload/2020/09/23/1080596/9f7af214a98431728fabd91eb3e5a660_1733935150091347568.jpg",
            "https://upload-os-bbs.mihoyo.com/upload/2020/09/15/1080596/42c72be59fe0bb9327a392a9ff5cc20b_4957885551410192780.jpg",
            "https://i.pinimg.com/originals/14/26/d5/1426d58b40465034177d543f2d8bdd20.jpg",
            "https://upload-os-bbs.mihoyo.com/upload/2021/01/27/43642920/0609da2a73baf39fe70fa557c318b0a7_1794917413466532898.jpg",
            "https://pbs.twimg.com/media/Em3kV2wVQAABy7l.jpg",
            "http://img1.reactor.cc/pics/post/Qiqi-(Genshin-Impact)-Genshin-Impact-фэндомы-nyaruin-6286637.png",
            "https://upload-os-bbs.mihoyo.com/upload/2020/01/19/1040716/d58ef6954f8a6973d5290cfe6edc9055_6192867544562212828.jpg",
            "https://upload-os-bbs.mihoyo.com/upload/2020/09/15/7826036/79155e85ebfd940f28d3f3434ea71431_424780609961066062.png",
            "https://upload-os-bbs.hoyolab.com/upload/2020/11/28/10201465/29421ebb211039e52ba3357089a96de2_7632347749757496342.png",
            "https://preview.redd.it/td0bflog5v261.png?width=960&crop=smart&auto=webp&s=d09a39787cd47789f280e83c9987b593622920ad",
            "https://d30womf5coomej.cloudfront.net/c/6a/733b3caa-c38b-49f5-bee7-9864ca3562b9.png",
            "https://upload-os-bbs.hoyolab.com/upload/2020/12/09/12293768/fb3bdfd10a5396ad312f09c6bbd75bbd_7521257894599811968.jpg",
            "https://upload-os-bbs.mihoyo.com/upload/2020/11/04/1013950/d66852e34edaababacf46e9599078cf8_3094945932433172740.png?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,png",
            "https://upload-os-bbs.mihoyo.com/upload/2020/08/24/1013950/864fc2c630c3a21bc7eabe1089cd2143_2010057496849673127.png?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,png",
            "https://upload-os-bbs.mihoyo.com/upload/2021/01/14/8331937/f8f6fdefbdfc4291ec05f8519e210e4d_5341269157733340934.png?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,jpg",
            "https://i.pinimg.com/originals/26/29/43/262943ae5871c094e12b0e01a372854b.jpg",
            "https://upload-os-bbs.mihoyo.com/upload/2020/07/14/1013950/cfe231c2ded4ddb1207446603306979f_7090196717731562114.jpg?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,jpg",
            "https://upload-os-bbs.mihoyo.com/upload/2020/07/21/1013950/53dbf4ea17d549a1034fa0844fc65b61_8948903456380173142.png?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,png",
            "https://upload-os-bbs.mihoyo.com/upload/2020/11/04/1013950/160f0e5effbb052daf15e3ef07089e29_5734410563923253843.png?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,png",
            "https://upload-os-bbs.mihoyo.com/upload/2020/11/04/1013950/a0edf0b2f8565492facf3b758290e42c_2829691252642300522.png?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,png",
            "https://i.pinimg.com/originals/23/57/3b/23573b04898071e8e3279160d07714de.jpg",
            "https://upload-os-bbs.mihoyo.com/upload/2020/11/04/1013950/de4d1e69c5636fb09e8bb3725f875379_1139668858622916055.png?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,png",
            "https://i.pinimg.com/originals/22/08/a3/2208a3c3adc5f0be6d5cdd29911b58e0.jpg",
            "https://upload-os-bbs.mihoyo.com/upload/2020/04/14/1013950/0df6b486f86726c09cf706d9860c6826_5495945356992863175.png?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,png",
            "https://i.pinimg.com/originals/8f/7e/5e/8f7e5e94853cc2e40dece9f0f85a8d53.jpg",
            "https://upload-os-bbs.mihoyo.com/upload/2020/11/04/1013950/16351fcf6f44720176a9793c16adcbb7_1280100820802675094.png?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,png",
            "https://upload-os-bbs.mihoyo.com/upload/2020/05/31/5027783/392a4de995825416b33c05d158bcb559_1019092597011251431.png?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,jpg",
            "https://upload-os-bbs.hoyolab.com/upload/2021/01/15/43753043/4cd96af66b90339825e350bedd099040_1075501064949025619.jpg?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,jpg",
            "https://upload-os-bbs.mihoyo.com/upload/2021/02/26/18485488/8bfc611e27e3a83fc4084d7e3633b18e_732838745570729225.png?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,jpg",
            "https://lh5.googleusercontent.com/proxy/g5AI7Bvv1aF76TsgjE8eVKEzwRk_rgy2PRVgGw16qbL9zs2kDgQ3CV2ZO1NxVX1BgWVWZCHAMoWjLG8Zacni-LFk4ddIiUSl58DV8ElzW-VQfNHyTPSfHWxAx8OE3oU0ijboIcLIE1Te22vRAI4FfbpuQt6lfqf0lMAyr4uDxwQTo4Wkzyeagzx6ExxfbIqyzbh7Q1M7bw1snv61qWaj=s0-d",
            "https://upload-os-bbs.mihoyo.com/upload/2020/11/04/1013950/5e9243883f6fe695c58da1cd19cce5c1_8160804410525094851.png?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,png",
            "https://static.zerochan.net/Qiqi.full.3157740.png",
            "https://static.zerochan.net/Klee.(Genshin.Impact).full.3186226.png",
            "https://upload-os-bbs.mihoyo.com/upload/2020/11/04/1013950/8b519504dfce27e619f07de508423bd0_1557615061651954493.png?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,png",
            "https://preview.redd.it/7c8kzlib1cs51.jpg?width=640&crop=smart&auto=webp&s=9e3b2e508f061b89d9283743ad29d71a77dd44ae",
            "https://upload-os-bbs.mihoyo.com/upload/2020/01/17/1017127/e4b5e86ab2f703bbcdefb6095f4b59b0_4284781544493788620.png?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,png",
            "https://upload-os-bbs.mihoyo.com/upload/2021/01/27/43642920/0609da2a73baf39fe70fa557c318b0a7_1794917413466532898.jpg?x-oss-process=image/resize,s_740/quality,q_80/auto-orient,0/interlace,1/format,jpg",
            "https://s1.zerochan.net/Genshin.Impact.600.3374915.jpg",
            "https://s1.zerochan.net/Genshin.Impact.600.3125636.jpg",
            "https://s1.zerochan.net/Xingqiu.600.3125760.jpg",
            "https://s1.zerochan.net/Genshin.Impact.600.3185340.jpg",
            "https://media.discordapp.net/attachments/871469925364039721/904353916806889543/IMG_20211031_182642_344.jpg",
        ]
        return rand_array(alive_imgs)

    @staticmethod
    def get_bot_cached_fid() -> str:
        return _BOT_CACHED_MEDIA

    @staticmethod
    def is_photo(file_id: str) -> bool:
        return bool(FileId.decode(file_id).file_type in PHOTO_TYPES)
