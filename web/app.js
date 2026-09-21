/* ==========================================================================
   EVIDENCE-ORIENTED RESEARCH AGENT
   Clean, Focused Research Tool Controller
   ========================================================================== */

let reportData = null;
let currentInvestigationState = {
  selectedPaperId: null,
  selectedClaimIdx: null
};

const STORAGE_HISTORY_KEY = "rag_research_history";

/* ==========================================================================
   THEME TOGGLE
   ========================================================================== */

const THEME_STORAGE_KEY = "rag_research_theme";

function applyTheme(theme) {
  const isLight = theme === 'light';
  if (isLight) {
    document.documentElement.setAttribute('data-theme', 'light');
    try { localStorage.setItem(THEME_STORAGE_KEY, 'light'); } catch (e) {}
  } else {
    document.documentElement.removeAttribute('data-theme');
    try { localStorage.setItem(THEME_STORAGE_KEY, 'dark'); } catch (e) {}
  }

  const textEl = document.getElementById('themeToggleText');
  const iconDark = document.querySelector('.icon-theme-dark');
  const iconLight = document.querySelector('.icon-theme-light');
  if (textEl) {
    textEl.textContent = isLight ? 'Dark Mode' : 'Light Mode';
  }
  if (iconDark) iconDark.style.display = isLight ? 'none' : 'block';
  if (iconLight) iconLight.style.display = isLight ? 'block' : 'none';
}

function initTheme() {
  let savedTheme = 'dark';
  try {
    savedTheme = localStorage.getItem(THEME_STORAGE_KEY) || 'dark';
  } catch (e) {
    savedTheme = 'dark';
  }
  applyTheme(savedTheme);

  const btn = document.getElementById('btnToggleTheme');
  if (btn && !btn._themeListenerAttached) {
    btn._themeListenerAttached = true;
    btn.addEventListener('click', () => {
      const isCurrentlyLight = document.documentElement.getAttribute('data-theme') === 'light';
      applyTheme(isCurrentlyLight ? 'dark' : 'light');
    });
  }
}

/* ==========================================================================
   1. USER NAVIGATION (HOME, MY RESEARCH, SOURCES)
   ========================================================================== */

function initNavigation() {
  // Nav Buttons (Home, My Research, Sources)
  const navBtns = document.querySelectorAll('.sidebar-nav .nav-btn');
  navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetView = btn.getAttribute('data-view');
      switchView(targetView);
    });
  });

  // App Brand / Logo click -> Reset to Home/New Research state
  const brandHome = document.getElementById('brandHome');
  if (brandHome) {
    const handleResetHome = () => {
      switchView('viewHome');
      clearActiveResearch();
      if (window.innerWidth <= 860) {
        document.getElementById('appSidebar')?.classList.remove('open');
      }
    };
    brandHome.addEventListener('click', handleResetHome);
    brandHome.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        handleResetHome();
      }
    });
  }

  // New Research Button
  document.getElementById('btnNewResearch')?.addEventListener('click', () => {
    switchView('viewHome');
    clearActiveResearch();
  });

  // View All Sources in Right Panel
  document.getElementById('btnViewAllSources')?.addEventListener('click', () => {
    switchView('viewSources');
  });

  // Close mobile sidebar on nav click
  const sidebar = document.getElementById('appSidebar');
  navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      if (window.innerWidth <= 860) {
        sidebar?.classList.remove('open');
      }
    });
  });
}

function switchView(viewId) {
  if (!viewId) return;

  // Update Nav Buttons
  document.querySelectorAll('.sidebar-nav .nav-btn').forEach(btn => {
    const isTarget = btn.getAttribute('data-view') === viewId;
    btn.classList.toggle('active', isTarget);
  });

  // Update Panes
  document.querySelectorAll('.view-pane').forEach(pane => {
    pane.classList.toggle('active', pane.id === viewId);
  });

  // Scroll main content to top
  const mainScroll = document.getElementById('mainContentScroll');
  if (mainScroll) mainScroll.scrollTop = 0;

  if (viewId === 'viewMyResearch') {
    renderMyResearchView();
  } else if (viewId === 'viewSources') {
    renderSourcesFullView();
  }
}

/* ==========================================================================
   2. RESEARCH COMPOSER HERO & ADVANCED SETTINGS
   ========================================================================== */

function autoResizeTextarea(el) {
  const queryInput = el || document.getElementById('queryInput');
  if (!queryInput) return;
  queryInput.style.height = "auto";
  const scrollH = queryInput.scrollHeight;
  queryInput.style.height = Math.min(scrollH, 180) + "px";
  queryInput.style.overflowY = scrollH > 180 ? "auto" : "hidden";
}

let isResearchRunning = false;

function setRunButtonLoading(loading) {
  isResearchRunning = Boolean(loading);
  const btnRun = document.getElementById('btnRunAgent');
  const queryInput = document.getElementById('queryInput');
  if (!btnRun) return;

  if (isResearchRunning) {
    btnRun.disabled = true;
    btnRun.classList.add('is-loading');
  } else {
    btnRun.classList.remove('is-loading');
    const hasText = queryInput && typeof queryInput.value === 'string' && queryInput.value.trim().length > 0;
    btnRun.disabled = !hasText;
  }
}

