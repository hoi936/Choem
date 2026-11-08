#!/usr/bin/env python3
"""Add conservative media categories and internal, unpublished display candidates."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/collection'))
import archive


def read(path,default):return archive.read_json(ROOT/path,default)
def write(path,value):archive.atomic_json(ROOT/path,value)


RECAP={
 '919178064579213':('Ảnh tập thể nhóm tham gia trước một khuôn viên trường; dải logo đơn vị đồng hành nằm phía dưới.','volunteer_group', ['homepage_hero','season_cover'], [4,5,3,4,5,4,4]),
 '919177997912553':('Màn hình giới thiệu Hành Trang Cho Em, nêu ngày 18/8/2026 và Trường Tiểu học Tà Long.','program_opening', ['program_cover','timeline_image'], [5,5,2,3,5,4,4]),
 '919178047912548':('Cổng Trường Tiểu học Tà Long, có tên trường và địa bàn hiển thị trên biển.','documented_location', ['timeline_image'], [4,4,1,3,5,4,3]),
 '919178101245876':('Các túi quà mang nhãn Hành Trang Cho Em được sắp xếp trước khi trao.','gift_preparation', ['gallery_featured','story_image'], [4,5,3,3,5,4,4]),
 '919178007912552':('Một người mặc áo xanh tương tác với nhóm học sinh trong lớp; có gương mặt trẻ em.','activity_with_children', ['story_image'], [5,5,5,3,5,4,4]),
}
CRITERIA=['historical_value','season_representativeness','human_value','project_development','source_quality','image_quality','website_suitability']


def main():
    photos=read('data/raw/photos.json',[])
    posts={p['post_id']:p for p in read('data/raw/posts.json',[])}
    featured=[]
    for p in photos:
        fbids=p.get('facebook_photo_ids',[])
        if p.get('local_sources') and not fbids:
            p['category']='unverified_project_mark'
            p['description']='Ảnh có sẵn trong thư mục dự án, chứa chữ CHO EM PROJECT; nguồn và vai trò logo chính thức chưa rõ.'
            p['classification_basis']='local_visual_inspection'
        elif fbids and fbids[0] in RECAP:
            description, category, roles, scores=RECAP[fbids[0]]
            p.update(description=description,category=category,classification_basis='visual_inspection_and_source_post',
                     importance_score=max(1,min(5,round(sum(scores)/len(scores)))))
            if fbids[0]=='919178007912552':p['children_visible']=True
            featured.append({'media_id':p['photo_id'],'photo_id':p['photo_id'],'facebook_photo_id':fbids[0],
                             'roles':roles,'reason':description,
                             'scores':dict(zip(CRITERIA,scores)),
                             'source_post_ids':p.get('post_ids',[]),
                             'selection_status':'internal_candidate_pending_rights_and_privacy_review',
                             'approved_for_publication':False,
                             'privacy_review_required':True})
        elif p.get('post_ids'):
            title=' '.join(posts[x].get('summary','') for x in p['post_ids'] if x in posts).casefold()
            if 'tri ân' in title or 'cảm ơn nhà tài trợ' in title:
                p['category']='sponsor_post_media'
            elif 'quyên góp sách' in title:
                p['category']='book_appeal_media'
            else:
                p['category']='post_media_unclassified'
            p['classification_basis']='source_post_context_not_full_visual_review'
        else:
            p['category']='page_gallery_unclassified'
            p['classification_basis']='page_gallery_without_post_link'
        p['rights_status']=p.get('rights_status') or 'unknown'
        p['privacy_review_required']=True
    write('data/raw/photos.json',photos)
    media=[{**p,'media_id':p['photo_id'],'media_type':'photo'} for p in photos]
    media += [{**v,'media_id':v['video_id'],'media_type':'video'} for v in read('data/raw/videos.json',[])]
    write('data/processed/media_index.json',media)
    write('data/unclassified/media.json',[m for m in media if not m.get('season_ids')])
    write('data/processed/featured_content.json',featured)
    season=next(s for s in read('data/processed/seasons.json',[]) if s['season_id']=='season_07')
    by_id={p['photo_id']:p for p in photos}
    write('data/seasons/season_07/media_manifest.json',[by_id[photo_id] for photo_id in season['photo_ids']])
    for category in ('covers','preparation','activities','journeys','highlights','closing'):
        (ROOT/'assets/seasons/season_07'/category).mkdir(parents=True,exist_ok=True)
    archive.checkpoint(ROOT,'review-media-candidates',{'internal_candidates':len(featured),
                        'approved_for_publication':0})
    print(json.dumps({'internal_candidates':len(featured),'approved_for_publication':0}))


if __name__=='__main__':main()
