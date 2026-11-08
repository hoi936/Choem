#!/usr/bin/env python3
"""Bounded public Facebook UI observation in a fresh, unauthenticated browser.

Uses only normal UI scrolling and the optional dialog's own Close button.
Stops on mandatory login, CAPTCHA, checkpoint, or repeated lack of new links.
No saved credentials, cookies, internal endpoints, or access-control workarounds.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '.tools/python'))
from playwright.sync_api import sync_playwright


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-scrolls', type=int, default=80)
    parser.add_argument('--delay', type=float, default=5)
    args = parser.parse_args()
    if not 1 <= args.max_scrolls <= 200 or args.delay < 4:
        parser.error('Use 1..200 scrolls and a delay of at least four seconds')
    directory = ROOT / 'research/sources' / ('public_feed_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S'))
    directory.mkdir(parents=True)
    audit = {'started_at': now(), 'source_url': 'https://www.facebook.com/people/CHO-EM-project/100094610840245/',
             'credentials_used': False, 'bypass_attempted': False, 'snapshots': [], 'all_links': [],
             'max_scrolls': args.max_scrolls, 'delay_seconds': args.delay, 'status': 'running'}
    def save():
        (directory / 'index.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    save()
    try:
        with sync_playwright() as pw:
            executable = Path('/home/user/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome')
            browser = pw.chromium.launch(headless=True, executable_path=str(executable) if executable.exists() else None)
            context = browser.new_context(locale='vi-VN', viewport={'width': 1365, 'height': 1000})
            page = context.new_page()
            response = page.goto(audit['source_url'], wait_until='domcontentloaded', timeout=35000)
            audit['http_status'] = response.status if response else None
            page.wait_for_timeout(7000)
            close = page.get_by_role('button', name='Đóng', exact=True)
            if close.count() and close.first.is_visible():
                close.first.click(timeout=3000)
                audit['optional_dialog_closed_via_visible_button'] = True
                page.wait_for_timeout(2000)
            known = set()
            stagnant = 0
            for step in range(args.max_scrolls + 1):
                text = page.locator('body').inner_text()
                links = page.locator('a[href]').evaluate_all('(els) => els.map(e => e.href)')
                relevant = set(u.split('&__cft__')[0].split('&__tn__')[0] for u in links
                               if any(s in u for s in ['/posts/', '/permalink.php?', '/photo/?', '/videos/', '/reel/']))
                new = relevant - known
                if new or step == 0:
                    prefix = directory / f'snapshot_{step:03}'
                    body = page.content().encode('utf-8')
                    prefix.with_suffix('.html').write_bytes(body)
                    prefix.with_suffix('.txt').write_text(text, encoding='utf-8')
                    audit['snapshots'].append({'step': step, 'collected_at': now(), 'response_path': str(prefix.with_suffix('.html').relative_to(ROOT)),
                                               'visible_text_path': str(prefix.with_suffix('.txt').relative_to(ROOT)),
                                               'sha256': hashlib.sha256(body).hexdigest(), 'new_links': sorted(new)})
                    known.update(relevant)
                    stagnant = 0
                else:
                    stagnant += 1
                audit.update(all_links=sorted(known), last_scroll=step, updated_at=now())
                save()
                print(json.dumps({'step': step, 'new_links': len(new), 'total_links': len(known), 'snapshots': len(audit['snapshots'])}), flush=True)
                if any(token in page.url.lower() for token in ['/checkpoint/', '/login/', '/login.php', '/captcha/']):
                    audit['status'] = 'stopped_access_requirement'
                    break
                if page.get_by_role('dialog').count():
                    audit['status'] = 'stopped_dialog_requires_user_action'
                    break
                if stagnant >= 4:
                    audit['status'] = 'stopped_no_new_links_after_four_scrolls'
                    break
                if step == args.max_scrolls:
                    audit['status'] = 'stopped_scroll_budget_reached_not_historical_end'
                    break
                page.mouse.wheel(0, 1800)
                page.wait_for_timeout(int(args.delay * 1000))
            page.screenshot(path=str(directory / 'final.png'), full_page=False)
            browser.close()
    except Exception as exc:
        audit.update(status='error', error=f'{type(exc).__name__}: {exc}')
    audit['finished_at'] = now()
    save()
    print(json.dumps({'index': str((directory / 'index.json').relative_to(ROOT)), 'status': audit['status'],
                      'links': len(audit['all_links']), 'snapshots': len(audit['snapshots'])}), flush=True)


if __name__ == '__main__':
    main()