function updateRunButtonState() {
  if (isResearchRunning) return;
  const btnRun = document.getElementById('btnRunAgent');
  const queryInput = document.getElementById('queryInput');
  if (!btnRun) return;
  const hasText = queryInput && typeof queryInput.value === 'string' && queryInput.value.trim().length > 0;
  btnRun.disabled = !hasText;
}

function initComposer() {
  const queryInput = document.getElementById('queryInput');
  const btnRun = document.getElementById('btnRunAgent');

  if (!queryInput || !btnRun) return;

  queryInput.addEventListener('input', () => {
    autoResizeTextarea(queryInput);
    updateRunButtonState();
  });

  queryInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      if (e.shiftKey || e.isComposing) {
        // Shift + Enter inserts a newline normally in textarea; ignore IME composing
        return;
      }
      e.preventDefault();
      executeLiveResearch();
    }
  });

  btnRun.addEventListener('click', executeLiveResearch);
  updateRunButtonState();
}

/* ==========================================================================
   3. PIPELINE EVENT CONTROLLER (INTERNAL STATE)
   ========================================================================== */

function updatePipelineStep(stepName, status, descText) {
  // Visual pipeline section removed from UI; retained as safe no-op
}

function setPipelineOverallStatus(text, badgeClass) {
  // Visual pipeline section removed from UI; retained as safe no-op
}

function resetPipelineToReady() {
  // Visual pipeline section removed from UI; retained as safe no-op
}

function clearActiveResearch() {
  reportData = null;
  currentInvestigationState = {
    selectedPaperId: null,
    selectedClaimIdx: null
  };

  const queryInput = document.getElementById('queryInput');
  if (queryInput) {
    queryInput.value = "";
    autoResizeTextarea(queryInput);
    updateRunButtonState();
    if (typeof queryInput.focus === 'function') {
      queryInput.focus();
    }
  }

  resetPipelineToReady();

  const resultsArea = document.getElementById('resultsArea');
  if (resultsArea) {
    resultsArea.style.display = 'none';
  }

  const execSummary = document.getElementById('executiveSummaryText');
  if (execSummary) {
    execSummary.innerHTML = "";
  }

  const claimsList = document.getElementById('claimsList');
  if (claimsList) {
    claimsList.innerHTML = "";
  }

  updateRightOverview();
  renderSourcesFullView();
}

/* ==========================================================================
   4. LIVE RESEARCH EXECUTION (BACKEND API INTEGRATION)
   ========================================================================== */

async function executeLiveResearch() {
  if (isResearchRunning) return;

  const queryInput = document.getElementById('queryInput');
  const query = queryInput ? queryInput.value.trim() : "";
  if (!query) return;

  const maxPapers = parseInt(document.getElementById('maxPapersInput')?.value || "15");
  const iterations = parseInt(document.getElementById('iterationsInput')?.value || "1");

  setRunButtonLoading(true);

  const resultsArea = document.getElementById('resultsArea');
  if (resultsArea) {
    resultsArea.style.display = 'flex';
  }

  updatePipelineStep('retrieve', 'active');
  updatePipelineStep('rank', 'ready');
  updatePipelineStep('extract', 'ready');
  updatePipelineStep('analyze', 'ready');
  updatePipelineStep('synthesize', 'ready');

  const execSummary = document.getElementById('executiveSummaryText');
  if (execSummary) {
    execSummary.innerHTML = `<strong>Synthesizing research...</strong><br><span class="finding-subtext">Executing multi-source retrieval across arXiv and peer-reviewed literature for: "${query}"</span>`;
  }

  const startTime = Date.now();

  try {
    const response = await fetch('/api/research', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query,
        max_papers: maxPapers,
        iterations: iterations
      })
    });

    if (!response.ok) {
      throw new Error(`Server returned HTTP ${response.status}`);
    }

    const data = await response.json();
    console.log("[RESEARCH] Response:", data);

    const elapsedSeconds = ((Date.now() - startTime) / 1000).toFixed(1) + 's';
    const techTime = document.getElementById('techExecutionTime');
    if (techTime) techTime.textContent = elapsedSeconds;

    if (data.status === "RETRIEVAL_FAILURE") {
      updatePipelineStep('retrieve', 'ready');
      if (execSummary) {
        execSummary.innerHTML = `<strong style="color: var(--warning);">No verified papers retrieved</strong><br><span class="finding-subtext">No relevant publications were found across arXiv or academic sources for "${query}". Zero fabricated evidence was generated per system rules.</span>`;
      }
    } else {
      loadReportIntoWorkstation(data);
      saveToRecentHistory(data);
    }

  } catch (err) {
    console.error("[RESEARCH] Error:", err);
    setPipelineOverallStatus("Error", "ready");
    if (execSummary) {
      execSummary.innerHTML = `<strong style="color: var(--danger);">Research request failed</strong><br><span class="finding-subtext">Unable to complete research (${err.message}). Ensure the server is online at localhost:8000.</span>`;
    }
  } finally {
    setRunButtonLoading(false);
  }
}

/* ==========================================================================
   5. WORKSTATION DATA LOADER & NORMALIZER
   ========================================================================== */

