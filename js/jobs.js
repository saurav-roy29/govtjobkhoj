/**
 * GovtJobKhoj — Recruitment Listings & Detail View Engine (Refined)
 * Manages job filtering, search, sorting, and dynamic detail page rendering.
 * All listings accurately represented as historical/archived notices from the 2025 database.
 */

(function () {
  'use strict';

  // Global state
  let allJobs = [];
  let filteredJobs = [];
  let currentCategory = 'all';
  let searchQuery = '';
  let currentSort = 'date-desc';
  let displayedCount = 8;
  const PAGE_INCREMENT = 6;

  // Initialize once DOM is ready
  document.addEventListener('DOMContentLoaded', async () => {
    await loadJobData();

    // Check if we are on the Job Details page
    if (document.getElementById('job-detail-root')) {
      renderJobDetailPage();
    }

    // Check if we are on the Home page or Jobs Archive page
    if (document.getElementById('jobs-list-container')) {
      initListingPage();
    }
  });

  /**
   * Load Jobs Dataset
   * Uses bundled window.GJK_JOBS_DATA first (works seamlessly on file:// protocol),
   * falls back to fetch('data/jobs.json') when served via HTTP.
   */
  async function loadJobData() {
    // 1. When served via HTTP/HTTPS, fetch fresh data/jobs.json
    if (window.location.protocol.startsWith('http')) {
      try {
        const response = await fetch('data/jobs.json');
        if (response.ok) {
          const data = await response.json();
          if (Array.isArray(data) && data.length > 0) {
            allJobs = data;
          }
        }
      } catch (err) {
        console.warn('Could not fetch data/jobs.json directly, falling back to bundled dataset:', err);
      }
    }

    // 2. Check bundled window.GJK_JOBS_DATA (offline & file:// protocol fallback)
    if ((!allJobs || allJobs.length === 0) && window.GJK_JOBS_DATA && Array.isArray(window.GJK_JOBS_DATA) && window.GJK_JOBS_DATA.length > 0) {
      allJobs = window.GJK_JOBS_DATA;
    }
    filteredJobs = Array.isArray(allJobs) ? [...allJobs] : [];
  }

  /**
   * Initialize Job Listing / Search Page
   */
  function initListingPage() {
    const urlParams = new URLSearchParams(window.location.search);
    const initialQuery = urlParams.get('q');
    const initialCat = urlParams.get('cat');
    const filterButtons = document.querySelectorAll('.filter-btn');

    // Determine page context and default category
    const loc = (window.location.pathname + window.location.href).toLowerCase();
    const isBankPage = loc.includes('bank-jobs.html');
    const isStatePage = loc.includes('state-jobs.html');
    const isFullArchive = loc.includes('jobs.html') || isBankPage || isStatePage;

    if (isFullArchive) {
      displayedCount = 20; // Show all available notices on dedicated pages
    }

    if (initialCat) {
      currentCategory = initialCat;
    } else if (isBankPage) {
      currentCategory = 'banking';
    } else if (isStatePage) {
      currentCategory = 'state';
    } else {
      const activeBtn = document.querySelector('.filter-btn.active[data-category]');
      if (activeBtn) {
        currentCategory = activeBtn.getAttribute('data-category') || 'all';
      }
    }

    // Sync button UI with currentCategory
    if (filterButtons && filterButtons.length > 0) {
      filterButtons.forEach(b => {
        if (b.getAttribute('data-category') === currentCategory) {
          b.classList.add('active');
        } else {
          b.classList.remove('active');
        }
      });

      // Setup Category Filter Buttons click
      filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
          const cat = btn.getAttribute('data-category');
          if (cat) {
            filterButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentCategory = cat;
            applyFiltersAndRender();
          }
        });
      });
    }

    // Setup Search Input
    const searchInput = document.getElementById('jobs-search-input');
    if (searchInput) {
      if (initialQuery) {
        searchInput.value = initialQuery;
        searchQuery = initialQuery.toLowerCase();
      }
      searchInput.addEventListener('input', (e) => {
        searchQuery = e.target.value.toLowerCase().trim();
        applyFiltersAndRender();
      });
    }

    // Setup Sort Select
    const sortSelect = document.getElementById('jobs-sort-select');
    if (sortSelect) {
      sortSelect.addEventListener('change', (e) => {
        currentSort = e.target.value;
        applyFiltersAndRender();
      });
    }

    // Setup Load More Button
    const loadMoreBtn = document.getElementById('load-more-btn');
    if (loadMoreBtn) {
      loadMoreBtn.addEventListener('click', () => {
        displayedCount += PAGE_INCREMENT;
        renderJobsList();
      });
    }

    // Handle Browser Back / Forward Navigation
    window.addEventListener('popstate', () => {
      const p = new URLSearchParams(window.location.search);
      const q = p.get('q') || '';
      const c = p.get('cat') || (isBankPage ? 'banking' : isStatePage ? 'state' : 'all');
      searchQuery = q.toLowerCase().trim();
      currentCategory = c;
      if (searchInput) searchInput.value = q;
      filterButtons.forEach(b => {
        if (b.getAttribute('data-category') === c) {
          b.classList.add('active');
        } else {
          b.classList.remove('active');
        }
      });
      applyFiltersAndRender();
    });

    applyFiltersAndRender();
  }

  /**
   * Filter and Sort Data
   */
  function applyFiltersAndRender() {
    filteredJobs = allJobs.filter(job => {
      // Category / Sector filter
      let matchesCat = true;
      if (currentCategory !== 'all') {
        if (currentCategory === 'banking') {
          matchesCat = job.sector === 'Banking' || job.sector === 'Banking & Agriculture' || job.categories.some(c => c.toLowerCase().includes('bank') || c.toLowerCase().includes('ibps') || c.toLowerCase().includes('sbi') || c.toLowerCase().includes('nabard'));
        } else if (currentCategory === 'state') {
          matchesCat = job.sector === 'State Government' || job.id === 105 || job.categories.some(c => c.toLowerCase().includes('bihar') || c.toLowerCase().includes('state govt'));
        } else if (currentCategory === 'central') {
          matchesCat = job.sector.includes('Central') || job.sector.includes('PSU') || job.categories.some(c => c.toLowerCase().includes('central') || c.toLowerCase().includes('upsc') || c.toLowerCase().includes('ssc'));
        } else {
          matchesCat = job.categories.some(c => c.toLowerCase() === currentCategory.toLowerCase());
        }
      }

      // Search Query filter (matches title, organization, qualification, and state/location)
      let matchesSearch = true;
      if (searchQuery) {
        const titleMatch = job.title.toLowerCase().includes(searchQuery);
        const orgMatch = job.org.toLowerCase().includes(searchQuery);
        const qualMatch = job.qualification.toLowerCase().includes(searchQuery);
        const locMatch = (job.location || '').toLowerCase().includes(searchQuery);
        const catMatch = job.categories.some(c => c.toLowerCase().includes(searchQuery));
        matchesSearch = titleMatch || orgMatch || qualMatch || locMatch || catMatch;
      }

      return matchesCat && matchesSearch;
    });

    // Sorting
    if (currentSort === 'date-desc') {
      filteredJobs.sort((a, b) => new Date(b.publish_date) - new Date(a.publish_date));
    } else if (currentSort === 'date-asc') {
      filteredJobs.sort((a, b) => new Date(a.publish_date) - new Date(b.publish_date));
    } else if (currentSort === 'vacancies-desc') {
      filteredJobs.sort((a, b) => {
        const numA = parseInt(a.vacancies.replace(/[^0-9]/g, '')) || 0;
        const numB = parseInt(b.vacancies.replace(/[^0-9]/g, '')) || 0;
        return numB - numA;
      });
    }

    renderJobsList();
  }

  /**
   * Helper: Determine badge style, icon, and label based on notice classification
   */
  function getNoticeBadge(job) {
    // 1. Preserved historical notices
    if (job.is_historical === true || job.status === 'Archived' || job.record_type === 'historical_listing') {
      return {
        className: 'badge-archived',
        label: job.status_label || 'Archived Notice (2025)',
        icon: '<svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>',
        title: 'Historical notice — verify details with the recruiting organization',
        styleColor: 'var(--color-archived)'
      };
    }

    // 2. Result Announcements
    if (job.record_type === 'result_announcement' || job.badge_type === 'result' || job.status === 'Result Declared') {
      return {
        className: 'badge-navy',
        label: job.status_label || 'Result Announcement',
        icon: '<svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="8" r="7"></circle><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"></polyline></svg>',
        title: 'Official result announcement from recruiting authority',
        styleColor: 'var(--color-midnight)'
      };
    }

    // 3. Admit Card / Call Letter
    if (job.record_type === 'admit_card_call_letter' || job.badge_type === 'call_letter' || job.status === 'Call Letter Available') {
      return {
        className: 'badge-saffron',
        label: job.status_label || 'Admit Card / Call Letter',
        icon: '<svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>',
        title: 'Call letter / admit card released on official portal',
        styleColor: 'var(--color-saffron)'
      };
    }

    // 4. Examination Schedule / Notification
    if (job.record_type === 'exam_notification' || job.badge_type === 'exam_schedule' || job.status === 'Exam Scheduled') {
      return {
        className: 'badge-navy',
        label: job.status_label || 'Examination Schedule',
        icon: '<svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>',
        title: 'Official examination notification or schedule',
        styleColor: 'var(--color-midnight)'
      };
    }

    // 5. Addendum / Corrigendum
    if (job.record_type === 'addendum_corrigendum' || job.badge_type === 'addendum' || job.status === 'Notice Update') {
      return {
        className: 'badge-saffron',
        label: job.status_label || 'Addendum / Corrigendum',
        icon: '<svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
        title: 'Corrigendum or amendment to earlier recruitment notice',
        styleColor: 'var(--color-saffron)'
      };
    }

    // 6. General Clarification
    if (job.record_type === 'general_clarification' || job.badge_type === 'clarification') {
      return {
        className: 'badge-navy',
        label: job.status_label || 'Official Clarification',
        icon: '<svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>',
        title: 'Official recruitment clarification circular',
        styleColor: 'var(--color-midnight)'
      };
    }

    // 7. Closed Recruitment
    if (job.status === 'Closed' || job.record_type === 'closed_recruitment') {
      return {
        className: 'badge-archived',
        label: 'Closed Recruitment',
        icon: '<svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>',
        title: 'Application period has ended',
        styleColor: 'var(--color-archived)'
      };
    }

    // 8. Open application (Only show active vacancy when verified open)
    if (job.is_open_vacancy === true && job.badge_type === 'active_vacancy') {
      return {
        className: 'badge-success',
        label: job.status_label || 'Active Vacancy',
        icon: '<svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>',
        title: 'Verified active recruitment notice with open application period',
        styleColor: '#059669'
      };
    }

    // 9. Default: Official Notification (New recruitment notice with unknown/unverified deadline)
    return {
      className: 'badge-saffron',
      label: job.status_label || 'Official Notification',
      icon: '<svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>',
      title: 'Official notification released on authorized commission portal',
      styleColor: 'var(--color-saffron)'
    };
  }

  /**
   * Render Cards Grid (Refined, Compact, and Consistent)
   */
  function renderJobsList() {
    const container = document.getElementById('jobs-list-container');
    const counterEl = document.getElementById('results-counter');
    const loadMoreBtn = document.getElementById('load-more-btn');

    if (!container) return;

    if (!allJobs || allJobs.length === 0) {
      container.innerHTML = `
        <div class="empty-state-box" style="grid-column: 1 / -1;">
          <div class="empty-state-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
          </div>
          <h3 class="empty-state-title">Unable to Load Recruitment Dataset</h3>
          <p class="empty-state-desc">The job notices dataset could not be loaded. Please ensure data/jobs.json or js/data.js is accessible.</p>
        </div>
      `;
      if (counterEl) counterEl.textContent = 'Error loading notices';
      if (loadMoreBtn) loadMoreBtn.style.display = 'none';
      return;
    }

    if (filteredJobs.length === 0) {
      if (counterEl) counterEl.textContent = '0 matching notices';
      container.innerHTML = `
        <div class="empty-state-box" style="grid-column: 1 / -1;">
          <div class="empty-state-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          </div>
          <h3 class="empty-state-title">No notices match your search</h3>
          <p class="empty-state-desc">Try clearing your search query or selecting a different category filter.</p>
          <button class="btn btn-navy btn-sm" onclick="resetFilters()">Reset All Filters</button>
        </div>
      `;
      if (loadMoreBtn) loadMoreBtn.style.display = 'none';
      return;
    }

    if (counterEl) {
      const scopeLabel = currentCategory === 'banking' ? 'banking notices' : 
                         currentCategory === 'state' ? 'state notices' : 
                         currentCategory === 'central' ? 'central/PSU notices' : 
                         'recruitment notices';
      counterEl.textContent = `Showing ${Math.min(displayedCount, filteredJobs.length)} of ${filteredJobs.length} ${scopeLabel}`;
    }

    const visibleItems = filteredJobs.slice(0, displayedCount);

    container.innerHTML = visibleItems.map(job => {
      const badgeInfo = getNoticeBadge(job);
      const badgeHtml = `
          <span class="badge ${badgeInfo.className}" title="${badgeInfo.title}">
            ${badgeInfo.icon}
            ${escapeHtml(badgeInfo.label)}
          </span>`;

      return `
      <article class="job-card" id="job-card-${job.id}">
        <!-- Top: Organization & Status -->
        <div class="job-card-header">
          <span class="job-org-tag" title="${escapeHtml(job.org)}">${escapeHtml(job.org)}</span>
          ${badgeHtml}
        </div>
        
        <!-- Middle: Title -->
        <h3 class="job-card-title">
          <a href="job-details.html?id=${job.id}" title="${escapeHtml(job.title)}">${escapeHtml(job.title)}</a>
        </h3>

        <!-- Bottom: Metadata Grid -->
        <div class="job-meta-grid">
          <div class="meta-field">
            <span class="meta-field-label">Vacancies</span>
            <span class="meta-field-value">${escapeHtml(job.vacancies)}</span>
          </div>
          <div class="meta-field">
            <span class="meta-field-label">Eligibility</span>
            <span class="meta-field-value" title="${escapeHtml(job.qualification)}">${truncate(job.qualification, 24)}</span>
          </div>
          <div class="meta-field">
            <span class="meta-field-label">Mode</span>
            <span class="meta-field-value">${escapeHtml(job.app_mode)}</span>
          </div>
          <div class="meta-field meta-field-deadline">
            <span class="meta-field-label">Deadline</span>
            <span class="meta-field-value deadline-val">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="vertical-align: -1px; margin-right: 2px;"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
              ${escapeHtml(job.last_date)}
            </span>
          </div>
        </div>

        <!-- Footer: Date & Action -->
        <div class="job-card-footer">
          <span class="job-publish-date">Published: ${job.publish_date}</span>
          <a href="job-details.html?id=${job.id}" class="btn btn-navy btn-sm btn-view-details">
            View Details
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"></polyline></svg>
          </a>
        </div>
      </article>
      `;
    }).join('');

    // Load More Visibility
    if (loadMoreBtn) {
      if (displayedCount >= filteredJobs.length) {
        loadMoreBtn.style.display = 'none';
      } else {
        loadMoreBtn.style.display = 'inline-flex';
      }
    }
  }

  /**
   * Reset Filters
   */
  window.resetFilters = function () {
    const loc = (window.location.pathname + window.location.href).toLowerCase();
    const isBankPage = loc.includes('bank-jobs.html');
    const isStatePage = loc.includes('state-jobs.html');
    
    currentCategory = isBankPage ? 'banking' : isStatePage ? 'state' : 'all';
    searchQuery = '';
    const searchInput = document.getElementById('jobs-search-input');
    if (searchInput) searchInput.value = '';
    
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(b => {
      if (b.getAttribute('data-category') === currentCategory) {
        b.classList.add('active');
      } else {
        b.classList.remove('active');
      }
    });
    applyFiltersAndRender();
  };

  /**
   * Render Job Detail View
   */
  function renderJobDetailPage() {
    const root = document.getElementById('job-detail-root');
    if (!root) return;

    const urlParams = new URLSearchParams(window.location.search);
    const jobId = urlParams.get('id');
    const jobSlug = urlParams.get('slug');

    // Find job
    let job = null;
    if (jobId) {
      job = allJobs.find(j => j.id === parseInt(jobId, 10));
    } else if (jobSlug) {
      job = allJobs.find(j => j.slug === jobSlug);
    } else if (allJobs.length > 0) {
      job = allJobs[0];
    }

    if (!job) {
      root.innerHTML = `
        <div class="empty-state-box">
          <div class="empty-state-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
          </div>
          <h2 class="empty-state-title">Recruitment Notice Not Found</h2>
          <p class="empty-state-desc">The requested recruitment notification could not be located in our archive dataset.</p>
          <a href="jobs.html" class="btn btn-primary btn-sm">Browse All Archived Opportunities</a>
        </div>
      `;
      return;
    }

    document.title = `${job.title} | GovtJobKhoj`;

    const relatedJobs = allJobs
      .filter(j => j.id !== job.id && (j.sector === job.sector || j.org === job.org))
      .slice(0, 3);

    const badgeInfo = getNoticeBadge(job);
    const statusBadge = `
      <span class="badge ${badgeInfo.className}" title="${badgeInfo.title}">
        ${badgeInfo.icon}
        ${escapeHtml(badgeInfo.label)}
      </span>`;
    
    const sourceStatusText = `
      <span class="fact-val" style="color: ${badgeInfo.styleColor}; font-weight: 700;">
        ${escapeHtml(badgeInfo.label)}
      </span>`;

    let alertBoxHtml = '';
    if (job.is_historical === true || job.status === 'Archived' || job.record_type === 'historical_listing') {
      alertBoxHtml = `
          <div class="notice-box" role="alert" style="margin-top: 0; margin-bottom: 1.75rem;">
            <div class="notice-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
            </div>
            <div class="notice-text">
              <strong>Historical notice — verify details directly with the recruiting organization.</strong> This listing was preserved from the August 2025 archive. Always verify eligibility, application dates, and recruitment details directly in the official notification circular prior to applying.
            </div>
          </div>`;
    } else if (job.record_type === 'result_announcement') {
      alertBoxHtml = `
          <div class="notice-box" role="alert" style="margin-top: 0; margin-bottom: 1.75rem; background-color: #F0F4F8; border: 1px solid #CBD5E1; color: var(--color-midnight);">
            <div class="notice-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="8" r="7"></circle><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"></polyline></svg>
            </div>
            <div class="notice-text">
              <strong>Official Result Announcement.</strong> This result circular was issued by ${escapeHtml(job.org)}. Verify recommendation lists, cut-off marks, and roll numbers via the official commission links below.
            </div>
          </div>`;
    } else if (job.record_type === 'admit_card_call_letter') {
      alertBoxHtml = `
          <div class="notice-box" role="alert" style="margin-top: 0; margin-bottom: 1.75rem; background-color: #FFF7ED; border: 1px solid #FED7AA; color: #9A3412;">
            <div class="notice-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
            </div>
            <div class="notice-text">
              <strong>Official Call Letter / Admit Card Release.</strong> Candidates are advised to download their exam call letter directly from the authorized portal (${escapeHtml(job.org)}) via the links provided below.
            </div>
          </div>`;
    } else if (job.record_type === 'exam_notification') {
      alertBoxHtml = `
          <div class="notice-box" role="alert" style="margin-top: 0; margin-bottom: 1.75rem; background-color: #F0F4F8; border: 1px solid #CBD5E1; color: var(--color-midnight);">
            <div class="notice-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
            </div>
            <div class="notice-text">
              <strong>Official Examination Schedule.</strong> This examination timetable / notification was released by ${escapeHtml(job.org)}. Review reporting times, exam slots, and instructions via the official source below.
            </div>
          </div>`;
    } else if (job.record_type === 'addendum_corrigendum') {
      alertBoxHtml = `
          <div class="notice-box" role="alert" style="margin-top: 0; margin-bottom: 1.75rem; background-color: #FFF7ED; border: 1px solid #FED7AA; color: #9A3412;">
            <div class="notice-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
            </div>
            <div class="notice-text">
              <strong>Official Corrigendum / Addendum.</strong> This notice introduces an amendment or update to an earlier recruitment process announced by ${escapeHtml(job.org)}. Read the official circular below.
            </div>
          </div>`;
    } else if (job.is_open_vacancy === true) {
      alertBoxHtml = `
          <div class="notice-box verified-notice-box" role="alert" style="margin-top: 0; margin-bottom: 1.75rem; background-color: #ECFDF5; border: 1px solid #A7F3D0; color: #065F46;">
            <div class="notice-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
            </div>
            <div class="notice-text">
              <strong>Verified Active Recruitment Notice.</strong> This recruitment circular was retrieved from the authorized commission portal (${escapeHtml(job.org)}). Verify full eligibility criteria, terms, and apply directly via the authorized links below.
            </div>
          </div>`;
    } else {
      alertBoxHtml = `
          <div class="notice-box" role="alert" style="margin-top: 0; margin-bottom: 1.75rem; background-color: #FFF7ED; border: 1px solid #FED7AA; color: #9A3412;">
            <div class="notice-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>
            </div>
            <div class="notice-text">
              <strong>Official Recruitment Circular.</strong> Published by ${escapeHtml(job.org)}. Check the official notification document below to verify qualification criteria, vacancy details, and application instructions.
            </div>
          </div>`;
    }

    root.innerHTML = `
      <div class="detail-layout-grid">
        <!-- Main Column -->
        <main class="detail-main">
          <!-- Breadcrumb Navigation -->
          <nav class="breadcrumbs" aria-label="Breadcrumb">
            <a href="index.html">Home</a>
            <span class="breadcrumbs-separator">/</span>
            <a href="jobs.html">Recruitments</a>
            <span class="breadcrumbs-separator">/</span>
            <span aria-current="page">${truncate(job.title, 36)}</span>
          </nav>

          <header class="detail-header">
            <div style="display: flex; gap: 0.4rem; align-items: center; flex-wrap: wrap; margin-bottom: 0.5rem;">
              <span class="badge badge-saffron">${escapeHtml(job.sector)}</span>
              ${statusBadge}
            </div>
            
            <h1 class="detail-title">${escapeHtml(job.title)}</h1>
            
            <div style="font-size: 0.8125rem; color: var(--color-muted-text); display: flex; gap: 1.25rem; flex-wrap: wrap;">
              <span><strong>Organization:</strong> ${escapeHtml(job.org)}</span>
              <span><strong>Notice Date:</strong> ${job.publish_date}</span>
            </div>
          </header>

          <!-- Key Facts Box -->
          <section class="quick-facts-box" aria-label="Key Recruitment Facts">
            <h2 class="quick-facts-title">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
              Key Recruitment Overview
            </h2>
            <div class="facts-grid">
              <div class="fact-item">
                <span class="fact-label">Total Vacancies</span>
                <span class="fact-val">${escapeHtml(job.vacancies)}</span>
              </div>
              <div class="fact-item">
                <span class="fact-label">Application Deadline</span>
                <span class="fact-val text-saffron">${escapeHtml(job.last_date)}</span>
              </div>
              <div class="fact-item">
                <span class="fact-label">Application Mode</span>
                <span class="fact-val">${escapeHtml(job.app_mode)}</span>
              </div>
              <div class="fact-item">
                <span class="fact-label">Eligibility / Qualification</span>
                <span class="fact-val">${escapeHtml(job.qualification)}</span>
              </div>
              <div class="fact-item">
                <span class="fact-label">Recruitment Status</span>
                <span class="fact-val">${escapeHtml(job.status)}</span>
              </div>
              <div class="fact-item">
                <span class="fact-label">Source Status</span>
                ${sourceStatusText}
              </div>
            </div>
          </section>

          <!-- Notice Alert Box -->
          ${alertBoxHtml}

          <!-- Original Article & Details Content (Hindi & English) -->
          <article class="post-rich-content hindi-text">
            ${job.content_html}
          </article>

          <!-- Original Recruitment Source Links -->
          <section style="margin-top: 2.5rem; padding-top: 1.5rem; border-top: 1px solid var(--color-border);">
            <h3 style="font-size: 1.15rem; font-weight: 800; color: var(--color-midnight); margin-bottom: 0.5rem;">
              Original Recruitment Source Links
            </h3>
            <p style="font-size: 0.8125rem; color: var(--color-muted-text); margin-bottom: 1rem;">
              Original recruitment source available below. Always check authoritative circular documents on the respective portal:
            </p>
            <div class="action-links-stack">
              ${job.official_links.map(link => {
                const domain = extractDomain(link.url);
                const isKnownOfficial = isOfficialDomain(domain);
                const badgeHtml = isKnownOfficial ? 
                  `<span class="badge badge-success" style="font-size: 0.6875rem;">Official Portal</span>` : 
                  `<span class="badge badge-archived" style="font-size: 0.6875rem;">Preserved Link (Verify at Source)</span>`;
                return `
                  <a href="${escapeHtml(link.url)}" target="_blank" rel="noopener noreferrer" class="official-btn primary" style="justify-content: space-between;">
                    <div style="display: flex; flex-direction: column; align-items: flex-start; text-align: left;">
                      <span style="font-weight: 700;">${escapeHtml(link.text)}</span>
                      <span style="font-size: 0.75rem; opacity: 0.85;">${escapeHtml(domain)}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                      ${badgeHtml}
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                    </div>
                  </a>
                `;
              }).join('')}
            </div>
          </section>
        </main>

        <!-- Sticky Sidebar Column -->
        <aside class="detail-sidebar">
          <div class="action-card">
            <h3 class="action-card-title">Recruitment Actions</h3>
            <div class="action-links-stack">
              ${job.official_links.length > 0 ? `
                <a href="${escapeHtml(job.official_links[0].url)}" target="_blank" rel="noopener noreferrer" class="btn btn-primary" style="width: 100%;">
                  Open Original Notice
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                </a>
              ` : ''}
              <button class="btn btn-secondary btn-sm" onclick="window.print()" style="width: 100%;">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 6 2 18 2 18 9"></polyline><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path><rect x="6" y="14" width="12" height="8"></rect></svg>
                Print Notice
              </button>
            </div>
          </div>

          <div class="action-card">
            <h3 class="action-card-title">Related Archive Notices</h3>
            <div style="display: flex; flex-direction: column; gap: 0.75rem;">
              ${relatedJobs.map(rj => `
                <div style="padding-bottom: 0.65rem; border-bottom: 1px solid var(--color-border-subtle);">
                  <span style="font-size: 0.6875rem; font-weight: 700; color: var(--color-saffron); text-transform: uppercase;">${escapeHtml(rj.org)}</span>
                  <h4 style="font-size: 0.8125rem; font-weight: 700; margin: 1px 0 3px;">
                    <a href="job-details.html?id=${rj.id}" style="color: var(--color-dark-text);">${truncate(rj.title, 50)}</a>
                  </h4>
                  <span style="font-size: 0.7rem; color: var(--color-muted-text);">Deadline: ${rj.last_date}</span>
                </div>
              `).join('')}
            </div>
            <a href="jobs.html" class="btn btn-secondary btn-sm" style="width: 100%; margin-top: 0.75rem;">View All Notices</a>
          </div>
        </aside>
      </div>
    `;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function truncate(str, max) {
    if (!str) return '';
    return str.length > max ? str.substring(0, max) + '...' : str;
  }

  function extractDomain(url) {
    try {
      const u = new URL(url);
      return u.hostname;
    } catch {
      return 'Official Portal';
    }
  }

  function isOfficialDomain(hostname) {
    if (!hostname) return false;
    const h = hostname.toLowerCase();
    const knownOfficial = [
      'sbi.co.in', 'ibps.in', 'bihar.gov.in', 'rbi.org.in', 'pnbindia.in',
      'bankofbaroda.in', 'centralbankofindia.co.in', 'punjabandsindbank.co.in',
      'brbnmpl.co.in', 'unionbankofindia.co.in', 'iob.in', 'ucobank.com',
      'mscbank.com', 'bankofmaharashtra.in', 'tmbnet.in', 'nabard.org', 'bobcaps.in',
      'upsc.gov.in', 'upsconline.nic.in', 'ncs.gov.in', 'ssc.gov.in', 'drdo.gov.in', 'isro.gov.in'
    ];
    return knownOfficial.some(domain => h === domain || h.endsWith('.' + domain)) || h.endsWith('.gov.in') || h.endsWith('.nic.in');
  }

})();
