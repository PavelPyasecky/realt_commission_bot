import ast
import gettext
import os
import struct


def _unquote(value):
    return ast.literal_eval(value)


def _compile_mo(po_path, mo_path):
    with open(po_path, "r", encoding="utf-8") as po_file:
        lines = po_file.readlines()

    messages = {}
    msgid = ""
    msgstr = ""
    in_msgid = False
    in_msgstr = False

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        if line.startswith("msgid "):
            in_msgid = True
            in_msgstr = False
            msgid = _unquote(line[6:])
            msgstr = ""
            continue
        if line.startswith("msgstr "):
            in_msgid = False
            in_msgstr = True
            msgstr = _unquote(line[7:])
            messages[msgid] = msgstr
            continue
        if line.startswith('"'):
            if in_msgid:
                msgid += _unquote(line)
            elif in_msgstr:
                msgstr += _unquote(line)
                messages[msgid] = msgstr

    ids = sorted(messages.keys())
    strs = [messages[_id] for _id in ids]

    offsets = []
    ids_str = b""
    strs_str = b""

    for _id in ids:
        encoded = _id.encode("utf-8")
        offsets.append((len(encoded), len(ids_str)))
        ids_str += encoded + b"\x00"

    for _str in strs:
        encoded = _str.encode("utf-8")
        offsets.append((len(encoded), len(strs_str)))
        strs_str += encoded + b"\x00"

    keystart = 7 * 4 + len(ids) * 8 * 2
    valuestart = keystart + len(ids_str)

    with open(mo_path, "wb") as mo_file:
        mo_file.write(
            struct.pack(
                "Iiiiiii",
                0x950412de,
                0,
                len(ids),
                7 * 4,
                7 * 4 + len(ids) * 8,
                0,
                0,
            )
        )

        for length, offset in offsets[: len(ids)]:
            mo_file.write(struct.pack("II", length, offset + keystart))
        for length, offset in offsets[len(ids) :]:
            mo_file.write(struct.pack("II", length, offset + valuestart))

        mo_file.write(ids_str)
        mo_file.write(strs_str)


def compile_translations():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    locale_dir = os.path.join(base_dir, "locales")
    if not os.path.isdir(locale_dir):
        return
    for locale in os.listdir(locale_dir):
        po_path = os.path.join(locale_dir, locale, "LC_MESSAGES", "messages.po")
        mo_path = os.path.join(locale_dir, locale, "LC_MESSAGES", "messages.mo")
        if os.path.exists(po_path):
            if not os.path.exists(mo_path) or os.path.getmtime(po_path) > os.path.getmtime(mo_path):
                _compile_mo(po_path, mo_path)


def get_translator():
    locale = os.environ.get("APP_LOCALE", "ru")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    locale_dir = os.path.join(base_dir, "locales")
    compile_translations()
    translation = gettext.translation("messages", localedir=locale_dir, languages=[locale], fallback=True)
    return translation.gettext


if __name__ == "__main__":
    compile_translations()
