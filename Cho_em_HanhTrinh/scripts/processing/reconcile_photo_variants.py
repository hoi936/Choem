#!/usr/bin/env python3
"""Group larger delivered versions with their existing Facebook photo IDs."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/collection'))
import archive


def read(path,default):return archive.read_json(ROOT/path,default)
def write(path,value):archive.atomic_json(ROOT/path,value)


def replace_ref(items,old,new):
    result=[]
    for value in items:
        selected=new if value==old else value
        if selected not in result:result.append(selected)
    return result


def main():
    upgrades=read('research/media_upgrade_manifest.json',[])
    photos=read('data/raw/photos.json',[])
    posts=read('data/raw/posts.json',[])
    seasons=read('data/processed/seasons.json',[])
    programs=read('data/processed/programs.json',[])
    timeline=read('data/processed/timeline.json',[])
    stories=read('data/processed/stories.json',[])
    swaps=[]
    for item in upgrades:
        fbid=item['facebook_photo_id']
        old=next((p for p in photos if fbid in p.get('facebook_photo_ids',[]) and
                  item['source_url'] not in p.get('source_urls',[])),None)
        new=next((p for p in photos if item['source_url'] in p.get('source_urls',[])),None)
        if not old or not new:
            continue
        if not new.get('local_path') or not (ROOT/new['local_path']).is_file():
            continue
        if (new.get('width') or 0)*(new.get('height') or 0) <= (old.get('width') or 0)*(old.get('height') or 0):
            continue
        if fbid not in new.setdefault('facebook_photo_ids',[]):new['facebook_photo_ids'].append(fbid)
        new['variant_group_id']='fbphoto_'+fbid
        new['variant_role']='preferred'
        new['variant_selection_basis']='larger_public_version_delivered_in_direct_post_snapshot'
        old['variant_group_id']='fbphoto_'+fbid
        old['variant_role']='alternate'
        old['preferred_photo_id']=new['photo_id']
        for key in ('post_ids','source_post_ids','source_post_urls','season_ids','program_ids','journey_ids'):
            for value in old.get(key,[]):
                if value not in new.setdefault(key,[]):new[key].append(value)
        if not new.get('source_post_url'):new['source_post_url']=old.get('source_post_url')
        if not new.get('published_at'):new['published_at']=old.get('published_at')
        swaps.append((old['photo_id'],new['photo_id']))
    for photo in photos:
        if photo.get('facebook_photo_ids') and not photo.get('variant_role'):
            photo['variant_group_id']='fbphoto_'+photo['facebook_photo_ids'][0]
            photo['variant_role']='preferred'
    for table in (posts,seasons,programs,timeline,stories):
        for row in table:
            if 'photo_ids' in row:
                for old,new in swaps:
                    row['photo_ids']=replace_ref(row['photo_ids'],old,new)
    write('data/raw/photos.json',photos)
    write('data/raw/posts.json',posts)
    for post in posts:write(f'data/raw/posts/{post["post_id"]}.json',post)
    write('data/unclassified/posts.json',[p for p in posts if not p.get('season_ids')])
    write('data/processed/seasons.json',seasons)
    write('data/processed/programs.json',programs)
    write('data/processed/timeline.json',timeline)
    write('data/processed/stories.json',stories)
    media=[{**p,'media_id':p['photo_id'],'media_type':'photo'} for p in photos]
    media += [{**v,'media_id':v['video_id'],'media_type':'video'} for v in read('data/raw/videos.json',[])]
    write('data/processed/media_index.json',media)
    write('data/unclassified/media.json',[m for m in media if not m.get('season_ids')])
    folder='data/seasons/season_07'
    season=next(s for s in seasons if s['season_id']=='season_07')
    write(f'{folder}/season_info.json',season)
    write(f'{folder}/posts.json',[p for p in posts if p['post_id'] in season['post_ids']])
    write(f'{folder}/programs.json',[p for p in programs if p['program_id'] in season['program_ids']])
    write(f'{folder}/timeline.json',[e for e in timeline if 'season_07' in e.get('season_ids',[])])
    by_id={p['photo_id']:p for p in photos}
    write(f'{folder}/media_manifest.json',[by_id[p] for p in season['photo_ids']])
    groups={}
    for p in photos:
        for fb in p.get('facebook_photo_ids',[]):
            group=groups.setdefault(fb,{'facebook_photo_id':fb,'photo_ids':[],'preferred_photo_id':None})
            if p['photo_id'] not in group['photo_ids']:group['photo_ids'].append(p['photo_id'])
            if p.get('variant_role')=='preferred':group['preferred_photo_id']=p['photo_id']
    write('research/media_variant_groups.json',list(groups.values()))
    archive.checkpoint(ROOT,'reconcile-photo-variants',{'upgraded':len(swaps),'unique_facebook_photos':len(groups)})
    print(json.dumps({'upgraded':len(swaps),'unique_facebook_photos':len(groups),
                      'physical_facebook_files':sum(p.get('download_status')=='downloaded' for p in photos)}))


if __name__=='__main__':main()
