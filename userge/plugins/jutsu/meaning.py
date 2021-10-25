from PyDictionary import PyDictionary

from userge import Message, userge


@userge.on_cmd(
    "mng",
    about={
        "header": "use this to find meaning of any word.",
        "examples": [
            "{tr}mng [word] or [reply to msg]",
        ],
    },
)
async def meaning_wrd(message: Message):
    """meaning of word"""
    await message.edit("`Searching for meaning...`")
    word = message.input_str or message.reply_to_message.text
    if not word:
        await message.err("no input!")
    else:
        dictionary = PyDictionary()
        words = dictionary.meaning(word)
        output = f"**Word :** __{word}__\n"
        try:
            for a, b in words.items():
                output = output + f"\n**{a}**\n"
                for i in b:
                    output = output + f"• __{i}__\n"
            await message.edit(output)
        except Exception:
            await message.err(f"Couldn't fetch meaning of {word}")


@userge.on_cmd(
    "syn",
    about={
        "header": "use this to find synonyms of any word.",
        "examples": [
            "{tr}syn [word] or [reply to msg]",
        ],
    },
)
async def synonym_wrd(message: Message):
    """synonym of word"""
    await message.edit("`Searching for synonyms...`")
    word = message.input_str or message.reply_to_message.text
    if not word:
        await message.err("no input!")
    else:
        dictionary = PyDictionary()
        words = dictionary.synonym(word)
        output = f"**Synonym for :** __{word}__\n"
        try:
            for a in words:
                output = output + f"• __{a}__\n"
            await message.edit(output)
        except Exception:
            await message.err(f"Couldn't fetch synonyms of {word}")


@userge.on_cmd(
    "ayn",
    about={
        "header": "use this to find antonym of any word.",
        "examples": [
            "{tr}ayn [word] or [reply to msg]",
        ],
    },
)
async def antonym_wrd(message: Message):
    """antonym of word"""
    await message.edit("`Searching for antonyms...`")
    word = message.input_str or message.reply_to_message.text
    if not word:
        await message.err("no input!")
    else:
        dictionary = PyDictionary()
        words = dictionary.antonym(word)
        output = f"**Antonym for :** __{word}__\n"
        try:
            for a in words:
                output = output + f"• __{a}__\n"
            await message.edit(output)
        except Exception:
            await message.err(f"Couldn't fetch antonyms of {word}")
