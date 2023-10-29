# ABS Chapters
This tool facilitates conversion between various audiobook chapter formats (audiobookshelf metadata json, m4b-tool, and cue sheets), as well as overwriting a book's ABS chapter metadata with a file you provide.  The goal is to make it easier for us to share chapter info with each other so we're not duplicating effort manually chapterizing audiobooks.

Inputs for the tool found in the `main()` function are:
- `base_url` - URL of your ABS server; e.g. `"https://audiobooks.myserver.com"`
- `api_key` - Your ABS API Token.  You can find this in Settings > Users > Click a user > API Token
- `book_id` - Unique id for your book in ABS.  Best way to find this is by looking at your book in a web browser and grabbing the 32 character id from the URL.

Then I have some example usages in the code, but you can either download chapters (grab the chapter metadata from ABS and write it to the file format of your choice), or upload chapters (supply a file and it will convert to ABS format and overwrite the metadata on the server).


## Chapter Specs
In its current state this tool doesn't handle a whole lot of edge cases.  I've made assumptions that chapters should look like the following:

#### m4b-tool
https://github.com/sandreas/m4b-tool#fixed-chapters
```
00:00:00.000 Intro
00:04:19.153 This is
00:09:24.078 A way to add
00:14:34.500 Chapters manually
```

#### audiobookshelf
https://api.audiobookshelf.org/#get-a-library-item
```
{
    "media": {
        "chapters": [
            {
                "id": 0,
                "start": 0,
                "end": 6004.6675,
                "title": "Terry Goodkind - SOT Bk01 - Wizards First Rule 01"
            },
            {
                "id": 1,
                "start": 6004.6675,
                "end": 12000.946,
                "title": "Terry Goodkind - SOT Bk01 - Wizards First Rule 02"
            }
        ],
    }
}
```

#### CUE
This format seems to be somewhat poorly defined, since it was made for CD-ROMs and the official spec therefore has some now unecessary limitations (e.g. maximum 99 tracks).  It seems that inAudible and Libation have their own pseudo-specs.  This is how the tool wants them to look:

```
FILE "" MP3
TRACK 1 AUDIO
  TITLE "Opening Credits"
  INDEX 01 0:00:00
TRACK 2 AUDIO
  TITLE "Introduction"
  INDEX 01 0:15:00
TRACK 3 AUDIO
  TITLE "Chapter One"
  INDEX 01 0:40:52
TRACK 4 AUDIO
  TITLE "Chapter Two"
  INDEX 01 18:14:94
```

This tool doesn't care about the Track or Index numbers or filename/format when reading, it just tries to read the title and timestamps.  When writing, it makes a blank filename, puts everything at INDEX 01 and numbers tracks sequentially.
