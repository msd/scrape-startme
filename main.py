from datetime import datetime
from enum import Enum, auto as enum_auto
from itertools import chain
import json
from pathlib import Path
from sys import stderr
from typing import Any
from urllib.parse import urlsplit

import click
import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:105.0) Gecko/20100101 Firefox/105.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br"
    # "DNT": "1",
    # "Sec-Fetch-Dest": "empty",
    # "Sec-Fetch-Mode": "cors",
    # "Sec-Fetch-Site": "same-origin",
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
    "pretty print json object"
    return json.dumps(o, indent=2)


class StartMe:
    @staticmethod
    def get_id_from_url(url: str) -> str:
        try:
            path_split = urlsplit(url).path.split("/")
            assert path_split[1] == "p"
            assert len(path_split[2]) == 6
            return path_split[2]
        except Exception:
            raise NotSupportedURL(
                "URL does not follow the expected start.me format: " + str(url)
            )

    @staticmethod
    def get_resource_url(url: str) -> str:
        page_id = StartMe.get_id_from_url(url)
        parts = urlsplit(url)
        return parts._replace(path=f"/p/{page_id}.json").geturl()


def parse_urllist_widget(w) -> list[dict[str, str]]:
    """return all links and their text"""

    def do_link(link):
        return {"type": "link", "text": link["title"], "url": link["url"]}

    items = w["items"]

    try:
        links = chain.from_iterable(folder["links"] for folder in items["folders"])
    except KeyError:
        links = items["links"]

    return [do_link(i) for i in links]


class UnexpectedWidgetType(Exception):
    ...


class NotSupportedURL(Exception):
    """url is not supported by the current function"""

    ...


class WidgetTypes(Enum):
    URL_LIST = "urllist"
    NOTES = "notes"
    RSS_LIST = "rsslist"


def parse_rsslist_widget(w):
    def do_feed(feed):
        return {"type": "feed", "text": feed["name"], "source": feed["url"]}

    return [do_feed(f) for f in w["items"]["feeds"]]


def parse_notes_widget(w):
    """return the text of the note(s)"""
    texts = [note["text"] for note in w["items"]["notes"]]
    return [{"type": "note", "texts": texts}]


class WidgetTypeMapper:
    maps = {
        WidgetTypes.URL_LIST: parse_urllist_widget,
        WidgetTypes.NOTES: parse_notes_widget,
        WidgetTypes.RSS_LIST: parse_rsslist_widget,
    }

    @staticmethod
    def map(x: WidgetTypes):
        try:
            return WidgetTypeMapper.maps[x]
        except KeyError:
            raise UnexpectedWidgetType


def parse_widget(w):
    wtype = WidgetTypes(w["widget_type"])
    try:
        handler = WidgetTypeMapper.map(wtype)
    except UnexpectedWidgetType:
        log_warn("Unrecognized widget type:", wtype)
        return []
    return handler(w)


def ilen(it):
    """consume iterable and return its length"""
    return sum(map(lambda _: 1, it))


write_temp_j = lambda o: Path("tmpout.json").write_text(json_pp(o), encoding="utf-8")

write_temp_t = lambda t: Path("tmpout.txt").write_text(t, encoding="utf-8")


def parse_result(response):
    """for each widget select an appropriate handler method and hand it the widget"""
    all_widgets = chain.from_iterable(
        column["widgets"] for column in response["page"]["columns"]
    )

    return list(chain.from_iterable(map(parse_widget, all_widgets)))


@click.command(
    help="Scrape the public page at the given URL",
    context_settings=dict(help_option_names=["-h", "--help"]),
)
@click.argument("url", type=str)
@click.option("out_path", "--out", "-o", type=Path, help="output file")
@click.option(
    "--keep-temp", "-k", type=bool, is_flag=True, help="save raw response by server"
)
@click.option("--debug-load-cached", type=bool, is_flag=True)
@click.option(
    "--pretty/--no-pretty",
    "-p",
    is_flag=True,
    type=bool,
    default=True,
    help="pretty-printing of JSON output",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(("csv", "json", "xml")),
    default="json",
    show_default=True,
)
def main(
    url: str,
    out_path: Path,
    keep_temp: bool,
    debug_load_cached: bool,
    pretty: bool,
    format: str,
):

    try:  # validate url format
        page_id = StartMe.get_id_from_url(url)
    except NotSupportedURL:
        log_error("URL not supported")
        exit(1)

    if out_path is None:
        out_path = Path(f"{page_id}.json")

    raw_out_path = out_path.with_name(out_path.stem + "-raw" + out_path.suffix)

    if debug_load_cached:  # use the existing raw file
        logt_info("Using cached version")
        try:
            with raw_out_path.open("r", encoding="utf-8") as f:
                response = json.load(f)
        except:
            logt_error("Failed when tried to load existing raw file")
            exit(1)
        logt_info("Loaded cached version")
    else:  # normal operation, download the live version
        resource = StartMe.get_resource_url(url)

        http_response = requests.get(resource, headers=headers)

        if http_response.status_code != 200:
            logt_error("Server returned bad status")
            exit(1)

        try:
            response = http_response.json()
        except requests.exceptions.JSONDecodeError:
            logt_error("Received response is not valid JSON")
            exit(1)

        logt_info("Download completed")

        if keep_temp:  # maybe rename to extra_files or save_raw ?
            with raw_out_path.open("w", encoding="utf-8") as raw_file:
                if pretty:
                    raw_file.write(json_pp(response))
                else:
                    json.dump(response, raw_file)

    logt_info("Starting parse")
    output = parse_result(response)
    logt_info("Finished parsing")
    if format == "json":
        out_path.write_text(
            (json_pp if pretty else json.dumps)(output), encoding="utf-8"
        )
    else:
        logt_error("Format not supported yet")
        exit(1)


if __name__ == "__main__":
    main()

    # example domains
    # TODO eventually create automated tests to see that the
    #      ad-hoc api is not broken

    # links only
    # https://start.me/p/rx6Qj8/nixintel-s-osint-resource-list

    # links and notes
    # https://start.me/p/rxRbpo/ti

    # links and rsslist
    # https://start.me/p/7kLY9R/osint-chine
