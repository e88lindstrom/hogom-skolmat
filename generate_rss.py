#!/usr/bin/env python3
"""Generate an RSS feed for today's lunch at Högoms skola from Mateo."""
import json
import os
import urllib.request
from datetime import datetime, timedelta
from email.utils import format_datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from xml.etree.ElementTree import Element, SubElement, ElementTree

TZ = ZoneInfo("Europe/Stockholm")
SCHOOL_ID = "673"
SCHOOL_URL = "https://meny.mateo.se/sundsvall/673"
API_URL = f"https://meny-api.mateo.se/api/v1/days/{SCHOOL_ID}"
OUTPUT = Path("docs/skolmat.xml")

def main():
    now = datetime.now(TZ)
    today = now.date()
    start = today - timedelta(days=1)
    end = today + timedelta(days=7)
    url = f"{API_URL}?from={start.isoformat()}&to={end.isoformat()}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "Referer": "https://mateo.se/",
        "User-Agent": "HogomSkolmatRSS/1.0"
    })
    with urllib.request.urlopen(req, timeout=25) as response:
        data = json.load(response)
    if not isinstance(data, list):
        raise ValueError("Unexpected Mateo response: expected list")
    today_entry = next((d for d in data if isinstance(d, dict) and
                        str(d.get("date", ""))[:10] == today.isoformat()), None)
    meals = today_entry.get("meals", []) if today_entry else []
    if not isinstance(meals, list):
        raise ValueError("Unexpected Mateo response: meals is not a list")
    dishes = [m.get("name", "").strip() for m in meals if isinstance(m, dict)
              and isinstance(m.get("name"), str) and m.get("name", "").strip()]
    if not dishes and today.weekday() < 5:
        # No published menu: don't overwrite a previously valid feed with invented food.
        print(f"No menu published for {today}; publishing a no-menu notice")
    title = "Dagens skolmat – Högoms skola"
    description = " | ".join(dishes) if dishes else "Ingen matsedel publicerad för idag."
    display_title = "  •  ".join(dishes) if dishes else "Ingen skolmat publicerad idag"
    rss = Element("rss", {"version": "2.0"})
    channel = SubElement(rss, "channel")
    for tag, value in (("title", title), ("link", SCHOOL_URL),
                       ("description", "Dagens skolmat från Mateo Meny för Högoms skola"),
                       ("language", "sv-SE"),
                       ("lastBuildDate", format_datetime(now))):
        SubElement(channel, tag).text = value
    item = SubElement(channel, "item")
    for tag, value in (("title", display_title),
                       ("description", description), ("link", SCHOOL_URL),
                       ("guid", f"hogom-{today.isoformat()}"),
                       ("pubDate", format_datetime(now))):
        el = SubElement(item, tag)
        if tag == "guid":
            el.set("isPermaLink", "false")
        el.text = value
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    ElementTree(rss).write(OUTPUT, encoding="utf-8", xml_declaration=True)
    print(f"Updated {OUTPUT} with {len(dishes)} meal(s) for {today}")

if __name__ == "__main__":
    main()
