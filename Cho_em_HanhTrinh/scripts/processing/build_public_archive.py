#!/usr/bin/env python3
"""Conservatively turn saved CHO EM public observations into archive records.

The script is idempotent. It never infers a season from a post's date and never
promotes a visible Facebook excerpt to a complete original caption.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/collection'))
import archive

EXTRACTION = ROOT / 'research/facebook_snapshot_extraction.json'
POST_SOURCE = 'research/sources/facebook_browser_02.html'
PAGE_URL = archive.PAGE_URL
SEASON_ID = 'season_07'
PROGRAM_ID = 'program_hanh_trang_cho_em_2026'
EVENT_ID = 'event_hanh_trang_cho_em_20260818'
EVIDENCE_SEASON = 'ev_season07_direct_caption'
EVIDENCE_PROGRAM = 'ev_hanh_trang_20260818_direct_caption'


def atomic(relative, value):
    archive.atomic_json(ROOT / relative, value)


def load(relative, fallback):
    return archive.read_json(ROOT / relative, fallback)


def upsert(relative, record, id_key):
    records = load(relative, [])
    found = next((i for i, item in enumerate(records) if item.get(id_key) == record[id_key]), None)
    if found is None:
        records.append(record)
    else:
        current = records[found]
        for key, value in record.items():
            if current.get(key) in (None, [], ''):
                current[key] = value
            elif isinstance(value, list):
                for element in value:
                    if element not in current[key]:
                        current[key].append(element)
        records[found] = current
    atomic(relative, records)
    return records[found if found is not None else -1]


def add_once(sequence, value):
    if value not in sequence:
        sequence.append(value)


def main():
    x = json.loads(EXTRACTION.read_text(encoding='utf-8'))
    exact = next(p for p in x['posts'] if p['facebook_post_id'] == '919178351245851')
    caption_evidence = exact['caption_evidence'][:1]
    post_url = exact['post_url']
    season = upsert('data/processed/seasons.json', {
        'season_id': SEASON_ID, 'season_number': 7, 'official_name': 'CHO EM mùa 7',
        'theme': None, 'slogan': None, 'start_date': None, 'end_date': None,
        'description': 'Caption tổng kết của dự án xác nhận mùa 7 và chương trình Hành Trang Cho Em.',
        'objectives': ['Giáo dục và tuyên truyền phòng chống tai nạn đuối nước cho học sinh Trường Tiểu học Tà Long.'],
        'locations': ['Trường Tiểu học Tà Long, Quảng Trị'],
        'program_ids': [PROGRAM_ID], 'journey_ids': [], 'post_ids': [], 'photo_ids': [],
        'video_ids': [], 'milestone_ids': [], 'source_urls': [post_url],
        'verification_status': 'verified', 'evidence_ids': [EVIDENCE_SEASON],
        'season_directory': f'data/seasons/{SEASON_ID}',
        'closing_announced_in_post_at': exact['published_at'],
        'research_notes': 'Chưa biết ngày mở đầu/kết thúc chính xác, chủ đề chính thức, thứ tự và hồ sơ các mùa trước. Bài 20/8/2026 nói mùa 7 đã khép lại; ngày đăng không mặc nhiên là ngày kết thúc.',
    }, 'season_id')
    program = upsert('data/processed/programs.json', {
        'program_id': PROGRAM_ID, 'name': 'Hành Trang Cho Em', 'season_ids': [SEASON_ID],
        'start_date': '2026-08-18', 'end_date': '2026-08-18',
        'locations': ['Trường Tiểu học Tà Long, Quảng Trị'],
        'purpose': 'Tuyên truyền, giáo dục phòng chống tai nạn đuối nước.',
        'context': None,
        'preparation': 'Caption tổng kết nêu gây quỹ bằng bán hàng online và workshop; chưa có ngày từng hoạt động.',
        'activities': ['Tuyên truyền và giáo dục phòng chống tai nạn đuối nước', 'Trao tặng quà, áo phao, sách và tủ sách'],
        'results': [
            {'metric': 'suất quà', 'value': 125, 'qualifier': 'exact'},
            {'metric': 'áo phao', 'value': 125, 'qualifier': 'exact'},
            {'metric': 'quyển sách', 'value': 100, 'qualifier': 'greater_than'},
            {'metric': 'tủ sách', 'value': 2, 'qualifier': 'exact'},
        ],
        'post_ids': [], 'photo_ids': [], 'source_urls': [post_url],
        'verification_status': 'verified', 'evidence_ids': [EVIDENCE_PROGRAM],
        'research_notes': 'Số sách là hơn 100, không được đổi thành đúng 100. Chưa có bằng chứng hành trình/chuyến đi riêng.',
    }, 'program_id')
    evidences = [
        {'evidence_id': EVIDENCE_SEASON, 'claim': 'Dự án CHO EM có mùa 7.',
         'entity_type': 'season', 'entity_id': SEASON_ID, 'verification_status': 'verified',
         'source_urls': [post_url], 'post_ids': [], 'evidence': caption_evidence,
         'source_status': 'direct_public_snapshot_json'},
        {'evidence_id': EVIDENCE_PROGRAM, 'claim': 'Ngày 18/8/2026 CHO EM mùa 7 tổ chức Hành Trang Cho Em tại Trường Tiểu học Tà Long, trao 125 quà, 125 áo phao, hơn 100 sách, 2 tủ sách.',
         'entity_type': 'program', 'entity_id': PROGRAM_ID, 'verification_status': 'verified',
         'source_urls': [post_url], 'post_ids': [], 'evidence': caption_evidence,
         'source_status': 'direct_public_snapshot_json'},
    ]
    for item in evidences:
        upsert('research/evidence_map.json', item, 'evidence_id')

    # The original, complete message is kept exactly as delivered. Other DOM
    # articles expose only excerpts. Their dates lack a year, so published_at
    # and season attribution stay unknown until further evidence arrives.
    normalized = [{'facebook_post_id': exact['facebook_post_id'], 'post_url': post_url,
                   'published_at': exact['published_at'], 'caption_original': exact['caption_original'],
                   'caption_completeness': 'complete', 'post_type': 'photo',
                   'season_ids': [SEASON_ID], 'program_ids': [PROGRAM_ID],
                   'location_mentions': ['Trường Tiểu học Tà Long', 'Quảng Trị'],
                   'keywords': ['mùa 7', 'Hành Trang Cho Em', 'phòng chống đuối nước']}]
    extra_by_url = {}
    for item in x['dom_post_discoveries']:
        for url in item.get('post_urls', []):
            if url == post_url:
                continue
            extra_by_url[url] = item
    for url, item in extra_by_url.items():
        normalized.append({'post_url': url, 'published_at': None, 'caption_original': None,
                           'caption_completeness': 'unknown', 'post_type': 'unknown'})
    norm_path = ROOT / 'research/normalized_public_posts.json'
    archive.atomic_json(norm_path, {'posts': normalized})
    with archive.archive_lock(ROOT):
        archive.import_export(ROOT, norm_path, requested_format='auto')
    posts = load('data/raw/posts.json', [])
    by_url = {p.get('post_url'): p for p in posts}
    for post in posts:
        if post['post_url'] == archive.canonical_url(post_url):
            post.update(source_status='direct_public_snapshot_json', verification_status='verified',
                        caption_evidence=caption_evidence, caption_status='exact_message_text_as_delivered_in_snapshot',
                        event_date_mentioned='2026-08-18',
                        summary='Tổng kết Hành Trang Cho Em thuộc mùa 7 tại Trường Tiểu học Tà Long.',
                        historical_significance='Bằng chứng trực tiếp về mùa 7 và kết quả chương trình.',
                        importance_score=5, keywords=['mùa 7','Hành Trang Cho Em','đuối nước'])
        else:
            item = extra_by_url.get(post['post_url'])
            if item:
                post.update(source_status='direct_public_dom_excerpt', caption_visible_excerpt=item.get('caption_visible_excerpt'),
                            visible_timestamp_labels=item.get('visible_timestamp_labels', []),
                            caption_status='visible_excerpt_only', verification_status='unknown')
    atomic('data/raw/posts.json', posts)
    for p in posts:
        atomic(f'data/raw/posts/{p["post_id"]}.json', p)
    atomic('data/unclassified/posts.json', [p for p in posts if not p.get('season_ids')])
    exact_post = by_url[archive.canonical_url(post_url)]
    post_id = exact_post['post_id']
    evidence = load('research/evidence_map.json', [])
    for e in evidence:
        if e['evidence_id'] in (EVIDENCE_SEASON, EVIDENCE_PROGRAM):
            e['post_ids'] = [post_id]
    atomic('research/evidence_map.json', evidence)
    for item, path in ((season, 'data/processed/seasons.json'), (program, 'data/processed/programs.json')):
        values = load(path, [])
        for value in values:
            if value.get('season_id') == SEASON_ID or value.get('program_id') == PROGRAM_ID:
                add_once(value['post_ids'], post_id)
        atomic(path, values)
    event = {'event_id': EVENT_ID, 'title': 'Hành Trang Cho Em tại Trường Tiểu học Tà Long',
             'event_date': '2026-08-18', 'date_precision': 'day', 'season_ids': [SEASON_ID],
             'program_ids': [PROGRAM_ID], 'event_type': 'program',
             'description': 'Giáo dục phòng chống đuối nước và trao quà, áo phao, sách, tủ sách.',
             'details': None, 'cover_photo_id': None, 'post_ids': [post_id], 'source_urls': [post_url],
             'verification_status': 'verified', 'evidence_ids': [EVIDENCE_PROGRAM]}
    upsert('data/processed/timeline.json', event, 'event_id')
    # A reel is visible as its own source link; no full video/caption or exact
    # publication year was delivered in the accessible DOM.
    reel = next((d for d in x['dom_post_discoveries'] if d.get('video_urls')), None)
    if reel:
        video_url = reel['video_urls'][0]
        upsert('data/raw/videos.json', {'video_id': 'video_1411736247503742',
            'source_url': video_url, 'post_url': video_url, 'published_at': None,
            'visible_timestamp_labels': reel.get('visible_timestamp_labels', []),
            'caption_original': None, 'caption_visible_excerpt': reel.get('caption_visible_excerpt'),
            'caption_completeness': 'unknown', 'duration_seconds': 144,
            'season_ids': [], 'program_ids': [], 'source_status': 'direct_public_dom_excerpt',
            'download_status': 'not_downloaded', 'rights_status': 'unknown',
            'thumbnail_path': None, 'privacy_review_required': True,
            'provenance_snapshot': reel.get('evidence', {}).get('snapshot_path')}, 'video_id')
        archive.discover(ROOT, [video_url], source_url=POST_SOURCE)
    archive.discover(ROOT, [PAGE_URL], source_url=POST_SOURCE)
    archive.checkpoint(ROOT, 'build-public-archive', {'full_captions': 1,
                        'other_visible_post_excerpts': len(extra_by_url), 'verified_seasons': 1})
    print(json.dumps({'season_id': SEASON_ID, 'program_id': PROGRAM_ID, 'post_id': post_id,
                      'posts': len(posts), 'videos': len(load('data/raw/videos.json', []))}, ensure_ascii=False))


if __name__ == '__main__':
    main()
