#!/usr/bin/env python3
"""Capture already-discovered public post links in a credential-free browser."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '.tools/python'))
from playwright.sync_api import sync_playwright


def main():
    extracted = json.loads((ROOT / 'research/facebook_snapshot_extraction.json').read_text())
    urls = []
    for item in extracted['dom_post_discoveries']:
        for url in item.get('post_urls', []):
            if 'id=100094610840245' in url and url not in urls:
                urls.append(url)
    already = extracted['posts'][0]['post_url']
    urls = [url for url in urls if url != already]
    log = {'started_at': datetime.now(timezone.utc).isoformat(), 'source': 'research/facebook_snapshot_extraction.json',
           'credentials_used': False, 'bypass_attempted': False, 'records': []}
    target = ROOT / 'research/sources/known_posts_capture.json'
    def persist():
        target.write_text(json.dumps(log, ensure_ascii=False, indent=2) + '\n')
    persist()
    with sync_playwright() as pw:
        executable = Path('/home/user/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome')
        browser = pw.chromium.launch(headless=True, executable_path=str(executable) if executable.exists() else None)
        context = browser.new_context(locale='vi-VN', viewport={'width':1365,'height':900})
        for index,url in enumerate(urls):
            digest = hashlib.sha256(url.encode()).hexdigest()[:12]
            prefix = ROOT / 'research/sources' / f'known_post_{index+1:02}_{digest}'
            if prefix.with_suffix('.html').exists():
                continue
            page = context.new_page()
            record={'url':url,'started_at':datetime.now(timezone.utc).isoformat()}
            try:
                response=page.goto(url,wait_until='domcontentloaded',timeout=35000)
                page.wait_for_timeout(6000)
                record.update(http_status=response.status if response else None, final_url=page.url,
                              title=page.title())
                if any(token in page.url.lower() for token in ['/login/','/checkpoint/','/captcha/']):
                    record['status']='stopped_access_requirement'
                    log['records'].append(record);persist();break
                body=page.content().encode('utf-8')
                prefix.with_suffix('.html').write_bytes(body)
                record.update(status='captured', sha256=hashlib.sha256(body).hexdigest(),
                              snapshot_path=str(prefix.with_suffix('.html').relative_to(ROOT)))
                prefix.with_suffix('.txt').write_text(page.locator('body').inner_text(),encoding='utf-8')
            except Exception as exc:
                record.update(status='error',error=f'{type(exc).__name__}: {exc}')
                log['records'].append(record);persist();break
            finally:
                page.close()
            log['records'].append(record);persist()
            print(json.dumps({'index':index+1,'status':record['status'],'snapshot':record.get('snapshot_path')}),flush=True)
        browser.close()
    log['finished_at']=datetime.now(timezone.utc).isoformat();persist()


if __name__=='__main__':
    main()