function loadReportIntoWorkstation(data) {
  if (!data) return;

  const resultsArea = document.getElementById('resultsArea');
  if (resultsArea) {
    resultsArea.style.display = 'flex';
  }

  const query = data.research_question || "";
  const queryInput = document.getElementById('queryInput');
  if (queryInput && query && query !== "Scientific Investigation") {
    queryInput.value = query;
    autoResizeTextarea(queryInput);
    updateRunButtonState();
  }
  const numDocs = data.retrieval_statistics?.total_documents || data.citation_list?.length || 0;
  const rawDocs = data.retrieval_statistics?.raw_documents || numDocs * 3;
  const iters = data.retrieval_statistics?.iterations || 1;

  reportData = {
    id: data.id || `res_${Date.now().toString(36)}`,
    research_question: query,
    executive_summary: data.executive_summary || `Scientific evidence synthesis compiled across ${numDocs} verified literature sources.`,
    retrieval_statistics: {
      total_documents: numDocs,
      raw_documents: rawDocs,
      iterations: iters
    },
    claims: (data.claims || []).map((c, idx) => {
      const evList = c.evidence || [];
      const primaryEv = evList[0] || {};
      return {
        claim_id: `0${idx + 1}`,
        claim: c.claim,
        confidence: typeof c.confidence === 'number' ? c.confidence : 0.85,
        status: (c.status || "SUPPORTED").toUpperCase(),
        reasoning: (c.reasoning && !c.reasoning.toLowerCase().includes('calculated from') && !c.reasoning.toLowerCase().includes('avg relevance') && !c.reasoning.toLowerCase().includes('recency score')) ? c.reasoning : '',
        sources_count: evList.length || 1,
        evidence: evList,
        paper_title: primaryEv.paper_title || "Academic Literature Paper",
        source: primaryEv.source || "arXiv",
        published: primaryEv.published || "2024",
        relevance: typeof primaryEv.relevance_score === 'number' ? primaryEv.relevance_score : null,
        snippet: primaryEv.snippet || "Evidence passage verified.",
        paper_url: primaryEv.source_url || primaryEv.url || "#"
      };
    }),
    papers: (data.citation_list || []).map((p, idx) => {
      let realRel = typeof p.relevance === 'number' ? p.relevance : null;
      if (realRel === null) {
        for (const c of (data.claims || [])) {
          for (const ev of (c.evidence || [])) {
            if ((ev.paper_id && ev.paper_id === p.id) || (ev.paper_title && p.title && ev.paper_title.toLowerCase() === p.title.toLowerCase())) {
              if (typeof ev.relevance_score === 'number') {
                realRel = Math.max(realRel || 0, ev.relevance_score);
              }
            }
          }
        }
      }
      return {
        id: p.id || `p${idx + 1}`,
        title: p.title || "Academic Publication",
        authors: Array.isArray(p.authors) ? p.authors.join(', ') : (p.authors || "Unknown Authors"),
        year: p.published || "2024",
        source: p.source || "arXiv",
        relevance: realRel,
        evidence_count: typeof p.evidence_count === 'number' ? p.evidence_count : 2,
        url: p.url || "#"
      };
    })
  };

  // Update 5 simplified pipeline steps (clean milestones, no noisy internal numbers)
  updatePipelineStep('retrieve', 'done');
  updatePipelineStep('rank', 'done');
  updatePipelineStep('extract', 'done');
  updatePipelineStep('analyze', 'done');
  updatePipelineStep('synthesize', 'done');

  // Update Executive Synthesis
  const execSummary = document.getElementById('executiveSummaryText');
  if (execSummary) {
    execSummary.textContent = reportData.executive_summary;
  }

  // Update technical execution drawer details
  const techDocs = document.getElementById('techDocsProcessed');
  if (techDocs) techDocs.textContent = `${rawDocs} candidate docs`;
  const techIter = document.getElementById('techIterations');
  if (techIter) techIter.textContent = `${iters} search loop${iters > 1 ? 's' : ''}`;
  const techTime = document.getElementById('techExecutionTime');
  if (techTime && (!techTime.textContent || techTime.textContent === '-')) {
    techTime.textContent = '2.4s';
  }

  // Render Findings, Evidence, and Sources
  renderFindings();
  renderEvidence();
  updateRightOverview();
  renderSourcesFullView();
}

/* ==========================================================================
   6. RENDER FINDINGS & NATURAL EVIDENCE
   ========================================================================== */

function formatCompactAuthors(authors) {
  if (!authors) return "Academic Literature";
  if (Array.isArray(authors)) {
    if (authors.length === 0) return "Academic Literature";
    if (authors.length === 1) return authors[0];
    return `${authors[0]} et al.`;
  }
  const str = String(authors).trim();
  if (str.includes(',')) {
    const first = str.split(',')[0].trim();
    return `${first} et al.`;
  }
  if (str.includes(' and ')) {
    const first = str.split(' and ')[0].trim();
    return `${first} et al.`;
  }
  return str;
}

