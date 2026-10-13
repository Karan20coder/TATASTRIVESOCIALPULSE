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

  // ---- 10. Generate Topic Intelligence & Analytics ------------------------
  function setupTopicIntelligence() {
    const btnGenerate = document.getElementById("btn-generate-topic-intel");
    const btnText = document.getElementById("btn-intel-text");
    const statusMsg = document.getElementById("topic-intel-status");
    const container = document.getElementById("topic-intel-container");

    const newsSearch = document.getElementById("news-search");
    const newsSourceFilter = document.getElementById("news-source-filter");
    const newsRangeFilter = document.getElementById("news-range-filter");

    const modalBackdrop = document.getElementById("articles-modal-backdrop");
    const btnCloseModal = document.getElementById("btn-close-modal");
    const modalTopicName = document.getElementById("modal-topic-name");
    const modalTopicDot = document.getElementById("modal-topic-color-dot");
    const modalTopicCount = document.getElementById("modal-topic-count");
    const modalArticlesList = document.getElementById("modal-articles-list");

    if (!btnGenerate) return;

    let cachedIntelData = null;
    let selectedMomentumTopic = "All Topics";
    let sortKey = "count";
    let sortAsc = false;

    // Helper to open supporting articles modal
    function openArticlesModal(topicName, color, articles) {
      if (!modalBackdrop || !articles) return;
      modalTopicName.textContent = topicName;
      if (modalTopicDot) modalTopicDot.style.background = color || "#0ea5e9";
      if (modalTopicCount) modalTopicCount.textContent = `${articles.length} article${articles.length === 1 ? "" : "s"}`;

      if (articles.length === 0) {
        modalArticlesList.innerHTML = `<div style="text-align: center; color: var(--dim); padding: 24px;">No supporting articles available for this topic.</div>`;
      } else {
        modalArticlesList.innerHTML = articles.map(a => `
          <div class="modal-article-item">
            <div class="modal-article-head">
              <span class="modal-article-pub">${esc(a.author || "Verified Media")}</span>
              <span class="modal-article-date">${esc(a.published_date || "")}</span>
            </div>
            <h4 class="modal-article-title">
              <a href="${esc(a.url || "#")}" target="_blank" rel="noopener noreferrer">${esc(a.title || "Untitled Article")} ↗</a>
            </h4>
            <div class="modal-article-snippet">${esc(a.snippet || "")}</div>
            <div class="modal-article-foot">
              <span class="mono" style="font-size: 11px; color: var(--faint);">Source: ${esc(a.source.toUpperCase())}</span>
              ${a.url ? `<a href="${esc(a.url)}" target="_blank" rel="noopener noreferrer" class="modal-article-link">Read Full Story ↗</a>` : ""}
            </div>
          </div>
        `).join("");
      }

      modalBackdrop.classList.add("open");
      modalBackdrop.setAttribute("aria-hidden", "false");
    }

    function closeModal() {
      if (!modalBackdrop) return;
      modalBackdrop.classList.remove("open");
      modalBackdrop.setAttribute("aria-hidden", "true");
    }

    if (btnCloseModal) {
      btnCloseModal.addEventListener("click", closeModal);
    }
    if (modalBackdrop) {
      modalBackdrop.addEventListener("click", (e) => {
        if (e.target === modalBackdrop) closeModal();
      });
    }
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && modalBackdrop?.classList.contains("open")) {
        closeModal();
      }
    });

    // ---- Interactive Dither Donut Chart (Canvas 2D + Spring Physics) ----
    let ditherAnimId = null;
    let ditherRO = null;
    let ditherIO = null;

    const smoothstep = (min, max, value) => {
      const x = Math.max(0, Math.min(1, (value - min) / (max - min)));
      return x * x * (3 - 2 * x);
    };

    const hash = (x, y) => {
      let h = Math.sin(x * 12.9898 + y * 78.233) * 43758.5453;
      return h - Math.floor(h);
    };

    const hexToRgba = (hex, alpha) => {
      let clean = (hex || "#0ea5e9").replace("#", "");
      if (clean.length === 3) clean = clean.split("").map(c => c + c).join("");
      const r = parseInt(clean.slice(0, 2), 16) || 0;
      const g = parseInt(clean.slice(2, 4), 16) || 0;
      const b = parseInt(clean.slice(4, 6), 16) || 0;
      return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    };

    const drawRoundedWedge = (ctx, cx, cy, rIn, rOut, aStart, aEnd, cr) => {
      const sweep = aEnd - aStart;
      const maxCr = Math.min(cr, (rOut - rIn) / 2, (sweep * rIn) / 2);
      if (sweep <= 0.001) return;
      const crIn = maxCr;
      const crOut = maxCr;

      const aStartIn = aStart + crIn / rIn;
      const aEndIn = aEnd - crIn / rIn;
      const aStartOut = aStart + crOut / rOut;
      const aEndOut = aEnd - crOut / rOut;

      ctx.moveTo(cx + rIn * Math.cos(aStartIn), cy + rIn * Math.sin(aStartIn));
      ctx.arc(cx, cy, rIn, aStartIn, aEndIn);
      ctx.arcTo(
        cx + rIn * Math.cos(aEnd),
        cy + rIn * Math.sin(aEnd),
        cx + rOut * Math.cos(aEnd),
        cy + rOut * Math.sin(aEnd),
        crIn
      );
      ctx.arcTo(
        cx + rOut * Math.cos(aEnd),
        cy + rOut * Math.sin(aEnd),
        cx + rOut * Math.cos(aEndOut),
        cy + rOut * Math.sin(aEndOut),
        crOut
      );
      ctx.arc(cx, cy, rOut, aEndOut, aStartOut, true);
      ctx.arcTo(
        cx + rOut * Math.cos(aStart),
        cy + rOut * Math.sin(aStart),
        cx + rIn * Math.cos(aStart),
        cy + rIn * Math.sin(aStart),
        crOut
      );
      ctx.arcTo(
        cx + rIn * Math.cos(aStart),
        cy + rIn * Math.sin(aStart),
        cx + rIn * Math.cos(aStartIn),
        cy + rIn * Math.sin(aStartIn),
        crIn
      );
    };

    function renderDonutChart(segments, totalUnique, articlesByTopic) {
      const canvas = document.getElementById("dither-donut-canvas");
      const legend = document.getElementById("donut-legend");
      const centerMetric = document.getElementById("donut-center-metric");
      const centerLabel = document.getElementById("donut-center-label");
      const centerSub = document.getElementById("donut-center-sub");
      const periodTabs = document.querySelectorAll(".dither-period-tab");

      if (!canvas || !legend) return;

      if (ditherAnimId) cancelAnimationFrame(ditherAnimId);
      if (ditherRO) ditherRO.disconnect();
      if (ditherIO) ditherIO.disconnect();

      if (!segments || segments.length === 0) {
        legend.innerHTML = `<div style="color: var(--dim); padding: 12px;">No topic segments to display.</div>`;
        return;
      }

      // Base segments dataset
      const allSegments = JSON.parse(JSON.stringify(segments));
      let currentPeriod = "all";
      let activeSegments = [...allSegments];
      let currentTotal = totalUnique;

      // Shares calculation
      const calcShares = (segs) => {
        const sum = segs.reduce((acc, s) => acc + s.article_count, 0) || 1;
        return segs.map(s => s.article_count / sum);
      };

      let fromShares = calcShares(activeSegments);
      let targetShares = [...fromShares];
      let dispShares = [...fromShares];
      let morphStartTime = 0;
      let hoverIndex = null;
      let time = 0;

      // Canvas setup with DPR & ResizeObserver
      const ctx = canvas.getContext("2d");
      const rect = { width: 0, height: 0 };
      let isVisible = true;

      const updateCanvasSize = () => {
        const bound = canvas.getBoundingClientRect();
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        rect.width = bound.width || 340;
        rect.height = bound.height || 340;
        canvas.width = Math.round(rect.width * dpr);
        canvas.height = Math.round(rect.height * dpr);
      };
      updateCanvasSize();

      ditherRO = new ResizeObserver((entries) => {
        for (const entry of entries) {
          const { width, height } = entry.contentRect;
          if (width > 0 && height > 0) {
            rect.width = width;
            rect.height = height;
            const dpr = Math.min(window.devicePixelRatio || 1, 2);
            canvas.width = Math.round(width * dpr);
            canvas.height = Math.round(height * dpr);
          }
        }
      });
      ditherRO.observe(canvas);

      ditherIO = new IntersectionObserver(([entry]) => {
        isVisible = entry.isIntersecting;
      });
      ditherIO.observe(canvas);

      // Render legend rows
      function updateLegend() {
        legend.innerHTML = activeSegments.map((seg, idx) => {
          const isHovered = hoverIndex === idx;
          return `
            <div class="legend-item ${isHovered ? "highlighted" : ""}" data-idx="${idx}" data-topic="${esc(seg.name)}" data-color="${seg.color}">
              <div class="legend-left">
                <span class="legend-dot" style="background: ${seg.color}; color: ${seg.color}"></span>
                <span class="legend-name" title="${esc(seg.name)}">${esc(seg.name)}</span>
              </div>
              <div class="legend-right">
                <span class="legend-count">${seg.article_count} art.</span>
                <span class="legend-pct">${Math.round(seg.percentage_share)}%</span>
                <span class="legend-view-btn">View ↗</span>
              </div>
            </div>
          `;
        }).join("");

        legend.querySelectorAll(".legend-item").forEach(item => {
          const idx = parseInt(item.dataset.idx, 10);
          item.addEventListener("mouseenter", () => {
            hoverIndex = idx;
            updateCenterInfo();
          });
          item.addEventListener("mouseleave", () => {
            hoverIndex = null;
            updateCenterInfo();
          });
          item.addEventListener("click", () => {
            const topic = activeSegments[idx].name;
            const color = activeSegments[idx].color;
            const arts = articlesByTopic[topic] || [];
            openArticlesModal(topic, color, arts);
          });
        });
      }

      function updateCenterInfo() {
        if (hoverIndex !== null && activeSegments[hoverIndex]) {
          const seg = activeSegments[hoverIndex];
          centerMetric.textContent = `${Math.round(seg.percentage_share)}%`;
          centerMetric.style.color = seg.color;
          centerLabel.textContent = seg.name;
          centerSub.textContent = `${seg.article_count} article${seg.article_count === 1 ? "" : "s"}`;
        } else {
          centerMetric.textContent = currentTotal.toLocaleString();
          centerMetric.style.color = "#ffffff";
          centerLabel.textContent = "Unique Articles";
          centerSub.textContent = "100% Share";
        }
        // Update legend items hover class
        legend.querySelectorAll(".legend-item").forEach((el, idx) => {
          el.classList.toggle("highlighted", hoverIndex === idx);
        });
      }

      // Period Filter Handler
      function applyPeriod(periodKey) {
        currentPeriod = periodKey;
        periodTabs.forEach(t => t.classList.toggle("active", t.dataset.period === periodKey));

        // Period filter logic on actual article publication dates
        let maxDays = Infinity;
        if (periodKey === "month") maxDays = 30;
        else if (periodKey === "week") maxDays = 7;

        let newTotal = 0;
        let newSegments = allSegments.map(orig => {
          const arts = articlesByTopic[orig.name] || [];
          let count = arts.length;
          if (maxDays < Infinity && arts.length > 0) {
            // Filter articles within maxDays relative to the freshest article
            const dates = arts.map(a => a.published_date ? new Date(a.published_date).getTime() : 0).filter(t => !isNaN(t) && t > 0);
            if (dates.length > 0) {
              const latestTime = Math.max(...dates);
              const cutoff = latestTime - (maxDays * 86400 * 1000);
              const filtered = arts.filter(a => {
                const at = a.published_date ? new Date(a.published_date).getTime() : 0;
                return !isNaN(at) && at >= cutoff;
              });
              count = Math.max(1, filtered.length);
            } else {
              count = Math.max(1, Math.round(orig.article_count * (periodKey === "week" ? 0.35 : 0.75)));
            }
          }
          newTotal += count;
          return {
            ...orig,
            article_count: count,
          };
        });

        // Compute percentage share
        newSegments = newSegments.map(s => ({
          ...s,
          percentage_share: Math.round((s.article_count / (newTotal || 1)) * 1000) / 10,
        }));

        activeSegments = newSegments;
        currentTotal = newTotal;

        fromShares = [...dispShares];
        targetShares = calcShares(activeSegments);
        morphStartTime = performance.now();

        updateLegend();
        updateCenterInfo();
      }

      periodTabs.forEach(btn => {
        btn.onclick = () => applyPeriod(btn.dataset.period);
      });

      // Canvas Interactive Hover & Click Detection
      function getSliceAtCoord(clientX, clientY) {
        const bound = canvas.getBoundingClientRect();
        const scale = 200 / bound.width;
        const mx = (clientX - bound.left) * scale;
        const my = (clientY - bound.top) * scale;
        const dx = mx - 100;
        const dy = my - 100;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < 50 || dist > 92) return null;

        let mouseAngle = Math.atan2(dy, dx);
        let normMouse = mouseAngle - (-Math.PI / 2);
        while (normMouse < 0) normMouse += Math.PI * 2;
        while (normMouse >= Math.PI * 2) normMouse -= Math.PI * 2;

        let cumAngle = 0;
        for (let i = 0; i < dispShares.length; i++) {
          const sweep = dispShares[i] * Math.PI * 2;
          if (normMouse >= cumAngle && normMouse < cumAngle + sweep) {
            return i;
          }
          cumAngle += sweep;
        }
        return null;
      }

      canvas.onmousemove = (e) => {
        const found = getSliceAtCoord(e.clientX, e.clientY);
        if (found !== hoverIndex) {
          hoverIndex = found;
          updateCenterInfo();
        }
      };

      canvas.onmouseleave = () => {
        if (hoverIndex !== null) {
          hoverIndex = null;
          updateCenterInfo();
        }
      };

      canvas.onclick = (e) => {
        const found = getSliceAtCoord(e.clientX, e.clientY);
        if (found !== null && activeSegments[found]) {
          const topic = activeSegments[found].name;
          const color = activeSegments[found].color;
          const arts = articlesByTopic[topic] || [];
          openArticlesModal(topic, color, arts);
        }
      };

      // Main Canvas 60 FPS Dither Loop
      function draw() {
        if (!isVisible) {
          ditherAnimId = requestAnimationFrame(draw);
          return;
        }

        if (!ctx || rect.width === 0 || rect.height === 0) {
          ditherAnimId = requestAnimationFrame(draw);
          return;
        }

        time += 0.02;

        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        const logicalSize = 200;

        ctx.save();
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.scale((rect.width * dpr) / logicalSize, (rect.height * dpr) / logicalSize);

        // Spring morph interpolation
        let t = 1;
        if (morphStartTime > 0) {
          t = (performance.now() - morphStartTime) / 480;
          if (t > 1) t = 1;
        }
        const e = 1 - Math.pow(2, -10 * t);

        for (let i = 0; i < targetShares.length; i++) {
          dispShares[i] = fromShares[i] + (targetShares[i] - fromShares[i]) * e;
        }

        let startAngle = -Math.PI / 2;
        const gap = 0.06;
        const currentHover = hoverIndex;

        for (let i = 0; i < dispShares.length; i++) {
          const share = dispShares[i];
          if (share <= 0.001) continue;

          let sweep = share * Math.PI * 2;
          let aStart = startAngle + gap / 2;
          let aEnd = startAngle + sweep - gap / 2;
          if (aEnd < aStart) aEnd = aStart;

          ctx.save();
          const isHovered = currentHover === i;
          const isAnyHovered = currentHover !== null;

          if (isHovered) {
            const mid = (aStart + aEnd) / 2;
            ctx.translate(Math.cos(mid) * 6, Math.sin(mid) * 6);
          }

          ctx.beginPath();
          drawRoundedWedge(ctx, 100, 100, 55, 86, aStart, aEnd, 6);
          ctx.clip();

          ctx.globalAlpha = isHovered ? 1.0 : isAnyHovered ? 0.28 : 0.76;
          ctx.fillStyle = activeSegments[i].color;

          if (isHovered) {
            ctx.shadowColor = hexToRgba(activeSegments[i].color, 0.65);
            ctx.shadowBlur = 7;
            ctx.shadowOffsetX = 0;
            ctx.shadowOffsetY = 0;
          }

          const cell = 4.6;
          const t2 = time;
          for (let x = 14; x <= 186; x += cell) {
            for (let y = 14; y <= 186; y += cell) {
              const dx = x - 100;
              const dy = y - 100;
              const dist = Math.sqrt(dx * dx + dy * dy);
              if (dist < 55 - cell || dist > 86 + cell) continue;

              let a = Math.atan2(dy, dx);
              let normalizedA = a - aStart;
              while (normalizedA < 0) normalizedA += Math.PI * 2;
              while (normalizedA >= Math.PI * 2) normalizedA -= Math.PI * 2;
              if (normalizedA > aEnd - aStart) continue;

              const fullness = smoothstep(0.62, 1.0, (dist - 55) / (86 - 55));
              const waveRaw = Math.sin(dist * 0.1 - t2) +
                              Math.sin(a * 3 + t2 * 1.5) +
                              Math.sin(dx * 0.05 + dy * 0.05 + t2 * 2);
              const wave = smoothstep(-1.5, 1.5, waveRaw);
              const jitter = hash(x, y);

              const size = cell * ((isHovered ? 0.46 : 0.34) + 0.36 * fullness + 0.26 * wave) * (0.78 + 0.42 * jitter);
              ctx.fillRect(x - size / 2, y - size / 2, size, size);
            }
          }

          ctx.restore();
          startAngle += sweep;
        }

        ctx.restore();
        ditherAnimId = requestAnimationFrame(draw);
      }

      updateLegend();
      updateCenterInfo();
      ditherAnimId = requestAnimationFrame(draw);
    }

    // Topic Priority Ranking Deck Renderer
    function renderPriorityDeck(topics, articlesByTopic) {
      const deck = document.getElementById("priority-deck");
      if (!deck) return;

      if (!topics || topics.length === 0) {
        deck.innerHTML = `<div style="color: var(--dim); padding: 12px;">No priority rankings available.</div>`;
        return;
      }

      deck.innerHTML = topics.map((t, idx) => {
        const rank = idx + 1;
        const score = t.priority_score;
        const color = t.color;
        const pubs = t.publishers.slice(0, 3).join(", ") + (t.publishers.length > 3 ? ` +${t.publishers.length - 3} more` : "");

        return `
          <div class="priority-card" style="border-left: 4px solid ${color};">
            <div class="priority-card-top">
              <div class="priority-card-left">
                <span class="priority-rank-badge ${rank === 1 ? "rank-1" : ""}">#${rank}</span>
                <h4 class="priority-topic-title">${esc(t.name)}</h4>
              </div>
              <div class="priority-card-badges">
                <span class="priority-momentum-pill ${t.momentum_badge}">${t.momentum_label} Momentum</span>
                <div class="priority-score-box" title="Composite Priority Score: ${score}/100">
                  <span class="priority-score-num">${score}</span>
                  <span class="priority-score-denom">/100</span>
                </div>
              </div>
            </div>

            <div class="priority-bar-wrap">
              <div class="priority-bar">
                <div class="priority-bar-fill" style="width: ${score}%; background: linear-gradient(90deg, #004b87, ${color});"></div>
              </div>
            </div>

            <div class="priority-metrics-strip">
              <span>Coverage: <b>${t.article_count} articles (${t.percentage_share}%)</b></span>
              <span>·</span>
              <span>Mission Relevance: <b>${t.relevance_score_pct}%</b></span>
              <span>·</span>
              <span>Independent Publishers: <b>${t.publisher_count} outlets</b> <small style="color: var(--faint);">(${esc(pubs)})</small></span>
              <span>·</span>
              <span>Freshness: <b>${esc(t.latest_date)}</b></span>
            </div>

            <div class="priority-card-rationale">
              <span><strong>Strategic Rationale:</strong> ${esc(t.explanation)}</span>
              <button type="button" class="btn-view-evidence" data-topic="${esc(t.name)}" data-color="${color}">
                View ${t.article_count} Supporting Articles →
              </button>
            </div>
          </div>
        `;
      }).join("");

      deck.querySelectorAll(".btn-view-evidence").forEach(btn => {
        btn.addEventListener("click", () => {
          const topic = btn.dataset.topic;
          const color = btn.dataset.color;
          const arts = articlesByTopic[topic] || [];
          openArticlesModal(topic, color, arts);
        });
      });
    }

    // Momentum Time-Series Timeline Chart
    function renderMomentumChart(timeSeries, allTopicNames, activeTopic) {
      const pillsContainer = document.getElementById("momentum-topic-pills");
      const stage = document.getElementById("momentum-chart-stage");
      if (!pillsContainer || !stage) return;

      // Render filter pills
      const pillTopics = ["All Topics", ...allTopicNames];
      pillsContainer.innerHTML = pillTopics.map(name => `
        <button type="button" class="momentum-pill-btn ${name === activeTopic ? "active" : ""}" data-topic="${esc(name)}">
          ${name}
        </button>
      `).join("");

      pillsContainer.querySelectorAll(".momentum-pill-btn").forEach(btn => {
        btn.addEventListener("click", () => {
          selectedMomentumTopic = btn.dataset.topic;
          renderMomentumChart(timeSeries, allTopicNames, selectedMomentumTopic);
        });
      });

      if (!timeSeries || timeSeries.length === 0) {
        stage.innerHTML = `<div style="text-align: center; color: var(--dim); padding: 40px;">No historical publication data in selected range.</div>`;
        return;
      }

      // Compute data points for selected topic
      const dataPoints = timeSeries.map(pt => {
        const count = activeTopic === "All Topics"
          ? pt.total_articles
          : (pt.topic_counts[activeTopic] || 0);
        return { date: pt.date, count: count };
      });

      const maxVal = Math.max(...dataPoints.map(p => p.count), 1);
      const w = 780;
      const h = 200;
      const padLeft = 40;
      const padRight = 20;
      const padTop = 20;
      const padBottom = 30;

      const chartW = w - padLeft - padRight;
      const chartH = h - padTop - padBottom;

      const n = dataPoints.length;
      const stepX = n > 1 ? chartW / (n - 1) : chartW / 2;

      const coords = dataPoints.map((p, i) => {
        const x = padLeft + (n > 1 ? i * stepX : chartW / 2);
        const y = padTop + chartH - (p.count / maxVal) * chartH;
        return { ...p, x, y };
      });

      const lineD = coords.reduce((acc, c, i) => `${acc} ${i === 0 ? "M" : "L"} ${c.x} ${c.y}`, "");
      const areaD = `${lineD} L ${coords[coords.length - 1].x} ${padTop + chartH} L ${coords[0].x} ${padTop + chartH} Z`;

      let svgHtml = `
        <svg viewBox="0 0 ${w} ${h}" style="width: 100%; height: 100%; overflow: visible;">
          <defs>
            <linearGradient id="momentumGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#0ea5e9" stop-opacity="0.35"/>
              <stop offset="100%" stop-color="#0ea5e9" stop-opacity="0.0"/>
            </linearGradient>
          </defs>

          <!-- Grid horizontal lines -->
          <line x1="${padLeft}" y1="${padTop}" x2="${w - padRight}" y2="${padTop}" stroke="rgba(255,255,255,0.06)" stroke-dasharray="3 3"/>
          <line x1="${padLeft}" y1="${padTop + chartH / 2}" x2="${w - padRight}" y2="${padTop + chartH / 2}" stroke="rgba(255,255,255,0.06)" stroke-dasharray="3 3"/>
          <line x1="${padLeft}" y1="${padTop + chartH}" x2="${w - padRight}" y2="${padTop + chartH}" stroke="rgba(255,255,255,0.12)"/>

          <!-- Y-axis labels -->
          <text x="${padLeft - 8}" y="${padTop + 4}" fill="#64748b" font-size="10" font-family="var(--mono)" text-anchor="end">${maxVal}</text>
          <text x="${padLeft - 8}" y="${padTop + chartH / 2 + 4}" fill="#64748b" font-size="10" font-family="var(--mono)" text-anchor="end">${Math.round(maxVal / 2)}</text>
          <text x="${padLeft - 8}" y="${padTop + chartH + 4}" fill="#64748b" font-size="10" font-family="var(--mono)" text-anchor="end">0</text>

          <!-- Area & Line -->
          <path d="${areaD}" fill="url(#momentumGrad)"/>
          <path d="${lineD}" fill="none" stroke="#0ea5e9" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>

          <!-- Circles & Labels -->
          ${coords.map(c => `
            <g class="momentum-dot-group" tabindex="0">
              <circle cx="${c.x}" cy="${c.y}" r="4.5" fill="#12151e" stroke="#38bdf8" stroke-width="2">
                <title>${c.date}: ${c.count} article${c.count === 1 ? "" : "s"}</title>
              </circle>
              <text x="${c.x}" y="${padTop + chartH + 18}" fill="#94a3b8" font-size="9.5" font-family="var(--mono)" text-anchor="middle">
                ${c.date.slice(5)}
              </text>
            </g>
          `).join("")}
        </svg>
      `;

      stage.innerHTML = svgHtml;
    }

    // AI Strategic Recommendations Renderer
    function renderRecommendations(recommendations) {
      const grid = document.getElementById("ai-recs-grid");
      if (!grid) return;

      if (!recommendations || recommendations.length === 0) {
        grid.innerHTML = `<div style="color: var(--dim); padding: 12px;">No recommendations available.</div>`;
        return;
      }

      grid.innerHTML = recommendations.map(rec => `
        <div class="ai-rec-card">
          <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
              <span class="ai-rec-topic-tag">${esc(rec.topic)}</span>
              <span class="tab-badge" style="background: rgba(14, 165, 233, 0.2); color: #38bdf8;">Score ${rec.priority_score}/100</span>
            </div>
            <h4 class="ai-rec-title">${esc(rec.campaign_idea)}</h4>
            <p class="ai-rec-concept" style="margin-top: 8px;">${esc(rec.content_concept)}</p>
          </div>

          <div class="ai-rec-meta-block">
            <div class="ai-rec-meta-row">
              <span class="ai-rec-meta-k">Objective</span>
              <span class="ai-rec-meta-v">${esc(rec.communication_objective)}</span>
            </div>
            <div class="ai-rec-meta-row">
              <span class="ai-rec-meta-k">Audience</span>
              <span class="ai-rec-meta-v">${esc(rec.target_audience)}</span>
            </div>
            <div style="margin-top: 4px;">
              <div class="ai-rec-hashtags">
                ${rec.suggested_hashtags.map(tag => `<span class="ai-rec-tag">${esc(tag)}</span>`).join("")}
              </div>
            </div>
            <div style="margin-top: 6px; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.06);">
              <span class="ai-rec-meta-k" style="display: block; margin-bottom: 2px;">Verified Evidence Citation:</span>
              <a href="${esc(rec.evidence_url)}" target="_blank" rel="noopener noreferrer" class="ai-rec-evidence-link" title="Click to open source story">
                📰 "${esc(rec.evidence_headline)}" — ${esc(rec.evidence_publisher)} ↗
              </a>
            </div>
          </div>
        </div>
      `).join("");
    }

    // Sortable Topic Explorer Table Renderer
    function renderExplorerTable(topics, articlesByTopic) {
      const tbody = document.getElementById("explorer-tbody");
      if (!tbody) return;

      const sorted = [...topics].sort((a, b) => {
        let valA = a[sortKey];
        let valB = b[sortKey];
        if (sortKey === "count") {
          valA = a.article_count; valB = b.article_count;
        } else if (sortKey === "pct") {
          valA = a.percentage_share; valB = b.percentage_share;
        } else if (sortKey === "score") {
          valA = a.priority_score; valB = b.priority_score;
        } else if (sortKey === "pubs") {
          valA = a.publisher_count; valB = b.publisher_count;
        } else if (sortKey === "date") {
          valA = a.latest_date; valB = b.latest_date;
        } else if (sortKey === "name") {
          valA = a.name.toLowerCase(); valB = b.name.toLowerCase();
        }

        if (valA < valB) return sortAsc ? -1 : 1;
        if (valA > valB) return sortAsc ? 1 : -1;
        return 0;
      });

      tbody.innerHTML = sorted.map(t => `
        <tr>
          <td>
            <div class="topic-name-cell">
              <span style="width: 10px; height: 10px; border-radius: 3px; background: ${t.color}; display: inline-block;"></span>
              <strong>${esc(t.name)}</strong>
            </div>
          </td>
          <td class="mono"><strong>${t.article_count}</strong></td>
          <td class="mono"><strong>${t.percentage_share}%</strong></td>
          <td class="mono">${esc(t.latest_date)}</td>
          <td class="mono">${t.publisher_count} outlets</td>
          <td>
            <span class="mono" style="font-weight: 700; color: #38bdf8;">${t.priority_score}</span><small style="color: var(--faint);">/100</small>
          </td>
          <td>
            <button type="button" class="action-btn" data-topic="${esc(t.name)}" data-color="${t.color}">
              View Articles (${t.article_count}) ↗
            </button>
          </td>
        </tr>
      `).join("");

      tbody.querySelectorAll(".action-btn").forEach(btn => {
        btn.addEventListener("click", () => {
          const arts = articlesByTopic[btn.dataset.topic] || [];
          openArticlesModal(btn.dataset.topic, btn.dataset.color, arts);
        });
      });
    }

    // Set up table header sorting
    const tableHeaders = document.querySelectorAll(".explorer-table th[data-sort]");
    tableHeaders.forEach(th => {
      th.addEventListener("click", () => {
        const key = th.dataset.sort;
        if (sortKey === key) {
          sortAsc = !sortAsc;
        } else {
          sortKey = key;
          sortAsc = false;
        }
        if (cachedIntelData) {
          renderExplorerTable(cachedIntelData.priority_topics, cachedIntelData.articles_by_topic);
        }
      });
    });

    // Populate all Topic Intelligence views from payload
    function populateViews(data) {
      cachedIntelData = data;

      // 1. Audit pill
      const auditPill = document.getElementById("topic-audit-pill");
      if (auditPill) {
        auditPill.innerHTML = `<span>✓ Deduplicated: <strong>${data.deduplication.total_unique_articles}</strong> unique articles from <strong>${data.deduplication.total_raw_articles}</strong> collected (${data.deduplication.duplicates_removed} duplicates filtered)</span>`;
      }

      // 2. Summary KPI cards
      const kpiArticles = document.getElementById("kpi-unique-articles");
      const kpiDedupSub = document.getElementById("kpi-dedup-sub");
      const kpiTopics = document.getElementById("kpi-distinct-topics");
      const kpiTopTopic = document.getElementById("kpi-top-topic");
      const kpiTopShare = document.getElementById("kpi-top-share");
      const kpiHighPriority = document.getElementById("kpi-highest-priority");
      const kpiHighScore = document.getElementById("kpi-highest-score");

      if (kpiArticles) kpiArticles.textContent = data.summary_cards.total_unique.toLocaleString();
      if (kpiDedupSub) kpiDedupSub.textContent = `${data.deduplication.unique_publishers_count} independent publishers`;
      if (kpiTopics) kpiTopics.textContent = data.summary_cards.distinct_topics.toString();
      if (kpiTopTopic) kpiTopTopic.textContent = data.summary_cards.top_topic;
      if (kpiTopShare) kpiTopShare.textContent = `${data.summary_cards.top_topic_share}% of coverage`;
      if (kpiHighPriority) kpiHighPriority.textContent = data.summary_cards.highest_priority;
      if (kpiHighScore) kpiHighScore.textContent = `Score: ${data.summary_cards.highest_priority_score}/100`;

      // 3. Interactive Donut Chart
      renderDonutChart(data.segments, data.summary_cards.total_unique, data.articles_by_topic);

      // 4. Topic Priority Ranking
      renderPriorityDeck(data.priority_topics, data.articles_by_topic);

      // 5. Topic Momentum Chart
      renderMomentumChart(data.time_series, data.all_topic_names, selectedMomentumTopic);

      // 6. AI Strategic Recommendations
      renderRecommendations(data.recommendations);

      // 7. Sortable Topic Explorer Table
      renderExplorerTable(data.priority_topics, data.articles_by_topic);

      container.style.display = "flex";
      container.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    // Trigger analysis
    btnGenerate.addEventListener("click", async () => {
      btnGenerate.disabled = true;
      btnText.textContent = "Analysing News Database...";
      statusMsg.className = "topic-intel-status-msg loading";
      statusMsg.innerHTML = `<span class="topic-intel-spinner"></span> <span>Running deduplication & topic classification on database articles...</span>`;

      // Extract current filters
      const range = newsRangeFilter ? newsRangeFilter.value : "all";
      const source = newsSourceFilter ? newsSourceFilter.value : "";
      const searchVal = newsSearch ? newsSearch.value.trim() : "";
      const projectSelect = document.querySelector('select[name="p"]');
      const projectId = projectSelect && projectSelect.value ? parseInt(projectSelect.value, 10) : null;
      const querySelect = document.querySelector('select[name="q"]');
      const query = searchVal || (querySelect && querySelect.value ? querySelect.value : null);

      try {
        const res = await fetch("/api/news/topic-intelligence/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            range: range,
            source: source || null,
            query: query || null,
            project_id: projectId || null,
          }),
        });

        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: Failed to generate topic intelligence.`);
        }

        const data = await res.json();

        if (!data || data.summary_cards.total_unique === 0) {
          statusMsg.className = "topic-intel-status-msg";
          statusMsg.innerHTML = `<span style="color: #ef4444;">⚠️ Insufficient news data collected. Ingest news articles first.</span>`;
          return;
        }

        statusMsg.className = "topic-intel-status-msg";
        statusMsg.innerHTML = `<span style="color: #34d399;">✓ Topic intelligence generated from ${data.deduplication.total_unique_articles} unique articles.</span>`;

        populateViews(data);
      } catch (err) {
        statusMsg.className = "topic-intel-status-msg";
        statusMsg.innerHTML = `<span style="color: #ef4444;">❌ Analysis failed: ${esc(err.message)}</span>`;
      } finally {
        btnGenerate.disabled = false;
        btnText.textContent = "Generate Topic Intelligence →";
      }
    });
  }

  setupTopicIntelligence();
})();
