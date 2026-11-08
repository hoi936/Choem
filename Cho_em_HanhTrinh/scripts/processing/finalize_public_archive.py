#!/usr/bin/env python3
"""Reconcile observed photo IDs with downloaded bytes and prepare season 7 bundle."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/collection'))
import archive

SEASON = 'season_07'
PROGRAM = 'program_hanh_trang_cho_em_2026'
POST_FB = '919178351245851'


def write(path, value):
    archive.atomic_json(ROOT / path, value)


def read(path, default=None):
    return archive.read_json(ROOT / path, default)


def append_unique(record, key, value):
    record.setdefault(key, [])
    if value is not None and value not in record[key]:
        record[key].append(value)


def main():
    manifest = read('research/media_manifest.json', [])
    extraction = read('research/facebook_snapshot_extraction.json', {})
    posts = read('data/raw/posts.json', [])
    exact = next(p for p in posts if p.get('facebook_post_id') == POST_FB)
    post_id = exact['post_id']
    photos = read('data/raw/photos.json', [])
    media_index = read('data/processed/media_index.json', [])
    attempts = read('research/download_attempts.json', [])
    photo_by_id = {p['photo_id']: p for p in photos}
    ids_in_program = []
    for item in manifest:
        fb_id = item['facebook_photo_id']
        source_url = item['source_url']
        found = next((p for p in photos if source_url in p.get('source_urls', [])), None)
        related = item.get('source_post_url') is not None and archive.canonical_url(item['source_post_url']) == exact['post_url']
        if not related:
            related = fb_id in extraction['posts'][0].get('photo_ids', [])
        if found:
            append_unique(found, 'facebook_photo_ids', fb_id)
            append_unique(found, 'source_photo_urls', (item.get('source_photo_urls') or [None])[0])
            if related:
                append_unique(found, 'season_ids', SEASON)
                append_unique(found, 'program_ids', PROGRAM)
                append_unique(found, 'post_ids', post_id)
                append_unique(found, 'source_post_ids', post_id)
                append_unique(found, 'source_post_urls', exact['post_url'])
                if found.get('source_post_url') is None:
                    found['source_post_url'] = exact['post_url']
                found['published_at'] = exact['published_at']
            photo_id = found['photo_id']
        else:
            photo_id = 'fbphoto_' + fb_id
            failed = any(a.get('source_url') == source_url and a.get('status') in ('error','access_stopped') for a in attempts)
            record = {'photo_id': photo_id, 'facebook_photo_ids': [fb_id],
                      'local_path': None, 'source_url': source_url, 'source_urls': [source_url],
                      'source_photo_urls': item.get('source_photo_urls', []),
                      'source_post_url': exact['post_url'] if related else None,
                      'source_post_urls': [exact['post_url']] if related else [],
                      'post_ids': [post_id] if related else [], 'source_post_ids': [post_id] if related else [],
                      'season_ids': [SEASON] if related else [], 'program_ids': [PROGRAM] if related else [],
                      'journey_ids': [], 'published_at': exact['published_at'] if related else None,
                      'downloaded_at': None, 'imported_at': None,
                      'download_status': 'failed' if failed else 'not_downloaded',
                      'width': item.get('width'), 'height': item.get('height'), 'format': None,
                      'file_size': None, 'sha256': None, 'description': None, 'category': None,
                      'importance_score': None, 'rights_status': 'unknown',
                      'privacy_review_required': True, 'publication_status': 'not_reviewed',
                      'provenance': {'method': item.get('source_status'),
                                     'snapshot_path': item.get('provenance_snapshot'),
                                     'evidence': item.get('evidence', [])}}
            photos.append(record)
            photo_by_id[photo_id] = record
        if related and photo_id not in ids_in_program:
            ids_in_program.append(photo_id)
    write('data/raw/photos.json', photos)
    photo_by_id = {p['photo_id']: p for p in photos}
    # Rebuild photo index from the source table, retaining any video entries.
    other = [m for m in media_index if m.get('media_type') != 'photo']
    media_index = [{**p, 'media_id': p['photo_id'], 'media_type': 'photo'} for p in photos] + other
    videos = read('data/raw/videos.json', [])
    for video in videos:
        if not any(m.get('media_id') == video['video_id'] for m in media_index):
            media_index.append({**video, 'media_id': video['video_id'], 'media_type': 'video'})
    write('data/processed/media_index.json', media_index)
    write('data/unclassified/media.json', [m for m in media_index if not m.get('season_ids')])
    for photo_id in ids_in_program:
        append_unique(exact, 'photo_ids', photo_id)
    write('data/raw/posts.json', posts)
    write(f'data/raw/posts/{post_id}.json', exact)
    seasons = read('data/processed/seasons.json', [])
    programs = read('data/processed/programs.json', [])
    season = next(s for s in seasons if s['season_id'] == SEASON)
    program = next(p for p in programs if p['program_id'] == PROGRAM)
    for photo_id in ids_in_program:
        append_unique(season, 'photo_ids', photo_id)
        append_unique(program, 'photo_ids', photo_id)
    milestone = {'milestone_id':'milestone_season07_recap_20260820',
                 'title':'CHO EM đăng bài tổng kết Hành Trang Cho Em và mùa 7',
                 'date':'2026-08-20', 'date_precision':'day', 'season_ids':[SEASON],
                 'program_ids':[PROGRAM], 'post_ids':[post_id], 'photo_ids':ids_in_program,
                 'source_urls':[exact['post_url']], 'verification_status':'verified',
                 'research_notes':'Đây là ngày đăng bài tổng kết, không phải ngày kết thúc mùa đã được chứng minh.'}
    milestones = read('data/processed/milestones.json', [])
    if not any(m['milestone_id'] == milestone['milestone_id'] for m in milestones):
        milestones.append(milestone)
    write('data/processed/milestones.json', milestones)
    append_unique(season, 'milestone_ids', milestone['milestone_id'])
    write('data/processed/seasons.json', seasons)
    write('data/processed/programs.json', programs)
    timeline = read('data/processed/timeline.json', [])
    recap = {'event_id':'event_season07_recap_post_20260820',
             'title':'Bài tổng kết Hành Trang Cho Em và mùa 7',
             'event_date':'2026-08-20', 'date_precision':'day', 'event_type':'recap_post',
             'season_ids':[SEASON], 'program_ids':[PROGRAM], 'post_ids':[post_id],
             'photo_ids':ids_in_program, 'cover_photo_id':None,
             'description':'Dự án công bố kết quả chương trình và nhắc chặng đường mùa 7 khép lại.',
             'source_urls':[exact['post_url']], 'verification_status':'verified',
             'research_notes':'Đây là mốc đăng bài; không gán ngày này là ngày kết thúc mùa.'}
    if not any(e['event_id'] == recap['event_id'] for e in timeline):
        timeline.append(recap)
    timeline.sort(key=lambda e: e.get('event_date') or '9999')
    write('data/processed/timeline.json', timeline)
    stories = read('data/processed/stories.json', [])
    story = {'story_id':'story_hanh_trang_2026','title':'Hành Trang Cho Em tại Tà Long',
             'summary':'Mùa 7 tổ chức buổi giáo dục phòng chống đuối nước và trao tặng học liệu, áo phao vào 18/8/2026.',
             'season_ids':[SEASON], 'program_ids':[PROGRAM], 'post_ids':[post_id],
             'photo_ids':ids_in_program, 'source_urls':[exact['post_url']],
             'verification_status':'verified', 'privacy_review_required':True,
             'publication_status':'not_reviewed'}
    if not any(s['story_id']==story['story_id'] for s in stories):
        stories.append(story)
    write('data/processed/stories.json', stories)
    page = read('data/raw/page_info.json', {})
    page.update(page_id='100094610840245', page_url=archive.PAGE_URL,
                canonical_url='https://www.facebook.com/p/CHO-EM-project-100094610840245/',
                project_name='CHO EM project', category='Tổ chức từ thiện',
                description_original='Cho Em Project - Góp phần nhỏ vì một tương lai tươi sáng hơn của trẻ em Quảng Trị',
                location_display='Đông Hà, Quảng Trị',
                source_status='direct_public_browser_snapshot',
                source_url=archive.PAGE_URL,
                source_snapshot='research/sources/facebook_browser_02.html',
                verification_status='verified', collected_at=extraction['collected_at'])
    write('data/raw/page_info.json', page)
    project = read('data/processed/project_info.json', {})
    project.update(name='CHO EM project', tagline_original=page['description_original'],
                   locality_display='Đông Hà, Quảng Trị', source_urls=[archive.PAGE_URL],
                   verification_status='verified_for_name_tagline_and_location_only',
                   research_notes='Ngày thành lập, ý nghĩa tên gọi, sứ mệnh và tầm nhìn chính thức chưa được xác minh.')
    write('data/processed/project_info.json', project)
    folder = f'data/seasons/{SEASON}'
    write(f'{folder}/season_info.json', season)
    write(f'{folder}/posts.json', [p for p in posts if p['post_id'] in season['post_ids']])
    write(f'{folder}/programs.json', [program])
    write(f'{folder}/journeys.json', [])
    write(f'{folder}/timeline.json', [e for e in timeline if SEASON in e.get('season_ids', [])])
    write(f'{folder}/media_manifest.json', [photo_by_id[p] for p in season['photo_ids']])
    (ROOT / folder / 'season_story.md').write_text(
        '# CHO EM mùa 7 — hồ sơ hiện có\n\n'
        'Bài tổng kết của dự án xác nhận mùa 7 và chương trình **Hành Trang Cho Em** tại Trường Tiểu học Tà Long, Quảng Trị, ngày 18/8/2026. Nội dung tập trung vào giáo dục phòng chống tai nạn đuối nước. Dự án công bố trao 125 suất quà, 125 áo phao, hơn 100 quyển sách và 2 tủ sách.\n\n'
        f'Bài tổng kết được đăng ngày 20/8/2026 và nói chặng đường mùa 7 khép lại. Chưa xác định được ngày mở đầu, ngày kết thúc chính xác, chủ đề hoặc khẩu hiệu chính thức của mùa. Chỉ có {len(ids_in_program)} ảnh thuộc bài được nhận diện riêng; số ảnh hiển thị trong album không được xem là số ảnh đã tải.\n\n'
        f'Nguồn: {exact["post_url"]}\n', encoding='utf-8')
    (ROOT / folder / 'sources.md').write_text(
        '# Nguồn mùa 7\n\n'
        f'- Bài tổng kết công khai, caption gốc và snapshot: {exact["post_url"]}\n'
        '- Bằng chứng tại `research/sources/facebook_browser_02.html` và `research/evidence_map.json`.\n'
        '- Các bài 11–18/8 khác mới có đoạn hiển thị một phần, chưa tự gán vào mùa 7.\n', encoding='utf-8')
    (ROOT / 'data/unclassified/research_notes.md').write_text(
        '# Chưa phân loại\n\nCác bài Facebook còn lại mới có đoạn caption hiển thị; năm đăng và mùa liên quan chưa được xác minh trực tiếp. Album/ảnh không được gán mùa chỉ theo thời điểm xuất hiện. Hoạt động Sân chơi cho em tại Hướng Phùng năm 2024 do hai báo nêu được lưu làm đầu mối nghiên cứu trong `research/season_research_findings.json`, chưa gán vào trang Facebook chính xác.\n', encoding='utf-8')
    archive.checkpoint(ROOT, 'finalize-public-archive', {'manifest_photos':len(manifest),
                        'physical_facebook_photos':sum(p.get('download_status')=='downloaded' for p in photos),
                        'linked_season_photos':len(ids_in_program)})
    print(json.dumps({'photo_metadata':len(photos),'facebook_downloaded':sum(p.get('download_status')=='downloaded' for p in photos),
                      'season_photo_links':len(ids_in_program),'programs':len(programs),'timeline':len(timeline)}))


if __name__=='__main__':
    main()