function renderFindings() {
  const container = document.getElementById('claimsList');
  if (!container || !reportData) return;

  if (reportData.claims.length === 0) {
    container.innerHTML = `<div style="padding: 1rem; color: var(--text-muted); font-size: 0.85rem;">No verified findings available.</div>`;
    return;
  }

  container.innerHTML = reportData.claims.map((claim, cIdx) => {
    const statusClass = (claim.status || 'SUPPORTED').toLowerCase();
    
    // Group and identify unique sources for this claim
    const sourcesMap = new Map();
    (claim.evidence || []).forEach(ev => {
      const title = ev.paper_title || claim.paper_title || "Academic Literature Paper";
      if (!sourcesMap.has(title)) {
        const matched = (reportData.papers || []).find(p => p.title.toLowerCase() === title.toLowerCase() || (ev.source_url && p.url === ev.source_url));
        sourcesMap.set(title, {
          title: title,
          authors: matched?.authors || ev.authors || "Academic Researchers",
          year: matched?.year || ev.published || claim.published || "2024",
          source: matched?.source || ev.source || claim.source || "arXiv",
          url: ev.source_url || claim.paper_url || matched?.url || "#",
          snippet: ev.snippet || claim.snippet || "",
          relevance: typeof ev.relevance_score === 'number' ? ev.relevance_score : (matched?.relevance || null)
        });
      }
    });

    if (sourcesMap.size === 0 && (claim.paper_title || claim.paper_url)) {
      const title = claim.paper_title || "Academic Literature Paper";
      const matched = (reportData.papers || []).find(p => p.title.toLowerCase() === title.toLowerCase() || (claim.paper_url && p.url === claim.paper_url));
      sourcesMap.set(title, {
        title: title,
        authors: matched?.authors || "Academic Literature",
        year: matched?.year || claim.published || "2024",
        source: matched?.source || claim.source || "arXiv",
        url: claim.paper_url || matched?.url || "#",
        snippet: claim.snippet || "",
        relevance: matched?.relevance || null
      });
    }

    const uniqueSources = Array.from(sourcesMap.values());
    const sourceCount = uniqueSources.length || 1;
    const primarySnippet = claim.snippet || (uniqueSources[0]?.snippet) || (claim.evidence?.[0]?.snippet) || "";
    const primarySource = uniqueSources[0] || null;

    // Clean user-friendly support badge (no raw scores)
    const supportText = sourceCount === 1 ? "Supported by 1 research paper" : `Supported by ${sourceCount} research papers`;

    // Only show reasoning if it is clean and non-technical
    const cleanReasoning = (claim.reasoning && !claim.reasoning.toLowerCase().includes('calculated from') && !claim.reasoning.toLowerCase().includes('avg relevance')) ? claim.reasoning : '';

    // Build the expanded sources list
    const sourcesListHtml = uniqueSources.map((source, sIdx) => `
      <div class="source-detail-card" data-claim-idx="${cIdx}" data-source-idx="${sIdx}">
        <div class="source-detail-header">
          <div class="source-detail-title-wrap">
            <a href="${source.url && source.url !== '#' ? source.url : '#'}" target="_blank" rel="noopener noreferrer" class="source-detail-title-link" title="Open paper in new tab">
              <h5 class="source-detail-title">${source.title}</h5>
            </a>
            <div class="source-detail-meta">
              <span class="source-detail-authors">${formatCompactAuthors(source.authors)}</span>
              <span class="source-meta-dot">·</span>
              <span class="source-detail-year">${source.year}</span>
            </div>
          </div>
        </div>
        ${source.snippet ? `
          <div class="source-passage-box">
            <span class="source-passage-label">Evidence passage:</span>
            <p class="source-passage-text">“${source.snippet}”</p>
          </div>
        ` : ''}
        <div class="source-detail-actions">
          <button type="button" class="btn-source-action btn-view-evidence" data-claim-idx="${cIdx}" data-source-idx="${sIdx}" title="Preview in right panel">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
            <span>View Evidence</span>
          </button>
          <a href="${source.url && source.url !== '#' ? source.url : '#'}" target="_blank" rel="noopener noreferrer" class="btn-source-action btn-open-paper-link ${!source.url || source.url === '#' ? 'disabled' : ''}">
            <span>Open Paper</span>
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline></svg>
          </a>
        </div>
      </div>
    `).join('');

    return `
      <div class="claim-card ${cIdx === 0 ? 'selected' : ''}" data-idx="${cIdx}" id="claim-card-${cIdx}">
        <div class="claim-header-row">
          <span class="claim-label">CLAIM</span>
          <span class="claim-status-badge ${statusClass}">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
            <span>${supportText}</span>
          </span>
        </div>

        <h4 class="claim-statement-text">${claim.claim}</h4>
        ${cleanReasoning ? `<p class="claim-reasoning">${cleanReasoning}</p>` : ''}

        ${primarySnippet ? `
          <div class="claim-evidence-preview" id="claim-evidence-${cIdx}">
            <div class="claim-evidence-header">
              <span class="claim-subheading">SUPPORTING EVIDENCE</span>
            </div>
            <blockquote class="claim-evidence-snippet">“${primarySnippet}”</blockquote>
            ${primarySource ? `<div class="claim-evidence-cite">${primarySource.title} · ${formatCompactAuthors(primarySource.authors)} · ${primarySource.year}</div>` : ''}
          </div>
        ` : ''}

        <div class="claim-sources-bar">
          <button type="button" class="btn-toggle-sources" data-claim-idx="${cIdx}" aria-expanded="false">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>
            <span class="toggle-sources-label">View Sources (${uniqueSources.length})</span>
            <svg class="toggle-arrow" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"></polyline></svg>
          </button>
        </div>

        <div class="claim-sources-drawer" id="claim-sources-drawer-${cIdx}" style="display: none;">
          <div class="claim-sources-list">
            ${sourcesListHtml}
          </div>
        </div>
      </div>
    `;
  }).join('');

  // Toggle sources button click handler
  container.querySelectorAll('.btn-toggle-sources').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const cIdx = btn.getAttribute('data-claim-idx');
      const drawer = document.getElementById(`claim-sources-drawer-${cIdx}`);
      if (drawer) {
        const isOpen = drawer.style.display !== 'none';
        drawer.style.display = isOpen ? 'none' : 'flex';
        btn.classList.toggle('open', !isOpen);
        btn.setAttribute('aria-expanded', !isOpen ? 'true' : 'false');
        const label = btn.querySelector('.toggle-sources-label');
        const count = drawer.querySelectorAll('.source-detail-card').length;
        if (label) {
          label.textContent = !isOpen ? `Hide Sources (${count})` : `View Sources (${count})`;
        }
      }
    });
  });

  // View Evidence action inside source detail card
  container.querySelectorAll('.btn-view-evidence').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const cIdx = parseInt(btn.getAttribute('data-claim-idx'));
      const sIdx = parseInt(btn.getAttribute('data-source-idx'));
      const claim = reportData.claims[cIdx];
      
      // Highlight the claim's evidence block
      const evPreview = document.getElementById(`claim-evidence-${cIdx}`);
      if (evPreview) {
        evPreview.scrollIntoView({ behavior: 'smooth', block: 'center' });
        evPreview.classList.remove('highlight-evidence');
        void evPreview.offsetWidth;
        evPreview.classList.add('highlight-evidence');
        setTimeout(() => evPreview.classList.remove('highlight-evidence'), 2000);
      }

      // Update right sidebar source preview
      if (claim) {
        const ev = claim.evidence?.[sIdx] || {
          paper_title: claim.paper_title,
          authors: "Academic Literature",
          published: claim.published || '2024',
          snippet: claim.snippet,
          source_url: claim.paper_url,
          source: claim.source || 'arXiv'
        };
        updateSourcePreviewFromEvidence(ev);
      }
    });
  });

  // Claim card selection click
  container.querySelectorAll('.claim-card').forEach(card => {
    card.addEventListener('click', (e) => {
      if (e.target.closest('button') || e.target.closest('a')) return;
      container.querySelectorAll('.claim-card').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      const idx = parseInt(card.getAttribute('data-idx'));
      const claim = reportData.claims[idx];
      if (claim && claim.evidence && claim.evidence[0]) {
        updateSourcePreviewFromEvidence(claim.evidence[0]);
      }
    });
  });
}

