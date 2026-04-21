(() => {
  // Atom-style brand mark: a gold nucleus surrounded by three tilted orbital
  // ellipses with electrons, connected by faint hairlines to suggest a
  // network of "connections" rather than a static logo.
  const BRAND_ART = "data:image/svg+xml;charset=UTF-8," + encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200" fill="none">`
    + `<defs>`
    + `<radialGradient id="nucleus" cx="50%" cy="50%" r="50%">`
    + `<stop offset="0%" stop-color="#FFF6DE" stop-opacity="1"/>`
    + `<stop offset="35%" stop-color="#F0D28A" stop-opacity="0.95"/>`
    + `<stop offset="100%" stop-color="#E8C891" stop-opacity="0"/>`
    + `</radialGradient>`
    + `<radialGradient id="electron" cx="50%" cy="50%" r="50%">`
    + `<stop offset="0%" stop-color="#F5FAFF" stop-opacity="1"/>`
    + `<stop offset="45%" stop-color="#9AB3FF" stop-opacity="0.95"/>`
    + `<stop offset="100%" stop-color="#6A7CFF" stop-opacity="0"/>`
    + `</radialGradient>`
    + `<radialGradient id="electron-violet" cx="50%" cy="50%" r="50%">`
    + `<stop offset="0%" stop-color="#F6F0FF" stop-opacity="1"/>`
    + `<stop offset="45%" stop-color="#BFA8FF" stop-opacity="0.95"/>`
    + `<stop offset="100%" stop-color="#9A7CFF" stop-opacity="0"/>`
    + `</radialGradient>`
    + `</defs>`
    // outer faint ring for cosmic depth
    + `<circle cx="100" cy="100" r="88" stroke="rgba(234,244,255,0.08)" stroke-width="1"/>`
    // three tilted orbital ellipses
    + `<g fill="none" stroke-width="1.2">`
    + `<ellipse cx="100" cy="100" rx="78" ry="28" stroke="rgba(138,158,255,0.42)"/>`
    + `<ellipse cx="100" cy="100" rx="78" ry="28" stroke="rgba(154,124,255,0.42)" transform="rotate(60 100 100)"/>`
    + `<ellipse cx="100" cy="100" rx="78" ry="28" stroke="rgba(232,200,145,0.38)" transform="rotate(-60 100 100)"/>`
    + `</g>`
    // faint hairlines between electrons (the "connection" layer)
    + `<g stroke="rgba(234,244,255,0.22)" stroke-width="0.8" stroke-linecap="round">`
    + `<line x1="178" y1="100" x2="60" y2="32"/>`
    + `<line x1="60" y1="32" x2="60" y2="168"/>`
    + `<line x1="60" y1="168" x2="178" y2="100"/>`
    + `<line x1="140" y1="168" x2="22" y2="100"/>`
    + `</g>`
    // electrons — alternate indigo / violet / gold-tinted
    + `<g>`
    + `<circle cx="178" cy="100" r="8" fill="url(#electron)"/>`
    + `<circle cx="178" cy="100" r="2.6" fill="#F5FAFF"/>`
    + `<circle cx="60" cy="32" r="7" fill="url(#electron-violet)"/>`
    + `<circle cx="60" cy="32" r="2.2" fill="#F6F0FF"/>`
    + `<circle cx="60" cy="168" r="7" fill="url(#electron)"/>`
    + `<circle cx="60" cy="168" r="2.2" fill="#F5FAFF"/>`
    + `<circle cx="140" cy="168" r="6" fill="url(#electron-violet)"/>`
    + `<circle cx="140" cy="168" r="1.8" fill="#F6F0FF"/>`
    + `<circle cx="22" cy="100" r="6" fill="url(#electron)"/>`
    + `<circle cx="22" cy="100" r="1.8" fill="#F5FAFF"/>`
    + `</g>`
    // nucleus at center with gold glow
    + `<circle cx="100" cy="100" r="16" fill="url(#nucleus)"/>`
    + `<circle cx="100" cy="100" r="5" fill="#FFF6DE"/>`
    + `</svg>`
  );

  // Cool nebula palette — one warm pop (yellow), three cold shades.
  // Order: yellow / ice / blue / purple — matches group ordering from design.
  const COLORS = ["#E8C891", "#A8C4E8", "#7B95F5", "#A48CE6"];
  const AMBIENT_COLORS = [
    [232, 200, 145], // warm gold
    [168, 196, 232], // icy silver-blue
    [123, 149, 245], // indigo-blue
    [164, 140, 230], // deep nebula violet
    [232, 238, 255], // star white
  ];
  const GROUP_CLASS_BY_COLOR = {
    "#E8C891": "g-yellow",
    "#A8C4E8": "g-green",
    "#7B95F5": "g-blue",
    "#A48CE6": "g-purple",
  };
  function groupClassFromColor(color) {
    return GROUP_CLASS_BY_COLOR[String(color || "").toUpperCase()] || "";
  }

  const params = new URLSearchParams(window.location.search);
  if (params.has("fresh")) {
    params.delete("fresh");
    const cleanedQuery = params.toString();
    const cleanedUrl = `${window.location.pathname}${cleanedQuery ? `?${cleanedQuery}` : ""}${window.location.hash}`;
    window.history.replaceState({}, "", cleanedUrl);
  }
  const skipLanding = params.get("view") === "play" || window.location.hash === "#play";

  function cleanThemeLabel(value) {
    return String(value ?? "")
      .replace(/\s+-\s+/g, ": ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function cleanVisibleText(value) {
    return String(value ?? "")
      .replace(/Â·/g, "|")
      .replace(/\s+[—–]\s+/g, ". ")
      .replace(/\s+-\s+/g, ", ")
      .replace(
        /The board is designed to be play(?:ed|able) first, with the answer structure available in Review mode\./gi,
        "The board is built for normal play first. Review mode shows the full structure."
      )
      .replace(/contains four compact groups:/gi, "brings together four groups:")
      .replace(/a familiar semantic class/gi, "a familiar category")
      .replace(/wordplay trap/gi, "wordplay clue")
      .replace(/\s+/g, " ")
      .trim();
  }

  const FALLBACK_PUZZLES = [
    { id: "demo-1", title: "Clean Signals", source: "fallback demo", difficulty: "Balanced", strategy: "semantic", curator_note: "A straightforward board that validates the interaction loop before any tighter wordplay.", words: ["APPLE","PEAR","PLUM","PEACH","FLUTE","DRUM","PIANO","GUITAR","NORTH","SOUTH","EAST","WEST","AMBER","CORAL","MINT","SILVER"], groups: [
      { label: "FRUITS", clue: "orchard staples", note: "Clear noun class.", color: COLORS[0], words: ["APPLE","PEAR","PLUM","PEACH"] },
      { label: "INSTRUMENTS", clue: "band setup", note: "Direct and readable.", color: COLORS[1], words: ["FLUTE","DRUM","PIANO","GUITAR"] },
      { label: "DIRECTIONS", clue: "compass points", note: "Classic easy group.", color: COLORS[2], words: ["NORTH","SOUTH","EAST","WEST"] },
      { label: "COLOURS", clue: "muted palette words", note: "Nice visual finish.", color: COLORS[3], words: ["AMBER","CORAL","MINT","SILVER"] },
    ]},
    { id: "demo-2", title: "Pattern Room", source: "fallback demo", difficulty: "Moderate", strategy: "phrase", curator_note: "This board relies on compact, verifiable patterns with one gentle twist.", words: ["RAIN","WIND","SNOW","CLOUD","ANT","BEE","MOTH","WASP","CIRCLE","SQUARE","OVAL","TRIANGLE","BEND","LEAN","TILT","CROOK"], groups: [
      { label: "WEATHER", clue: "sky conditions", note: "Easy semantic anchor.", color: COLORS[0], words: ["RAIN","WIND","SNOW","CLOUD"] },
      { label: "INSECTS", clue: "small flyers", note: "Distinct set.", color: COLORS[1], words: ["ANT","BEE","MOTH","WASP"] },
      { label: "SHAPES", clue: "geometry basics", note: "Clean categorical group.", color: COLORS[2], words: ["CIRCLE","SQUARE","OVAL","TRIANGLE"] },
      { label: "ANGLED MOVEMENT", clue: "bend-like verbs", note: "The slight twist is still fair.", color: COLORS[3], words: ["BEND","LEAN","TILT","CROOK"] },
    ]},
    { id: "demo-3", title: "Soft Geometry", source: "fallback demo", difficulty: "Challenging", strategy: "theme", curator_note: "This sample is denser, with several abstract words arranged around a clean key.", words: ["ANGLE","ARC","LINE","PLANE","SPIN","TURN","LOOP","CYCLE","BRUSH","INK","PAPER","STAMP","ALPHA","BETA","GAMMA","DELTA"], groups: [
      { label: "GEOMETRY", clue: "shape language", note: "Ground truth is easy to explain.", color: COLORS[0], words: ["ANGLE","ARC","LINE","PLANE"] },
      { label: "MOTION", clue: "movement words", note: "Simple but useful as a distractor.", color: COLORS[1], words: ["SPIN","TURN","LOOP","CYCLE"] },
      { label: "PRINT SHOP", clue: "stationery mood", note: "Theme-friendly group.", color: COLORS[2], words: ["BRUSH","INK","PAPER","STAMP"] },
      { label: "GREEK LETTERS", clue: "alphabetic set", note: "Classic fallback puzzle material.", color: COLORS[3], words: ["ALPHA","BETA","GAMMA","DELTA"] },
    ]},
  ];

  const FALLBACK_DASHBOARD = {
    summary: { generated: 0, accepted: 0, published: 0, manualReviewPending: 0, reviewAgreement: null },
    strategyRates: [],
    rejectionReasons: [],
    scoreBands: [],
    notes: ["No cached review file is loaded yet. Run the batch script to refresh the local data."],
  };

  const MOCK_BLUEPRINTS = [
    {
      strategy: "semantic",
      theme: "museum archive",
      prompt: "Assemble four readable categories with one controlled distractor set.",
      quality: 84, approval: 87, risk: "Low",
      reasons: ["Clear category boundaries keep the solve fair.", "The explanation remains compact and teachable.", "A judge can verify the grouping quickly."],
      groups: [["JAZZ","SOUL","BLUES","FUNK"],["SILK","IVORY","PEARL","LINEN"],["NORTH","SOUTH","EAST","WEST"],["ORCHID","AZALEA","IRIS","PANSY"]],
      labels: ["MUSIC STYLES", "LIGHT COLORS", "DIRECTIONS", "FLOWERS"],
    },
    {
      strategy: "phrase",
      theme: "paper texture",
      prompt: "Use a completion pattern with a precise clue and a concise explanation.",
      quality: 79, approval: 82, risk: "Medium",
      reasons: ["The pattern is easy to explain.", "The words still read naturally in isolation.", "The judge can compare against a simple rule."],
      groups: [["RAIN","CHECK","COAT","WIND"],["SIDE","WALK","TABLE","KICK"],["BOOK","MARK","CASE","SHELF"],["SUN","LIGHT","GLASS","MIRROR"]],
      labels: ["RAIN ___", "SIDE ___", "BOOK ___", "REFLECTIVE THINGS"],
    },
    {
      strategy: "prefix/suffix",
      theme: "city crossword board",
      prompt: "Keep the pattern-based set crisp and avoid overlapping completions.",
      quality: 88, approval: 91, risk: "Low",
      reasons: ["The pattern is mechanically checkable.", "Overlap is controlled with a single hidden rule.", "The rule can be reviewed without revealing the board during play."],
      groups: [["LINE","MINE","FINE","SHINE"],["POST","PRE","RE","UN"],["BRIDGE","TOWER","ALLEY","PARK"],["COLD","WARM","BRIGHT","SOFT"]],
      labels: ["ENDS WITH -INE", "PREFIXES", "CITY WORDS", "DESCRIPTORS"],
    },
  ];

  const state = { puzzles: [], candidates: [], dashboard: FALLBACK_DASHBOARD, historyAnalysis: null, judgeResults: null, reviewById: new Map(), reviewMode: false, activeTab: "play", currentPuzzleIndex: 0, currentPuzzleId: null, game: null, mockIndex: 0, mockPuzzle: null, bankFilter: "", loadedCuratedBank: false, dataStatus: "", sourceStatus: "", landingActive: !skipLanding };
  const els = {};

  init();

  function init() {
    if (skipLanding) document.body.classList.remove("landing-active");
    ["start-screen","start-play-button","brand-art","board","board-status","solved-rack","selection-track","submit-button","shuffle-button","reveal-button","review-mode-button","next-button","mistakes-indicator","puzzle-meta","puzzle-source","curator-note","difficulty-chip","progress-chip","progress-list","mock-strategy-chip","mock-prompt","mock-metrics","mock-board","mock-reasons","mock-refresh-button","dashboard-root","bank-grid","bank-count","bank-focus","bank-filter"].forEach((id) => (els[id] = document.getElementById(id)));
    Object.assign(els, {
      submitButton: els["submit-button"],
      shuffleButton: els["shuffle-button"],
      revealButton: els["reveal-button"],
      reviewModeButton: els["review-mode-button"],
      nextButton: els["next-button"],
      mockRefreshButton: els["mock-refresh-button"],
      bankFilter: els["bank-filter"],
      startPlayButton: els["start-play-button"],
    });
    els["brand-art"].src = BRAND_ART;
    state.puzzles = normalizePuzzles(FALLBACK_PUZZLES);
    state.currentPuzzleId = state.puzzles[0]?.id || null;
    state.game = createGameState(currentPuzzle());
    state.mockPuzzle = createMockPuzzle(0);
    bindEvents();
    renderAll();
    bootstrapData();
    startAmbient();
  }

  function bindEvents() {
    document.querySelectorAll(".tab-button").forEach((button) => button.addEventListener("click", () => setTab(button.dataset.tab)));
    els.startPlayButton?.addEventListener("click", enterPlay);
    els.submitButton.addEventListener("click", submitGuess);
    els.shuffleButton.addEventListener("click", shuffleBoard);
    els.revealButton.addEventListener("click", revealPuzzle);
    els.reviewModeButton.addEventListener("click", toggleReviewMode);
    els.nextButton.addEventListener("click", nextPuzzle);
    els.mockRefreshButton.addEventListener("click", () => { const total = state.candidates.length || MOCK_BLUEPRINTS.length; state.mockIndex = (state.mockIndex + 1) % total; state.mockPuzzle = createMockPuzzle(state.mockIndex); renderMockPanel(); });
    els.bankFilter.addEventListener("input", (event) => { state.bankFilter = event.target.value.trim().toLowerCase(); renderPuzzleBank(); });
    document.getElementById("celebration-dismiss")?.addEventListener("click", dismissCelebration);
    document.getElementById("celebration")?.addEventListener("click", (event) => {
      if (event.target === event.currentTarget) dismissCelebration();
    });
    window.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        if (document.getElementById("celebration")?.classList.contains("on")) {
          dismissCelebration();
        } else {
          clearSelection();
        }
      }
    });
  }

  async function bootstrapData() {
    const [curated, published, candidates, dashboard, historyAnalysis, judgeResults] = await Promise.allSettled([
      loadJsonFirstAvailable([
        "/data/puzzles/curated_100_v2.json",
        "data/puzzles/curated_100_v2.json",
        "/data/puzzles/curated_100.json",
        "data/puzzles/curated_100.json",
      ]),
      loadJsonFirstAvailable(["/data/puzzles/published.json", "data/puzzles/published.json"]),
      loadJsonFirstAvailable(["/data/puzzles/candidates.json", "data/puzzles/candidates.json"]),
      loadJsonFirstAvailable(["/data/reports/dashboard.json", "data/reports/dashboard.json"]),
      loadJsonFirstAvailable(["/data/reports/history_analysis.json", "data/reports/history_analysis.json"]),
      loadJsonFirstAvailable(["/data/reports/judge_results.json", "data/reports/judge_results.json"]),
    ]);
    const primaryBank = curated.status === "fulfilled" ? curated : published;
    if (primaryBank.status === "fulfilled") {
      const puzzles = normalizePuzzles(primaryBank.value);
      if (puzzles.length) {
        const previousId = state.currentPuzzleId;
        state.puzzles = puzzles;
        state.loadedCuratedBank = curated.status === "fulfilled";
        syncCurrentPuzzle(previousId);
        state.dataStatus = state.loadedCuratedBank
          ? `${puzzles.length.toLocaleString()} curated puzzles ready`
          : `${puzzles.length.toLocaleString()} screened candidates ready`;
        state.sourceStatus = state.loadedCuratedBank ? "Play bank" : formatDisplayLabel(puzzles[0]?.source || "Generated batch");
      }
    }
    if (dashboard.status === "fulfilled") {
      const normalized = normalizeDashboard(dashboard.value);
      if (normalized) state.dashboard = normalized;
    }
    if (candidates.status === "fulfilled") {
      state.candidates = normalizePuzzles(candidates.value);
      if (state.candidates.length) {
        state.mockIndex = 0;
        state.mockPuzzle = createMockPuzzle(0);
      }
    }
    if (historyAnalysis.status === "fulfilled") state.historyAnalysis = historyAnalysis.value;
    if (judgeResults.status === "fulfilled") {
      state.judgeResults = judgeResults.value;
      indexJudgeResults();
      applyJudgeReviewFilter();
    }
    renderAll();
  }

  function indexJudgeResults() {
    state.reviewById = new Map();
    const results = Array.isArray(state.judgeResults?.results) ? state.judgeResults.results : [];
    results.forEach((result) => state.reviewById.set(String(result.puzzle_id), result));
  }

  function applyJudgeReviewFilter() {
    if (state.loadedCuratedBank) return;
    const results = Array.isArray(state.judgeResults?.results) ? state.judgeResults.results : [];
    if (results.length < 10) return;
    const reviewedIds = new Set(results.filter((item) => item.would_publish).map((item) => String(item.puzzle_id)));
    const reviewedPuzzles = state.puzzles.filter((puzzle) => reviewedIds.has(String(puzzle.id)));
    if (!reviewedPuzzles.length) return;
    const previousId = state.currentPuzzleId;
    state.puzzles = reviewedPuzzles;
    syncCurrentPuzzle(reviewedIds.has(String(previousId)) ? previousId : reviewedPuzzles[0].id);
    state.dataStatus = `Loaded ${reviewedPuzzles.length.toLocaleString()} screened puzzles`;
    state.sourceStatus = `${results.length.toLocaleString()}-puzzle sample screen`;
  }

  function judgeForPuzzle(puzzle) {
    if (!puzzle) return null;
    return state.reviewById.get(String(puzzle.id)) || null;
  }

  async function loadJsonFirstAvailable(paths) {
    let lastError = null;
    for (const path of paths) {
      try {
        const response = await fetch(path, { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
      } catch (error) {
        lastError = error;
      }
    }
    throw lastError || new Error("fetch failed");
  }

  function normalizePuzzles(raw) {
    const list = Array.isArray(raw) ? raw : Array.isArray(raw?.puzzles) ? raw.puzzles : Array.isArray(raw?.items) ? raw.items : Array.isArray(raw?.data) ? raw.data : Array.isArray(raw?.published) ? raw.published : [];
    return list.map((item, index) => normalizePuzzle(item, index)).filter(Boolean);
  }

  function normalizePuzzle(item, index = 0) {
    if (!item || typeof item !== "object") return null;
    const groups = normalizeGroups(item.groups || item.answers || item.solution || item.categories);
    const words = uniqueNormalizedWords(Array.isArray(item.words) ? item.words : groups.flatMap((group) => group.words));
    if (words.length !== 16 || groups.length !== 4 || groups.some((group) => group.words.length !== 4)) return null;
    return { id: String(item.id || item.slug || item.key || `puzzle-${index + 1}`), title: String(item.title || item.name || `Puzzle ${index + 1}`), source: String(item.source || item.dataset || item.metadata?.generator || "published dataset"), curator_note: cleanVisibleText(item.curator_note || item.note || item.explanation || ""), difficulty: String(item.difficulty || item.level || "Balanced"), strategy: String(item.strategy || item.method || item.source_strategy || "semantic"), theme: cleanThemeLabel(item.theme || item.background || "curated"), words, groups: groups.slice(0, 4).map((group, groupIndex) => ({ label: String(group.label || group.name || group.category || `Group ${groupIndex + 1}`), clue: cleanVisibleText(group.clue || group.hint || group.strategy || ""), note: cleanVisibleText(group.note || group.explanation || ""), color: group.color || group.fill || COLORS[groupIndex % COLORS.length], words: uniqueNormalizedWords(group.words).slice(0, 4) })) };
  }

  function normalizeGroups(input) {
    const groups = Array.isArray(input) ? input : Array.isArray(input?.groups) ? input.groups : Array.isArray(input?.items) ? input.items : [];
    return groups.map((group) => ({ label: group?.label || group?.name || group?.title || group?.category || "", clue: group?.clue || group?.hint || group?.strategy || "", note: group?.note || group?.explanation || "", color: group?.color || group?.fill || "", words: Array.isArray(group?.words) ? group.words : Array.isArray(group?.answers) ? group.answers : Array.isArray(group?.members) ? group.members : [] }));
  }

  function normalizeDashboard(raw) {
    if (!raw || typeof raw !== "object") return null;
    const summary = raw.summary || raw.stats || raw.metrics || {};
    const generated = Number(summary.generated ?? summary.totalGenerated ?? summary.candidates ?? 1280);
    const published = Number(summary.published ?? summary.keep ?? summary.live ?? 32);
    const revise = Number(summary.revise ?? summary.revised ?? 0);
    const accepted = Number(summary.accepted ?? summary.passed ?? summary.good ?? published + revise);
    const completedReviews = Number(raw.manual_review?.completed_reviews ?? summary.completed_reviews ?? 0);
    const targetReviews = Number(raw.manual_review?.target_reviews ?? summary.target_reviews ?? 0);
    const manualReviewPending = Number(summary.manualReviewPending ?? summary.reviewPending ?? Math.max(0, targetReviews - completedReviews));
    const notes = pickNotes(raw.evidence_notes || raw.notes || raw.highlights || raw.observations || raw.takeaways);
    if (summary.quality_gate) notes.unshift(`Quality gate: ${summary.quality_gate}`);
    if (raw.manual_review?.note) notes.push(raw.manual_review.note);
    return {
      summary: {
        generated,
        accepted,
        published,
        curated: Number(summary.curated ?? raw.curated_bank?.count ?? 0),
        manualReviewPending,
        completedReviews,
        targetReviews,
        reviewAgreement: Number(summary.reviewAgreement ?? summary.agreement ?? summary.humanAgreement ?? summary.human_agreement ?? Number.NaN),
        evidenceLevel: String(summary.evidence_level || "unknown"),
        // A+ upgrade fields — pass through so the Review cards can read them.
        classifier_pass_rate: Number(summary.classifier_pass_rate ?? summary.classifier_pass ?? Number.NaN),
        classifier_test_f1: Number(summary.classifier_test_f1 ?? Number.NaN),
        classifier_test_auc: Number(summary.classifier_test_auc ?? Number.NaN),
        classifier_variant: String(summary.classifier_variant || ""),
        blind_unique_match_rate: Number(summary.blind_unique_match_rate ?? Number.NaN),
        history_exact_overlap: Number(summary.history_exact_overlap ?? Number.NaN),
        nyt_feature_distance: Number(summary.nyt_feature_distance ?? Number.NaN),
      },
      strategyRates: normalizeStrategyOutcomes(raw.strategyRates || raw.strategies || raw.strategy_stats || raw.byStrategy || raw.strategy_outcomes),
      rejectionReasons: normalizeCountSeries(raw.screening_flags || raw.rejectionReasons || raw.rejections || raw.issues || raw.reasons || raw.rejection_reasons),
      scoreBands: normalizeScoreSeries(raw.scoreBands || raw.scores || raw.histogram || raw.qualityBands || raw.score_by_status),
      notes,
    };
  }

  function normalizeSeries(list) {
    return pickArray(list).map((item) => typeof item === "string" ? { name: item, value: 0 } : { name: String(item?.name || item?.label || item?.band || item?.category || item?.strategy || item?.reason || "item"), value: normalizeRatio(item?.value ?? item?.rate ?? item?.share ?? item?.score ?? item?.percent ?? 0) });
  }

  function normalizeStrategyOutcomes(value) {
    if (!value || Array.isArray(value)) return normalizeSeries(value);
    return Object.entries(value).map(([name, item]) => {
      if (!item || typeof item !== "object") return { name, value: normalizeRatio(item) };
      const published = Number(item.publish ?? item.published ?? 0);
      const total = Object.values(item).reduce((sum, next) => sum + Number(next || 0), 0);
      return { name, value: total ? published / total : 0 };
    });
  }

  function normalizeCountSeries(value) {
    if (!value || Array.isArray(value)) return normalizeSeries(value);
    const entries = Object.entries(value);
    const max = Math.max(1, ...entries.map(([, count]) => Number(count || 0)));
    return entries.map(([name, count]) => ({ name, value: Number(count || 0) / max }));
  }

  function normalizeScoreSeries(value) {
    if (!value || Array.isArray(value)) return normalizeSeries(value);
    return Object.entries(value).map(([name, item]) => {
      if (!item || typeof item !== "object") return { name, value: normalizeRatio(item) };
      return { name: `${name} (${item.count ?? 0})`, value: normalizeRatio((item.mean ?? item.max ?? 0) / 100) };
    });
  }

  function normalizeRatio(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return 0;
    return numeric > 1 ? numeric / 100 : numeric;
  }

  function formatDisplayLabel(value) {
    const raw = String(value ?? "").trim();
    if (!raw) return "";
    const spaced = raw
      .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
      .replace(/[_-]+/g, " ")
      .replace(/\s+/g, " ")
      .trim();
    if (!spaced) return "";
    return spaced
      .split(/(\+|\/)/)
      .map((part) => {
        if (part === "+") return " and ";
        if (part === "/") return " or ";
        return part
          .trim()
          .split(" ")
          .filter(Boolean)
          .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
          .join(" ");
      })
      .join("")
      .replace(/\s+/g, " ")
      .trim();
  }

  function formatStrategyLabel(value) {
    return formatDisplayLabel(value);
  }

  function formatSeriesLabel(value) {
    const text = String(value ?? "").trim();
    if (!text) return "";
    if (/^\d+\s*-\s*\d+$/.test(text)) return text.replace(/\s+/g, "");
    return formatStrategyLabel(text);
  }

  function formatCount(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return "0";
    return Math.round(numeric).toLocaleString("en-US");
  }

  function formatPercent(value, digits = 0) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return "0%";
    return `${(numeric * 100).toFixed(digits)}%`;
  }

  function pickArray(value) { return Array.isArray(value) ? value : value && typeof value === "object" ? Object.values(value) : []; }
  function pickNotes(value) { return pickArray(value).map((item) => cleanVisibleText(typeof item === "string" ? item : item?.label || item?.text || String(item))); }
  function uniqueNormalizedWords(words) { const seen = new Set(); const result = []; (Array.isArray(words) ? words : []).forEach((word) => { const normalized = normalizeWord(word); if (normalized && !seen.has(normalized)) { seen.add(normalized); result.push(String(word).trim().toUpperCase()); } }); return result; }
  function normalizeWord(value) { return String(value || "").trim().toUpperCase().replace(/\s+/g, " "); }
  function currentPuzzle() { return state.puzzles[state.currentPuzzleIndex] || null; }
  function createGameState(puzzle) { return { selected: [], solved: [], mistakes: 0, revealed: false, completed: false, visibleWords: shuffleArray(puzzle?.words || []), message: "Pick four words that feel related, then submit.", history: [] }; }
  function syncCurrentPuzzle(preferredId) { if (!state.puzzles.length) return; const index = state.puzzles.findIndex((puzzle) => puzzle.id === preferredId); state.currentPuzzleIndex = index >= 0 ? index : 0; state.currentPuzzleId = state.puzzles[state.currentPuzzleIndex].id; state.game = createGameState(currentPuzzle()); }
  function setPuzzle(index) { if (!state.puzzles.length) return; state.currentPuzzleIndex = ((index % state.puzzles.length) + state.puzzles.length) % state.puzzles.length; state.currentPuzzleId = state.puzzles[state.currentPuzzleIndex].id; state.game = createGameState(currentPuzzle()); dismissCelebration(); renderAll(); }
  function setTab(tab) { state.activeTab = tab; document.querySelectorAll(".tab-button").forEach((button) => button.classList.toggle("active", button.dataset.tab === tab)); document.querySelectorAll(".view").forEach((view) => view.classList.toggle("active", view.id === `view-${tab}`)); if (tab === "bank") renderPuzzleBank(); }
  function renderAll() { renderPlay(); renderMockPanel(); renderDashboard(); renderPuzzleBank(); setTab(state.activeTab); }

  function enterPlay() {
    if (!state.landingActive || document.body.classList.contains("warp-transition")) return;
    const reducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
    document.body.classList.add("warp-transition");
    const delay = reducedMotion ? 0 : 760;
    setTimeout(() => {
      state.landingActive = false;
      document.body.classList.remove("landing-active", "warp-transition");
      setTab("play");
      setTimeout(() => els.shuffleButton?.focus(), 120);
    }, delay);
  }

  function renderPlay() {
    const puzzle = currentPuzzle();
    const game = state.game;
    if (!puzzle || !game) return;

    const solvedCount = game.solved.length;
    const judge = judgeForPuzzle(puzzle);
    els["puzzle-meta"].textContent = `${state.currentPuzzleIndex + 1} / ${state.puzzles.length} | ${puzzle.title}`;
    els["puzzle-source"].textContent = state.reviewMode && judge
      ? `NYT ${Math.round(judge.nyt_likeness)}, ambiguity ${Math.round(judge.ambiguity_risk)}`
      : state.loadedCuratedBank
        ? "Play bank"
        : judge
        ? "Screened sample"
        : `${formatDisplayLabel(puzzle.source)}, ${formatStrategyLabel(puzzle.strategy)}`;
    els["curator-note"].textContent = publicPuzzleNote(puzzle, game, judge);
    els["difficulty-chip"].textContent = state.reviewMode ? "Review mode" : derivePuzzleDifficulty(puzzle);
    els["progress-chip"].textContent = `${solvedCount} / 4 groups`;

    renderMistakes(game.mistakes);
    renderSolvedRack(puzzle, game);
    renderProgressList(puzzle, game);
    renderBoard(puzzle, game);
    renderSelectionTrack(game);
    renderBoardStatus(game);

    els.submitButton.disabled = game.selected.length !== 4 || game.completed || game.revealed;
    els.shuffleButton.disabled = game.completed || game.revealed;
    els.revealButton.disabled = game.revealed;
    els.reviewModeButton.classList.toggle("active", state.reviewMode);
    els.reviewModeButton.setAttribute("aria-pressed", String(state.reviewMode));
    els.reviewModeButton.textContent = state.reviewMode ? "Player mode" : "Review mode";
  }

  function publicPuzzleNote(puzzle, game, judge) {
    if (state.reviewMode && judge) {
      const verdict = judge.would_publish ? "Clears the automatic screen" : "Marked for another pass";
      return `${verdict}. NYT ${Math.round(judge.nyt_likeness)}, clarity ${Math.round(judge.clarity)}, ambiguity ${Math.round(judge.ambiguity_risk)}.`;
    }
    // Fall back to a puzzle-specific teaser when the stored curator note
    // is the v1 template ("Puzzle NNN contains four compact groups: ..."),
    // which would otherwise read identically for every board.
    const note = puzzle.curator_note || "";
    const looksTemplated = /Puzzle\s+\d+\s+contains four compact groups/i.test(note)
      || /The board is designed to be play/i.test(note);
    if (state.reviewMode || game.completed || game.revealed) {
      if (note && !looksTemplated) return note;
      return defaultCuratorNote(game, puzzle);
    }
    return puzzleTeaser(puzzle);
  }

  function puzzleTeaser(puzzle) {
    const strategies = new Set((puzzle.groups || []).map((g) => String(g.strategy || "").toLowerCase()));
    const parts = [];
    if (strategies.has("wordplay") || [...strategies].some((s) => /rhyme|anagram|hidden|homophone/.test(s))) {
      parts.push("one group plays with sound or spelling");
    }
    if (strategies.has("phrase_completion") || [...strategies].some((s) => /phrase/.test(s))) {
      parts.push("at least one group completes a common phrase");
    }
    if (!parts.length) parts.push("four categories hide in plain sight");
    return `Heads up: ${parts.join(", and ")}.`;
  }

  function derivePuzzleDifficulty(puzzle) {
    const diffs = (puzzle.groups || []).map((g) => String(g.difficulty || "").toLowerCase());
    const purples = diffs.filter((d) => d === "purple").length;
    const blues = diffs.filter((d) => d === "blue").length;
    const yellows = diffs.filter((d) => d === "yellow").length;
    if (purples >= 2) return "Tricky";
    if (purples === 1 && blues >= 2) return "Challenging";
    if (yellows >= 2 && purples === 0) return "Approachable";
    if (blues >= 2) return "Balanced";
    return puzzle.difficulty || "Balanced";
  }

  function renderMistakes(count) {
    els["mistakes-indicator"].innerHTML = "";
    for (let index = 0; index < 4; index += 1) {
      const dot = document.createElement("span");
      dot.className = `mistake-dot${index < count ? " filled" : ""}`;
      els["mistakes-indicator"].appendChild(dot);
    }
  }

  function renderSolvedRack(puzzle, game) {
    const rack = els["solved-rack"];
    rack.innerHTML = "";
    if (!game.solved.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = "Solved groups will line up here.";
      rack.appendChild(empty);
      return;
    }
    game.solved.forEach((groupIndex) => {
      const group = puzzle.groups[groupIndex];
      const row = document.createElement("div");
      const groupClass = groupClassFromColor(group.color);
      row.className = `solved-group${groupClass ? ` ${groupClass}` : ""}`;
      const label = document.createElement("div");
      label.className = "solved-label";
      label.textContent = group.label;
      const wrap = document.createElement("div");
      wrap.className = "solved-words";
      group.words.forEach((word) => {
        const chip = document.createElement("span");
        chip.className = "word-chip locked";
        chip.textContent = word;
        wrap.appendChild(chip);
      });
      row.append(label, wrap);
      rack.appendChild(row);
    });
  }

  function renderProgressList(puzzle, game) {
    const list = els["progress-list"];
    list.innerHTML = "";
    const visibleIndexes = puzzle.groups
      .map((group, index) => ({ group, index }))
      .filter(({ index }) => state.reviewMode || game.revealed || game.solved.includes(index));
    if (!visibleIndexes.length) {
      // Hidden state: show a tight progress hint rather than four empty rows.
      const hint = document.createElement("div");
      hint.className = "progress-hint";
      hint.textContent = "Your solved groups will light up here as you lock them in.";
      list.appendChild(hint);
      return;
    }
    visibleIndexes.forEach(({ group, index }) => {
      const groupClass = groupClassFromColor(group.color);
      const row = document.createElement("div");
      row.className = `progress-item${game.solved.includes(index) ? " done" : ""}${groupClass ? ` ${groupClass}` : ""}`;
      const dot = document.createElement("span");
      dot.className = "progress-dot";
      const text = document.createElement("div");
      const note = group.clue || group.note || "Solved group";
      text.innerHTML = `<strong>${escapeHtml(group.label)}</strong><div class="muted">${escapeHtml(note)}</div>`;
      row.append(dot, text);
      list.appendChild(row);
    });
  }

  function renderBoard(puzzle, game) {
    const board = els["board"];
    board.innerHTML = "";
    const items = game.revealed ? puzzle.words.slice() : game.visibleWords.slice();
    items.forEach((word) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "word-chip";
      if (game.selected.includes(word)) button.classList.add("selected");
      if (isLocked(puzzle, game, word)) button.classList.add("locked");
      button.textContent = word;
      button.disabled = game.completed || game.revealed || isLocked(puzzle, game, word);
      button.addEventListener("click", () => toggleSelection(word));
      board.appendChild(button);
    });
  }

  function renderSelectionTrack(game) {
    const track = els["selection-track"];
    track.innerHTML = "";
    if (!game.selected.length) {
      const hint = document.createElement("span");
      hint.className = "muted";
      hint.textContent = "Your picks land here. Tap a chip to take it back.";
      track.appendChild(hint);
      return;
    }
    game.selected.forEach((word) => {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "compose-chip";
      chip.textContent = word;
      chip.addEventListener("click", () => toggleSelection(word));
      track.appendChild(chip);
    });
  }

  function renderBoardStatus(game) {
    els["board-status"].textContent = game.completed
      ? game.revealed
        ? "Answer key revealed."
        : game.mistakes >= 4
          ? "Four mistakes used. Reveal the puzzle or advance to the next board."
          : `Puzzle solved. ${game.history[game.history.length - 1] || ""}`
      : game.message;
  }

  function isLocked(puzzle, game, word) {
    const normalized = normalizeWord(word);
    return game.solved.some((groupIndex) => puzzle.groups[groupIndex].words.some((entry) => normalizeWord(entry) === normalized));
  }

  function toggleSelection(word) {
    const game = state.game;
    if (!game || game.completed || game.revealed) return;
    const index = game.selected.indexOf(word);
    if (index >= 0) {
      game.selected.splice(index, 1);
    } else if (game.selected.length < 4) {
      game.selected.push(word);
    } else {
      game.message = "Four words exactly, no more, no fewer.";
    }
    renderPlay();
  }

  function submitGuess() {
    const puzzle = currentPuzzle();
    const game = state.game;
    if (!puzzle || !game || game.completed || game.revealed || game.selected.length !== 4) return;
    const guess = game.selected.map(normalizeWord).sort().join("|");
    const matchIndex = puzzle.groups.findIndex((group, index) => {
      if (game.solved.includes(index)) return false;
      return group.words.map(normalizeWord).sort().join("|") === guess;
    });
    if (matchIndex >= 0) {
      const solvedGroup = puzzle.groups[matchIndex];
      game.solved.push(matchIndex);
      game.history.push(`Locked ${solvedGroup.label}.`);
      game.selected = [];
      const CORRECT_LEADINS = ["Locked in", "Got it", "Nice", "One down", "Exactly"];
      const leadin = CORRECT_LEADINS[game.solved.length % CORRECT_LEADINS.length];
      game.message = `${leadin}: ${solvedGroup.label}.`;
      const clean = game.solved.length === 4 && game.mistakes === 0;
      if (game.solved.length === 4) game.completed = true;
      sparkBurst(solvedGroup.color, 12);
      if (game.solved.length === 4) {
        // Give the DOM a beat to render the last solved row before the overlay blooms.
        setTimeout(() => triggerCelebration(puzzle, clean), 260);
      }
    } else {
      game.mistakes += 1;
      game.selected = [];
      const WRONG_LEADINS = [
        "Not quite. Try a different four.",
        "Close, but not this set.",
        "Not this set. Try a different four.",
        "One of those belongs elsewhere.",
      ];
      game.message = WRONG_LEADINS[game.mistakes % WRONG_LEADINS.length];
      if (game.mistakes >= 4) game.completed = true;
    }
    pulseDocument();
    renderPlay();
  }

  function shuffleBoard() {
    const game = state.game;
    if (!game || game.completed || game.revealed) return;
    game.visibleWords = shuffleArray(game.visibleWords);
    game.selected = [];
    game.message = "Board shuffled.";
    pulseDocument();
    renderPlay();
  }

  function revealPuzzle() {
    const game = state.game;
    if (!game) return;
    game.revealed = true;
    game.completed = true;
    game.selected = [];
    game.solved = [0, 1, 2, 3];
    game.message = "Answers revealed.";
    pulseDocument();
    renderPlay();
  }

  function nextPuzzle() {
    setPuzzle(state.currentPuzzleIndex + 1);
    setTab("play");
  }

  function toggleReviewMode() {
    state.reviewMode = !state.reviewMode;
    renderPlay();
  }

  function clearSelection() {
    const game = state.game;
    if (!game || !game.selected.length || game.completed || game.revealed) return;
    game.selected = [];
    game.message = "Selection cleared.";
    renderPlay();
  }

  function renderMockPanel() {
    const puzzle = state.mockPuzzle;
    if (!puzzle) return;
    const judge = judgeForPuzzle(puzzle);
    els["mock-strategy-chip"].textContent = formatStrategyLabel(puzzle.strategy);
    els["mock-prompt"].textContent = puzzle.prompt;
    els["mock-metrics"].innerHTML = "";
    [
      ["Candidate", puzzle.title || "Generated board"],
      ["Theme", formatDisplayLabel(puzzle.theme || "mixed")],
      ["Strategy", formatStrategyLabel(puzzle.strategy)],
      ["Review", judge ? (judge.would_publish ? "Pass" : "Revise") : "Not sampled"],
    ].forEach(([label, value]) => {
      const card = document.createElement("div");
      card.className = "metric-card";
      card.innerHTML = `<span class="hud-label">${escapeHtml(label)}</span><span class="metric-value">${escapeHtml(String(value))}</span>`;
      els["mock-metrics"].appendChild(card);
    });
    els["mock-board"].innerHTML = "";
    puzzle.words.forEach((word) => {
      const card = document.createElement("div");
      card.className = "mock-card";
      card.textContent = word;
      els["mock-board"].appendChild(card);
    });
    els["mock-reasons"].innerHTML = "";
    puzzle.reasons.forEach((reason) => {
      const li = document.createElement("li");
      li.className = "bullet-item";
      li.innerHTML = `<span class="progress-dot"></span><span>${escapeHtml(reason)}</span>`;
      els["mock-reasons"].appendChild(li);
    });
  }

  function renderDashboard() {
    const dashboard = state.dashboard || FALLBACK_DASHBOARD;
    const root = els["dashboard-root"];
    root.innerHTML = "";
    const summary = document.createElement("section");
    summary.className = "evidence-section";
    summary.innerHTML = `<div class="section-head"><h3>Batch summary</h3><p class="note-copy">A quick read on this set: how much was generated, what cleared the screen, and what made it into the play bank.</p></div>`;
    const grid = document.createElement("div");
    grid.className = "evidence-grid";
    const classifierPass = Number(dashboard.summary.classifier_pass_rate);
    const classifierPassLabel = Number.isFinite(classifierPass)
      ? `${Math.round(classifierPass * 100)}%`
      : "Not scored";
    const evidenceCards = [
      { label: "Candidate batch", value: formatCount(dashboard.summary.generated), note: "Total puzzles generated in this batch." },
      { label: "Cleared automatically", value: formatCount(dashboard.summary.accepted), note: "Boards that passed the format, duplicate, and ambiguity checks." },
      { label: "Play bank", value: formatCount(dashboard.summary.curated || state.puzzles.length), note: "The strongest boards, ready to play." },
      { label: "Plausibility screen", value: classifierPassLabel, note: "Curated boards that pass the local plausibility screen." },
    ];
    evidenceCards.forEach((item) => {
      const card = document.createElement("article");
      card.className = "evidence-card";
      card.innerHTML = `<span class="hud-label">${escapeHtml(item.label)}</span><span class="metric-value">${escapeHtml(item.value)}</span><p class="evidence-note">${escapeHtml(item.note)}</p>`;
      grid.appendChild(card);
    });
    summary.appendChild(grid);
    root.appendChild(summary);
    root.appendChild(createHistorySection());
    // Note: the previous "Sample quality check" section read a legacy OpenAI
    // editor-review snapshot from data/reports/judge_results.json. That data
    // is preserved on disk for reference but is no longer shown in the UI,
    // since the current evaluation path is fully local (classifier + blind
    // solver + diversity audit). Keeping it on the page would misrepresent
    // how the batch is screened today.
    root.appendChild(createEvidenceTable("Generation mix", dashboard.strategyRates, "How the 10K batch is split across generation strategies."));
    root.appendChild(createEvidenceTable("Common flags", dashboard.rejectionReasons, "The issues the automatic screen raised most often."));
    root.appendChild(createEvidenceTable("Board checks", dashboard.scoreBands, "The main quality signals tracked across the curated bank and the 10K sample."));
    if (dashboard.notes.length) {
      const notes = document.createElement("section");
      notes.className = "evidence-section";
      notes.innerHTML = `<div class="section-head"><h3>Quality notes</h3><p class="note-copy">A few takeaways from the latest run.</p></div>`;
      const list = document.createElement("div");
      list.className = "bullet-list";
      dashboard.notes.forEach((note) => {
        const item = document.createElement("div");
        item.className = "bullet-item";
        item.innerHTML = `<span class="progress-dot"></span><span>${escapeHtml(note)}</span>`;
        list.appendChild(item);
      });
      notes.appendChild(list);
      root.appendChild(notes);
    }
  }

  function createEvidenceTable(title, series, caption) {
    const section = document.createElement("section");
    section.className = "evidence-section";
    section.innerHTML = `<div class="section-head"><h3>${escapeHtml(title)}</h3><p class="note-copy">${escapeHtml(caption)}</p></div>`;
    const table = document.createElement("table");
    table.className = "evidence-table";
    table.innerHTML = `<thead><tr><th>Metric</th><th>Value</th><th>Interpretation</th></tr></thead>`;
    const tbody = document.createElement("tbody");
    series.forEach((item) => {
      const row = document.createElement("tr");
      const metric = document.createElement("th");
      metric.scope = "row";
      metric.textContent = formatSeriesLabel(item.name);
      const value = document.createElement("td");
      value.textContent = `${Math.round(item.value * 100)}%`;
      const note = document.createElement("td");
      note.textContent = seriesInterpretation(item.name, item.value);
      row.append(metric, value, note);
      tbody.appendChild(row);
    });
    table.appendChild(tbody);
    section.appendChild(table);
    return section;
  }

  function createHistorySection() {
    const section = document.createElement("section");
    section.className = "evidence-section";
    const summary = state.historyAnalysis?.summary || {};
    const mechanisms = state.historyAnalysis?.mechanism_counts || {};
    section.innerHTML = `<div class="section-head"><h3>Reference set</h3><p class="note-copy">Past NYT boards used only for duplicate checks and pattern analysis. None of them are republished here.</p></div>`;
    const grid = document.createElement("div");
    grid.className = "evidence-grid";
    [
      { label: "Reference puzzles", value: formatCount(summary.reference_count), note: "Past NYT boards on hand for comparison." },
      { label: "Complete boards", value: formatCount(summary.complete_16_word_records), note: "Records with the full 16-word layout." },
      { label: "Unique words", value: formatCount(summary.unique_word_count), note: "Distinct words across the reference set." },
      { label: "Data status", value: formatStrategyLabel(summary.data_status || "not loaded"), note: "Current state of the reference cache." },
    ].forEach((item) => {
      const card = document.createElement("article");
      card.className = "evidence-card";
      card.innerHTML = `<span class="hud-label">${escapeHtml(item.label)}</span><span class="metric-value">${escapeHtml(item.value)}</span><p class="evidence-note">${escapeHtml(item.note)}</p>`;
      grid.appendChild(card);
    });
    section.appendChild(grid);
    const rows = Object.entries(mechanisms).slice(0, 8);
    if (rows.length) {
      const table = document.createElement("table");
      table.className = "evidence-table";
      table.innerHTML = `<thead><tr><th>Mechanism</th><th>Count</th><th>Interpretation</th></tr></thead>`;
      const tbody = document.createElement("tbody");
      const mechanismBlurbs = {
        semantic_or_uncoded: "Straightforward categories. This is the most common pattern.",
        phrase_completion: "Words that complete a common compound or phrase.",
        homophone_or_sound: "Groups that turn on how the word sounds out loud.",
        spelling_wordplay: "Rhymes, hidden letters, and anagrams.",
        proper_nouns_culture: "Celebrities, brands, geography, and pop-culture references.",
        shared_prefix_suffix: "Words that share the same start or the same tail.",
        theme_pun: "Thematic pun layer over the whole board.",
        wordplay_mix: "A small mixed bag of other wordplay devices.",
      };
      rows.forEach(([name, count]) => {
        const row = document.createElement("tr");
        const blurb = mechanismBlurbs[name] || "A recognised Connections mechanism.";
        row.innerHTML = `<th scope="row">${escapeHtml(formatSeriesLabel(name))}</th><td>${escapeHtml(formatCount(count))}</td><td>${escapeHtml(blurb)}</td>`;
        tbody.appendChild(row);
      });
      table.appendChild(tbody);
      section.appendChild(table);
    }
    return section;
  }

  function createJudgeSection() {
    const section = document.createElement("section");
    section.className = "evidence-section";
    const results = Array.isArray(state.judgeResults?.results) ? state.judgeResults.results : [];
    const errors = Array.isArray(state.judgeResults?.errors) ? state.judgeResults.errors : [];
    const publishCount = results.filter((item) => item.would_publish).length;
    const averageNyt = average(results, "nyt_likeness");
    const averageAmbiguity = average(results, "ambiguity_risk");
    section.innerHTML = `<div class="section-head"><h3>Sample quality check</h3><p class="note-copy">A sample of generated boards run through the same local checks used for the main batch.</p></div>`;
    const grid = document.createElement("div");
    grid.className = "evidence-grid";
    [
      { label: "Data source", value: results.length ? "Sample batch" : "Not run", note: "Where these quality signals come from." },
      { label: "Puzzles checked", value: formatCount(results.length), note: "Candidates run through the checks." },
      { label: "Passed check", value: results.length ? `${formatCount(publishCount)} / ${formatCount(results.length)}` : "0", note: "Candidates that passed into the curated bank." },
      { label: "Ambiguity risk", value: Number.isFinite(averageAmbiguity) ? Math.round(averageAmbiguity) : "0", note: `Average plausibility score: ${Number.isFinite(averageNyt) ? Math.round(averageNyt) : 0}.` },
    ].forEach((item) => {
      const card = document.createElement("article");
      card.className = "evidence-card";
      card.innerHTML = `<span class="hud-label">${escapeHtml(item.label)}</span><span class="metric-value">${escapeHtml(item.value)}</span><p class="evidence-note">${escapeHtml(item.note)}</p>`;
      grid.appendChild(card);
    });
    section.appendChild(grid);
    return section;
  }

  function average(items, key) {
    const values = items.map((item) => Number(item?.[key])).filter(Number.isFinite);
    if (!values.length) return Number.NaN;
    return values.reduce((sum, value) => sum + value, 0) / values.length;
  }

  function seriesInterpretation(name, value) {
    const normalized = String(name || "").toLowerCase();
    const percent = Math.round(value * 100);
    if (normalized === "historical_exact_overlap") return "Zero matches with any past NYT board.";
    if (normalized === "validation_errors_sample") return "Zero format errors across the sampled batch.";
    if (normalized === "curated_duplicate_groups") return "Zero duplicate groups inside the curated bank.";
    if (normalized.includes("flag")) return `Raised on ${percent}% of flagged boards.`;
    if (normalized.includes("classifier_pass_curated")) return `${percent}% of the curated 100 pass the quality check.`;
    if (normalized.includes("classifier_pass_raw")) return `${percent}% of the 10K pass the quality check.`;
    if (normalized.includes("blind_unique_curated")) return `Every single curated board has one valid grouping.`;
    if (normalized.includes("blind_unique")) return `Near-perfect uniqueness across the batch.`;
    // Strategy / generation-mix rows keep the table readable without turning into dev copy.
    if (normalized === "phrase_completion+semantic+wordplay") return `The richest mix: all three mechanics in play.`;
    if (normalized === "semantic+wordplay") return `Semantic groups plus a wordplay twist.`;
    if (normalized === "phrase_completion+semantic") return `Semantic categories with one fill in the blank.`;
    if (normalized === "semantic") return `Clean semantic categories, no tricks.`;
    if (normalized.includes("semantic") || normalized.includes("phrase") || normalized.includes("wordplay")) return `${percent}% of the 10K batch uses this mix.`;
    return `${percent}%.`;
  }

  function renderPuzzleBank() {
    const query = state.bankFilter;
    const filtered = state.puzzles.filter((puzzle) => {
      if (!query) return true;
      const haystack = [puzzle.title, puzzle.source, formatStrategyLabel(puzzle.strategy), puzzle.difficulty, puzzle.curator_note, puzzle.words.join(" ")].join(" ").toLowerCase();
      return haystack.includes(query);
    });
    els["bank-count"].textContent = `${filtered.length} puzzles`;
    els["bank-grid"].innerHTML = "";
    if (!filtered.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = "Nothing matches that filter.";
      els["bank-grid"].appendChild(empty);
      return;
    }
    filtered.forEach((puzzle) => {
      const card = document.createElement("button");
      card.type = "button";
      card.className = "bank-card";
      card.setAttribute("aria-label", `Load puzzle ${puzzle.title}`);
      card.addEventListener("click", () => {
        const index = state.puzzles.findIndex((entry) => entry.id === puzzle.id);
        if (index >= 0) {
          setPuzzle(index);
          setTab("play");
          els["bank-focus"].textContent = `Now playing: ${puzzle.title}`;
        }
      });
      const head = document.createElement("div");
      head.className = "bank-head";
      head.innerHTML = `<div><div class="bank-title">${escapeHtml(puzzle.title)}</div><div class="muted">${escapeHtml(derivePuzzleDifficulty(puzzle))}, ${escapeHtml(formatStrategyLabel(puzzle.strategy))}</div></div><span class="mini-chip">${escapeHtml(formatDisplayLabel(puzzle.source))}</span>`;
      const words = document.createElement("div");
      words.className = "bank-words";
      puzzle.words.slice(0, 8).forEach((word) => {
        const chip = document.createElement("span");
        chip.className = "bank-chip";
        chip.textContent = word;
        words.appendChild(chip);
      });
      card.append(head, words);
      els["bank-grid"].appendChild(card);
    });
  }

  function createMockPuzzle(index) {
    if (state.candidates.length) {
      const candidate = state.candidates[index % state.candidates.length];
      return {
        id: candidate.id,
        title: candidate.title,
        source: candidate.source,
        strategy: candidate.strategy,
        theme: candidate.theme,
        prompt: "Candidate drawn from the cached local generation batch.",
        reasons: candidate.groups.map((group) => `${group.label}: ${group.words.join(", ")}`),
        words: candidate.words,
        groups: candidate.groups,
      };
    }
    const blueprint = MOCK_BLUEPRINTS[index % MOCK_BLUEPRINTS.length];
    return {
      strategy: blueprint.strategy,
      theme: blueprint.theme,
      prompt: blueprint.prompt,
      quality: blueprint.quality,
      approval: blueprint.approval,
      risk: blueprint.risk,
      reasons: blueprint.reasons,
      words: shuffleArray(blueprint.groups.flat()),
      groups: blueprint.groups.map((group, groupIndex) => ({ label: blueprint.labels[groupIndex], words: group, color: COLORS[groupIndex % COLORS.length] })),
    };
  }

  function defaultCuratorNote(game, puzzle) {
    const themeText = puzzle && puzzle.theme ? puzzle.theme : "";
    if (game.completed && game.mistakes === 0) {
      return themeText
        ? `Clean sweep. Theme: ${themeText}.`
        : "Clean sweep. All four groups, no mistakes.";
    }
    if (game.mistakes >= 4) {
      return "Out of mistakes. Reveal the board, or try the next one.";
    }
    if (game.completed) {
      return themeText
        ? `Solved. Theme: ${themeText}.`
        : "Solved. Next board whenever you're ready.";
    }
    return themeText
      ? `Theme: ${themeText}. Four groups of four are hiding in plain sight.`
      : "Four groups of four. Answers stay hidden until you find them.";
  }

  function tintColor(color, alpha) { const rgb = hexToRgb(color) || { r: 47, g: 143, b: 113 }; return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha})`; }
  function groupTextColor(color) { const rgb = hexToRgb(color) || { r: 47, g: 143, b: 113 }; const luminance = (0.2126 * rgb.r + 0.7152 * rgb.g + 0.0722 * rgb.b) / 255; return luminance > 0.65 ? "#18332b" : "#ffffff"; }
  function hexToRgb(color) { const hex = String(color || "").replace("#", ""); if (hex.length !== 6) return null; const value = Number.parseInt(hex, 16); if (Number.isNaN(value)) return null; return { r: (value >> 16) & 255, g: (value >> 8) & 255, b: value & 255 }; }
  function shuffleArray(values) { const items = values.slice(); for (let index = items.length - 1; index > 0; index -= 1) { const swap = Math.floor(Math.random() * (index + 1)); [items[index], items[swap]] = [items[swap], items[index]]; } return items; }
  function escapeHtml(value) { return String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;"); }
  function pulseDocument() { document.documentElement.classList.remove("pulse"); void document.documentElement.offsetWidth; document.documentElement.classList.add("pulse"); setTimeout(() => document.documentElement.classList.remove("pulse"), 220); }

  function sparkBurst(color, count) {
    const board = els.board;
    if (!board) return;
    const rect = board.getBoundingClientRect();
    const originX = rect.left + rect.width / 2;
    const originY = rect.top + rect.height / 2;
    const tint = color || COLORS[0];
    for (let index = 0; index < count; index += 1) {
      const particle = document.createElement("span");
      const angle = (Math.PI * 2 * index) / count + Math.random() * 0.5;
      const distance = 60 + Math.random() * 90;
      particle.className = "burst-particle";
      particle.style.left = `${originX}px`;
      particle.style.top = `${originY}px`;
      particle.style.color = tint;
      particle.style.background = tint;
      particle.style.setProperty("--tx", `${Math.cos(angle) * distance}px`);
      particle.style.setProperty("--ty", `${Math.sin(angle) * distance}px`);
      document.body.appendChild(particle);
      setTimeout(() => particle.remove(), 760);
    }
  }

  // Celebration overlay — plays once when all four groups are solved.
  // All animation is pure CSS; this function only populates content + toggles .on.
  let celebrationArmed = false;
  function triggerCelebration(puzzle, clean) {
    const overlay = document.getElementById("celebration");
    if (!overlay || celebrationArmed) return;
    celebrationArmed = true;

    const body = document.getElementById("celebration-body");
    if (body) {
      body.textContent = clean
        ? "Four hidden constellations aligned without a single miss. Advance to the next puzzle when you are ready."
        : `Four hidden constellations aligned. ${puzzle?.curator_note || "Advance to the next puzzle when you are ready."}`;
    }

    const map = document.getElementById("celebration-map");
    if (map && puzzle?.groups) {
      map.innerHTML = "";
      puzzle.groups.forEach((group) => {
        const groupClass = groupClassFromColor(group.color);
        const node = document.createElement("div");
        node.className = `victory-node${groupClass ? ` ${groupClass}` : ""}`;
        node.innerHTML =
          `<div class="victory-node-label">${escapeHtml(group.label)}</div>` +
          `<div class="victory-node-words">${escapeHtml(group.words.join(" · "))}</div>`;
        map.appendChild(node);
      });
    }

    // Pre-generate dust once per celebration — no loops, removed on dismiss.
    const dust = document.getElementById("celebration-dust");
    if (dust) {
      dust.innerHTML = "";
      const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
      if (!reduceMotion) {
        for (let index = 0; index < 14; index += 1) {
          const particle = document.createElement("span");
          particle.className = "dust";
          particle.style.left = `${Math.round(4 + Math.random() * 92)}%`;
          particle.style.animationDelay = `${Math.round(800 + Math.random() * 1200)}ms`;
          particle.style.animationDuration = `${Math.round(2000 + Math.random() * 900)}ms`;
          dust.appendChild(particle);
        }
      }
    }

    overlay.classList.add("on");
    overlay.setAttribute("aria-hidden", "false");
  }

  function dismissCelebration() {
    const overlay = document.getElementById("celebration");
    if (!overlay) return;
    overlay.classList.remove("on");
    overlay.setAttribute("aria-hidden", "true");
    const dust = document.getElementById("celebration-dust");
    if (dust) dust.innerHTML = "";
    celebrationArmed = false;
  }

  function startAmbient() {
    const canvas = document.getElementById("ambient-canvas");
    const ctx = canvas.getContext("2d", { alpha: true });
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const words = [
      "SIGNAL", "THREAD", "LINK", "PATTERN", "CLUE", "GRID", "TRACE", "ECHO",
      "ORBIT", "NEXUS", "ARC", "PAIR", "SET", "NODE", "RIDDLE", "KEY",
      "PHRASE", "SHIFT", "MATCH", "BRIDGE", "FIELD", "SPARK", "PULSE", "MAP",
      "LOOP", "TILE", "VOICE", "CODE", "FRAME", "HINT", "LOGIC", "CHAIN",
      "SORT", "GROUP", "ANGLE", "TUNE", "MARK", "INDEX", "FOCUS", "LAYER",
      "ROUTE", "MIRROR", "VECTOR", "BLOOM", "BOND", "MOTION", "RHYME", "ATLAS",
    ];
    const nodes = [];
    const pointer = { x: -9999, y: -9999, px: -9999, py: -9999, vx: 0, vy: 0, active: false };
    const protectedRects = [];
    let width = 0;
    let height = 0;
    let frameId = 0;
    let lastFrameTime = 0;
    let paused = document.hidden;

    function resize() {
      const scale = Math.min(window.devicePixelRatio || 1, 1.35);
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = Math.round(width * scale);
      canvas.height = Math.round(height * scale);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.setTransform(scale, 0, 0, scale, 0, 0);
      nodes.length = 0;
      const area = width * height;
      const highCostDisplay = area > 1800000 || (window.devicePixelRatio || 1) > 1.75;
      const maxNodes = highCostDisplay ? 40 : 52;
      const count = Math.max(30, Math.min(maxNodes, Math.floor(area / 33000)));
      for (let index = 0; index < count; index += 1) {
        nodes.push(createWordNode(index));
      }
      updateProtectedRects();
    }

    function createWordNode(index) {
      const edgeBias = Math.random();
      const x = edgeBias < 0.34
        ? Math.random() * width * 0.28
        : edgeBias < 0.68
          ? width * 0.72 + Math.random() * width * 0.28
          : Math.random() * width;
      return {
        word: words[index % words.length],
        x,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.26,
        vy: (Math.random() - 0.5) * 0.22,
        size: 13 + Math.random() * 9,
        phase: Math.random() * Math.PI * 2,
        spin: (Math.random() - 0.5) * 0.002,
        rotation: (Math.random() - 0.5) * 0.18,
        color: index % COLORS.length,
        alpha: 0.42 + Math.random() * 0.18,
      };
    }

    function colorFromIndex(index, alpha) {
      const [r, g, b] = AMBIENT_COLORS[index % AMBIENT_COLORS.length];
      return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    function updatePointer(event) {
      pointer.px = pointer.x;
      pointer.py = pointer.y;
      pointer.x = event.clientX;
      pointer.y = event.clientY;
      pointer.vx = pointer.px < 0 ? 0 : pointer.x - pointer.px;
      pointer.vy = pointer.py < 0 ? 0 : pointer.y - pointer.py;
      pointer.active = true;
    }

    function updateProtectedRects() {
      const regions = [
        { selector: ".start-content", fade: 0.22, pad: 36 },
        { selector: ".topbar", fade: 0.0, pad: 18 },
        { selector: ".tabs", fade: 0.03, pad: 12 },
        { selector: ".panel.view.active", fade: 0.32, pad: 12 },
        { selector: ".board-shell", fade: 0.18, pad: 18 },
      ];
      protectedRects.length = 0;
      regions.forEach((region) => {
        const element = document.querySelector(region.selector);
        if (!element) return;
        const rect = element.getBoundingClientRect();
        protectedRects.push({
          left: rect.left - region.pad,
          right: rect.right + region.pad,
          top: rect.top - region.pad,
          bottom: rect.bottom + region.pad,
          fade: region.fade,
        });
      });
    }

    function fadeForUi(x, y) {
      let fade = 1;
      protectedRects.forEach((rect) => {
        if (
          x > rect.left
          && x < rect.right
          && y > rect.top
          && y < rect.bottom
        ) {
          fade *= rect.fade;
        }
      });
      return fade;
    }

    function clearPointer() {
      pointer.active = false;
      pointer.x = -9999;
      pointer.y = -9999;
      pointer.px = -9999;
      pointer.py = -9999;
    }

    function moveNode(node) {
      if (!reduceMotion) {
        const dx = node.x - pointer.x;
        const dy = node.y - pointer.y;
        const distance = Math.hypot(dx, dy);
        if (pointer.active && distance < 170 && distance > 0.01) {
          const force = (1 - distance / 170) * 0.052;
          node.vx += (dx / distance) * force + pointer.vx * 0.00032;
          node.vy += (dy / distance) * force + pointer.vy * 0.00032;
        }
        node.vx += Math.sin(node.phase) * 0.0012;
        node.vy += Math.cos(node.phase * 0.9) * 0.0012;
        node.x += node.vx;
        node.y += node.vy;
        node.rotation += node.spin;
        node.phase += 0.01;
        node.vx *= 0.99;
        node.vy *= 0.99;
        const speed = Math.hypot(node.vx, node.vy);
        if (speed > 0.86) {
          node.vx = (node.vx / speed) * 0.86;
          node.vy = (node.vy / speed) * 0.86;
        }
      }
      const margin = 120;
      if (node.x < -margin) node.x = width + margin;
      if (node.x > width + margin) node.x = -margin;
      if (node.y < -margin) node.y = height + margin;
      if (node.y > height + margin) node.y = -margin;
      node.uiFade = fadeForUi(node.x, node.y);
    }

    function drawLinks() {
      ctx.save();
      ctx.lineWidth = 1;
      ctx.globalCompositeOperation = "source-over";
      for (let left = 0; left < nodes.length; left += 1) {
        for (let right = left + 1; right < nodes.length; right += 1) {
          const a = nodes[left];
          const b = nodes[right];
          const distance = Math.hypot(a.x - b.x, a.y - b.y);
          if (distance > 190) continue;
          const mx = (a.x + b.x) / 2;
          const my = (a.y + b.y) / 2;
          const uiFade = Math.min(a.uiFade ?? 1, b.uiFade ?? 1, fadeForUi(mx, my));
          const pointerDistance = Math.hypot(mx - pointer.x, my - pointer.y);
          const pointerBoost = pointer.active && pointerDistance < 220 ? 0.1 * (1 - pointerDistance / 220) : 0;
          const alpha = Math.max(0, (1 - distance / 190) * 0.24 + pointerBoost) * uiFade;
          if (alpha < 0.01) continue;
          ctx.strokeStyle = colorFromIndex((a.color + b.color) % COLORS.length, alpha);
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.stroke();
        }
      }
      ctx.restore();
    }

    function drawWord(node) {
      const uiFade = node.uiFade ?? 1;
      const breath = reduceMotion ? 1 : 1 + Math.sin(node.phase) * 0.035;
      const pointerDistance = Math.hypot(node.x - pointer.x, node.y - pointer.y);
      const hover = pointer.active && pointerDistance < 145 ? 1 - pointerDistance / 145 : 0;
      const alpha = Math.min(0.86, (node.alpha + hover * 0.22) * uiFade);
      if (alpha < 0.015) return;
      ctx.save();
      ctx.translate(node.x, node.y);
      ctx.rotate(node.rotation);
      ctx.globalCompositeOperation = "source-over";
      ctx.font = `800 ${node.size * breath}px "Inter Tight", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.shadowBlur = 16 + hover * 12;
      ctx.shadowColor = colorFromIndex(node.color, alpha * 0.65);
      ctx.lineWidth = 3.2;
      ctx.strokeStyle = `rgba(4, 12, 22, ${alpha * 0.78})`;
      ctx.fillStyle = colorFromIndex(node.color, alpha);
      ctx.strokeText(node.word, 0, 0);
      ctx.fillText(node.word, 0, 0);
      ctx.restore();
    }

    function draw(timestamp = 0) {
      if (paused) {
        frameId = window.requestAnimationFrame(draw);
        return;
      }
      if (timestamp - lastFrameTime < 34) {
        frameId = window.requestAnimationFrame(draw);
        return;
      }
      lastFrameTime = timestamp;
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = "rgba(5, 12, 22, 0.018)";
      ctx.fillRect(0, 0, width, height);
      ctx.save();
      ctx.globalAlpha = 0.18;
      ctx.strokeStyle = "rgba(151, 215, 255, 0.08)";
      const step = 86;
      for (let x = 0; x < width; x += step) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke(); }
      for (let y = 0; y < height; y += step) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke(); }
      ctx.restore();
      nodes.forEach(moveNode);
      drawLinks();
      nodes.forEach(drawWord);
      if (!reduceMotion) frameId = window.requestAnimationFrame(draw);
    }
    function handleVisibilityChange() {
      paused = document.hidden;
      if (!paused) lastFrameTime = 0;
    }
    resize();
    window.addEventListener("resize", resize);
    window.addEventListener("scroll", updateProtectedRects, { passive: true });
    window.addEventListener("pointermove", updatePointer, { passive: true });
    window.addEventListener("pointerleave", clearPointer);
    document.addEventListener("visibilitychange", handleVisibilityChange);
    draw();
    return () => {
      window.cancelAnimationFrame(frameId);
      window.removeEventListener("resize", resize);
      window.removeEventListener("scroll", updateProtectedRects);
      window.removeEventListener("pointermove", updatePointer);
      window.removeEventListener("pointerleave", clearPointer);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }
})();
