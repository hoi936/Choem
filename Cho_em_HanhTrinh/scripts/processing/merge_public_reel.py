#!/usr/bin/env python3
"""Archive the public Reel caption while keeping the video file unavailable."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/collection'))
import archive


def read(path,default):return archive.read_json(ROOT/path,default)
def write(path,value):archive.atomic_json(ROOT/path,value)
def add(obj,key,value):
    obj.setdefault(key,[])
    if value not in obj[key]:obj[key].append(value)


def main():
    source=ROOT/'research/facebook_reel_extraction.json'
    x=json.loads(source.read_text(encoding='utf-8'))
    p=x['posts'][0]
    reel_url='https://www.facebook.com/reel/1411736247503742/'
    video_id='video_1411736247503742'
    norm=ROOT/'research/normalized_public_reel.json'
    write('research/normalized_public_reel.json',{'posts':[{'facebook_post_id':p['facebook_post_id'],
         'post_url':reel_url,'published_at':p['published_at'],'caption_original':p['caption_original'],
         'caption_completeness':'complete','post_type':'video','season_ids':['season_07'],
         'program_ids':['program_hanh_trang_cho_em_2026'],'video_ids':[video_id],
         'location_mentions':['Trường Tiểu học Tà Long','Quảng Trị']} ]})
    with archive.archive_lock(ROOT):
        archive.import_export(ROOT,norm,requested_format='auto')
    posts=read('data/raw/posts.json',[])
    post=next(item for item in posts if item['post_url']==archive.canonical_url(reel_url))
    post.update(source_status='direct_public_snapshot_json',verification_status='verified',
                caption_evidence=p['caption_evidence'][:1],caption_status='exact_message_text_as_delivered_in_snapshot',
                source_role='public_reel', season_attribution_basis='matching_program_topic_location_one_day_before_event',
                season_link_status='inferred', program_link_status='inferred',
                summary='Các thành viên chuẩn bị đến Trường Tiểu học Tà Long để tuyên truyền phòng chống đuối nước.',
                caption_clean=re.sub(r'\s+',' ',p['caption_original']).strip(),
                hashtags=p.get('hashtags',[]),
                provenance={'method':'direct_public_snapshot_json','source_file':'research/facebook_reel_extraction.json',
                            'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                            'json_pointer':'/posts/0','caption_field':'caption_original',
                            'snapshot_path':p['caption_evidence'][0]['snapshot_path']})
    write('data/raw/posts.json',posts)
    write(f'data/raw/posts/{post["post_id"]}.json',post)
    videos=read('data/raw/videos.json',[])
    video=next(v for v in videos if v['video_id']==video_id)
    video.update(published_at=p['published_at'],caption_original=p['caption_original'],
                 caption_completeness='complete',caption_evidence=p['caption_evidence'][:1],
                 source_status='direct_public_snapshot_json',season_ids=['season_07'],
                 program_ids=['program_hanh_trang_cho_em_2026'],post_id=post['post_id'],
                 post_ids=[post['post_id']],source_post_ids=[post['post_id']],
                 source_snapshot='research/sources/facebook_reel_browser.html',
                 season_link_status='inferred',program_link_status='inferred')
    write('data/raw/videos.json',videos)
    media=read('data/processed/media_index.json',[])
    media=[{**video,'media_id':video_id,'media_type':'video'} if m.get('media_id')==video_id else m for m in media]
    write('data/processed/media_index.json',media)
    write('data/unclassified/media.json',[m for m in media if not m.get('season_ids')])
    seasons=read('data/processed/seasons.json',[])
    programs=read('data/processed/programs.json',[])
    season=next(s for s in seasons if s['season_id']=='season_07')
    program=next(a for a in programs if a['program_id']=='program_hanh_trang_cho_em_2026')
    add(season,'post_ids',post['post_id'])
    add(season,'video_ids',video_id)
    add(program,'post_ids',post['post_id'])
    add(program,'video_ids',video_id)
    write('data/processed/seasons.json',seasons)
    write('data/processed/programs.json',programs)
    folder='data/seasons/season_07'
    write(f'{folder}/season_info.json',season)
    write(f'{folder}/posts.json',[q for q in posts if q['post_id'] in season['post_ids']])
    write(f'{folder}/programs.json',[program])
    write('data/unclassified/posts.json',[q for q in posts if not q.get('season_ids')])
    timeline=read('data/processed/timeline.json',[])
    event={'event_id':'event_reel_departure_20260817','title':'Reel chuẩn bị chương trình tại Tà Long',
           'event_date':'2026-08-17','date_precision':'day','event_type':'reel_publication',
           'description':'Reel đăng trước chương trình, nói về việc chuẩn bị đến trường để tuyên truyền phòng chống đuối nước.',
           'season_ids':['season_07'],'program_ids':['program_hanh_trang_cho_em_2026'],
           'post_ids':[post['post_id']],'video_ids':[video_id],'photo_ids':[],
           'source_urls':[reel_url],'verification_status':'verified',
           'season_link_status':'inferred','research_notes':'Ngày là ngày Reel đăng; không suy thành ngày khởi hành.'}
    if not any(e['event_id']==event['event_id'] for e in timeline):timeline.append(event)
    timeline.sort(key=lambda e:e.get('event_date') or '9999')
    write('data/processed/timeline.json',timeline)
    write(f'{folder}/timeline.json',[e for e in timeline if 'season_07' in e.get('season_ids',[])])
    archive.checkpoint(ROOT,'merge-public-reel',{'reel_caption_complete':True})
    print(json.dumps({'post_id':post['post_id'],'video_id':video_id,'caption_chars':len(p['caption_original'])}))


if __name__=='__main__':main()