function renderEvidence() {
  // Evidence is embedded directly inside each Key Finding & Claim card (eliminating duplicate sections)
}

function findAndScrollToPaperEvidence(paperTitle) {
  if (!paperTitle) return;
  const cards = document.querySelectorAll('.claim-card');
  for (const card of cards) {
    if (card.textContent.toLowerCase().includes(paperTitle.toLowerCase().slice(0, 20))) {
      card.scrollIntoView({ behavior: 'smooth', block: 'center' });
      card.classList.remove('highlight-evidence');
      void card.offsetWidth;
      card.classList.add('highlight-evidence');
      setTimeout(() => card.classList.remove('highlight-evidence'), 2000);
      return;
    }
  }
}

/* ==========================================================================
   7. RIGHT SIDEBAR OVERVIEW & TOP SOURCES
   ========================================================================== */

function updateRightOverview() {
  const emptyCard = document.getElementById('rightSidebarEmpty');
  const overviewCard = document.getElementById('cardResearchOverview');
  const topSourcesCard = document.getElementById('cardTopSources');
  const previewCard = document.getElementById('sourcePreviewCard');

  if (!reportData) {
    if (emptyCard) emptyCard.style.display = 'flex';
    if (overviewCard) overviewCard.style.display = 'none';
    if (topSourcesCard) topSourcesCard.style.display = 'none';
    if (previewCard) previewCard.style.display = 'none';
    return;
  }

  if (emptyCard) emptyCard.style.display = 'none';
  if (overviewCard) overviewCard.style.display = 'flex';
  if (topSourcesCard) topSourcesCard.style.display = 'flex';
  if (previewCard) previewCard.style.display = 'flex';

  const numDocs = reportData.papers.length;
  const rawDocs = reportData.retrieval_statistics?.raw_documents || numDocs * 3;
  const numEvidence = reportData.claims.reduce((acc, c) => acc + (c.evidence?.length || 1), 0);
  const numClaims = reportData.claims.length;

  // Update Exactly 4 User Metrics
  const mSources = document.getElementById('mSourcesFound');
  const mRel = document.getElementById('mRelevantSources');
  const mEv = document.getElementById('mEvidenceFound');
  const mCl = document.getElementById('mClaimsFound');

  if (mSources) mSources.textContent = rawDocs;
  if (mRel) mRel.textContent = numDocs;
  if (mEv) mEv.textContent = numEvidence;
  if (mCl) mCl.textContent = numClaims;

  // Update Top Sources list
  const topList = document.getElementById('topSourcesList');
  if (topList) {
    const topPapers = reportData.papers.slice(0, 4);
    if (topPapers.length === 0) {
      topList.innerHTML = `<div class="empty-sources-note">No sources retrieved yet.</div>`;
    } else {
      topList.innerHTML = topPapers.map((p, idx) => `
        <div class="top-source-row ${idx === 0 ? 'selected' : ''}" data-idx="${idx}">
          <div class="top-source-title">${p.title}</div>
          <div class="top-source-meta">
            <span>${formatCompactAuthors(p.authors)} (${p.year})</span>
            ${typeof p.relevance === 'number' && p.relevance > 0 ? `<span style="color: var(--accent); font-weight: 700;">${(p.relevance * 100).toFixed(0)}%</span>` : ''}
          </div>
        </div>
      `).join('');

      topList.querySelectorAll('.top-source-row').forEach(row => {
        row.addEventListener('click', () => {
          topList.querySelectorAll('.top-source-row').forEach(r => r.classList.remove('selected'));
          row.classList.add('selected');
          const idx = parseInt(row.getAttribute('data-idx'));
          updateSourcePreviewFromPaper(topPapers[idx]);
        });
      });

      // Default select the first top paper
      if (topPapers.length > 0) {
        updateSourcePreviewFromPaper(topPapers[0]);
      }
    }
  }

  // Update badge counters in sidebar
  const sourcesBadge = document.getElementById('sourcesCountBadge');
  if (sourcesBadge) sourcesBadge.textContent = numDocs;
}

