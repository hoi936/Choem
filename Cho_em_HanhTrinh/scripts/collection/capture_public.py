#!/usr/bin/env python3
"""Capture one public URL, without credentials, retries or bypasses.

Network permission is provided by the execution environment, not this script.
Captures are immutable by label; use a new label for another observation.
"""
import argparse
import gzip
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '.tools/python'))


class PublicHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
        self.links = []
        self.text = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('script', 'style'):
            self.skip += 1
        if tag == 'meta' and ('property' in attrs or 'name' in attrs):
            self.meta[attrs.get('property', attrs.get('name'))] = attrs.get('content')
        if tag == 'a' and attrs.get('href'):
            self.links.append(attrs['href'])

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip = max(0, self.skip - 1)

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.text.append(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--browser', action='store_true')
    args = parser.parse_args()
    parsed = urllib.parse.urlparse(args.url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        parser.error('Only public HTTPS URLs without credentials are supported.')
    if not args.label.replace('_', '').replace('-', '').isalnum():
        parser.error('label must contain letters, numbers, underscores or hyphens')
    dest = ROOT / 'research/sources' / args.label
    if dest.with_suffix('.json').exists():
        print(f'Already captured: {dest.with_suffix(".json")}')
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    record = dict(source_url=args.url, collected_at=datetime.now(timezone.utc).isoformat(),
                  method='public_browser' if args.browser else 'public_https_get',
                  credentials_used=False, bypass_attempted=False)
    try:
        if args.browser:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                executable = next((ROOT2 for ROOT2 in [
                    Path('/home/user/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome'),
                    Path('/home/user/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome'),
                ] if ROOT2.exists()), None)
                browser = pw.chromium.launch(headless=True, executable_path=str(executable) if executable else None)
                context = browser.new_context(locale='vi-VN', viewport={'width': 1365, 'height': 900})
                page = context.new_page()
                response = page.goto(args.url, wait_until='domcontentloaded', timeout=35000)
                page.wait_for_timeout(7000)
                record.update(http_status=response.status if response else None,
                              final_url=page.url, title=page.title())
                record['links'] = page.locator('a[href]').evaluate_all('(els) => els.map(e => ({url:e.href,text:e.innerText}))')
                record['visible_text'] = page.locator('body').inner_text()
                record['screenshot_path'] = str(dest.with_suffix('.png').relative_to(ROOT))
                page.screenshot(path=str(dest.with_suffix('.png')), full_page=True)
                body = page.content().encode('utf-8')
                browser.close()
        else:
            request = urllib.request.Request(args.url, headers={'User-Agent': 'CHO-EM-Archive-Research/1.0'})
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read(5_000_001)
                if len(body) > 5_000_000:
                    raise ValueError('Response exceeded 5MB; capture stopped')
                record.update(http_status=response.status, final_url=response.url,
                              content_type=response.headers.get('Content-Type'),
                              content_encoding=response.headers.get('Content-Encoding'))
                if record['content_encoding'] == 'gzip' or body.startswith(b'\x1f\x8b'):
                    dest.with_suffix('.wire.gz').write_bytes(body)
                    record['wire_sha256'] = hashlib.sha256(body).hexdigest()
                    body = gzip.decompress(body)
                    if len(body) > 20_000_000:
                        raise ValueError('Decompressed response exceeded 20MB')
        html = PublicHTML()
        html.feed(body.decode('utf-8', errors='replace'))
        record['meta'] = html.meta
        record.setdefault('visible_text', '\n'.join(html.text))
        record.setdefault('links', html.links)
        record.update(bytes_received=len(body), sha256=hashlib.sha256(body).hexdigest(),
                      response_path=str(dest.with_suffix('.html').relative_to(ROOT)))
        dest.with_suffix('.html').write_bytes(body)
        dest.with_suffix('.txt').write_text(record['visible_text'], encoding='utf-8')
    except Exception as exc:
        record['error'] = f'{type(exc).__name__}: {exc}'
        if isinstance(exc, urllib.error.HTTPError):
            record['http_status'] = exc.code
    dest.with_suffix('.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    logdir = ROOT / 'logs'
    logdir.mkdir(exist_ok=True)
    with (logdir / 'collection.log').open('a', encoding='utf-8') as log:
        log.write(json.dumps({k: v for k, v in record.items() if k not in ('visible_text', 'links', 'meta')}, ensure_ascii=False) + '\n')
    if record.get('error'):
        with (logdir / 'errors.log').open('a', encoding='utf-8') as log:
            log.write(json.dumps(record, ensure_ascii=False) + '\n')
    print(json.dumps({k: v for k, v in record.items() if k not in ('visible_text', 'links', 'meta')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
