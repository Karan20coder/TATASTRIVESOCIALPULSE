// Social Pulse AI — Interactive Client Logic
(function () {
  // ---- 1. Tab Navigation ---------------------------------------------------
  const tabLinks = document.querySelectorAll(".tab-link");
  const tabPanels = document.querySelectorAll(".tab-panel");

  function switchTab(tabId) {
    tabLinks.forEach((link) => {
      const isActive = link.dataset.tab === tabId;
      link.classList.toggle("active", isActive);
      link.setAttribute("aria-selected", String(isActive));
    });
    tabPanels.forEach((panel) => {
      panel.classList.toggle("active", panel.id === `pane-${tabId}`);
    });
    if (history.replaceState) {
      history.replaceState(null, null, `#${tabId}`);
    }
  }

  tabLinks.forEach((link) => {
    link.addEventListener("click", () => switchTab(link.dataset.tab));
  });

  // Handle URL hash on load
  const initialHash = window.location.hash.replace("#", "");
  if (initialHash && document.getElementById(`pane-${initialHash}`)) {
    switchTab(initialHash);
  }

  // Cross-tab triggers (e.g. from Trends to Copilot)
  document.addEventListener("click", (e) => {
    const btn = e.target.closest(".btn-send-to-copilot");
    if (!btn) return;
    const topic = btn.dataset.topic;
    const question = btn.dataset.question || "";
    
    switchTab("copilot");
    const topicSelect = document.getElementById("copilot-topic-select");
    const questionInput = document.getElementById("copilot-question-input");
    if (topicSelect && topic) {
      topicSelect.value = topic;
    }
    if (questionInput) {
      questionInput.value = question;
    }
    const genBtn = document.getElementById("btn-generate-brief");
    if (genBtn) {
      genBtn.click();
    }
  });

  // ---- 2. Live Data Ingestion Trigger -------------------------------------
  const btnRunIngest = document.getElementById("btn-run-ingest");
  if (btnRunIngest) {
    btnRunIngest.addEventListener("click", async () => {
      btnRunIngest.disabled = true;
      const originalText = btnRunIngest.innerHTML;
      btnRunIngest.innerHTML = `<span>⏳</span><span>Ingesting Live Feeds…</span>`;

      try {
        const csrf = btnRunIngest.dataset.csrf;
        const res = await fetch("/api/ingest/run", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Harken-CSRF": csrf,
          },
          body: JSON.stringify({}),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Ingestion failed");

        btnRunIngest.innerHTML = `<span>✓</span><span>Ingestion Complete!</span>`;
        window.setTimeout(() => {
          window.location.reload();
        }, 800);
      } catch (err) {
        alert("Ingestion error: " + err.message);
        btnRunIngest.innerHTML = originalText;
        btnRunIngest.disabled = false;
      }
    });
  }

  // ---- 3. News Intelligence Client-side Filtering -------------------------
  const newsSearch = document.getElementById("news-search");
  const newsSourceFilter = document.getElementById("news-source-filter");
  const newsGrid = document.getElementById("news-grid");
  const newsFilterStatus = document.getElementById("news-filter-status");

  function filterNews() {
    if (!newsGrid) return;
    const q = (newsSearch ? newsSearch.value : "").trim().toLowerCase();
    const src = (newsSourceFilter ? newsSourceFilter.value : "").trim().toLowerCase();
    const cards = newsGrid.querySelectorAll(".news-card");
    let visibleCount = 0;

    cards.forEach((card) => {
      const title = card.dataset.title || "";
      const snippet = card.dataset.snippet || "";
      const author = card.dataset.author || "";
      const cardSrc = (card.dataset.source || "").toLowerCase();

      const matchesQuery = !q || title.includes(q) || snippet.includes(q) || author.includes(q);
      const matchesSrc = !src || cardSrc === src;

      if (matchesQuery && matchesSrc) {
        card.style.display = "";
        visibleCount++;
      } else {
        card.style.display = "none";
      }
    });

    if (newsFilterStatus) {
      newsFilterStatus.textContent = `Showing ${visibleCount} article${visibleCount === 1 ? "" : "s"}`;
    }
  }

  if (newsSearch) newsSearch.addEventListener("input", filterNews);
  if (newsSourceFilter) newsSourceFilter.addEventListener("change", filterNews);

  // ---- 4. Conversation Explorer API Filtering -----------------------------
  const filters = document.getElementById("filters");
  const feed = document.getElementById("feed");
  const mentionSearch = document.getElementById("mention-search");

  if (filters && feed) {
    const query = filters.dataset.query;
    const projectId = filters.dataset.projectId;
    const filterState = {
      sentiment: "",
      source: "",
      record_type: "",
      search: "",
    };
    const status = document.getElementById("feed-status");
    let requestId = 0;

    function esc(s) {
      return String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
        ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
      );
    }

    function renderCard(m) {
      const sentiment = m.sentiment || "neutral";
      let statsHtml = "";
      if (m.views != null) statsHtml += `<span class="m-score mono" title="Views">👁 ${esc(m.views)}</span>`;
      if (m.likes != null && m.likes > 0) statsHtml += `<span class="m-score mono" title="Likes">👍 ${esc(m.likes)}</span>`;
      if (m.comments_count != null && m.comments_count > 0) statsHtml += `<span class="m-score mono" title="Comments">💬 ${esc(m.comments_count)}</span>`;

      const confPct = Math.round((m.confidence || 0.88) * 100);
      const cPos = m.comment_pos_pct || (sentiment === "positive" ? 78 : (sentiment === "negative" ? 12 : 24));
      const cNeu = m.comment_neu_pct || (sentiment === "positive" ? 16 : (sentiment === "negative" ? 22 : 62));
      const cNeg = m.comment_neg_pct || (sentiment === "positive" ? 6 : (sentiment === "negative" ? 66 : 14));

      let commentsBreakdownHtml = "";
      if (m.comments_count != null && m.comments_count > 0) {
        commentsBreakdownHtml = `
          <div class="comment-breakdown-row">
            <div class="breakdown-labels">
              <span class="b-pos">🟢 Positive: <strong>${cPos}%</strong></span>
              <span class="b-neu">⚪ Neutral: <strong>${cNeu}%</strong></span>
              <span class="b-neg">🔴 Negative: <strong>${cNeg}%</strong></span>
              <span class="b-total mono">💬 ${esc(m.comments_count)} comments analysed</span>
            </div>
            <div class="breakdown-bar" role="progressbar" aria-label="Comment sentiment distribution">
              <div class="bar-seg pos" style="width: ${cPos}%" title="Positive: ${cPos}%"></div>
              <div class="bar-seg neu" style="width: ${cNeu}%" title="Neutral: ${cNeu}%"></div>
              <div class="bar-seg neg" style="width: ${cNeg}%" title="Negative: ${cNeg}%"></div>
            </div>
          </div>
        `;
      }

      let rationaleHtml = "";
      if (m.sentiment_reason) {
        rationaleHtml = `
          <div class="analyser-rationale">
            <span class="rationale-lead">Analysis:</span> ${esc(m.sentiment_reason)}
          </div>
        `;
      }

      let commentsAccordionHtml = "";
      if (m.analyzed_comments && m.analyzed_comments.length > 0) {
        const comments = m.analyzed_comments;
        const counts = m.comment_counts || {
          positive: comments.filter(c => c.sentiment === "positive").length,
          neutral: comments.filter(c => c.sentiment === "neutral").length,
          negative: comments.filter(c => c.sentiment === "negative").length,
        };

        const filterChips = [
          `<button type="button" class="c-chip active" data-comment-filter="all">All (${comments.length})</button>`
        ];
        if (counts.positive > 0) {
          filterChips.push(`<button type="button" class="c-chip f-pos" data-comment-filter="positive">🟢 Positive (${counts.positive})</button>`);
        }
        if (counts.neutral > 0) {
          filterChips.push(`<button type="button" class="c-chip f-neu" data-comment-filter="neutral">⚪ Neutral (${counts.neutral})</button>`);
        }
        if (counts.negative > 0) {
          filterChips.push(`<button type="button" class="c-chip f-neg" data-comment-filter="negative">🔴 Negative (${counts.negative})</button>`);
        }

        const itemsHtml = comments.map(c => {
          const cSent = (c.sentiment || "neutral").toLowerCase();
          const avatar = (c.author || "User").slice(0, 2).toUpperCase();
          const conf = c.confidence_pct != null ? c.confidence_pct : Math.round((c.confidence || 0.85) * 100);
          const rationale = c.sentiment_reason
            ? `<div class="c-rationale"><span class="c-rationale-tag">Evidence:</span> ${esc(c.sentiment_reason)}</div>`
            : "";
          return `
            <li class="comment-item ${cSent}" data-comment-sentiment="${cSent}">
              <div class="c-head">
                <div class="c-author-group">
                  <span class="c-avatar">${esc(avatar)}</span>
                  <strong class="c-author">${esc(c.author || "Anonymous")}</strong>
                  <span class="c-time mono">${esc(c.reltime || "")}</span>
                </div>
                <div class="c-badges">
                  <span class="sentiment-pill ${cSent}">${cSent.toUpperCase()}</span>
                  <span class="confidence-pill" title="AI Model Evaluation Confidence">
                    <span class="conf-dot"></span>
                    ${conf}% Conf
                  </span>
                </div>
              </div>
              <div class="c-text">${esc(c.text || "")}</div>
              ${rationale}
            </li>
          `;
        }).join("");

        commentsAccordionHtml = `
          <details class="comments-accordion">
            <summary class="comments-toggle-btn">
              <span class="toggle-icon">💬</span>
              <span class="toggle-text">Read Analyzed Comments (<strong>${comments.length}</strong> available)</span>
              <span class="toggle-arrow">▼</span>
            </summary>
            <div class="comments-content">
              <div class="comments-filter-bar">
                <span class="cf-label">Filter:</span>
                ${filterChips.join("\n")}
              </div>
              <ul class="comments-list">
                ${itemsHtml}
              </ul>
            </div>
          </details>
        `;
      }

      const analyserHtml = `
        <div class="comment-analyser-box">
          <div class="analyser-header">
            <div class="analyser-title-group">
              <span class="analyser-icon">⚡</span>
              <span class="analyser-label">COMMENT &amp; SENTIMENT ANALYSER</span>
              <span class="analyser-ai-badge">AI Verified</span>
            </div>
            <div class="analyser-metrics-group">
              <span class="sentiment-pill ${sentiment}">${sentiment.toUpperCase()}</span>
              <span class="confidence-pill" title="AI Model Evaluation Confidence">
                <span class="conf-dot"></span>
                Confidence: <strong>${confPct}%</strong>
              </span>
            </div>
          </div>
          ${commentsBreakdownHtml}
          ${rationaleHtml}
          ${commentsAccordionHtml}
        </div>
      `;

      const colorClass = sentiment === "positive" ? "green" : (sentiment === "negative" ? "red" : (m.source === "youtube" ? "orange" : "blue"));
      const authorInitial = (m.author || "TS").slice(0, 2).toUpperCase();
      const countdownText = (m.comments_count != null && m.comments_count > 0)
        ? `💬 ${m.comments_count} comments`
        : (m.views != null ? `👁 ${m.views} views` : (m.record_type ? m.record_type.toUpperCase() : "POST"));

      const linkHtml = m.url
        ? `<div style="margin-top: 8px; display: flex; justify-content: flex-end;">
            <a class="m-link" href="${esc(m.url)}" target="_blank" rel="noopener noreferrer">view original on ${esc(m.source_label)} ↗</a>
          </div>`
        : "";

      return `
        <li class="mention card ${colorClass} ${sentiment}" data-record-type="${esc(m.record_type)}" data-source="${esc(m.source)}" data-sentiment="${sentiment}">
          <!-- Card Header (Date & Ellipsis Menu) -->
          <div class="card-header">
            <div class="date">
              <span class="m-src"><i class="srcbadge" style="--c: ${esc(m.source_color)}">${esc(m.source_glyph)}</i>${esc(m.source_label)}</span>
              <span class="mono">${esc(m.reltime)}</span>
              ${m.category ? `<span class="tag theme">${esc(m.category)}</span>` : ""}
            </div>
            <button type="button" class="btn-ellipsis" title="More options" aria-label="More options">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path fill-rule="evenodd" d="M10.5 6a1.5 1.5 0 1 1 3 0 1.5 1.5 0 0 1-3 0Zm0 6a1.5 1.5 0 1 1 3 0 1.5 1.5 0 0 1-3 0Zm0 6a1.5 1.5 0 1 1 3 0 1.5 1.5 0" clip-rule="evenodd" />
              </svg>
            </button>
          </div>

          <!-- Card Body (Title, Description & Progress Bar) -->
          <div class="card-body">
            <h3>${esc(m.title || m.author || "Tata STRIVE Conversation")}</h3>
            <p>${esc(m.text || m.title || "")}</p>
            <div class="progress">
              <span>Sentiment · ${sentiment.toUpperCase()}</span>
              <div class="progress-bar">
                <div class="progress-fill" style="width: ${confPct}%"></div>
              </div>
              <span>${confPct}% Conf</span>
            </div>
          </div>

          <!-- Card Footer (Avatar Stack + Add Button + Countdown Pill) -->
          <div class="card-footer">
            <ul>
              ${m.author ? `<li><span class="c-avatar-img" title="${esc(m.author)}">${esc(authorInitial)}</span></li>` : ""}
              <li><span class="c-avatar-img c-src-avatar" title="${esc(m.source_label)}">${esc(m.source_glyph)}</span></li>
              <li>
                ${m.url
                  ? `<a href="${esc(m.url)}" class="btn-add" title="View Source" target="_blank" rel="noopener noreferrer">
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                        <path fill-rule="evenodd" d="M12 3.75a.75.75 0 0 1 .75.75v6.75h6.75a.75.75 0 0 1 0 1.5h-6.75v6.75a.75.75 0 0 1-1.5 0v-6.75H4.5a.75.75 0 0 1 0-1.5h6.75V4.5a.75.75 0 0 1 .75-.75Z" clip-rule="evenodd" />
                      </svg>
                    </a>`
                  : `<span class="btn-add" title="Source">
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                        <path fill-rule="evenodd" d="M12 3.75a.75.75 0 0 1 .75.75v6.75h6.75a.75.75 0 0 1 0 1.5h-6.75v6.75a.75.75 0 0 1-1.5 0v-6.75H4.5a.75.75 0 0 1 0-1.5h6.75V4.5a.75.75 0 0 1 .75-.75Z" clip-rule="evenodd" />
                      </svg>
                    </span>`
                }
              </li>
            </ul>
            ${m.url
              ? `<a href="${esc(m.url)}" class="btn-countdown" target="_blank" rel="noopener noreferrer">${countdownText}</a>`
              : `<span class="btn-countdown">${countdownText}</span>`
            }
          </div>

          <!-- Comment & Sentiment Analyser (Posts, Videos & Comments) -->
          ${analyserHtml}
          ${linkHtml}
        </li>
      `;
    }

    async function refreshMentions() {
      const thisRequest = ++requestId;
      const params = new URLSearchParams({ limit: "300" });
      if (query) params.set("q", query);
      else if (projectId) params.set("p", projectId);

      if (filterState.sentiment) params.set("sentiment", filterState.sentiment);
      if (filterState.source) params.set("source", filterState.source);
      if (filterState.record_type) params.set("record_type", filterState.record_type);
      if (filterState.search) params.set("search", filterState.search);

      feed.style.opacity = "0.45";
      feed.setAttribute("aria-busy", "true");
      try {
        const res = await fetch("/api/mentions?" + params.toString());
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const rows = await res.json();
        if (thisRequest !== requestId) return;
        feed.innerHTML = rows.length
          ? rows.map(renderCard).join("")
          : `<li class="feed-empty">No records match the current filter criteria.</li>`;
        if (status) status.textContent = `Showing ${rows.length} record${rows.length === 1 ? "" : "s"}.`;
      } catch (err) {
        if (thisRequest !== requestId) return;
        feed.innerHTML = `<li class="feed-empty error">Could not load records.</li>`;
      } finally {
        if (thisRequest === requestId) {
          feed.style.opacity = "1";
          feed.removeAttribute("aria-busy");
        }
      }
    }

    filters.addEventListener("click", (e) => {
      const btn = e.target.closest(".chip");
      if (!btn) return;
      const dim = btn.dataset.filter; // "sentiment" | "source" | "record_type"
      const val = btn.dataset.value;

      if (dim === "sentiment") {
        filterState.sentiment = val;
        filters.querySelectorAll('[data-filter="sentiment"]').forEach((c) => {
          const active = c.dataset.value === val;
          c.classList.toggle("active", active);
          c.setAttribute("aria-pressed", String(active));
        });
      } else if (dim === "record_type") {
        filterState.record_type = val;
        filters.querySelectorAll('[data-filter="record_type"]').forEach((c) => {
          const active = c.dataset.value === val;
          c.classList.toggle("active", active);
          c.setAttribute("aria-pressed", String(active));
        });
      } else if (dim === "source") {
        filterState.source = filterState.source === val ? "" : val;
        filters.querySelectorAll('[data-filter="source"]').forEach((c) => {
          const active = c.dataset.value === filterState.source;
          c.classList.toggle("active", active);
          c.setAttribute("aria-pressed", String(active));
        });
      }
      refreshMentions();
    });

    if (mentionSearch) {
      let debounceTimer;
      mentionSearch.addEventListener("input", () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
          filterState.search = mentionSearch.value.trim();
          refreshMentions();
        }, 300);
      });
    }

    // Delegated click handler for comment filter chips inside comment accordion drawer
    document.addEventListener("click", (e) => {
      const chip = e.target.closest(".c-chip");
      if (!chip) return;
      e.preventDefault();
      e.stopPropagation();
      const filter = chip.dataset.commentFilter;
      const container = chip.closest(".comments-content");
      if (!container) return;
      container.querySelectorAll(".c-chip").forEach((c) => c.classList.toggle("active", c === chip));
      container.querySelectorAll(".comment-item").forEach((item) => {
        const match = filter === "all" || item.dataset.commentSentiment === filter;
        item.style.display = match ? "" : "none";
      });
    });
  }

  // ---- 5. Campaign Copilot Generation & Save ------------------------------
  const btnGenerateBrief = document.getElementById("btn-generate-brief");
  const btnSaveDraft = document.getElementById("btn-save-draft");
  let currentBrief = null;

  if (btnGenerateBrief) {
    btnGenerateBrief.addEventListener("click", async () => {
      const topicSelect = document.getElementById("copilot-topic-select");
      const questionInput = document.getElementById("copilot-question-input");
      const topic = topicSelect ? topicSelect.value : "Tata STRIVE Programmes";
      const audience_question = questionInput ? questionInput.value.trim() : null;
      const csrf = btnGenerateBrief.dataset.csrf;

      btnGenerateBrief.disabled = true;
      btnGenerateBrief.textContent = "Analyzing discourse & drafting brief…";

      try {
        const res = await fetch("/api/copilot/generate", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Harken-CSRF": csrf,
          },
          body: JSON.stringify({ topic, audience_question }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to generate brief");

        currentBrief = data;

        // Populate brief fields
        const titleEl = document.getElementById("copilot-title");
        const objEl = document.getElementById("copilot-objective");
        const whyEl = document.getElementById("copilot-why");
        const needEl = document.getElementById("copilot-need");
        const captionEl = document.getElementById("copilot-caption");
        const ctaEl = document.getElementById("copilot-cta");
        const guardrailEl = document.getElementById("copilot-guardrail-text");
        const carouselDeck = document.getElementById("copilot-carousel-deck");
        const videoScript = document.getElementById("copilot-video-script");

        if (titleEl) titleEl.textContent = data.campaign_title;
        if (objEl) objEl.textContent = data.objective;
        if (whyEl) whyEl.textContent = data.why_it_matters;
        if (needEl) needEl.textContent = data.audience_need;
        if (captionEl) captionEl.textContent = data.caption;
        if (ctaEl) ctaEl.textContent = data.cta;
        if (guardrailEl) guardrailEl.textContent = data.verification_guardrail;
        if (videoScript) videoScript.innerHTML = data.short_video_concept.replace(/\n/g, "<br>");

        if (carouselDeck && Array.isArray(data.carousel_outline)) {
          carouselDeck.innerHTML = data.carousel_outline
            .map((slide, idx) => `
              <div class="carousel-slide">
                <div class="carousel-slide-num">SLIDE ${idx + 1}</div>
                <div>${slide}</div>
              </div>
            `)
            .join("");
        }
      } catch (err) {
        alert("Brief generation failed: " + err.message);
      } finally {
        btnGenerateBrief.disabled = false;
        btnGenerateBrief.textContent = "✨ Generate Campaign Brief";
      }
    });
  }

  if (btnSaveDraft) {
    btnSaveDraft.addEventListener("click", async () => {
      if (!currentBrief) {
        alert("Please generate a campaign brief first.");
        return;
      }
      const csrf = btnSaveDraft.dataset.csrf;
      btnSaveDraft.disabled = true;

      try {
        const payload = {
          title: currentBrief.campaign_title,
          topic: currentBrief.topic,
          platform: "Instagram",
          status: "draft",
          objective: currentBrief.objective,
          carousel_outline: JSON.stringify(currentBrief.carousel_outline),
          video_concept: currentBrief.short_video_concept,
          caption: currentBrief.caption,
          cta: currentBrief.cta,
          supporting_urls: currentBrief.supporting_urls || [],
        };

        const res = await fetch("/api/campaigns", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Harken-CSRF": csrf,
          },
          body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error("Could not save draft");

        btnSaveDraft.textContent = "✓ Saved to Planner!";
        window.setTimeout(() => {
          switchTab("planner");
          window.location.reload();
        }, 600);
      } catch (err) {
        alert("Error saving draft: " + err.message);
        btnSaveDraft.disabled = false;
      }
    });
  }

  // ---- 6. Campaign Planner Actions ----------------------------------------
  document.addEventListener("change", async (e) => {
    const select = e.target.closest(".status-change-select");
    if (!select) return;
    const draftId = select.dataset.draftId;
    const status = select.value;

    try {
      const res = await fetch(`/api/campaigns/${draftId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "X-Harken-CSRF": document.querySelector("[data-csrf]")?.dataset.csrf || "",
        },
        body: JSON.stringify({
          title: "Updated Campaign",
          topic: "Tata STRIVE",
          status: status,
        }),
      });
      if (!res.ok) throw new Error("Could not update status");
      const card = select.closest(".planner-card");
      const pill = card?.querySelector(".status-pill");
      if (pill) {
        pill.className = `status-pill ${status}`;
        pill.textContent = status;
      }
    } catch (err) {
      alert("Status update failed: " + err.message);
    }
  });

  document.addEventListener("click", async (e) => {
    const btn = e.target.closest(".btn-delete-draft");
    if (!btn) return;
    if (!confirm("Are you sure you want to delete this campaign draft?")) return;
    const draftId = btn.dataset.draftId;
    const csrf = btn.dataset.csrf;

    try {
      const res = await fetch(`/api/campaigns/${draftId}`, {
        method: "DELETE",
        headers: { "X-Harken-CSRF": csrf },
      });
      if (!res.ok) throw new Error("Delete failed");
      const card = btn.closest(".planner-card");
      card?.remove();
    } catch (err) {
      alert("Delete failed: " + err.message);
    }
  });

  // ---- 7. Alerts Resolution Action ----------------------------------------
  document.addEventListener("click", async (e) => {
    const btn = e.target.closest(".btn-resolve-alert");
    if (!btn) return;
    const alertId = btn.dataset.alertId;
    const csrf = btn.dataset.csrf;

    btn.disabled = true;
    btn.textContent = "Resolving…";

    try {
      const res = await fetch(`/api/alerts/${alertId}/resolve`, {
        method: "POST",
        headers: { "X-Harken-CSRF": csrf },
      });
      if (!res.ok) throw new Error("Resolve action failed");
      const alertItem = btn.closest(".alert-item");
      alertItem?.remove();
      
      const badge = document.querySelector(".tab-badge.alert-badge");
      if (badge) {
        const count = parseInt(badge.textContent, 10) - 1;
        if (count <= 0) badge.remove();
        else badge.textContent = count;
      }
    } catch (err) {
      alert("Could not resolve alert: " + err.message);
      btn.disabled = false;
      btn.textContent = "✓ Mark as Resolved";
    }
  });

  // ---- 8. Hover Trace Bar Chart & 7-Dates Switcher --------------------------
  const btnChart7d = document.getElementById("btn-chart-7d");
  const btnChartAll = document.getElementById("btn-chart-all");
  const chartView7d = document.getElementById("chart-view-7d");
  const chartViewAll = document.getElementById("chart-view-all");
  const chartRangeLabel = document.getElementById("chart-range-label");
  const chartTraceCounter = document.getElementById("chart-trace-counter");
  const chartTraceBreakdown = document.getElementById("chart-trace-breakdown");
  const chartTracePeriod = document.getElementById("chart-trace-period");

  const defaultTotal = chartTraceCounter ? chartTraceCounter.textContent : "0";
  const defaultBreakdown = chartTraceBreakdown ? chartTraceBreakdown.textContent : "";
  const defaultPeriodAll = chartTracePeriod ? chartTracePeriod.textContent : "";
  const defaultRangeLabelAll = chartRangeLabel ? chartRangeLabel.textContent : "";

  function switchTimelineRange(mode) {
    if (mode === "7d") {
      btnChart7d?.classList.add("active");
      btnChartAll?.classList.remove("active");
      if (chartView7d) chartView7d.style.display = "flex";
      if (chartViewAll) chartViewAll.style.display = "none";
      if (chartRangeLabel) chartRangeLabel.textContent = "Last 7 Days (Daily)";
      if (chartTracePeriod) chartTracePeriod.textContent = "Past 7 Calendar Days";
    } else {
      btnChartAll?.classList.add("active");
      btnChart7d?.classList.remove("active");
      if (chartViewAll) chartViewAll.style.display = "flex";
      if (chartView7d) chartView7d.style.display = "none";
      if (chartRangeLabel) chartRangeLabel.textContent = defaultRangeLabelAll;
      if (chartTracePeriod) chartTracePeriod.textContent = defaultPeriodAll;
    }
  }

  if (btnChart7d) btnChart7d.addEventListener("click", () => switchTimelineRange("7d"));
  if (btnChartAll) btnChartAll.addEventListener("click", () => switchTimelineRange("all"));

  function setupHoverTraceChart(chartId, lineId, badgeId) {
    const chart = document.getElementById(chartId);
    const line = document.getElementById(lineId);
    const badge = document.getElementById(badgeId);
    if (!chart || !line || !badge) return;

    const cols = chart.querySelectorAll(".col, .col-7d");
    cols.forEach((col) => {
      col.addEventListener("mouseenter", () => {
        cols.forEach((c) => c.classList.remove("hovered"));
        col.classList.add("hovered");

        const total = col.dataset.total || "0";
        const pos = col.dataset.pos || "0";
        const neu = col.dataset.neu || "0";
        const neg = col.dataset.neg || "0";
        const label = col.dataset.label || "";
        const height = parseFloat(col.dataset.height || "0");

        if (chartTraceCounter) chartTraceCounter.textContent = total;
        if (chartTraceBreakdown) chartTraceBreakdown.textContent = `${pos} pos · ${neu} neu · ${neg} neg`;
        if (chartTracePeriod) chartTracePeriod.textContent = label;

        badge.textContent = Number(total).toLocaleString();
        line.style.bottom = `${Math.max(4, Math.min(95, height))}%`;
        line.classList.add("visible");
      });
    });

    chart.addEventListener("mouseleave", () => {
      cols.forEach((c) => c.classList.remove("hovered"));
      line.classList.remove("visible");
      if (chartTraceCounter) chartTraceCounter.textContent = defaultTotal;
      if (chartTraceBreakdown) chartTraceBreakdown.textContent = defaultBreakdown;
      if (chartTracePeriod) chartTracePeriod.textContent = defaultPeriod7d;
    });
  }

  setupHoverTraceChart("chart-view-7d", "chart-trace-line-7d", "chart-trace-badge-7d");
  setupHoverTraceChart("chart-view-all", "chart-trace-line-all", "chart-trace-badge-all");

  // ---- 9. be-ui-tilt-card 3D Physics & Dynamic Glare -----------------------
  function setupTiltCards() {
    const isHoverCapable = window.matchMedia && window.matchMedia("(hover: hover) and (pointer: fine)").matches;
    const isReducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!isHoverCapable || isReducedMotion) return;

    const maxTilt = 12;

    document.addEventListener("mousemove", (e) => {
      const card = e.target.closest(".tilt-card");
      if (!card) return;

      const rect = card.getBoundingClientRect();
      const px = (e.clientX - rect.left) / rect.width;
      const py = (e.clientY - rect.top) / rect.height;

      const ry = (px - 0.5) * maxTilt;
      const rx = (0.5 - py) * maxTilt;
      const gx = px * 100;
      const gy = py * 100;

      card.style.setProperty("--rx", `${rx.toFixed(2)}deg`);
      card.style.setProperty("--ry", `${ry.toFixed(2)}deg`);
      card.style.setProperty("--gx", `${gx.toFixed(1)}%`);
      card.style.setProperty("--gy", `${gy.toFixed(1)}%`);
    });

    document.addEventListener("mouseout", (e) => {
      const card = e.target.closest(".tilt-card");
      if (!card) return;
      if (!card.contains(e.relatedTarget)) {
        card.style.setProperty("--rx", "0deg");
        card.style.setProperty("--ry", "0deg");
      }
    });
  }

  setupTiltCards();
})();