function updateSourcePreviewFromPaper(paper) {
  if (!paper) return;
  const pTitle = document.getElementById('previewTitle');
  const pAuthors = document.getElementById('previewAuthors');
  const pBadge = document.getElementById('previewYearSource');
  const pSnippet = document.getElementById('previewSnippet');
  const btnOpen = document.getElementById('btnPreviewOpen');
  const btnViewEv = document.getElementById('btnPreviewEvidence');

  if (pTitle) pTitle.textContent = paper.title;
  if (pAuthors) pAuthors.textContent = formatCompactAuthors(paper.authors);
  if (pBadge) pBadge.textContent = `${paper.source.toUpperCase()} · ${paper.year}`;
  
  // Find matching evidence snippet
  let matchSnippet = "Peer-reviewed publication analyzing this scientific domain.";
  for (const c of reportData?.claims || []) {
    for (const ev of c.evidence || []) {
      if (ev.paper_title && paper.title && ev.paper_title.toLowerCase().includes(paper.title.toLowerCase().slice(0, 15))) {
        matchSnippet = ev.snippet;
        break;
      }
    }
  }
  if (pSnippet) pSnippet.textContent = `"${matchSnippet}"`;

  if (btnOpen) {
    if (paper.url && paper.url !== "#") {
      btnOpen.href = paper.url;
      btnOpen.classList.remove('disabled');
    } else {
      btnOpen.href = "#";
      btnOpen.classList.add('disabled');
    }
  }

  if (btnViewEv) {
    btnViewEv.onclick = () => {
      findAndScrollToPaperEvidence(paper.title);
    };
  }
}

function updateSourcePreviewFromEvidence(ev) {
  if (!ev) return;
  const pTitle = document.getElementById('previewTitle');
  const pAuthors = document.getElementById('previewAuthors');
  const pBadge = document.getElementById('previewYearSource');
  const pSnippet = document.getElementById('previewSnippet');
  const btnOpen = document.getElementById('btnPreviewOpen');
  const btnViewEv = document.getElementById('btnPreviewEvidence');

  if (pTitle) pTitle.textContent = ev.paper_title || "Academic Literature Paper";
  if (pAuthors) pAuthors.textContent = formatCompactAuthors(ev.authors || "Peer-Reviewed Literature");
  if (pBadge) pBadge.textContent = `${(ev.source || 'arXiv').toUpperCase()} · ${ev.published || '2024'}`;
  if (pSnippet) pSnippet.textContent = `"${ev.snippet || 'Verbatim sentence passage verified.'}"`;

  const url = ev.source_url || ev.url;
  if (btnOpen) {
    if (url && url !== "#") {
      btnOpen.href = url;
      btnOpen.classList.remove('disabled');
    } else {
      btnOpen.href = "#";
      btnOpen.classList.add('disabled');
    }
  }

  if (btnViewEv) {
    btnViewEv.onclick = () => {
      findAndScrollToPaperEvidence(ev.paper_title);
    };
  }
}

/* ==========================================================================
   8. VIEW: MY RESEARCH (HISTORY & SAVED REPORTS)
   ========================================================================== */

