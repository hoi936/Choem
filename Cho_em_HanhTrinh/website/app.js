/**
 * DỰ ÁN CHO EM (2023 – 2026) — INTERACTIVE ARCHIVE APPLICATION
 * Consumes normalized `window.CHO_EM_ARCHIVE` from `website/data/archive_bundle.js`
 */

(function () {
  'use strict';

  const archive = window.CHO_EM_ARCHIVE;
  if (!archive || !Array.isArray(archive.seasons)) {
    console.error('Không tìm thấy dữ liệu window.CHO_EM_ARCHIVE.');
    return;
  }

  /* --------------------------------------------------------------------------
     1. VIETNAMESE UNICODE SAFETY NORMALIZER & QUOTE HIGHLIGHT FORMATTER
     -------------------------------------------------------------------------- */

  function cleanText(input) {
    if (!input) return '';
    return String(input)
      .normalize('NFKC')
      .replace(/[\u200B-\u200D\uFEFF\uFE0E\uFE0F]/g, '')
      .replace(/^[-\s_—–=]{4,}$/gm, '')
      .replace(/"([^"\n]{1,120})"/g, '“$1”')
      .replace(/(?<!\w)'([^'\n]{2,120})'(?!\w)/g, '“$1”')
      .replace(/\n{3,}/g, '\n\n')
      .normalize('NFC')
      .trim();
  }

  function escapeHtml(str) {
    return cleanText(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  /**
   * Escapes text and highlights any phrase inside typographic quotes “...”
   * with <em class="quote-highlight">“...”</em> (italic + accent color).
   */
  function formatRichText(str) {
    const escaped = escapeHtml(str);
    return escaped.replace(/“([^”]+)”/g, '<em class="quote-highlight">“$1”</em>');
  }

  function formatViDate(isoStr) {
    if (!isoStr) return 'Tư liệu lưu trữ';
    const d = new Date(isoStr);
    if (Number.isNaN(d.getTime())) return cleanText(isoStr);
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    return `${day}/${month}/${year}`;
  }

  function formatSeasonDuration(s) {
    if (s.duration_label) return cleanText(s.duration_label);
    if (s.start_date && s.end_date) {
      return `${formatViDate(s.start_date)} – ${formatViDate(s.end_date)}`;
    }
    if (s.event_date) return formatViDate(s.event_date);
    return '2023 – 2026';
  }

  function formatShortMonthYear(isoStr) {
    if (!isoStr) return '';
    const d = new Date(isoStr);
    if (Number.isNaN(d.getTime())) return cleanText(isoStr);
    const month = String(d.getMonth() + 1).padStart(2, '0');
    return `Tháng ${month}/${d.getFullYear()}`;
  }

  function formatMetricValue(metricObj) {
    if (!metricObj) return '';
    const val = metricObj.value;
    const label = cleanText(metricObj.metric || '');
    if (typeof val === 'number') {
      const formattedNum = val.toLocaleString('vi-VN');
      if (val >= 100000) {
        return `${formattedNum} VNĐ`;
      }
      return `${formattedNum} ${label}`;
    }
    return `${cleanText(val)} ${label}`.trim();
  }

  /* --------------------------------------------------------------------------
     2. FLATTENED GLOBAL INDEXES (563 PHOTOS, 135 POSTS, 8 VIDEOS)
     -------------------------------------------------------------------------- */

  const seasons = archive.seasons;
  const allPhotos = [];
  const allPosts = [];
  const allVideos = [];
  const postLookup = new Map();
  const photoByPath = new Map();

  function getImgCropClass(photoPath) {
    const ph = photoByPath.get(photoPath);
    return ph && ph.has_bottom_banner ? 'crop-bottom-banner' : '';
  }

  seasons.forEach((season) => {
    const locationStr = (season.locations || []).join(' · ');
    (season.resolved_posts || []).forEach((post) => {
      const enrichedPost = {
        ...post,
        title_clean: cleanText(post.title_clean || post.summary || season.official_name),
        body_clean: cleanText(post.body_clean || post.caption_original || season.description),
        category_id: post.category_id || 'recap',
        category_label: cleanText(post.category_label || 'Tổng kết & ký sự'),
        hashtags: Array.isArray(post.hashtags) ? post.hashtags : [],
        season_id: season.season_id,
        season_number: season.season_number,
        season_name: cleanText(season.official_name),
        season_locations: cleanText(locationStr),
      };
      allPosts.push(enrichedPost);
      postLookup.set(post.post_id, enrichedPost);
    });

    (season.resolved_photos || []).forEach((photo) => {
      const parentPost = photo.post_id ? postLookup.get(photo.post_id) : null;
      const enrichedPhoto = {
        ...photo,
        title_clean: cleanText(
          photo.title_clean ||
            (parentPost && parentPost.title_clean) ||
            `${season.official_name} — ${season.theme}`
        ),
        description: cleanText(
          photo.description ||
            (parentPost && parentPost.body_clean) ||
            season.description
        ),
        category_id: photo.category_id || (parentPost && parentPost.category_id) || 'recap',
        category_label: cleanText(
          photo.category_label || (parentPost && parentPost.category_label) || 'Hình ảnh chuyến đi'
        ),
        hashtags: (parentPost && parentPost.hashtags) || [],
        post_url: (parentPost && parentPost.post_url) || 'https://www.facebook.com/profile.php?id=100094610840245',
        season_id: season.season_id,
        season_number: season.season_number,
        season_name: cleanText(season.official_name),
        season_theme: cleanText(season.theme),
        season_locations: cleanText(locationStr),
      };
      allPhotos.push(enrichedPhoto);
      photoByPath.set(enrichedPhoto.local_path, enrichedPhoto);
    });

    (season.resolved_videos || []).forEach((video, vIdx) => {
      const seasonPhotos = season.resolved_photos || [];
      const fallbackPoster =
        (seasonPhotos[vIdx] && seasonPhotos[vIdx].local_path) ||
        season.hero_photo ||
        'Ảnh/Anh1.jpg';
      allVideos.push({
        ...video,
        poster_photo: fallbackPoster,
        title_clean: cleanText(video.title_clean || season.official_name),
        body_clean: cleanText(video.body_clean || video.caption_original || season.description),
        season_id: season.season_id,
        season_number: season.season_number,
        season_name: cleanText(season.official_name),
        season_locations: cleanText(locationStr),
      });
    });
  });

  /* --------------------------------------------------------------------------
     3. APPLICATION STATE
     -------------------------------------------------------------------------- */

  const state = {
    activeSeasonIndex: 0,
    seasonSubTab: 'photos', // 'photos' | 'posts' | 'activities' | 'videos'
    seasonPostCategory: 'all',
    seasonPhotoLimit: 12,
    timelineYear: 'all',
    timelineExpanded: false,
    archiveMode: 'photos', // 'photos' | 'posts'
    archiveSeason: 'all',
    archiveCategory: 'all',
    archiveQuery: '',
    archiveLimit: 20,
    lightboxList: allPhotos,
    lightboxIndex: 0,
  };

  /* --------------------------------------------------------------------------
     4. HERO SECTION & TOP LEDGER INITIALIZATION
     -------------------------------------------------------------------------- */

  function renderHeroSection() {
    const stats = archive.stats || {};
    const setStat = (id, val) => {
      const el = document.getElementById(id);
      if (el && val !== undefined) el.textContent = String(val).padStart(2, '0');
    };
    setStat('stat-seasons', stats.total_seasons || 7);
    setStat('stat-posts', stats.total_posts || 135);
    setStat('stat-photos', stats.total_photos || 563);
    setStat('stat-videos', stats.total_videos || 8);

    const collageEl = document.getElementById('hero-collage');
    if (!collageEl) return;

    const s7 = seasons[6] || seasons[0];
    const s1 = seasons[0];
    const s6 = seasons[5] || seasons[2] || seasons[0];

    const heroCards = [
      {
        featured: true,
        seasonIndex: 6,
        badge: `MÙA 7 · ${formatShortMonthYear(s7.event_date || s7.start_date).toUpperCase()} · ĐAKRÔNG`,
        photo: s7.hero_photo,
        title: `${cleanText(s7.official_name)} — 125 áo phao & 02 tủ sách tri thức tại Tiểu học Tà Long`,
        meta: cleanText((s7.locations && s7.locations[0]) || 'Điểm trường Pa Hy — Tiểu học Tà Long, huyện Đakrông, Quảng Trị'),
      },
      {
        featured: false,
        seasonIndex: 0,
        badge: `MÙA 1 · ${formatShortMonthYear(s1.event_date || s1.start_date).toUpperCase()}`,
        photo: s1.hero_photo,
        title: `${cleanText(s1.official_name)} — 02 sân chơi tái chế tại bản Ho Le & Tà Rùng`,
        meta: cleanText((s1.locations && s1.locations[0]) || 'Xã Húc, huyện Hướng Hóa, tỉnh Quảng Trị'),
      },
      {
        featured: false,
        seasonIndex: 5,
        badge: `MÙA 6 · ${formatShortMonthYear(s6.event_date || s6.start_date).toUpperCase()}`,
        photo: s6.hero_photo,
        title: `${cleanText(s6.official_name)} — Áo ấm mùa đông & kỹ năng sơ cứu tại Vĩnh Ô`,
        meta: cleanText((s6.locations && s6.locations[0]) || 'Trường PTDTBT Tiểu học Vĩnh Ô, huyện Vĩnh Linh, Quảng Trị'),
      },
    ];

    collageEl.innerHTML = heroCards
      .map(
        (card) => `
        <article class="hero-field-card ${card.featured ? 'featured' : ''}" data-jump-season="${card.seasonIndex}" tabindex="0" role="button" aria-label="Xem chi tiết ${escapeHtml(card.title)}">
          <div class="hero-card-media">
            <img src="${escapeHtml(card.photo)}" alt="${escapeHtml(card.title)}" class="${getImgCropClass(card.photo)}" loading="eager" />
            <span class="hero-card-badge">${escapeHtml(card.badge)}</span>
          </div>
          <div class="hero-card-footer">
            <h2 class="hero-card-title">${formatRichText(card.title)}</h2>
            <p class="hero-card-meta">${escapeHtml(card.meta)}</p>
          </div>
        </article>
      `
      )
      .join('');

    collageEl.querySelectorAll('[data-jump-season]').forEach((cardEl) => {
      const activate = () => {
        const idx = Number(cardEl.getAttribute('data-jump-season')) || 0;
        selectSeason(idx, true);
      };
      cardEl.addEventListener('click', activate);
      cardEl.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          activate();
        }
      });
    });
  }

  /* --------------------------------------------------------------------------
     5. CHƯƠNG 01: SỨ MỆNH, CHIẾT TỰ "CHO EM" & 4 THẾ HỆ BAN TỔ CHỨC
     -------------------------------------------------------------------------- */

  function renderMissionHeritage() {
    const info = archive.project_info || {};

    // 5-letter Acrostic C - H - O - E - M
    const acrosticEl = document.getElementById('acrostic-list');
    if (acrosticEl) {
      const poem =
        (info.name_meaning && info.name_meaning.acrostic_poem) || [
          { letter: 'C', line: 'Chia sẻ hơi ấm từ những trái tim biết yêu thương.' },
          { letter: 'H', line: 'Hướng về những mảnh đời nhỏ bé còn nhiều thiệt thòi.' },
          { letter: 'O', line: 'Ôm ấp ước mơ trong trẻo của các em bằng sự sẻ chia.' },
          { letter: 'E', line: 'Em là mầm xanh xứng đáng được chở che và tiếp sức.' },
          { letter: 'M', line: 'Mang hy vọng đến gần hơn với tuổi thơ vùng cao.' },
        ];

      acrosticEl.innerHTML = poem
        .map(
          (item) => `
          <div class="acrostic-row">
            <span class="acrostic-char" aria-hidden="true">${escapeHtml(item.letter)}</span>
            <p class="acrostic-text"><em class="quote-highlight">“${escapeHtml(item.letter)}”</em> — ${formatRichText(item.line)}</p>
          </div>
        `
        )
        .join('');
    }

    // 3 Evolution Stages (Natural, warm Vietnamese wording)
    const stagesEl = document.getElementById('evolution-stages');
    if (stagesEl) {
      const stages = [
        {
          stage: 'Chặng 1 · Những viên gạch đầu tiên & sân chơi tái chế (2023)',
          seasons: 'MÙA 1 (“SÂN CHƠI CHO EM” · 07–08/2023)',
          focus: 'Bắt đầu từ ngày 17/07/2023 tại Đông Hà, các thành viên đã tự làm nơ thủ công và vận động quyên góp được 27.381.403 VNĐ để tự tay sơn vẽ, lắp đặt 02 sân chơi từ lốp xe cũ cho các em nhỏ bản Ho Le và bản Tà Rùng (xã Húc, Hướng Hóa).',
        },
        {
          stage: 'Chặng 2 · Vừa trao quà, vừa dạy kỹ năng cho các em (2024)',
          seasons: 'MÙA 2 (“RĂNG XINH CHO EM”) · MÙA 3 · MÙA 4 (“PHAO XINH CHO EM”)',
          focus: 'Mở rộng hành trình từ vùng biển bãi ngang Triệu Vân lên miền núi Hướng Phùng (Chênh Vênh, Hướng Choa), kết hợp dựng sân chơi với các vở kịch vui nhộn hướng dẫn chăm sóc răng miệng “Răng xinh cho em” và phòng tránh đuối nước “Phao xinh cho em”.',
        },
        {
          stage: 'Chặng 3 · Trang bị kỹ năng an toàn & tiếp sức đến trường (2025 – 2026)',
          seasons: 'MÙA 5 (“AN TOÀN CHO EM”) · MÙA 6 · MÙA 7 (“HÀNH TRANG CHO EM”)',
          focus: 'Tổ chức chuỗi buổi học trực quan về sơ cứu và tự bảo vệ bản thân “An toàn cho em” tại Tân Thành (Hướng Hóa), Vĩnh Ô (Vĩnh Linh) và mang chương trình “Hành trang cho em” cùng tủ sách thiếu nhi lên điểm trường Pa Hy — Tiểu học Tà Long (Đakrông).',
        },
      ];

      stagesEl.innerHTML = stages
        .map(
          (st) => `
          <article class="stage-card">
            <div class="stage-meta">${escapeHtml(st.seasons)}</div>
            <h4 class="stage-title">${formatRichText(st.stage)}</h4>
            <p class="stage-desc">${formatRichText(st.focus)}</p>
          </article>
        `
        )
        .join('');
    }

    // 4 Core Values (Simple, relatable Vietnamese wording)
    const valuesEl = document.getElementById('core-values-grid');
    if (valuesEl) {
      const values = [
        {
          title: 'Tự tay làm từng phần việc',
          description: 'Các thành viên trực tiếp đi tiền trạm, tự sơn từng chiếc lốp xe, tập từng vở kịch nhỏ và lên tận điểm trường lắp đặt cùng thầy cô.',
        },
        {
          title: 'Rõ ràng trong từng khoản thu chi',
          description: 'Mọi khoản tiền từ bán đồ thủ công, gian hàng gây quỹ và sự ủng hộ của các nhà hảo tâm đều được công khai minh bạch sau mỗi mùa.',
        },
        {
          title: 'Trao kiến thức đi cùng quà tặng',
          description: 'Không chỉ tặng quà, dự án luôn lồng ghép các buổi hướng dẫn vệ sinh cá nhân, sơ cứu vết thương và phòng tránh đuối nước dễ nhớ cho trẻ.',
        },
        {
          title: 'Bốn thế hệ học sinh nối tiếp nhau',
          description: 'Khi khóa anh chị ra trường, khóa đàn em lại tiếp nhận và giữ lửa dự án suốt từ mùa hè năm 2023 đến năm 2026.',
        },
      ];

      valuesEl.innerHTML = values
        .map(
          (v) => `
          <div class="value-card">
            <h4 class="value-title">${formatRichText(v.title)}</h4>
            <p class="value-desc">${formatRichText(v.description)}</p>
          </div>
        `
        )
        .join('');
    }

    // 4 Leadership Generations with real student leader names & curated photo headers
    const gensEl = document.getElementById('generations-grid');
    if (gensEl) {
      const gens = [
        {
          seasonIdx: 0,
          photo: 'assets/originals/images/9844d396e4a5c67492bea7d86eb63dafc975d0c616c8d2f7b2d931c11628a910.jpg',
          badge: 'THẾ HỆ SÁNG LẬP · 2023 – ĐẦU 2024',
          title: 'Mùa 1 & mùa 2 — Đặt viên gạch đầu tiên',
          period: 'Bản Ho Le, Tà Rùng (xã Húc) & xã Triệu Vân',
          focus: 'Khởi lập dự án ngày 17/07/2023 dưới sự bảo trợ của Thành đoàn Đông Hà, tự thi công 02 sân chơi tái chế đầu tiên và mang vở kịch “Răng xinh cho em” về vùng biển bãi ngang.',
          leaders: [
            { name: 'Trần Ngọc Tâm Phúc', role: 'Sáng lập & Quản lý dự án (Founder)' },
            { name: 'Nguyễn Thùy Linh', role: 'Trưởng ban Truyền thông' },
          ],
        },
        {
          seasonIdx: 2,
          photo: 'assets/originals/images/9e0e3c10cbe01ac5805ade5c52cc6554bca269eee8a9a8e85e369ceb3309f54d.jpg',
          badge: 'THẾ HỆ MỞ RỘNG · HÈ 2024 – ĐẦU 2025',
          title: 'Mùa 3 & mùa 4 — Vươn xa lên đỉnh đèo & biển cát',
          period: 'Chênh Vênh, Hướng Choa (Hướng Phùng) & Triệu Vân',
          focus: 'Tiếp nối ngọn lửa của thế hệ anh chị, khánh thành thêm 02 sân chơi tái chế hoàn chỉnh tại Hướng Phùng và mở đầu chuỗi kỹ năng phòng chống đuối nước “Phao xinh cho em”.',
          leaders: [
            { name: 'Lê Thị Thúy Như', role: 'Trưởng Ban tổ chức' },
            { name: 'Nguyễn Văn Linh', role: 'Đồng Trưởng Ban tổ chức' },
            { name: 'Trần Thiên Hương', role: 'Trưởng ban Truyền thông' },
          ],
        },
        {
          seasonIdx: 4,
          photo: 'assets/originals/images/s5_tan_thanh_03.jpg',
          badge: 'THẾ HỆ CHUYÊN SÂU · MÙA HÈ 2025',
          title: 'Mùa 5 — Chuyên đề kỹ năng “An toàn cho em”',
          period: 'Trường TH&THCS Tân Thành (Hướng Hóa)',
          focus: 'Dưới sự đồng hành của Đoàn trường THPT Chuyên Lê Quý Đôn và cô cố vấn Nguyễn Thị Thanh Huyền, mang lớp học sơ cứu trực quan cùng 100 đôi giày mới lên biên giới Tân Thành.',
          leaders: [
            { name: 'Trần Mai Hương Nguyên', role: 'Trưởng Ban tổ chức' },
            { name: 'Trần Thiên Hương', role: 'Trưởng ban Truyền thông' },
            { name: 'Đậu Khắc Gia Bảo', role: 'Phụ trách Tài chính' },
          ],
        },
        {
          seasonIdx: 6,
          photo: 'assets/originals/images/6ecca86af231ae5f30c18bb9c07ac7d09cb3c6b5854115f0034bde28a5d5e398.jpg',
          badge: 'THẾ HỆ KẾ THỪA · CUỐI 2025 – 2026',
          title: 'Mùa 6 & mùa 7 — Lá chắn an toàn & tủ sách đại ngàn',
          period: 'Xã vùng sâu Vĩnh Ô (Vĩnh Linh) & Tà Long (Đakrông)',
          focus: 'Vượt đèo mùa đông mang áo ấm, bộ sơ cứu lên Vĩnh Ô và trao tặng 125 áo phao cứu sinh cùng 02 “Tủ sách tri thức” (345 đầu sách) cho học sinh điểm trường Tà Long.',
          leaders: [
            { name: 'Lê Khánh Linh', role: 'Trưởng Ban tổ chức' },
            { name: 'Phan Thanh Huyền', role: 'Phó Ban tổ chức' },
            { name: 'Võ Ngọc Gia Linh', role: 'Điều phối Hậu cần & Hiện vật' },
          ],
        },
      ];

      gensEl.innerHTML = gens
        .map(
          (g) => `
          <article class="gen-card" data-jump-season="${g.seasonIdx}" tabindex="0" role="button" aria-label="Xem hành trình của ${escapeHtml(g.title)}">
            <div class="gen-card-thumb">
              <img src="${escapeHtml(g.photo)}" alt="${escapeHtml(g.title)}" class="${getImgCropClass(g.photo)}" loading="lazy" />
            </div>
            <div class="gen-card-body">
              <span class="gen-badge">${escapeHtml(g.badge)}</span>
              <h4 class="gen-title">${formatRichText(g.title)}</h4>
              <span class="gen-period">${escapeHtml(g.period)}</span>
              <p class="gen-focus">${formatRichText(g.focus)}</p>
              <div class="gen-leaders-list">
                ${g.leaders
                  .map(
                    (l) =>
                      `<div class="gen-leader-row">• <strong>${escapeHtml(l.name)}</strong> — ${escapeHtml(l.role)}</div>`
                  )
                  .join('')}
              </div>
            </div>
          </article>
        `
        )
        .join('');

      gensEl.querySelectorAll('[data-jump-season]').forEach((cardEl) => {
        const activate = () => {
          const idx = Number(cardEl.getAttribute('data-jump-season')) || 0;
          selectSeason(idx, true);
        };
        cardEl.addEventListener('click', activate);
        cardEl.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            activate();
          }
        });
      });
    }

    // Interactive Footprint Route Across 8 Schools in 4 Districts of Quang Tri
    const footprintEl = document.getElementById('footprint-grid');
    if (footprintEl) {
      const regions = [
        {
          regionTag: 'VÙNG NÚI BIÊN GIỚI PHÍA TÂY',
          distance: '~65 – 85 km từ Đông Hà',
          district: 'Huyện Hướng Hóa (5 điểm trường)',
          schools: [
            'Điểm trường Bản Ho Le — Mầm non Húc (Mùa 1)',
            'Điểm trường Bản Tà Rùng — Mầm non Húc (Mùa 1)',
            'Điểm trường Bản Chênh Vênh — Mầm non Hướng Phùng (Mùa 3)',
            'Điểm trường Bản Hướng Choa — Mầm non Hướng Phùng (Mùa 3)',
            'Trường TH&THCS Tân Thành (Mùa 5)',
          ],
          seasons: [
            { label: 'Mùa 1 (Xã Húc) →', idx: 0 },
            { label: 'Mùa 3 (Hướng Phùng) →', idx: 2 },
            { label: 'Mùa 5 (Tân Thành) →', idx: 4 },
          ],
        },
        {
          regionTag: 'VÙNG CÁT BÃI NGANG VEN BIỂN',
          distance: '~25 km về phía Đông Nam',
          district: 'Huyện Triệu Phong (2 mùa ghé thăm)',
          schools: [
            'Trường TH&THCS Triệu Vân — Chương trình “Răng xinh cho em” (Mùa 2)',
            'Trường TH&THCS Triệu Vân — Ngày hội kỹ năng “Phao xinh cho em” (Mùa 4)',
          ],
          seasons: [
            { label: 'Mùa 2 (Răng xinh) →', idx: 1 },
            { label: 'Mùa 4 (Phao xinh) →', idx: 3 },
          ],
        },
        {
          regionTag: 'MIỀN NÚI PHÍA TÂY BẮC',
          distance: '~55 km vượt đèo lên Vĩnh Linh',
          district: 'Huyện Vĩnh Linh (Xã vùng sâu)',
          schools: [
            'Trường PTDTBT Tiểu học Vĩnh Ô — Chuyên đề sơ cứu “An toàn cho em 2” & trao 67 suất quà Tết, áo ấm mùa đông (Mùa 6)',
          ],
          seasons: [{ label: 'Mùa 6 (Vĩnh Ô) →', idx: 5 }],
        },
        {
          regionTag: 'ĐẠI NGÀN PHÍA TÂY NAM',
          distance: '~50 km dọc Quốc lộ 9 – Đakrông',
          district: 'Huyện Đakrông (Thôn Pa Hy)',
          schools: [
            'Trường Tiểu học Tà Long — Trao 125 áo phao cứu sinh, 125 bộ học phẩm & 02 “Tủ sách tri thức” 345 đầu sách (Mùa 7)',
          ],
          seasons: [{ label: 'Mùa 7 (Tà Long) →', idx: 6 }],
        },
      ];

      footprintEl.innerHTML = regions
        .map(
          (reg) => `
          <article class="footprint-card">
            <div class="footprint-top">
              <span class="footprint-region-tag">${escapeHtml(reg.regionTag)}</span>
              <span class="footprint-distance">${escapeHtml(reg.distance)}</span>
            </div>
            <h4 class="footprint-district">${escapeHtml(reg.district)}</h4>
            <ul class="footprint-schools-list">
              ${reg.schools.map((sch) => `<li>${formatRichText(sch)}</li>`).join('')}
            </ul>
            <div class="footprint-season-buttons">
              ${reg.seasons
                .map(
                  (btn) =>
                    `<button type="button" class="footprint-jump-btn" data-jump-season="${btn.idx}">${escapeHtml(btn.label)}</button>`
                )
                .join('')}
            </div>
          </article>
        `
        )
        .join('');

      footprintEl.querySelectorAll('[data-jump-season]').forEach((btn) => {
        btn.addEventListener('click', () => {
          const idx = Number(btn.getAttribute('data-jump-season')) || 0;
          selectSeason(idx, true);
        });
      });
    }
  }

  /* --------------------------------------------------------------------------
     6. CHƯƠNG 02: KHÔNG GIAN TƯƠNG TÁC 7 MÙA HÀNH TRÌNH (ALL-IN-ONE HUB)
     -------------------------------------------------------------------------- */

  function renderSeasonTabs() {
    const tabsContainer = document.getElementById('season-tabs');
    if (!tabsContainer) return;

    tabsContainer.innerHTML = seasons
      .map((s, idx) => {
        const isActive = idx === state.activeSeasonIndex;
        const shortName = cleanText(s.official_name).replace(/^CHO\s+EM\s+mùa\s+\d+\s*[—–-]\s*/i, '');
        return `
          <button
            type="button"
            role="tab"
            class="season-tab-btn ${isActive ? 'active' : ''}"
            aria-selected="${isActive ? 'true' : 'false'}"
            data-season-idx="${idx}"
          >
            <span class="season-tab-num">MÙA 0${s.season_number}</span>
            <strong class="season-tab-name">${formatRichText(shortName)}</strong>
            <span class="season-tab-date">${escapeHtml(formatShortMonthYear(s.event_date || s.start_date))}</span>
          </button>
        `;
      })
      .join('');

    tabsContainer.querySelectorAll('[data-season-idx]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const idx = Number(btn.getAttribute('data-season-idx')) || 0;
        selectSeason(idx, false);
      });
    });

    const indicator = document.getElementById('season-step-indicator');
    if (indicator) {
      indicator.textContent = `Mùa ${state.activeSeasonIndex + 1} / ${seasons.length}`;
    }
  }

  function selectSeason(index, scrollIntoView) {
    const safeIdx = Math.max(0, Math.min(seasons.length - 1, index));
    state.activeSeasonIndex = safeIdx;
    state.seasonPreviewPhoto = null;
    state.seasonPostCategory = 'all';
    state.seasonPhotoLimit = 12;

    renderSeasonTabs();
    renderActiveSeasonWorkspace();

    try {
      const url = new URL(window.location.href);
      url.searchParams.set('season', String(safeIdx + 1));
      window.history.replaceState({}, '', url.toString());
    } catch (_) {
      // Ignore
    }

    if (scrollIntoView) {
      const hub = document.getElementById('seasons-hub');
      if (hub) hub.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  function buildSeasonKpiCards(s) {
    const rawResults = Array.isArray(s.results_summary) ? s.results_summary : [];
    const cards = [];

    rawResults.slice(0, 4).forEach((item) => {
      cards.push({
        label: cleanText(item.metric || 'KẾT QUẢ ĐẠT ĐƯỢC').toUpperCase(),
        value: formatMetricValue(item),
      });
    });

    const fallbackCards = [
      {
        label: 'CHỦ ĐỀ CỦA MÙA',
        value: cleanText(s.theme || s.official_name),
      },
      {
        label: 'ĐIỂM TRƯỜNG ĐẾN THĂM',
        value: cleanText((s.locations && s.locations[0]) || 'Tỉnh Quảng Trị'),
      },
      {
        label: 'THỜI GIAN TỔ CHỨC',
        value: formatSeasonDuration(s),
      },
      {
        label: 'ĐƠN VỊ ĐỒNG HÀNH',
        value: cleanText(s.patron || 'Đoàn Thanh niên & nhà trường địa phương'),
      },
    ];

    let fbIdx = 0;
    while (cards.length < 4 && fbIdx < fallbackCards.length) {
      cards.push(fallbackCards[fbIdx]);
      fbIdx += 1;
    }

    return cards;
  }

  function renderActiveSeasonWorkspace() {
    const workspace = document.getElementById('season-workspace');
    if (!workspace) return;

    const s = seasons[state.activeSeasonIndex];
    if (!s) return;

    const storyObj = s.story || {};
    const storyTitle = cleanText(storyObj.title || s.theme);
    const storySummary = cleanText(storyObj.summary || '');
    const narrativeText = cleanText(storyObj.narrative || s.description);
    const sPhotos = allPhotos.filter((p) => p.season_id === s.season_id);
    const sPosts = allPosts.filter((p) => p.season_id === s.season_id);
    const sVideos = allVideos.filter((v) => v.season_id === s.season_id);
    const kpiItems = buildSeasonKpiCards(s);
    const highlightPhotos =
      Array.isArray(s.highlight_photos) && s.highlight_photos.length > 0
        ? s.highlight_photos
        : sPhotos.slice(0, 4).map((p) => p.local_path);
    const activeHeroPhoto = state.seasonPreviewPhoto || s.hero_photo;
    const activeHeroObj = photoByPath.get(activeHeroPhoto);
    const activeHeroCaption =
      (activeHeroObj && activeHeroObj.title_clean) || s.official_name;

    workspace.innerHTML = `
      <div class="season-overview-grid">
        <figure class="season-hero-figure">
          <div class="season-hero-img-wrap" id="season-hero-trigger" tabindex="0" role="button" aria-label="Phóng to ảnh tiêu biểu của ${escapeHtml(s.official_name)}" style="cursor:pointer">
            <img id="season-main-preview-img" src="${escapeHtml(activeHeroPhoto)}" alt="${escapeHtml(activeHeroCaption)}" class="${getImgCropClass(activeHeroPhoto)}" />
          </div>
          ${
            highlightPhotos.length > 1
              ? `<div class="season-filmstrip" role="group" aria-label="Chọn nhanh 4 khoảnh khắc tiêu biểu của mùa">
                  ${highlightPhotos
                    .slice(0, 4)
                    .map(
                      (hp, hIdx) => `
                      <button type="button" class="filmstrip-thumb-btn ${hp === activeHeroPhoto ? 'active' : ''}" data-filmstrip-src="${escapeHtml(hp)}" aria-label="Xem ảnh tiêu biểu số ${hIdx + 1}">
                        <img src="${escapeHtml(hp)}" alt="Khoảnh khắc ${hIdx + 1}" class="${getImgCropClass(hp)}" loading="lazy" />
                      </button>
                    `
                    )
                    .join('')}
                </div>`
              : ''
          }
          <figcaption class="season-hero-caption">
            <span id="season-hero-caption-text"><strong>Khoảnh khắc tiêu biểu:</strong> ${formatRichText(activeHeroCaption)}</span>
            <span class="meta-pill accent" id="season-hero-zoom-pill" style="cursor:pointer">Bấm để phóng to ↗</span>
          </figcaption>
        </figure>

        <div class="season-narrative-col">
          <div class="season-meta-pills">
            <span class="meta-pill accent">MÙA 0${s.season_number}</span>
            <span class="meta-pill">${escapeHtml(formatSeasonDuration(s))}</span>
            <span class="meta-pill">${escapeHtml((s.locations && s.locations[0]) || 'Quảng Trị')}</span>
          </div>

          <h3 class="season-main-title">${formatRichText(s.official_name)}</h3>
          <p class="season-theme-banner">${formatRichText(storyTitle)}</p>
          ${storySummary ? `<p class="season-story-text"><strong>Cảm xúc chuyến đi:</strong> ${formatRichText(storySummary)}</p>` : ''}
          <p class="season-story-text">${formatRichText(narrativeText)}</p>

          <div class="season-locations-box">
            <strong>Điểm trường đến thăm:</strong> ${escapeHtml((s.locations || []).join(' · '))}<br />
            <strong>Thông điệp của mùa:</strong> ${formatRichText(s.slogan || s.theme)}
          </div>
        </div>
      </div>

      <!-- 4 Quantitative KPI Cards -->
      <div class="season-impact-strip" aria-label="Kết quả đạt được của mùa hoạt động">
        ${kpiItems
          .map(
            (kpi) => `
            <div class="season-kpi-card">
              <div class="season-kpi-label">${escapeHtml(kpi.label)}</div>
              <div class="season-kpi-val">${formatRichText(kpi.value)}</div>
            </div>
          `
          )
          .join('')}
      </div>

      <!-- Sub-Tab Navigation -->
      <div class="season-subtabs-bar">
        <div class="subtab-buttons" role="tablist" aria-label="Nội dung chi tiết của ${escapeHtml(s.official_name)}">
          <button type="button" role="tab" class="subtab-btn ${state.seasonSubTab === 'photos' ? 'active' : ''}" data-subtab="photos" aria-selected="${state.seasonSubTab === 'photos'}">
            Hình ảnh trong mùa (${sPhotos.length})
          </button>
          <button type="button" role="tab" class="subtab-btn ${state.seasonSubTab === 'posts' ? 'active' : ''}" data-subtab="posts" aria-selected="${state.seasonSubTab === 'posts'}">
            Bài viết của mùa (${sPosts.length})
          </button>
          <button type="button" role="tab" class="subtab-btn ${state.seasonSubTab === 'activities' ? 'active' : ''}" data-subtab="activities" aria-selected="${state.seasonSubTab === 'activities'}">
            Mục tiêu &amp; việc đã làm
          </button>
          ${
            sVideos.length > 0
              ? `<button type="button" role="tab" class="subtab-btn ${state.seasonSubTab === 'videos' ? 'active' : ''}" data-subtab="videos" aria-selected="${state.seasonSubTab === 'videos'}">
                  Video của mùa (${sVideos.length})
                </button>`
              : ''
          }
        </div>
      </div>

      <div id="season-subtab-content"></div>
    `;

    // Bind Hero image click & filmstrip switcher
    const heroTrigger = document.getElementById('season-hero-trigger');
    const zoomPill = document.getElementById('season-hero-zoom-pill');
    if (heroTrigger && sPhotos.length > 0) {
      const openHeroLightbox = () => {
        const currentSrc = state.seasonPreviewPhoto || s.hero_photo;
        const heroIdx = sPhotos.findIndex((p) => p.local_path === currentSrc);
        openLightbox(sPhotos, heroIdx >= 0 ? heroIdx : 0);
      };
      heroTrigger.addEventListener('click', openHeroLightbox);
      if (zoomPill) zoomPill.addEventListener('click', openHeroLightbox);
      heroTrigger.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          openHeroLightbox();
        }
      });
    }

    workspace.querySelectorAll('[data-filmstrip-src]').forEach((thumbBtn) => {
      thumbBtn.addEventListener('click', () => {
        const newSrc = thumbBtn.getAttribute('data-filmstrip-src');
        if (!newSrc) return;
        state.seasonPreviewPhoto = newSrc;
        const mainImg = document.getElementById('season-main-preview-img');
        const capText = document.getElementById('season-hero-caption-text');
        const phObj = photoByPath.get(newSrc);
        if (mainImg) {
          mainImg.src = newSrc;
          mainImg.className = getImgCropClass(newSrc);
        }
        if (capText) {
          const titleStr = (phObj && phObj.title_clean) || s.official_name;
          capText.innerHTML = `<strong>Khoảnh khắc tiêu biểu:</strong> ${formatRichText(titleStr)}`;
        }
        workspace.querySelectorAll('[data-filmstrip-src]').forEach((b) => {
          b.classList.toggle('active', b === thumbBtn);
        });
      });
    });

    // Bind Sub-tab buttons
    workspace.querySelectorAll('[data-subtab]').forEach((btn) => {
      btn.addEventListener('click', () => {
        state.seasonSubTab = btn.getAttribute('data-subtab') || 'photos';
        renderActiveSeasonWorkspace();
      });
    });

    renderSeasonSubTabContent(s, sPhotos, sPosts, sVideos);

    workspace.classList.remove('animate-fade-up');
    void workspace.offsetWidth;
    workspace.classList.add('animate-fade-up');
  }

  function renderSeasonSubTabContent(s, sPhotos, sPosts, sVideos) {
    const container = document.getElementById('season-subtab-content');
    if (!container) return;

    if (state.seasonSubTab === 'photos') {
      const visiblePhotos = sPhotos.slice(0, state.seasonPhotoLimit);
      const hasMore = sPhotos.length > visiblePhotos.length;

      container.innerHTML = `
        <div class="season-photos-grid">
          ${visiblePhotos
            .map(
              (ph, idx) => `
              <article class="photo-card card-cascade-in" style="--cascade-delay:${Math.min(idx % 12, 11) * 40}ms" data-season-photo-idx="${idx}" tabindex="0" role="button" aria-label="Xem ảnh ${escapeHtml(ph.title_clean)}">
                <div class="photo-thumb-wrap">
                  <img src="${escapeHtml(ph.local_path)}" alt="${escapeHtml(ph.title_clean)}" class="${getImgCropClass(ph.local_path)}" loading="lazy" />
                  <span class="photo-cat-tag">${escapeHtml(ph.category_label)}</span>
                </div>
                <div class="photo-card-body">
                  <h4 class="photo-card-title">${formatRichText(ph.title_clean)}</h4>
                  <span class="photo-card-date">${formatViDate(ph.published_at)}</span>
                </div>
              </article>
            `
            )
            .join('')}
        </div>
        ${
          hasMore
            ? `<div class="archive-load-more-wrap">
                <button type="button" class="btn-secondary" id="btn-season-more-photos">
                  Xem thêm ảnh của ${formatRichText(s.official_name)} (còn ${sPhotos.length - visiblePhotos.length} ảnh)
                </button>
              </div>`
            : ''
        }
      `;

      container.querySelectorAll('[data-season-photo-idx]').forEach((card) => {
        const activate = () => {
          const idx = Number(card.getAttribute('data-season-photo-idx')) || 0;
          openLightbox(sPhotos, idx);
        };
        card.addEventListener('click', activate);
        card.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            activate();
          }
        });
      });

      const moreBtn = document.getElementById('btn-season-more-photos');
      if (moreBtn) {
        moreBtn.addEventListener('click', () => {
          state.seasonPhotoLimit += 16;
          renderSeasonSubTabContent(s, sPhotos, sPosts, sVideos);
        });
      }
      return;
    }

    if (state.seasonSubTab === 'posts') {
      const categories = [
        { id: 'all', label: `Tất cả (${sPosts.length})` },
        { id: 'recap', label: 'Tổng kết chuyến đi' },
        { id: 'campaign', label: 'Gây quỹ & chuẩn bị' },
        { id: 'knowledge', label: 'Chia sẻ kiến thức' },
        { id: 'team', label: 'Thành viên & tuyển quân' },
        { id: 'sponsor', label: 'Cảm ơn nhà tài trợ' },
      ];

      const filteredPosts =
        state.seasonPostCategory === 'all'
          ? sPosts
          : sPosts.filter((p) => p.category_id === state.seasonPostCategory);

      container.innerHTML = `
        <div class="category-pills-row" role="group" aria-label="Lọc bài đăng theo nhóm nội dung">
          ${categories
            .map((cat) => {
              const count =
                cat.id === 'all'
                  ? sPosts.length
                  : sPosts.filter((p) => p.category_id === cat.id).length;
              if (cat.id !== 'all' && count === 0) return '';
              const labelText = cat.id === 'all' ? cat.label : `${cat.label} (${count})`;
              return `<button type="button" class="cat-pill-btn ${state.seasonPostCategory === cat.id ? 'active' : ''}" data-season-cat="${cat.id}">${escapeHtml(labelText)}</button>`;
            })
            .join('')}
        </div>

        <div class="season-posts-grid">
          ${filteredPosts.map((post) => renderPostCardHtml(post)).join('')}
        </div>
      `;

      container.querySelectorAll('[data-season-cat]').forEach((btn) => {
        btn.addEventListener('click', () => {
          state.seasonPostCategory = btn.getAttribute('data-season-cat') || 'all';
          renderSeasonSubTabContent(s, sPhotos, sPosts, sVideos);
        });
      });

      bindPostCardInteractions(container);
      return;
    }

    if (state.seasonSubTab === 'videos') {
      container.innerHTML = `
        <div class="season-posts-grid">
          ${sVideos
            .map(
              (v) => `
              <article class="post-card">
                <div class="cinema-video-wrap">
                  <video controls preload="metadata" poster="${escapeHtml(v.poster_photo || s.hero_photo)}" src="${escapeHtml(v.local_path)}"></video>
                </div>
                <div class="post-card-top">
                  <span class="category-badge cat-recap">Video kỷ niệm</span>
                  <time class="post-date">${formatViDate(v.published_at)}</time>
                </div>
                <h4 class="post-title">${formatRichText(v.title_clean)}</h4>
                <p class="post-excerpt">${formatRichText(v.body_clean)}</p>
              </article>
            `
            )
            .join('')}
        </div>
      `;
      return;
    }

    // 'activities' sub-tab
    const objectives = s.objectives || [];
    const activities = (s.program && s.program.activities) || s.main_activities || [];
    const leaders = s.leaders || [];
    const progContext = cleanText((s.program && s.program.context) || s.description || '');
    const progPrep = cleanText(
      (s.program && s.program.preparation) ||
        'Tuyển tình nguyện viên, truyền thông vận động quyên góp và tổ chức sự kiện gây quỹ cộng đồng tại Đông Hà.'
    );

    container.innerHTML = `
      <div class="season-posts-grid">
        <div class="post-card">
          <span class="panel-tag">BỐI CẢNH &amp; MỤC TIÊU CHUYẾN ĐI</span>
          <h4 class="post-title">Mong muốn gửi trao trong ${formatRichText(s.official_name)}</h4>
          ${progContext ? `<p class="post-excerpt" style="-webkit-line-clamp:unset">${formatRichText(progContext)}</p>` : ''}
          <ul class="verify-badges-list" style="margin-top:0.5rem">
            ${objectives.map((obj) => `<li>✓ ${formatRichText(obj)}</li>`).join('')}
          </ul>
          ${
            leaders.length > 0
              ? `<div style="margin-top:0.75rem;padding-top:0.75rem;border-top:1px solid var(--border-subtle);font-size:0.85rem;color:var(--ink-700)">
                  <strong>Các bạn phụ trách chính:</strong><br/>
                  ${leaders.map((l) => `${escapeHtml(l.name)} (${escapeHtml(l.role)})`).join(' · ')}
                </div>`
              : ''
          }
        </div>
        <div class="post-card">
          <span class="panel-tag">CHUẨN BỊ TẠI ĐÔNG HÀ &amp; TRIỂN KHAI TẠI ĐIỂM TRƯỜNG</span>
          <h4 class="post-title">Hoạt động từ lúc gây quỹ đến ngày lên điểm trường</h4>
          <p class="post-excerpt" style="-webkit-line-clamp:unset"><strong>Công tác chuẩn bị:</strong> ${formatRichText(progPrep)}</p>
          <ul class="verify-badges-list" style="margin-top:0.5rem">
            ${activities.map((act) => `<li>• ${formatRichText(act)}</li>`).join('')}
          </ul>
        </div>
      </div>
    `;
  }

  function renderPostCardHtml(post) {
    const hashtagsHtml = (post.hashtags || [])
      .slice(0, 4)
      .map((tag) => `<span class="hashtag-chip">${escapeHtml(tag)}</span>`)
      .join('');

    const photoPaths = Array.isArray(post.photo_paths) ? post.photo_paths : [];
    const previewPhotos = photoPaths.slice(0, 3);
    const extraCount = photoPaths.length - previewPhotos.length;

    const mediaStripHtml =
      previewPhotos.length > 0
        ? `<div class="post-media-strip" style="--media-cols:${previewPhotos.length}">
            ${previewPhotos
              .map(
                (pPath, pIdx) => `
                <div class="post-media-thumb" data-post-photo-path="${escapeHtml(pPath)}" tabindex="0" role="button" aria-label="Xem ảnh đính kèm bài viết">
                  <img src="${escapeHtml(pPath)}" alt="${escapeHtml(post.title_clean)}" class="${getImgCropClass(pPath)}" loading="lazy" />
                  ${pIdx === 2 && extraCount > 0 ? `<span class="post-media-more">+${extraCount} ảnh</span>` : ''}
                </div>
              `
              )
              .join('')}
          </div>`
        : '';

    return `
      <article class="post-card" data-post-id="${escapeHtml(post.post_id)}">
        <div class="post-card-top">
          <span class="category-badge cat-${escapeHtml(post.category_id)}">${escapeHtml(post.category_label)}</span>
          <time class="post-date">Mùa ${post.season_number} · ${formatViDate(post.published_at)}</time>
        </div>
        ${mediaStripHtml}
        <h4 class="post-title">${formatRichText(post.title_clean)}</h4>
        <div class="post-excerpt">${formatRichText(post.body_clean)}</div>
        ${hashtagsHtml ? `<div class="post-hashtags">${hashtagsHtml}</div>` : ''}
        <div class="post-card-footer">
          <button type="button" class="btn-text-action" data-toggle-expand>Đọc toàn bộ nội dung ↓</button>
          <a href="${escapeHtml(post.post_url || 'https://www.facebook.com/profile.php?id=100094610840245')}" target="_blank" rel="noopener noreferrer" class="btn-text-action">
            Bài gốc Facebook ↗
          </a>
        </div>
      </article>
    `;
  }

  function bindPostCardInteractions(rootEl) {
    rootEl.querySelectorAll('[data-toggle-expand]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const card = btn.closest('.post-card');
        if (!card) return;
        const expanded = card.classList.toggle('expanded');
        btn.textContent = expanded ? 'Thu gọn nội dung ↑' : 'Đọc toàn bộ nội dung ↓';
      });
    });

    rootEl.querySelectorAll('[data-post-photo-path]').forEach((thumb) => {
      const openPostPhoto = () => {
        const pPath = thumb.getAttribute('data-post-photo-path');
        const card = thumb.closest('.post-card');
        const pid = card ? card.getAttribute('data-post-id') : null;
        const postPhotos = pid ? allPhotos.filter((ph) => ph.post_id === pid) : [];
        if (postPhotos.length > 0) {
          const idx = postPhotos.findIndex((ph) => ph.local_path === pPath);
          openLightbox(postPhotos, idx >= 0 ? idx : 0);
        } else {
          const idx = allPhotos.findIndex((ph) => ph.local_path === pPath);
          openLightbox(allPhotos, idx >= 0 ? idx : 0);
        }
      };
      thumb.addEventListener('click', openPostPhoto);
      thumb.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          openPostPhoto();
        }
      });
    });
  }

  /* --------------------------------------------------------------------------
     7. CHƯƠNG 03: BẢNG MINH BẠCH TÀI CHÍNH, 15 DẤU MỐC & TRI ÂN ĐỒNG HÀNH
     -------------------------------------------------------------------------- */

  function renderGratitudeWall() {
    const gridEl = document.getElementById('gratitude-grid');
    if (!gridEl) return;

    const groups = [
      {
        tag: 'ĐƠN VỊ BẢO TRỢ & NHÀ TRƯỜNG',
        title: 'Điểm tựa pháp lý & kết nối bản làng',
        desc: 'Những cơ quan Đoàn thể và Ban Giám hiệu các nhà trường đã luôn tin tưởng, cấp phép và đón đoàn tình nguyện CHO EM bằng tất cả sự ấm áp.',
        chips: [
          { label: 'Thành đoàn Đông Hà', highlight: true },
          { label: 'Tỉnh đoàn Quảng Trị', highlight: true },
          { label: 'Đoàn trường THPT Chuyên Lê Quý Đôn', highlight: true },
          { label: 'Đoàn phường Nam Đông Hà', highlight: true },
          { label: 'Trường Mầm non Húc (Ho Le & Tà Rùng)', highlight: false },
          { label: 'Trường TH&THCS Triệu Vân', highlight: false },
          { label: 'Trường Mầm non Hướng Phùng (Chênh Vênh & Hướng Choa)', highlight: false },
          { label: 'Trường TH&THCS Tân Thành', highlight: false },
          { label: 'Trường PTDTBT Tiểu học Vĩnh Ô', highlight: false },
          { label: 'Trường Tiểu học Tà Long (Điểm trường Pa Hy)', highlight: false },
        ],
      },
      {
        tag: 'QUÝ THẦY CÔ & NHÀ HẢO TÂM',
        title: 'Những người thầy, người cô & tấm lòng vàng',
        desc: 'Sự dìu dắt tận tình của cô cố vấn cùng những khoản đóng góp quý báu từ các thầy cô giáo và mạnh thường quân qua nhiều mùa liên tiếp.',
        chips: [
          { label: 'Cô Nguyễn Thị Thanh Huyền (Cố vấn dự án)', highlight: true },
          { label: 'Chú Lê Minh Tuấn (Tài trợ 100 đôi giày mới)', highlight: true },
          { label: 'Lớp Hóa Cô Lê Na (Colena)', highlight: true },
          { label: 'Lớp Anh Team Miss Kha', highlight: false },
          { label: 'Lớp Toán Thầy Thông', highlight: false },
          { label: 'Lớp Toán Cô Thu Hồng Lê (Miss Pink)', highlight: false },
          { label: 'Cô Lê Tú Linh Kha', highlight: false },
          { label: 'Cô Hạnh Nguyên', highlight: false },
          { label: 'Gia đình Dì Lê Thị Vân', highlight: false },
        ],
      },
      {
        tag: 'DOANH NGHIỆP & ĐƠN VỊ ĐỒNG HÀNH',
        title: 'Những thương hiệu địa phương giàu lòng nhân ái',
        desc: 'Các nhà sách, nhà thuốc, quán cà phê và cửa hàng tại Đông Hà – Quảng Trị đã tài trợ hiện kim, sách vở, thuốc y tế và không gian tổ chức Workshop gây quỹ.',
        chips: [
          { label: 'Nhà sách Sang Hiếu', highlight: true },
          { label: 'Nhà thuốc Bảo Châu', highlight: true },
          { label: 'Green Centre', highlight: true },
          { label: 'Gạo Coffee & Tea', highlight: false },
          { label: 'Gé Nhà Coffee', highlight: false },
          { label: 'Dimori Coffee', highlight: false },
          { label: 'The Moment Cafe & Food', highlight: false },
          { label: 'Nhà hàng Sky Garden', highlight: false },
          { label: 'Chút Chíu', highlight: false },
          { label: 'Mây Mart', highlight: false },
          { label: 'Mầm non Joy School', highlight: false },
          { label: 'Hạt Màu Nắng', highlight: false },
          { label: 'Apical Bud', highlight: false },
        ],
      },
    ];

    gridEl.innerHTML = groups
      .map(
        (g) => `
        <article class="gratitude-card">
          <span class="panel-tag">${escapeHtml(g.tag)}</span>
          <h4 class="gratitude-card-title">${escapeHtml(g.title)}</h4>
          <p class="gratitude-card-desc">${escapeHtml(g.desc)}</p>
          <div class="partner-chips">
            ${g.chips
              .map(
                (c) =>
                  `<span class="partner-chip ${c.highlight ? 'highlight' : ''}">${escapeHtml(c.label)}</span>`
              )
              .join('')}
          </div>
        </article>
      `
      )
      .join('');
  }

  function renderImpactLedgerAndTimeline() {
    const tbody = document.getElementById('impact-table-body');
    if (tbody) {
      tbody.innerHTML = seasons
        .map((s, idx) => {
          const rawResults = Array.isArray(s.results_summary) ? s.results_summary : [];
          const metricsHtml =
            rawResults.length > 0
              ? rawResults
                  .slice(0, 4)
                  .map((m) => `• <strong>${escapeHtml(formatMetricValue(m))}</strong>`)
                  .join('<br />')
              : `• Trao quà khuyến học và tổ chức hoạt động vui chơi cho các em nhỏ`;

          return `
            <tr data-jump-season="${idx}" style="cursor:pointer" title="Nhấn để xem chi tiết ${escapeHtml(s.official_name)}">
              <td>
                <span class="table-season-pill">Mùa 0${s.season_number}</span><br />
                <small style="color:var(--ink-500);font-family:var(--font-mono);font-size:0.72rem">${escapeHtml(formatShortMonthYear(s.event_date || s.start_date))}</small>
              </td>
              <td>
                <strong>${formatRichText(s.official_name)}</strong><br />
                <span style="color:var(--ink-700);font-size:0.82rem">${escapeHtml((s.locations || []).join(' · '))}</span>
              </td>
              <td style="font-size:0.84rem;line-height:1.55">
                ${metricsHtml}
              </td>
            </tr>
          `;
        })
        .join('');

      tbody.querySelectorAll('[data-jump-season]').forEach((row) => {
        row.addEventListener('click', () => {
          const idx = Number(row.getAttribute('data-jump-season')) || 0;
          selectSeason(idx, true);
        });
      });
    }

    renderTimelineMilestones();
    renderGratitudeWall();

    const yearFilters = document.getElementById('timeline-year-filters');
    if (yearFilters) {
      yearFilters.querySelectorAll('[data-year]').forEach((btn) => {
        btn.addEventListener('click', () => {
          state.timelineYear = btn.getAttribute('data-year') || 'all';
          state.timelineExpanded = false;
          yearFilters.querySelectorAll('[data-year]').forEach((b) => b.classList.remove('active'));
          btn.classList.add('active');
          renderTimelineMilestones();
        });
      });
    }
  }

  function renderTimelineMilestones() {
    const listEl = document.getElementById('milestone-list');
    if (!listEl) return;

    const events =
      Array.isArray(archive.timeline) && archive.timeline.length > 0
        ? archive.timeline
        : archive.milestones || [];

    const filtered =
      state.timelineYear === 'all'
        ? events
        : events.filter((ev) => String(ev.event_date || ev.date || '').startsWith(state.timelineYear));

    const defaultVisibleCount = 6;
    const shouldTruncate =
      state.timelineYear === 'all' && !state.timelineExpanded && filtered.length > defaultVisibleCount;
    const visibleEvents = shouldTruncate ? filtered.slice(0, defaultVisibleCount) : filtered;

    listEl.innerHTML = visibleEvents
      .map((ev) => {
        const rawDate = ev.event_date || ev.date || '';
        const seasonId =
          ev.season_id ||
          (Array.isArray(ev.season_ids) && ev.season_ids[0]) ||
          'season_01';
        const sIndex = seasons.findIndex((s) => s.season_id === seasonId);
        const seasonNum = sIndex >= 0 ? sIndex + 1 : 1;

        return `
          <li class="milestone-item" data-milestone-season="${sIndex >= 0 ? sIndex : 0}">
            <span class="milestone-date">${escapeHtml(formatViDate(rawDate))} · Mùa 0${seasonNum}</span>
            <h4 class="milestone-title">${formatRichText(ev.title)}</h4>
            <p class="milestone-desc">${formatRichText(ev.description)}</p>
          </li>
        `;
      })
      .join('');

    let toggleWrap = document.getElementById('timeline-toggle-wrap');
    if (state.timelineYear === 'all' && filtered.length > defaultVisibleCount) {
      if (!toggleWrap) {
        toggleWrap = document.createElement('div');
        toggleWrap.id = 'timeline-toggle-wrap';
        toggleWrap.className = 'timeline-toggle-wrap';
        listEl.insertAdjacentElement('afterend', toggleWrap);
      }
      toggleWrap.innerHTML = `
        <button type="button" class="btn-secondary" id="btn-toggle-timeline" style="padding: 0.55rem 1.15rem; font-size: 0.84rem;">
          ${state.timelineExpanded ? 'Thu gọn danh sách dấu mốc ↑' : `Xem đầy đủ ${filtered.length} dấu mốc qua các mùa ↓`}
        </button>
      `;
      const btnToggle = document.getElementById('btn-toggle-timeline');
      if (btnToggle) {
        btnToggle.addEventListener('click', () => {
          state.timelineExpanded = !state.timelineExpanded;
          renderTimelineMilestones();
        });
      }
    } else if (toggleWrap) {
      toggleWrap.remove();
    }

    listEl.querySelectorAll('[data-milestone-season]').forEach((item) => {
      item.addEventListener('click', () => {
        const idx = Number(item.getAttribute('data-milestone-season')) || 0;
        selectSeason(idx, true);
      });
    });
  }

  /* --------------------------------------------------------------------------
     8. CHƯƠNG 04: RẠP PHIM TƯ LIỆU THỰC ĐỊA (8 VIDEOS)
     -------------------------------------------------------------------------- */

  function renderCinemaSection() {
    const grid = document.getElementById('cinema-grid');
    if (!grid) return;

    grid.innerHTML = allVideos
      .map(
        (v) => `
        <article class="cinema-card">
          <div class="cinema-video-wrap">
            <video controls preload="metadata" poster="${escapeHtml(v.poster_photo)}" src="${escapeHtml(v.local_path)}"></video>
          </div>
          <div class="cinema-body">
            <div class="cinema-meta">
              <span>MÙA 0${v.season_number} · ${formatRichText(v.season_name)}</span>
              <time>${formatViDate(v.published_at)}</time>
            </div>
            <h3 class="cinema-title">${formatRichText(v.title_clean)}</h3>
            <p class="cinema-desc">${formatRichText(v.body_clean)}</p>
          </div>
        </article>
      `
      )
      .join('');
  }

  /* --------------------------------------------------------------------------
     9. CHƯƠNG 05: KHO LƯU TRỮ SỐ HÓA TOÀN DIỆN (563 ẢNH & 135 BÀI VIẾT)
     -------------------------------------------------------------------------- */

  function initFullArchiveControls() {
    const seasonSelect = document.getElementById('archive-season-select');
    if (seasonSelect) {
      seasonSelect.innerHTML =
        `<option value="all">Tất cả 7 mùa (2023 – 2026)</option>` +
        seasons
          .map(
            (s) =>
              `<option value="${escapeHtml(s.season_id)}">${escapeHtml(s.official_name)}</option>`
          )
          .join('');

      seasonSelect.addEventListener('change', () => {
        state.archiveSeason = seasonSelect.value;
        state.archiveLimit = 20;
        renderFullArchiveResults();
      });
    }

    const catSelect = document.getElementById('archive-category-select');
    if (catSelect) {
      catSelect.addEventListener('change', () => {
        state.archiveCategory = catSelect.value;
        state.archiveLimit = 20;
        renderFullArchiveResults();
      });
    }

    const searchInput = document.getElementById('archive-search-input');
    const clearBtn = document.getElementById('archive-clear-btn');
    if (searchInput) {
      searchInput.addEventListener('input', () => {
        state.archiveQuery = searchInput.value.trim();
        state.archiveLimit = 20;
        if (clearBtn) clearBtn.hidden = state.archiveQuery.length === 0;
        renderFullArchiveResults();
      });
    }

    if (clearBtn && searchInput) {
      clearBtn.addEventListener('click', () => {
        searchInput.value = '';
        state.archiveQuery = '';
        clearBtn.hidden = true;
        renderFullArchiveResults();
      });
    }

    const resetBtn = document.getElementById('archive-reset-all');
    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        state.archiveSeason = 'all';
        state.archiveCategory = 'all';
        state.archiveQuery = '';
        state.archiveLimit = 20;
        if (seasonSelect) seasonSelect.value = 'all';
        if (catSelect) catSelect.value = 'all';
        if (searchInput) searchInput.value = '';
        if (clearBtn) clearBtn.hidden = true;
        renderFullArchiveResults();
      });
    }

    document.querySelectorAll('[data-archive-mode]').forEach((tabBtn) => {
      tabBtn.addEventListener('click', () => {
        const mode = tabBtn.getAttribute('data-archive-mode') || 'photos';
        state.archiveMode = mode;
        state.archiveLimit = 20;
        document.querySelectorAll('[data-archive-mode]').forEach((b) => {
          const active = b === tabBtn;
          b.classList.toggle('active', active);
          b.setAttribute('aria-selected', active ? 'true' : 'false');
        });
        renderFullArchiveResults();
      });
    });

    const loadMoreBtn = document.getElementById('btn-load-more');
    if (loadMoreBtn) {
      loadMoreBtn.addEventListener('click', () => {
        state.archiveLimit += 24;
        renderFullArchiveResults();
      });
    }
  }

  function renderFullArchiveResults() {
    const gridEl = document.getElementById('archive-results-grid');
    const summaryEl = document.getElementById('archive-result-summary');
    const loadMoreWrap = document.getElementById('archive-load-more-wrap');
    if (!gridEl) return;

    const q = state.archiveQuery.toLowerCase();

    if (state.archiveMode === 'photos') {
      gridEl.classList.remove('posts-mode');
      const filteredPhotos = allPhotos.filter((ph) => {
        if (state.archiveSeason !== 'all' && ph.season_id !== state.archiveSeason) return false;
        if (state.archiveCategory !== 'all' && ph.category_id !== state.archiveCategory) return false;
        if (q) {
          const haystack = `${ph.title_clean} ${ph.description} ${ph.season_name} ${ph.season_theme} ${ph.season_locations} ${ph.category_label}`.toLowerCase();
          return haystack.includes(q);
        }
        return true;
      });

      const visible = filteredPhotos.slice(0, state.archiveLimit);
      if (summaryEl) {
        summaryEl.textContent = `Đang hiển thị ${visible.length} / ${filteredPhotos.length} bức ảnh kỷ niệm.`;
      }

      if (filteredPhotos.length === 0) {
        gridEl.innerHTML = `<div class="post-card" style="grid-column: 1 / -1; text-align:center; padding: 2.5rem;">
          <h4 class="post-title">Không tìm thấy bức ảnh nào khớp từ khóa <em class="quote-highlight">“${escapeHtml(state.archiveQuery)}”</em></h4>
          <p class="post-excerpt">Hãy thử tìm với tên địa danh như “Tà Long”, “Chênh Vênh”, “Vĩnh Ô”, “Ho Le” hoặc chọn “Tất cả phân loại”.</p>
        </div>`;
      } else {
        gridEl.innerHTML = visible
          .map(
            (ph, idx) => `
            <article class="photo-card" data-archive-photo-idx="${idx}" tabindex="0" role="button" aria-label="Phóng to ảnh ${escapeHtml(ph.title_clean)}">
              <div class="photo-thumb-wrap">
                <img src="${escapeHtml(ph.local_path)}" alt="${escapeHtml(ph.title_clean)}" class="${getImgCropClass(ph.local_path)}" loading="lazy" />
                <span class="photo-cat-tag">Mùa ${ph.season_number} · ${escapeHtml(ph.category_label)}</span>
              </div>
              <div class="photo-card-body">
                <h4 class="photo-card-title">${formatRichText(ph.title_clean)}</h4>
                <span class="photo-card-date">${formatViDate(ph.published_at)} · ${formatRichText(ph.season_name)}</span>
              </div>
            </article>
          `
          )
          .join('');

        gridEl.querySelectorAll('[data-archive-photo-idx]').forEach((card) => {
          const activate = () => {
            const idx = Number(card.getAttribute('data-archive-photo-idx')) || 0;
            openLightbox(filteredPhotos, idx);
          };
          card.addEventListener('click', activate);
          card.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              activate();
            }
          });
        });
      }

      if (loadMoreWrap) {
        loadMoreWrap.style.display = filteredPhotos.length > visible.length ? 'flex' : 'none';
      }
      return;
    }

    // 'posts' mode
    gridEl.classList.add('posts-mode');
    const filteredPosts = allPosts.filter((post) => {
      if (state.archiveSeason !== 'all' && post.season_id !== state.archiveSeason) return false;
      if (state.archiveCategory !== 'all' && post.category_id !== state.archiveCategory) return false;
      if (q) {
        const haystack = `${post.title_clean} ${post.body_clean} ${post.season_name} ${post.season_locations} ${post.category_label} ${(post.hashtags || []).join(' ')}`.toLowerCase();
        return haystack.includes(q);
      }
      return true;
    });

    const visiblePosts = filteredPosts.slice(0, state.archiveLimit);
    if (summaryEl) {
      summaryEl.textContent = `Đang hiển thị ${visiblePosts.length} / ${filteredPosts.length} bài viết từ Fanpage dự án.`;
    }

    if (filteredPosts.length === 0) {
      gridEl.innerHTML = `<div class="post-card" style="grid-column: 1 / -1; text-align:center; padding: 2.5rem;">
        <h4 class="post-title">Không tìm thấy bài viết nào khớp từ khóa <em class="quote-highlight">“${escapeHtml(state.archiveQuery)}”</em></h4>
        <p class="post-excerpt">Hãy thử đổi sang mùa khác hoặc nhấn “Đặt lại bộ lọc”.</p>
      </div>`;
    } else {
      gridEl.innerHTML = visiblePosts.map((post) => renderPostCardHtml(post)).join('');
      bindPostCardInteractions(gridEl);
    }

    if (loadMoreWrap) {
      loadMoreWrap.style.display = filteredPosts.length > visiblePosts.length ? 'flex' : 'none';
    }
  }

  /* --------------------------------------------------------------------------
     10. ACCESSIBLE LIGHTBOX MODAL
     -------------------------------------------------------------------------- */

  function openLightbox(photoList, startIndex) {
    if (!Array.isArray(photoList) || photoList.length === 0) return;
    state.lightboxList = photoList;
    state.lightboxIndex = Math.max(0, Math.min(photoList.length - 1, startIndex));

    const modal = document.getElementById('lightbox-modal');
    if (!modal) return;
    modal.hidden = false;
    document.body.style.overflow = 'hidden';
    updateLightboxSlide();

    const closeBtn = document.getElementById('lightbox-close');
    if (closeBtn) closeBtn.focus();
  }

  function closeLightbox() {
    const modal = document.getElementById('lightbox-modal');
    if (!modal) return;
    modal.hidden = true;
    document.body.style.overflow = '';
  }

  function stepLightbox(delta) {
    const list = state.lightboxList || [];
    if (list.length === 0) return;
    state.lightboxIndex = (state.lightboxIndex + delta + list.length) % list.length;
    updateLightboxSlide();
  }

  function updateLightboxSlide() {
    const list = state.lightboxList || [];
    const item = list[state.lightboxIndex];
    if (!item) return;

    const imgEl = document.getElementById('lightbox-image');
    const seasonBadge = document.getElementById('lightbox-season-badge');
    const catBadge = document.getElementById('lightbox-category-badge');
    const counterEl = document.getElementById('lightbox-counter');
    const dateEl = document.getElementById('lightbox-date');
    const titleEl = document.getElementById('lightbox-title');
    const captionEl = document.getElementById('lightbox-caption');
    const hashtagsEl = document.getElementById('lightbox-hashtags');
    const fbLink = document.getElementById('lightbox-fb-link');

    if (imgEl) {
      imgEl.src = item.local_path;
      imgEl.alt = item.title_clean || item.season_name;
    }
    if (seasonBadge) seasonBadge.textContent = item.season_name || `Mùa ${item.season_number}`;
    if (catBadge) catBadge.textContent = item.category_label || 'Hình ảnh kỷ niệm';
    if (counterEl) counterEl.textContent = `${state.lightboxIndex + 1} / ${list.length}`;
    if (dateEl) dateEl.textContent = `Ngày đăng: ${formatViDate(item.published_at)} · ${item.season_locations || 'Quảng Trị'}`;
    if (titleEl) titleEl.innerHTML = formatRichText(item.title_clean || item.season_name);
    if (captionEl) captionEl.innerHTML = formatRichText(item.description || '');
    if (hashtagsEl) {
      hashtagsEl.innerHTML = (item.hashtags || [])
        .map((tag) => `<span class="hashtag-chip">${escapeHtml(tag)}</span>`)
        .join('');
    }
    if (fbLink) {
      fbLink.href = item.post_url || 'https://www.facebook.com/profile.php?id=100094610840245';
    }
  }

  function initLightboxEvents() {
    const modal = document.getElementById('lightbox-modal');
    const closeBtn = document.getElementById('lightbox-close');
    const prevBtn = document.getElementById('lightbox-prev');
    const nextBtn = document.getElementById('lightbox-next');

    if (closeBtn) closeBtn.addEventListener('click', closeLightbox);
    if (prevBtn) prevBtn.addEventListener('click', () => stepLightbox(-1));
    if (nextBtn) nextBtn.addEventListener('click', () => stepLightbox(1));

    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) closeLightbox();
      });
    }

    document.addEventListener('keydown', (e) => {
      if (!modal || modal.hidden) return;
      if (e.key === 'Escape') closeLightbox();
      if (e.key === 'ArrowLeft') stepLightbox(-1);
      if (e.key === 'ArrowRight') stepLightbox(1);
    });
  }

  /* --------------------------------------------------------------------------
     11. FOOTER LINKS & GLOBAL NAVIGATION
     -------------------------------------------------------------------------- */

  function initFooterAndGlobalNav() {
    const footerList = document.getElementById('footer-season-links');
    if (footerList) {
      footerList.innerHTML = seasons
        .map(
          (s, idx) =>
            `<li><a href="#seasons-hub" data-footer-season="${idx}">${formatRichText(s.official_name)} (${escapeHtml(formatShortMonthYear(s.event_date || s.start_date))})</a></li>`
        )
        .join('');

      footerList.querySelectorAll('[data-footer-season]').forEach((link) => {
        link.addEventListener('click', (e) => {
          e.preventDefault();
          const idx = Number(link.getAttribute('data-footer-season')) || 0;
          selectSeason(idx, true);
        });
      });
    }

    const prevSeasonBtn = document.getElementById('btn-prev-season');
    const nextSeasonBtn = document.getElementById('btn-next-season');
    if (prevSeasonBtn) {
      prevSeasonBtn.addEventListener('click', () => {
        const nextIdx = (state.activeSeasonIndex - 1 + seasons.length) % seasons.length;
        selectSeason(nextIdx, false);
      });
    }
    if (nextSeasonBtn) {
      nextSeasonBtn.addEventListener('click', () => {
        const nextIdx = (state.activeSeasonIndex + 1) % seasons.length;
        selectSeason(nextIdx, false);
      });
    }

    try {
      const params = new URLSearchParams(window.location.search);
      const sParam = Number(params.get('season'));
      if (sParam >= 1 && sParam <= seasons.length) {
        state.activeSeasonIndex = sParam - 1;
      }
    } catch (_) {
      // ignore
    }
  }

  /* --------------------------------------------------------------------------
     12. MOTION CHOREOGRAPHY, SCROLL REVEAL & MUSIC PLAYER (“NẤU ĂN CHO EM”)
     -------------------------------------------------------------------------- */

  function initScrollProgressAndNavSpy() {
    const progressBar = document.getElementById('scroll-progress-bar');
    const navLinks = Array.from(document.querySelectorAll('.nav-link[data-nav-section]'));
    const sectionIds = navLinks.map((l) => l.getAttribute('data-nav-section')).filter(Boolean);

    let ticking = false;
    const updateOnScroll = () => {
      const scrollTop = window.scrollY || document.documentElement.scrollTop;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const ratio = docHeight > 0 ? Math.min(1, Math.max(0, scrollTop / docHeight)) : 0;

      if (progressBar) {
        progressBar.style.transform = `scaleX(${ratio.toFixed(4)})`;
      }

      let currentSection = '';
      const offset = window.innerHeight * 0.28;
      sectionIds.forEach((id) => {
        const el = document.getElementById(id);
        if (el) {
          const rect = el.getBoundingClientRect();
          if (rect.top <= offset && rect.bottom >= 120) {
            currentSection = id;
          }
        }
      });

      navLinks.forEach((link) => {
        const isMatch = link.getAttribute('data-nav-section') === currentSection;
        link.classList.toggle('active', isMatch);
      });

      ticking = false;
    };

    window.addEventListener(
      'scroll',
      () => {
        if (!ticking) {
          window.requestAnimationFrame(updateOnScroll);
          ticking = true;
        }
      },
      { passive: true }
    );
    updateOnScroll();
  }

  function initStatCounters() {
    const counters = Array.from(document.querySelectorAll('.counter-num[data-count-target]'));
    if (counters.length === 0) return;

    const prefersReducedMotion =
      window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion || !('IntersectionObserver' in window)) return;

    const animateCounter = (el) => {
      const target = Number(el.getAttribute('data-count-target')) || 0;
      const pad = Number(el.getAttribute('data-count-pad')) || 0;
      const suffix = el.getAttribute('data-count-suffix') || '';
      const fmt = el.getAttribute('data-count-format') || '';
      const duration = 1350;
      const startTime = performance.now();

      const formatVal = (n) => {
        let str = fmt === 'vi' ? n.toLocaleString('vi-VN') : String(n);
        if (pad > 0 && n < 10) {
          str = String(n).padStart(pad, '0');
        }
        return `${str}${suffix}`;
      };

      const step = (now) => {
        const elapsed = now - startTime;
        const progress = Math.min(1, elapsed / duration);
        // easeOutQuart
        const eased = 1 - Math.pow(1 - progress, 4);
        const current = Math.round(target * eased);
        el.textContent = formatVal(current);
        if (progress < 1) {
          window.requestAnimationFrame(step);
        } else {
          el.textContent = formatVal(target);
        }
      };

      window.requestAnimationFrame(step);
    };

    const observer = new IntersectionObserver(
      (entries, obs) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            animateCounter(entry.target);
            obs.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.35 }
    );

    counters.forEach((c) => observer.observe(c));
  }

  function initScrollReveal() {
    const prefersReducedMotion =
      window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion || !('IntersectionObserver' in window)) return;

    const groups = [
      { selector: '.hero-copy, .hero-field-card', stagger: 90 },
      { selector: '.ledger-item', stagger: 65 },
      { selector: '.section-header', stagger: 0 },
      { selector: '.acrostic-panel, .stage-card, .value-card', stagger: 75 },
      { selector: '.gen-card', stagger: 80 },
      { selector: '.footprint-card', stagger: 80 },
      { selector: '.season-selector-bar, .season-workspace', stagger: 90 },
      { selector: '.financial-card, .timeline-card', stagger: 100 },
      { selector: '.gratitude-card', stagger: 85 },
      { selector: '.cinema-card', stagger: 70 },
      { selector: '.archive-toolbar', stagger: 0 },
    ];

    const targets = [];
    groups.forEach((g) => {
      const nodes = Array.from(document.querySelectorAll(g.selector));
      nodes.forEach((node, idx) => {
        node.classList.add('reveal-on-scroll');
        if (g.stagger > 0) {
          node.style.setProperty('--reveal-delay', `${Math.min(idx, 6) * g.stagger}ms`);
        }
        targets.push(node);
      });
    });

    const observer = new IntersectionObserver(
      (entries, obs) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            obs.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );

    targets.forEach((t) => observer.observe(t));
  }

  function initMusicPlayer() {
    const audio = document.getElementById('bg-audio');
    const widget = document.getElementById('music-widget');
    const toggleBtn = document.getElementById('music-toggle-btn');
    const metaTrigger = document.getElementById('music-meta-trigger');
    const playIcon = document.getElementById('music-play-icon');
    const statusSub = document.getElementById('music-status-sub');
    const collapseBtn = document.getElementById('music-collapse-btn');

    if (!audio || !widget) return;

    audio.volume = 0.5;
    let userPausedManually = false;
    let pausedByVideo = false;
    let unlocked = false;

    const unlockEvents = [
      'pointerdown',
      'touchstart',
      'click',
      'keydown',
      'wheel',
      'scroll',
      'mousemove',
    ];

    const removeUnlockListeners = () => {
      unlockEvents.forEach((evt) => {
        window.removeEventListener(evt, tryAutoUnlock, { capture: true });
      });
    };

    const syncUi = () => {
      const playing = !audio.paused && !audio.ended;
      widget.classList.toggle('is-playing', playing);
      if (playIcon) playIcon.textContent = playing ? '❚❚' : '▶';
      if (statusSub) {
        statusSub.textContent = playing
          ? 'Đen Vâu ft. PiaLinh · Bấm để dừng'
          : 'Đen Vâu ft. PiaLinh · Đã tạm dừng';
      }
    };

    const togglePlayback = (e) => {
      if (e) e.stopPropagation();
      unlocked = true;
      removeUnlockListeners();
      if (audio.paused) {
        userPausedManually = false;
        audio.play().then(syncUi).catch(syncUi);
      } else {
        userPausedManually = true;
        audio.pause();
        syncUi();
      }
    };

    if (toggleBtn) toggleBtn.addEventListener('click', togglePlayback);
    if (metaTrigger) {
      metaTrigger.addEventListener('click', togglePlayback);
      metaTrigger.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          togglePlayback(e);
        }
      });
    }

    if (collapseBtn) {
      collapseBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const collapsed = widget.classList.toggle('is-collapsed');
        collapseBtn.textContent = collapsed ? '+' : '–';
        collapseBtn.setAttribute('aria-label', collapsed ? 'Mở rộng trình phát nhạc' : 'Thu gọn trình phát nhạc');
      });
    }

    audio.addEventListener('play', syncUi);
    audio.addEventListener('pause', syncUi);

    function tryAutoUnlock(ev) {
      if (unlocked || userPausedManually || pausedByVideo) return;
      if (ev && ev.target && ev.target.closest && ev.target.closest('#music-widget, video')) return;
      audio
        .play()
        .then(() => {
          unlocked = true;
          removeUnlockListeners();
          syncUi();
        })
        .catch(() => {});
    }

    // Pause background music automatically when a documentary video plays
    document.addEventListener(
      'play',
      (e) => {
        if (e.target && e.target.tagName === 'VIDEO') {
          if (!audio.paused) {
            pausedByVideo = true;
            audio.pause();
          }
          document.querySelectorAll('video').forEach((v) => {
            if (v !== e.target && !v.paused) v.pause();
          });
        }
      },
      true
    );

    document.addEventListener(
      'pause',
      (e) => {
        if (e.target && e.target.tagName === 'VIDEO' && pausedByVideo && !userPausedManually) {
          const anyVideoPlaying = Array.from(document.querySelectorAll('video')).some((v) => !v.paused);
          if (!anyVideoPlaying) {
            pausedByVideo = false;
            audio.play().then(syncUi).catch(() => {});
          }
        }
      },
      true
    );

    // Attempt immediate autoplay on page open; fallback to instant start on first movement/scroll/click
    audio
      .play()
      .then(() => {
        unlocked = true;
        syncUi();
      })
      .catch(() => {
        syncUi();
        unlockEvents.forEach((evt) => {
          window.addEventListener(evt, tryAutoUnlock, { capture: true, passive: true });
        });
      });
  }

  /* --------------------------------------------------------------------------
     13. BOOTSTRAP APPLICATION
     -------------------------------------------------------------------------- */

  function init() {
    initFooterAndGlobalNav();
    renderHeroSection();
    renderMissionHeritage();
    renderSeasonTabs();
    renderActiveSeasonWorkspace();
    renderImpactLedgerAndTimeline();
    renderCinemaSection();
    initFullArchiveControls();
    renderFullArchiveResults();
    initLightboxEvents();
    initScrollProgressAndNavSpy();
    initStatCounters();
    initScrollReveal();
    initMusicPlayer();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
