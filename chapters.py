import json
from typing import Literal
import requests


def abs_to_m4b(abs_list: list) -> list:
    m4b_list = []
    for chapter in abs_list:
        title = chapter["title"]
        seconds = chapter["start"]
        mm, ss = divmod(seconds, 60)
        hh, mm = divmod(mm, 60)
        time_str = f"{int(hh):02}:{int(mm):02}:{ss:06.3f}"

        m4b_list.append(f"{time_str} {title}")

    return m4b_list


def m4b_to_abs(m4b_text: str, duration: float) -> list[dict]:
    lines = m4b_text.split("\n")

    titles = []
    times = []
    for line in lines:
        if not line:
            continue

        time, title = line.split(maxsplit=1)
        titles.append(title)

        hh, mm, ss = [float(t) for t in time.split(":")]
        total_seconds = hh * 3600 + mm * 60 + ss
        times.append(total_seconds)

    times.append(duration)

    chapter_list = []
    for i, title in enumerate(titles):
        start = times[i]
        end = times[i + 1]
        chapter_dict = {"id": i, "start": start, "end": end, "title": title}
        chapter_list.append(chapter_dict)

    return chapter_list


def abs_to_cue(abs_list: list, audio_ext: str) -> list:
    if audio_ext == ".mp3":
        cue_list = ['FILE "" MP3']
    else:
        cue_list = ['FILE "" MP4']

    for i, chapter in enumerate(abs_list, start=1):
        title = chapter["title"]
        seconds = chapter["start"]
        mm, ss = divmod(seconds, 60)
        time_str = f"{int(mm)}:{ss:05.2f}".replace(".", ":")

        cue_list.append(
            f"""\
TRACK {i} AUDIO
  TITLE "{title}"
  INDEX 01 {time_str}"""
        )

    return cue_list


def cue_to_abs(cue_text: str, duration: float) -> list[dict]:
    lines = cue_text.split("\n")

    titles = []
    times = []
    for line in lines:
        if not line or line.upper().startswith("FILE") or line.upper().startswith("TRACK"):
            continue

        if line.strip().upper().startswith("TITLE"):
            _, title = line.split(maxsplit=1)
            title = title.strip('"')
            titles.append(title)
            continue

        if line.strip().upper().startswith("INDEX"):
            _, _, time = line.split()
            mm, ss = time.split(":", maxsplit=1)
            mm = int(mm)
            ss = float(ss.replace(":", "."))
            total_seconds = mm * 60 + ss
            times.append(total_seconds)

    times.append(duration)

    chapter_list = []
    for i, title in enumerate(titles):
        start = times[i]
        end = times[i + 1]
        chapter_dict = {"id": i, "start": start, "end": end, "title": title}
        chapter_list.append(chapter_dict)

    return chapter_list


def abs_to_mam_comment(chapter_list, audio_ext):
    # ABS format
    chapters_abs_str = json.dumps(chapter_list, indent=2)
    chapters_abs = chapters_abs_str.replace("\n", "[br]\n")

    # m4b-tool format
    chapters_m4b = "[br]\n".join(abs_to_m4b(chapter_list))

    # CUE format
    chapters_cue = "\n".join(abs_to_cue(chapter_list, audio_ext)).replace("\n", "[br]\n")

    comment = f"""Thank you!  Here are the chapters I found:[br][br]

ABS format:

[hide][fw]{chapters_abs}[/fw][/hide]

m4b-tool format:

[hide][fw]{chapters_m4b}[/fw][/hide]

CUE format:

[hide][fw]{chapters_cue}[/fw][/hide]"""

    return comment


def get_item_data(base_url, item_id, api_key):
    url = f"{base_url}/api/items/{item_id}?expanded=1"
    response = requests.get(url=url, headers={"Authorization": f"Bearer {api_key}"}, timeout=10)
    return response.json()


