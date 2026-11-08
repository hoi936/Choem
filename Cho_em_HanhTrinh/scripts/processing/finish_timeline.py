#!/usr/bin/env python3
"""Add verified publication dates of archived posts without guessing event dates."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/collection'))
import archive

posts=archive.read_json(ROOT/'data/raw/posts.json',[])
events=archive.read_json(ROOT/'data/processed/timeline.json',[])
for post in posts:
    if post.get('post_type')=='video' or post.get('facebook_post_id')=='919178351245851':
        continue
    if not post.get('published_at') or not post.get('caption_original'):
        continue
    event_id='event_post_publication_'+str(post['facebook_post_id'])
    if any(e['event_id']==event_id for e in events):
        continue
    date=post['published_at'][:10]
    events.append({'event_id':event_id,'title':'Bài đăng: '+post.get('summary','CHO EM'),
                   'event_date':date,'date_precision':'day','event_type':'post_publication',
                   'description':'Ngày bài viết xuất hiện trên trang CHO EM; ngày này không mặc nhiên là ngày hoạt động được nhắc tới.',
                   'details':None,'season_ids':post.get('season_ids',[]),
                   'program_ids':post.get('program_ids',[]),'post_ids':[post['post_id']],
                   'photo_ids':post.get('photo_ids',[]),'video_ids':[],
                   'source_urls':[post['post_url']],'verification_status':'verified',
                   'season_link_status':'verified' if post.get('season_attribution_basis')=='explicit_season_mention' else ('inferred' if post.get('season_ids') else 'unknown')})
events.sort(key=lambda e:e.get('event_date') or '9999')
archive.atomic_json(ROOT/'data/processed/timeline.json',events)
archive.atomic_json(ROOT/'data/seasons/season_07/timeline.json',
                    [e for e in events if 'season_07' in e.get('season_ids',[])])
archive.checkpoint(ROOT,'finish-timeline',{'events':len(events)})
print(json.dumps({'timeline_events':len(events)}))
