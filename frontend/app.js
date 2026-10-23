/**
 * DESIGNS / LAW — Application Logic & API Client
 * Connects research interface to FastAPI RAG backend with strict citation rendering.
 */

document.addEventListener('DOMContentLoaded', () => {
  'use strict';

  // Determine API Base URL (Supports relative when served from FastAPI /app or absolute for standalone frontend)
  const isSameOriginBackend = window.location.port === '8000' || window.location.pathname.startsWith('/app');
  const API_BASE = isSameOriginBackend ? '' : 'http://127.0.0.1:8000';

  // DOM Elements
  const form = document.getElementById('ask-form');
  const questionInput = document.getElementById('question-input');
  const charCounter = document.getElementById('char-counter');
  const submitBtn = document.getElementById('submit-btn');
  const sampleChips = document.querySelectorAll('.sample-chip');

  const responseContainer = document.getElementById('response-container');
  const loadingState = document.getElementById('loading-state');
  const resultCard = document.getElementById('result-card');
  const errorCard = document.getElementById('error-card');
  const errorMessage = document.getElementById('error-message');

  const echoQuestion = document.getElementById('echo-question');
  const answerContent = document.getElementById('answer-content');
  const verdictBadge = document.getElementById('verdict-badge');
  const citationsSection = document.getElementById('citations-section');
  const citationsGrid = document.getElementById('citations-grid');
  const citationsCount = document.getElementById('citations-count');
  const notFoundExplanation = document.getElementById('not-found-explanation');

  const copyBtn = document.getElementById('copy-btn');
  const copyText = document.getElementById('copy-text');
  const resetBtn = document.getElementById('reset-btn');
  const systemStatus = document.getElementById('system-status');

  // Check Backend Health on Mount
  async function checkHealth() {
    try {
      const res = await fetch(`${API_BASE}/health`, { method: 'GET' });
      if (res.ok) {
        const data = await res.json();
        if (systemStatus) {
          const label = systemStatus.querySelector('.status-label');
          if (data.database_initialized) {
            label.textContent = `INDEX READY (${data.embedding_provider.toUpperCase()})`;
          } else {
            label.textContent = 'DATABASE UNINDEXED';
          }
        }
      }
    } catch (e) {
      if (systemStatus) {
        const label = systemStatus.querySelector('.status-label');
        label.textContent = 'SERVER OFFLINE';
        systemStatus.style.borderColor = 'rgba(239, 68, 68, 0.4)';
        const dot = systemStatus.querySelector('.status-dot');
        if (dot) dot.style.backgroundColor = '#ef4444';
      }
    }
  }
  checkHealth();

  // Check URL query parameters for direct link or automated query execution
  const urlParams = new URLSearchParams(window.location.search);
  const initialQuery = urlParams.get('q');
  if (initialQuery) {
    questionInput.value = initialQuery;
    updateCharCount();
    // Execute after brief delay so health check starts
    setTimeout(() => {
      handleQuerySubmit(initialQuery);
    }, 150);
  }


  // Character counter and auto-expand textarea
  function updateCharCount() {
    const len = questionInput.value.length;
    charCounter.textContent = `${len} / 500`;
    // Auto-grow textarea height
    questionInput.style.height = 'auto';
    questionInput.style.height = `${Math.min(questionInput.scrollHeight, 180)}px`;
  }

  questionInput.addEventListener('input', updateCharCount);

  // Keyboard shortcut: Enter to submit, Shift+Enter for new line
  questionInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      form.requestSubmit();
    }
  });

  // Sample Chips: Click-to-fill and immediate execution
  sampleChips.forEach((chip) => {
    chip.addEventListener('click', () => {
      const q = chip.getAttribute('data-question');
      if (q) {
        questionInput.value = q;
        updateCharCount();
        handleQuerySubmit(q);
      }
    });
  });

  // Form submission handler
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const query = questionInput.value.trim();
    if (!query) return;
    handleQuerySubmit(query);
  });

  // Query Execution
  async function handleQuerySubmit(question) {
    // UI state transitions
    submitBtn.disabled = true;
    responseContainer.classList.remove('hidden');
    loadingState.classList.remove('hidden');
    resultCard.classList.add('hidden');
    errorCard.classList.add('hidden');

    // Smooth scroll into view
    responseContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    try {
      const response = await fetch(`${API_BASE}/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({ question }),
      });

      loadingState.classList.add('hidden');

      if (!response.ok) {
        let errDetail = `Server returned status ${response.status}`;
        try {
          const errData = await response.json();
          if (errData.detail) {
            errDetail = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
          }
        } catch (_) {}
        showError(errDetail);
        return;
      }

      const data = await response.json();
      renderResult(data);
    } catch (networkError) {
      loadingState.classList.add('hidden');
      showError(
        'Unable to connect to the Designs Law Assistant API server. ' +
        'Please ensure FastAPI is running at ' + (API_BASE || 'http://127.0.0.1:8000') + '.'
      );
    } finally {
      submitBtn.disabled = false;
    }
  }

  // Safe DOM Rendering for Results
  function renderResult(data) {
    resultCard.classList.remove('hidden');
    echoQuestion.textContent = data.question;

    const isFound = data.found === true && data.answer !== 'Not found';

    if (isFound) {
      // Grounded state
      verdictBadge.textContent = 'SOURCE VERIFIED';
      verdictBadge.className = 'verdict-badge';
      answerContent.className = 'answer-content';
      answerContent.textContent = data.answer;

      notFoundExplanation.classList.add('hidden');
      citationsSection.classList.remove('hidden');

      // Populate citations
      citationsGrid.replaceChildren();
      const citations = data.citations || [];
      citationsCount.textContent = `${citations.length} verified ${citations.length === 1 ? 'citation' : 'citations'} attached`;

      citations.forEach((cit) => {
        const card = document.createElement('div');
        card.className = 'citation-card';

        const topRow = document.createElement('div');
        topRow.className = 'citation-top';

        const pageBadge = document.createElement('span');
        pageBadge.className = 'citation-page-badge';
        pageBadge.textContent = `PDF PAGE ${cit.page}`;

        const sourceName = document.createElement('span');
        sourceName.className = 'citation-source-name';
        sourceName.textContent = cit.source;

        topRow.appendChild(pageBadge);
        topRow.appendChild(sourceName);

        const secTitle = document.createElement('h4');
        secTitle.className = 'citation-section-title';
        secTitle.textContent = cit.section || 'Manual of Designs Practice';

        const excerptEl = document.createElement('p');
        excerptEl.className = 'citation-excerpt';
        excerptEl.textContent = `"${cit.excerpt}"`;

        card.appendChild(topRow);
        card.appendChild(secTitle);
        card.appendChild(excerptEl);
        citationsGrid.appendChild(card);
      });
    } else {
      // Exact Not Found state
      verdictBadge.textContent = 'UNSUPPORTED BY MANUAL';
      verdictBadge.className = 'verdict-badge unsupported';

      answerContent.className = 'answer-content not-found-text';
      answerContent.textContent = 'Not found';

      citationsSection.classList.add('hidden');
      notFoundExplanation.classList.remove('hidden');
    }
  }

  // Display Error State
  function showError(msg) {
    errorCard.classList.remove('hidden');
    errorMessage.textContent = msg;
  }

  // Copy to Clipboard
  copyBtn.addEventListener('click', async () => {
    const textToCopy = answerContent.textContent;
    if (!textToCopy) return;

    try {
      await navigator.clipboard.writeText(textToCopy);
      copyText.textContent = 'Copied!';
      setTimeout(() => {
        copyText.textContent = 'Copy Answer';
      }, 2000);
    } catch (e) {
      console.warn('Clipboard write failed:', e);
    }
  });

  // Reset Action
  resetBtn.addEventListener('click', () => {
    questionInput.value = '';
    updateCharCount();
    responseContainer.classList.add('hidden');
    resultCard.classList.add('hidden');
    errorCard.classList.add('hidden');
    questionInput.focus();
  });
});
