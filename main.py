from datetime import datetime
from enum import Enum, auto as enum_auto
from itertools import chain
import json
from pathlib import Path
from sys import stderr
from urllib.parse import urlsplit

import requests

headers_original = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:105.0) Gecko/20100101 Firefox/105.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip",
    "DNT": "1",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:105.0) Gecko/20100101 Firefox/105.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip bzip ",
    "DNT": "1",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}


def with_args(f, *pargs, **kwargs):
    return lambda *p, **kw: f(*pargs, *p, **kw, **kwargs)


log_error = with_args(print, "[ ERRO ]", file=stderr)
log_warn = with_args(print, "[ WARN ]")
log_info = with_args(print, "[ INFO ]")
logt_error = with_args(log_error, datetime.now().time())
logt_warn = with_args(log_warn, datetime.now().time())
logt_info = with_args(log_info, datetime.now().time())

def json_pp(o) -> str:
    " pretty print json object "
    return json.dumps(o, indent=2)


class StartMe:
    @staticmethod
    def get_id_from_url(url: str) -> str:
        path_split = urlsplit(url).path.split("/")
        assert path_split[1] == "p"
        return path_split[2]

    @staticmethod
    def get_resource_url(url: str) -> str:
        page_id = StartMe.get_id_from_url(url)
        parts = urlsplit(url)
        return parts._replace(path=f"/p/{page_id}.json").geturl()


def parse_urllist_widget(w):
    " return all links and their text "
    def do_link(link):
        return link["title"] + " ! " + link["url"]

    items = w["items"]

    try:
        links = chain.from_iterable(folder["links"] for folder in items["folders"])
    except KeyError:
        links = items["links"]

    return "\n".join(map(do_link, links))


class WidgetTypes(Enum):
    URL_LIST = "urllist"
    NOTES = "notes"


class UnexpectedWidgetType(Exception):
    ...


def parse_notes_widget(w):
    """ return the text of the note(s) """
    texts = [note["text"] for note in w["items"]["notes"]]
    return "\n".join(texts)


class WidgetTypeMapper:
    maps = {
        WidgetTypes.URL_LIST: parse_urllist_widget,
        WidgetTypes.NOTES: parse_notes_widget,
    }

    @staticmethod
    def map(x: WidgetTypes):
        try:
            return WidgetTypeMapper.maps[x]
        except KeyError:
            raise UnexpectedWidgetType


def parse_widget(w):
    wtype = WidgetTypes(w["widget_type"])
    handler = WidgetTypeMapper.map(wtype)
    return handler(w)
    log_warn("Unrecognized widget type:", wtype)


def ilen(it):
    """ consume iterable and return its length """
    return sum(map(lambda _: 1, it))


write_temp_j = lambda o: Path("tmpout.json").write_text(json_pp(o), encoding="utf-8")

write_temp_t = lambda t: Path("tmpout.txt").write_text(t, encoding="utf-8")


def parse_result(response):
    """ for each widget select an appropriate handler method and hand it the widget """
    all_widgets = chain.from_iterable(
        column["widgets"] for column in response["page"]["columns"]
    )

    text = "\n".join(map(parse_widget, all_widgets))
    write_temp_t(text)


def main():
    # url = "https://start.me/p/rx6Qj8/nixintel-s-osint-resource-list"
    url = "https://start.me/p/rxRbpo/ti" #< the url to be scraped
    page_id = StartMe.get_id_from_url(url)
    raw_filename = f"{page_id}-raw.json"

    if download := 1: # download the live version
        resource = StartMe.get_resource_url(url)

        response = requests.get(resource, headers=headers).json()

        logt_info("Download completed")

        Path(raw_filename).write_text(json_pp(response), encoding="utf-8")
    else: # use the cached version
        with Path(raw_filename).open("r", encoding="utf-8") as f:
            response = json.load(f)

    logt_info("Starting parse")
    parse_result(response)
    logt_info("Finished parsing")


if __name__ == "__main__":
    main()