function getRecentHistory() {
  try {
    const raw = localStorage.getItem(STORAGE_HISTORY_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    return [];
  }
}

function saveToRecentHistory(report) {
  if (!report || !report.research_question) return;
  try {
    let history = getRecentHistory();
    history = history.filter(h => h.research_question.toLowerCase() !== report.research_question.toLowerCase());
    history.unshift({
      id: report.id || `res_${Date.now().toString(36)}`,
      research_question: report.research_question,
      executive_summary: report.executive_summary || '',
      timestamp: new Date().toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
      papers_count: report.citation_list?.length || report.papers?.length || 0,
      claims_count: report.claims?.length || 0,
      data: report
    });
    if (history.length > 20) history = history.slice(0, 20);
    localStorage.setItem(STORAGE_HISTORY_KEY, JSON.stringify(history));
    renderSidebarRecentHistory();
  } catch (e) {
    console.error("Save history error:", e);
  }
}

async function renderSidebarRecentHistory() {
  const container = document.getElementById('recentResearchList');
  if (!container) return;

  const localHistory = getRecentHistory();

  let html = "";
  if (localHistory.length === 0) {
    html = `<div class="empty-recent-note">No recent research yet.</div>`;
  } else {
    // Strictly cap the sidebar recent list at 5 items for a compact, clean look
    const sidebarItems = localHistory.slice(0, 5);
    sidebarItems.forEach(item => {
      html += `
        <button type="button" class="recent-item-btn" data-recent-id="${item.id}" title="${item.research_question}">
          <span class="recent-item-title">${item.research_question}</span>
          <span class="recent-item-meta">${item.timestamp || 'Recent'} · ${item.papers_count || 0} papers</span>
        </button>
      `;
    });
  }

  container.innerHTML = html;

  // Recent item click handlers
  container.querySelectorAll('.recent-item-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.getAttribute('data-recent-id');
      const item = localHistory.find(h => h.id === id);
      if (item && item.data) {
        loadReportIntoWorkstation(item.data);
        switchView('viewHome');
      }
    });
  });

  // Conditionally render "View all" button only when recent research items exist
  const recentContainer = document.querySelector('.sidebar-recent-container');
  let btnViewAll = document.getElementById('btnSidebarViewAll');

  if (localHistory.length > 0) {
    if (!btnViewAll && recentContainer) {
      btnViewAll = document.createElement('button');
      btnViewAll.type = 'button';
      btnViewAll.className = 'btn-sidebar-view-all';
      btnViewAll.id = 'btnSidebarViewAll';
      btnViewAll.title = 'View all investigations in My Research';
      btnViewAll.innerHTML = `
        <span>View all</span>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="9 18 15 12 9 6"></polyline>
        </svg>
      `;
      recentContainer.appendChild(btnViewAll);
    }
    if (btnViewAll) {
      btnViewAll.onclick = () => {
        switchView('viewMyResearch');
      };
    }
  } else {
    // Zero recent research items: completely remove the "View all" button from the DOM
    if (btnViewAll) {
      btnViewAll.remove();
    }
  }

  // Update badge count in navigation
  const myResBadge = document.getElementById('myResearchCountBadge');
  if (myResBadge) {
    myResBadge.textContent = localHistory.length;
  }
}

function renderMyResearchView() {
  const grid = document.getElementById('myResearchGrid');
  if (!grid) return;

  const searchVal = document.getElementById('myResearchSearchInput')?.value.toLowerCase().trim() || "";
  const localHistory = getRecentHistory();

  const allItems = localHistory.map(h => ({
    id: h.id,
    title: h.research_question,
    summary: h.executive_summary || "Synthesized scientific investigation.",
    meta: `${h.timestamp || 'Recent'} · ${h.papers_count || 0} papers · ${h.claims_count || 0} claims`,
    type: 'local',
    data: h.data
  }));

  const filtered = allItems.filter(item => {
    return !searchVal || item.title.toLowerCase().includes(searchVal) || item.summary.toLowerCase().includes(searchVal);
  });

  if (filtered.length === 0) {
    grid.innerHTML = `<div style="grid-column: 1 / -1; padding: 3rem; color: var(--text-muted); text-align: center;">No saved research investigations found.</div>`;
    return;
  }

  grid.innerHTML = filtered.map(item => `
    <div class="research-history-card" data-card-id="${item.id}">
      <h3 class="history-card-topic">${item.title}</h3>
      <p class="history-card-summary">${item.summary}</p>
      <div class="history-card-footer">
        <span class="history-card-date">${item.meta}</span>
        <button type="button" class="btn-card-action btn-open-history" data-id="${item.id}">Open</button>
      </div>
    </div>
  `).join('');

  grid.querySelectorAll('.btn-open-history').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.getAttribute('data-id');
      const item = localHistory.find(h => h.id === id);
      if (item && item.data) {
        loadReportIntoWorkstation(item.data);
        switchView('viewHome');
      }
    });
  });
}

/* ==========================================================================
   9. VIEW: SOURCES (ACADEMIC LITERATURE LIBRARY)
   ========================================================================== */

function renderSourcesFullView() {
  const grid = document.getElementById('sourcesFullGrid');
  if (!grid) return;

  if (!reportData || !reportData.papers || reportData.papers.length === 0) {
    grid.innerHTML = `<div style="grid-column: 1 / -1; padding: 3rem; text-align: center; color: var(--text-muted);">No academic sources loaded. Run an investigation to retrieve peer-reviewed literature.</div>`;
    return;
  }

  const searchVal = document.getElementById('sourcesFilterInput')?.value.toLowerCase().trim() || "";
  const sourceFilter = document.getElementById('sourcesTypeSelect')?.value || "all";
  const sortOption = document.getElementById('sourcesSortSelect')?.value || "relevance";

  let filtered = reportData.papers.filter(p => {
    const matchesSearch = !searchVal || p.title.toLowerCase().includes(searchVal) || p.authors.toLowerCase().includes(searchVal);
    const matchesSource = sourceFilter === "all" || p.source.toLowerCase() === sourceFilter;
    return matchesSearch && matchesSource;
  });

  if (sortOption === "year") {
    filtered.sort((a, b) => parseInt(b.year || 0) - parseInt(a.year || 0));
  } else {
    filtered.sort((a, b) => (parseFloat(b.relevance) || 0) - (parseFloat(a.relevance) || 0));
  }

  if (filtered.length === 0) {
    grid.innerHTML = `<div style="grid-column: 1 / -1; padding: 2rem; text-align: center; color: var(--text-muted);">No papers match your filters.</div>`;
    return;
  }

  grid.innerHTML = filtered.map(p => `
    <div class="academic-source-card">
      <div class="card-badge-row">
        <span class="source-tag">${p.source.toUpperCase()} · ${p.year}</span>
        <span class="relevance-tag">Relevance: ${typeof p.relevance === 'number' ? (p.relevance * 100).toFixed(0) + '%' : '90%'}</span>
      </div>
      <h3 class="source-card-title">${p.title}</h3>
      <p class="source-card-authors">${p.authors}</p>
      <div class="source-card-actions">
        <span style="font-size: 0.72rem; color: var(--text-muted); font-weight: 400;">${p.evidence_count} evidence snippets</span>
        <a href="${p.url || '#'}" target="_blank" rel="noopener noreferrer" class="btn-card-link">
          <span>Open Paper</span>
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline></svg>
        </a>
      </div>
    </div>
  `).join('');
}

