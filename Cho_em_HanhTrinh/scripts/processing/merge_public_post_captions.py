#!/usr/bin/env python3
"""Merge complete messages from ordinary public post pages, preserving provenance."""
from __future__ import annotations

import glob
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/collection'))
import archive

SEASON='season_07'
PROGRAM='program_hanh_trang_cho_em_2026'


def read(path,default):
    return archive.read_json(ROOT/path,default)


def write(path,value):
    archive.atomic_json(ROOT/path,value)


def add(record,key,value):
    values=record.setdefault(key,[])
    if value not in values:values.append(value)


def main():
    paths=sorted(glob.glob(str(ROOT/'research/known_post_*_extraction.json')))
    posts=read('data/raw/posts.json',[])
    photos=read('data/raw/photos.json',[])
    seasons=read('data/processed/seasons.json',[])
    programs=read('data/processed/programs.json',[])
    season=next(s for s in seasons if s['season_id']==SEASON)
    program=next(p for p in programs if p['program_id']==PROGRAM)
    by_url={p['post_url']:p for p in posts}
    photo_by_fbid={fb:p for p in photos for fb in p.get('facebook_photo_ids',[])}
    matched=0
    for absolute in paths:
        path=Path(absolute)
        x=json.loads(path.read_text(encoding='utf-8'))
        for index,source in enumerate(x['posts']):
            url=archive.canonical_url(source['post_url'])
            post=by_url.get(url)
            if post is None:
                continue
            caption=source.get('caption_original')
            if not isinstance(caption,str):
                continue
            sha=hashlib.sha256(path.read_bytes()).hexdigest()
            post['facebook_post_id']=str(source['facebook_post_id'])
            post['facebook_post_ids']=list(dict.fromkeys([post['facebook_post_id'],source['facebook_post_id']]))
            post['published_at']=source['published_at']
            post['caption_original']=caption
            post['caption_clean']=re.sub(r'\s+',' ',caption).strip()
            post['caption_completeness']='complete'
            post['caption_status']='exact_message_text_as_delivered_in_snapshot'
            post['caption_evidence']=source['caption_evidence'][:1]
            post['hashtags']=re.findall(r'#[\w]+',caption,re.UNICODE)
            post['source_status']='direct_public_snapshot_json'
            post['verification_status']='verified'
            post['post_type']='photo' if source.get('photo_ids') else 'text'
            post['summary']=re.sub(r'\s+',' ',caption.split('\n',1)[0]).strip()
            post['provenance']={'method':'direct_public_snapshot_json',
                                'source_file':path.relative_to(ROOT).as_posix(),
                                'source_sha256':sha,
                                'json_pointer':f'/posts/{index}',
                                'caption_field':'caption_original',
                                'snapshot_path':source['caption_evidence'][0]['snapshot_path']}
            normalized=unicodedata.normalize('NFKC',caption).casefold()
            direct_season='mùa 7' in normalized
            direct_program='hành trang cho em' in normalized
            if direct_season or direct_program:
                add(post,'season_ids',SEASON)
                add(season,'post_ids',post['post_id'])
                post['season_attribution_basis']='explicit_season_mention' if direct_season else 'explicit_program_name_in_verified_season'
            if direct_program:
                add(post,'program_ids',PROGRAM)
                add(program,'post_ids',post['post_id'])
            if 'tà long' in normalized:
                add(post,'location_mentions','Trường Tiểu học Tà Long')
            for photo_fb in source.get('photo_ids',[]):
                photo=photo_by_fbid.get(photo_fb)
                if not photo:continue
                add(post,'photo_ids',photo['photo_id'])
                add(photo,'post_ids',post['post_id'])
                add(photo,'source_post_ids',post['post_id'])
                add(photo,'source_post_urls',post['post_url'])
                if photo.get('source_post_url') is None:photo['source_post_url']=post['post_url']
                photo['published_at']=source['published_at']
                if post['season_ids']:
                    add(photo,'season_ids',SEASON)
                    add(season,'photo_ids',photo['photo_id'])
                if post['program_ids']:
                    add(photo,'program_ids',PROGRAM)
                    add(program,'photo_ids',photo['photo_id'])
            matched+=1
    write('data/raw/posts.json',posts)
    for post in posts:
        write(f'data/raw/posts/{post["post_id"]}.json',post)
    write('data/unclassified/posts.json',[p for p in posts if not p.get('season_ids')])
    write('data/raw/photos.json',photos)
    media=read('data/processed/media_index.json',[])
    media=[{**p,'media_id':p['photo_id'],'media_type':'photo'} for p in photos]+[m for m in media if m.get('media_type')!='photo']
    write('data/processed/media_index.json',media)
    write('data/unclassified/media.json',[m for m in media if not m.get('season_ids')])
    write('data/processed/seasons.json',seasons)
    write('data/processed/programs.json',programs)
    discoveries=read('data/raw/discovered_urls.json',[])
    for item in discoveries:
        post=by_url.get(item['url'])
        if post:
            item['post_id']=post['post_id']
            item['pipeline']['content_extracted']=post['caption_completeness']=='complete'
            item['pipeline']['season_classified']=bool(post['season_ids'])
            item['pipeline']['verified']=post['verification_status']=='verified'
    write('data/raw/discovered_urls.json',discoveries)
    folder=f'data/seasons/{SEASON}'
    write(f'{folder}/season_info.json',season)
    write(f'{folder}/posts.json',[p for p in posts if p['post_id'] in season['post_ids']])
    write(f'{folder}/programs.json',[program])
    write(f'{folder}/media_manifest.json',[p for p in photos if p['photo_id'] in season['photo_ids']])
    archive.checkpoint(ROOT,'merge-public-post-captions',{'new_complete_captions':matched})
    print(json.dumps({'merged_complete_captions':matched,
                      'season_posts':len(season['post_ids']),'program_posts':len(program['post_ids']),
                      'season_photos':len(season['photo_ids'])}))


if __name__=='__main__':main()