def download_chapters(item_data, out_path, chapter_format: Literal["abs", "m4b-tool", "cue", "comment"]):
    chapter_list = item_data["media"]["chapters"]
    audio_ext = item_data["media"]["audioFiles"][0]["metadata"]["ext"]

    if chapter_format == "abs":
        with open(out_path, "w", encoding="utf-8") as file:
            json.dump(chapter_list, file, indent=2)
        print(f"Wrote chapters to {out_path}")
        return

    elif chapter_format == "comment":
        text = abs_to_mam_comment(chapter_list, audio_ext)
    elif chapter_format == "m4b-tool":
        text = "\n".join(abs_to_m4b(chapter_list))
    elif chapter_format == "cue":
        text = "\n".join(abs_to_cue(chapter_list, audio_ext))

    with open(out_path, "wt", encoding="utf-8") as file:
        file.write(text)
        print(f"Wrote chapters to {out_path}")


def update_item_chapters(base_url, chapter_list, item_id, api_key):
    url = f"{base_url}/api/items/{item_id}/chapters"
    response = requests.post(
        url=url,
        headers={"Authorization": f"Bearer {api_key}"},
        json={"chapters": chapter_list},
        timeout=10,
    )
    print(json.dumps(response.json(), indent=2))


def convert_chapters(item_data, chapter_file, chapter_format: Literal["abs", "m4b-tool", "cue"]):
    duration = item_data["media"]["duration"]

    if chapter_format == "abs":
        with open(chapter_file, "rt", encoding="utf-8") as file:
            return json.load(file)
    if chapter_format == "m4b-tool":
        with open(chapter_file, "rt", encoding="utf-8") as file:
            m4b_str = file.read()
        return m4b_to_abs(m4b_str, duration)
    if chapter_format == "cue":
        with open(chapter_file, "rt", encoding="utf-8") as file:
            cue_str = file.read()
        return cue_to_abs(cue_str, duration)

    return None


def main():
    base_url = "https://audiobooks.mydomain.com"
    api_key = "my-api-key"

    book_id = "vtyi0jzd-7ups-evvh-krt5-xfba09mf2n8n"  # look at url for ABS in browser or "Cover" metadata
    book_data = get_item_data(base_url, book_id, api_key)

    # # # # # # # # # # # # # # # # # # # #
    # # #  DOWNLOAD CHAPTERS EXAMPLES # # #
    # # # # # # # # # # # # # # # # # # # #

    # CREATE MAM COMMENT
    out_file = "example-data\\the-shining-comment.txt"
    download_chapters(item_data=book_data, out_path=out_file, chapter_format="comment")

    # # CREATE AUDIOBOOKSHELF .JSON
    # out_file = "example-data\\the-shining-abs.json"
    # download_chapters(item_data=book_data, out_path=out_file, chapter_format="abs")

    # # CREATE M4B-TOOL TXT
    # out_file = "example-data\\the-shining-m4b.txt"
    # download_chapters(item_data=book_data, out_path=out_file, chapter_format="m4b-tool")

    # # CREATE CUE
    # out_file = "example-data\\the-shining-cue.cue"
    # download_chapters(item_data=book_data, out_path=out_file, chapter_format="cue")

    # # # # # # # # # # # # # # # # # # # # # # # #
    # # #  UPLOAD/OVERWRITE CHAPTERS EXAMPLES # # #
    # # # # # # # # # # # # # # # # # # # # # # # #

    # OVERWRITE FROM ABS JSON
    new_chapters_file = "example-data\\the_shining.json"
    new_chapters_list = convert_chapters(item_data=book_data, chapter_file=new_chapters_file, chapter_format="abs")
    update_item_chapters(base_url, new_chapters_list, book_id, api_key)

    # # OVERWRITE FROM CUE
    # new_chapters_file = "my_book.cue"
    # new_chapters_list = convert_chapters(item_data=book_data, chapter_file=new_chapters_file, chapter_format="cue")
    # update_item_chapters(base_url, new_chapters_list, book_id, api_key)

    # # OVERWRITE FROM M4B-TOOL TXT
    # new_chapters_file = "my_book.txt"
    # new_chapters_list = convert_chapters(
    #     item_data=book_data, chapter_file=new_chapters_file, chapter_format="m4b-tool"
    # )
    # update_item_chapters(base_url, new_chapters_list, book_id, api_key)


if __name__ == "__main__":
    main()