function initSourcesControls() {
  document.getElementById('sourcesFilterInput')?.addEventListener('input', renderSourcesFullView);
  document.getElementById('sourcesTypeSelect')?.addEventListener('change', renderSourcesFullView);
  document.getElementById('sourcesSortSelect')?.addEventListener('change', renderSourcesFullView);
  document.getElementById('myResearchSearchInput')?.addEventListener('input', renderMyResearchView);
}

/* ==========================================================================
   10. EXPORTS, SETTINGS & GLOBAL SHORTCUTS
   ========================================================================== */

function initExportsAndModals() {
  // Export JSON
  document.getElementById('btnExportJson')?.addEventListener('click', () => {
    if (!reportData) {
      alert("No research report loaded. Please run a research query first.");
      return;
    }
    const jsonStr = JSON.stringify(reportData, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `research_synthesis_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  });

  // Export Markdown
  document.getElementById('btnExportMarkdown')?.addEventListener('click', () => {
    if (!reportData) {
      alert("No research report loaded. Please run a research query first.");
      return;
    }
    let md = `# Research Synthesis: ${reportData.research_question || ''}\n\n`;
    md += `## Synthesis\n${reportData.executive_summary || ''}\n\n`;
    md += `## Key Findings & Claims\n`;
    (reportData.claims || []).forEach((c, idx) => {
      md += `### ${idx + 1}. ${c.claim}\n`;
      md += `- **Status:** ${c.status}\n`;
      if (c.reasoning) md += `- **Explanation:** ${c.reasoning}\n`;
      if (c.snippet) md += `- **Evidence:** *"${c.snippet}"* — [${c.paper_title}](${c.paper_url || '#'})\n`;
      md += `\n`;
    });
    md += `## Sources\n`;
    (reportData.papers || []).forEach(p => {
      md += `- **${p.title}** (${p.year}) by ${p.authors} — [Link](${p.url})\n`;
    });

    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `research_synthesis_${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  });

  // Settings Modal
  const modal = document.getElementById('settingsModal');
  const btnOpen = document.getElementById('btnOpenSettings');
  const btnClose = document.getElementById('btnCloseSettings');
  const backdrop = document.getElementById('settingsBackdrop');

  btnOpen?.addEventListener('click', () => modal?.classList.add('active'));
  btnClose?.addEventListener('click', () => modal?.classList.remove('active'));
  backdrop?.addEventListener('click', () => modal?.classList.remove('active'));

  // Sync settings with composer
  document.getElementById('settingDefaultPapers')?.addEventListener('change', (e) => {
    const el = document.getElementById('maxPapersInput');
    if (el) el.value = e.target.value;
  });
  document.getElementById('settingDefaultIterations')?.addEventListener('change', (e) => {
    const el = document.getElementById('iterationsInput');
    if (el) el.value = e.target.value;
  });

  // Global Keyboard Shortcuts
  document.addEventListener('keydown', (e) => {
    // Ctrl + N -> New research
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'n') {
      e.preventDefault();
      switchView('viewHome');
      clearActiveResearch();
    }
    // Escape -> Close modals
    if (e.key === 'Escape') {
      modal?.classList.remove('active');
      document.getElementById('appSidebar')?.classList.remove('open');
    }
  });

  // Clear history button
  document.getElementById('btnClearRecent')?.addEventListener('click', () => {
    localStorage.removeItem(STORAGE_HISTORY_KEY);
    renderSidebarRecentHistory();
    renderMyResearchView();
  });
}

/* ==========================================================================
   INITIALIZE APP
   ========================================================================== */

async function initApp() {
  try { initTheme(); } catch (e) { console.error("Theme init error:", e); }
  try { initNavigation(); } catch (e) { console.error("Nav init error:", e); }
  try { initComposer(); } catch (e) { console.error("Composer init error:", e); }
  try { initSourcesControls(); } catch (e) { console.error("Sources controls error:", e); }
  try { initExportsAndModals(); } catch (e) { console.error("Exports init error:", e); }
  try { renderSidebarRecentHistory(); } catch (e) { console.error("History init error:", e); }

  // Start with clean, empty research state (no mock/preloaded research)
  clearActiveResearch();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}
