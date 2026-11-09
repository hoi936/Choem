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
      if (label.toLowerCase().includes('vnđ') || val >= 100000) {
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
    const s3 = seasons[2] || seasons[0];

    const heroCards = [
      {
        featured: true,
        seasonIndex: 6,
        badge: `MÙA 7 · ${formatShortMonthYear(s7.event_date || s7.start_date).toUpperCase()} · ĐAKRÔNG`,
        photo: s7.hero_photo,
        title: `${cleanText(s7.official_name)} — ${cleanText(s7.theme)}`,
        meta: cleanText((s7.locations && s7.locations[0]) || 'Xã Tà Long, huyện Đakrông, tỉnh Quảng Trị'),
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
        seasonIndex: 2,
        badge: `MÙA 3 · ${formatShortMonthYear(s3.event_date || s3.start_date).toUpperCase()}`,
        photo: s3.hero_photo,
        title: `${cleanText(s3.official_name)} — Tiếp nối sứ mệnh sân chơi vùng cao`,
        meta: cleanText((s3.locations && s3.locations[0]) || 'Xã Hướng Phùng, huyện Hướng Hóa, tỉnh Quảng Trị'),
      },
    ];

    collageEl.innerHTML = heroCards
      .map(
        (card) => `
        <article class="hero-field-card ${card.featured ? 'featured' : ''}" data-jump-season="${card.seasonIndex}" tabindex="0" role="button" aria-label="Xem chi tiết ${escapeHtml(card.title)}">
          <div class="hero-card-media">
            <img src="${escapeHtml(card.photo)}" alt="${escapeHtml(card.title)}" loading="eager" />
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

    // 4 Leadership Generations derived from actual seasons
    const gensEl = document.getElementById('generations-grid');
    if (gensEl) {
      const gens = [
        {
          badge: 'THẾ HỆ SÁNG LẬP · 2023',
          title: 'Mùa 1 — “Sân chơi cho em”',
          period: 'Trần Ngọc Tâm Phúc (Founder) · Nguyễn Thùy Linh',
          focus: 'Khởi lập dự án dưới sự bảo trợ của Thành đoàn Đông Hà, thi công 02 sân chơi tái chế tại bản Ho Le & Tà Rùng (xã Húc).',
        },
        {
          badge: 'THẾ HỆ MỞ RỘNG · ĐẦU 2024',
          title: 'Mùa 2 & mùa 3',
          period: 'Triệu Vân (Triệu Phong) & Hướng Phùng (Hướng Hóa)',
          focus: 'Đưa mô hình kịch giáo dục sức khỏe “Răng xinh cho em” về vùng bãi ngang và khánh thành sân chơi tại Chênh Vênh, Hướng Choa.',
        },
        {
          badge: 'THẾ HỆ CHUYÊN SÂU · 2024 – 2025',
          title: 'Mùa 4, mùa 5 & mùa 6',
          period: 'Triệu Vân · Tân Thành · Vĩnh Ô (Vĩnh Linh)',
          focus: 'Tập trung sâu vào kỹ năng sinh tồn và bảo vệ trẻ em qua 3 chiến dịch “Phao xinh cho em”, “An toàn cho em” và “An toàn cho em 2”.',
        },
        {
          badge: 'THẾ HỆ KẾ THỪA · 2025 – 2026',
          title: 'Mùa 7 — “Hành trang cho em”',
          period: 'Điểm trường Pa Hy · Tiểu học Tà Long (Đakrông)',
          focus: 'Tuyên truyền phòng chống đuối nước, trao tặng 137 bộ dụng cụ học tập, áo trắng và 345 đầu sách thiếu nhi trước thềm năm học mới.',
        },
      ];

      gensEl.innerHTML = gens
        .map(
          (g) => `
          <article class="gen-card">
            <span class="gen-badge">${escapeHtml(g.badge)}</span>
            <h4 class="gen-title">${formatRichText(g.title)}</h4>
            <span class="gen-period">${escapeHtml(g.period)}</span>
            <p class="gen-focus">${formatRichText(g.focus)}</p>
          </article>
        `
        )
        .join('');
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

    workspace.innerHTML = `
      <div class="season-overview-grid">
        <figure class="season-hero-figure" id="season-hero-trigger" tabindex="0" role="button" aria-label="Phóng to ảnh tiêu biểu của ${escapeHtml(s.official_name)}">
          <div class="season-hero-img-wrap">
            <img src="${escapeHtml(s.hero_photo)}" alt="${escapeHtml(s.official_name)} — ${escapeHtml(s.theme)}" />
          </div>
          <figcaption class="season-hero-caption">
            <span><strong>Hình ảnh tiêu biểu:</strong> ${formatRichText(s.official_name)}</span>
            <span class="meta-pill accent">Bấm để xem ảnh lớn ↗</span>
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

    // Bind Hero image click to open Lightbox
    const heroTrigger = document.getElementById('season-hero-trigger');
    if (heroTrigger && sPhotos.length > 0) {
      const openHeroLightbox = () => {
        const heroIdx = sPhotos.findIndex((p) => p.local_path === s.hero_photo);
        openLightbox(sPhotos, heroIdx >= 0 ? heroIdx : 0);
      };
      heroTrigger.addEventListener('click', openHeroLightbox);
      heroTrigger.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          openHeroLightbox();
        }
      });
    }

    // Bind Sub-tab buttons
    workspace.querySelectorAll('[data-subtab]').forEach((btn) => {
      btn.addEventListener('click', () => {
        state.seasonSubTab = btn.getAttribute('data-subtab') || 'photos';
        renderActiveSeasonWorkspace();
      });
    });

    renderSeasonSubTabContent(s, sPhotos, sPosts, sVideos);
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
              <article class="photo-card" data-season-photo-idx="${idx}" tabindex="0" role="button" aria-label="Xem ảnh ${escapeHtml(ph.title_clean)}">
                <div class="photo-thumb-wrap">
                  <img src="${escapeHtml(ph.local_path)}" alt="${escapeHtml(ph.title_clean)}" loading="lazy" />
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

    container.innerHTML = `
      <div class="season-posts-grid">
        <div class="post-card">
          <span class="panel-tag">MỤC TIÊU CỦA CHUYẾN ĐI</span>
          <h4 class="post-title">Mong muốn gửi trao trong ${formatRichText(s.official_name)}</h4>
          <ul class="verify-badges-list">
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
          <span class="panel-tag">NHỮNG VIỆC ĐÃ CÙNG NHAU THỰC HIỆN</span>
          <h4 class="post-title">Hoạt động từ lúc gây quỹ đến ngày lên điểm trường</h4>
          <ul class="verify-badges-list">
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

    return `
      <article class="post-card" data-post-id="${escapeHtml(post.post_id)}">
        <div class="post-card-top">
          <span class="category-badge cat-${escapeHtml(post.category_id)}">${escapeHtml(post.category_label)}</span>
          <time class="post-date">Mùa ${post.season_number} · ${formatViDate(post.published_at)}</time>
        </div>
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
  }

  /* --------------------------------------------------------------------------
     7. CHƯƠNG 03: BẢNG MINH BẠCH TÀI CHÍNH & DÒNG THỜI GIAN 15 CỘT MỐC
     -------------------------------------------------------------------------- */

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
                <img src="${escapeHtml(ph.local_path)}" alt="${escapeHtml(ph.title_clean)}" loading="lazy" />
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
     12. BOOTSTRAP APPLICATION
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
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
