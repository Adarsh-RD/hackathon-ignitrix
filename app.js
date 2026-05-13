/* ===== returnX AI — app.js (always-on, accumulating) ===== */
(function () {
    'use strict';

    // ── Storage Keys ──
    const KEY_API     = 'returnx_groq_key';
    const KEY_INCOME  = 'returnx_income';

    const KEY_LOG     = 'returnx_log';

    // ── DOM refs ──
    const textarea   = document.getElementById('message-input');
    const charCount  = document.getElementById('char-count');
    const addBtn     = document.getElementById('add-btn');
    const apiKeyIn   = document.getElementById('api-key-input');
    const errorArea  = document.getElementById('error-area');

    // API key collapse
    const apikeyToggle = document.getElementById('apikey-toggle');
    const apikeyArrow  = document.getElementById('apikey-arrow');
    const apikeyBody   = document.getElementById('apikey-body');

    // Dashboard
    const incomeTbody    = document.getElementById('income-tbody');
    const incomeEmpty    = document.getElementById('income-empty');
    const incomeCount    = document.getElementById('income-count');
    const incomeTotalVal = document.getElementById('income-total-val');
    const totalIncomeEl  = document.getElementById('total-income');
    const summaryTds     = document.getElementById('summary-tds');
    const summary44ad    = document.getElementById('summary-44ad');
    const historyList    = document.getElementById('history-list');
    const historyEmpty   = document.getElementById('history-empty');
    const clearAllBtn    = document.getElementById('clear-all-btn');

    // ── Helpers ──
    const fmt = n => '₹' + Math.round(Number(n)).toLocaleString('en-IN');

    function loadJSON(key, fallback) {
        try { return JSON.parse(localStorage.getItem(key)) || fallback; }
        catch { return fallback; }
    }
    function saveJSON(key, data) { localStorage.setItem(key, JSON.stringify(data)); }

    // ── State ──
    let allIncome   = loadJSON(KEY_INCOME, []);

    let activityLog = loadJSON(KEY_LOG, []);

    // ── Init API key ──
    apiKeyIn.value = localStorage.getItem(KEY_API) || '';
    apiKeyIn.addEventListener('input', () => {
        localStorage.setItem(KEY_API, apiKeyIn.value.trim());
    });

    // ── API key collapse toggle ──
    // Auto-open if no key saved
    if (apiKeyIn.value) {
        apikeyBody.classList.remove('collapse-body--open');
    } else {
        apikeyBody.classList.add('collapse-body--open');
        apikeyArrow.classList.add('collapse-btn__arrow--up');
    }
    apikeyToggle.addEventListener('click', () => {
        apikeyBody.classList.toggle('collapse-body--open');
        apikeyArrow.classList.toggle('collapse-btn__arrow--up');
    });

    // ── Character count ──
    textarea.addEventListener('input', () => {
        const len = textarea.value.length;
        charCount.textContent = len.toLocaleString('en-IN') + ' chars';
        hideError();
    });

    // ── Error helpers ──
    function showError(msg) {
        hideError();
        const el = document.createElement('div');
        el.className = 'error-msg';
        el.innerHTML = '<span class="material-icons-round">error_outline</span> ' + msg;
        errorArea.appendChild(el);
    }
    function hideError() { errorArea.innerHTML = ''; }

    // ── Render dashboard from accumulated state ──
    function renderDashboard() {
        // Income table
        incomeTbody.innerHTML = '';
        if (allIncome.length === 0) {
            document.getElementById('income-table').style.display = 'none';
            incomeEmpty.style.display = 'block';
        } else {
            document.getElementById('income-table').style.display = '';
            incomeEmpty.style.display = 'none';
            for (const item of allIncome) {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td>${item.platform || 'Unknown'}</td>
                    <td class="amt-green">+ ${fmt(item.amount)}</td>
                    <td class="date-cell">${item.date && item.date !== 'unknown' ? item.date : '—'}</td>`;
                incomeTbody.appendChild(tr);
            }
        }

        // Totals
        const totalInc = allIncome.reduce((s, i) => s + (Number(i.amount) || 0), 0);

        incomeTotalVal.textContent  = fmt(totalInc);
        totalIncomeEl.textContent   = fmt(totalInc);
        summaryTds.textContent      = fmt(totalInc * 0.01);
        summary44ad.textContent     = fmt(totalInc * 0.06);

        // Counts
        incomeCount.textContent  = allIncome.length + ' entr' + (allIncome.length === 1 ? 'y' : 'ies');

        // Activity log
        renderHistory();

        // Charts
        renderCharts(totalInc);

        // Insights
        renderInsights(totalInc);
    }

    // ── Chart instances (destroy before recreating) ──
    let incomeChartInstance = null;


    function renderCharts(totalInc) {
        // -- Income bar chart: aggregate by platform --
        const incomeByPlatform = {};
        for (const item of allIncome) {
            const key = (item.platform || 'Other').trim();
            incomeByPlatform[key] = (incomeByPlatform[key] || 0) + (Number(item.amount) || 0);
        }
        const incomeLabels = Object.keys(incomeByPlatform);
        const incomeValues = Object.values(incomeByPlatform);

        const incomeCanvas = document.getElementById('income-chart');
        const incomeChartEmpty = document.getElementById('income-chart-empty');

        if (incomeChartInstance) incomeChartInstance.destroy();

        if (incomeLabels.length === 0) {
            incomeCanvas.style.display = 'none';
            incomeChartEmpty.style.display = '';
        } else {
            incomeCanvas.style.display = '';
            incomeChartEmpty.style.display = 'none';

            const barColors = ['#059669','#0D9F6E','#34D399','#6EE7B7','#A7F3D0','#10B981'];
            incomeChartInstance = new Chart(incomeCanvas, {
                type: 'bar',
                data: {
                    labels: incomeLabels,
                    datasets: [{
                        label: 'Income (₹)',
                        data: incomeValues,
                        backgroundColor: incomeLabels.map((_, i) => barColors[i % barColors.length]),
                        borderRadius: 6,
                        borderSkipped: false,
                        maxBarThickness: 48,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: { duration: 800, easing: 'easeOutQuart' },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: ctx => '₹' + Math.round(ctx.raw).toLocaleString('en-IN')
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: v => '₹' + (v >= 1000 ? (v/1000).toFixed(0) + 'K' : v),
                                font: { size: 11, family: 'Inter' },
                                color: '#94A3B8'
                            },
                            grid: { color: '#F1F5F9' }
                        },
                        x: {
                            ticks: { font: { size: 11, weight: 600, family: 'Inter' }, color: '#64748B' },
                            grid: { display: false }
                        }
                    }
                }
            });
        }

    }

    // ── Insights ──
    function renderInsights(totalInc) {
        const insightsBody = document.getElementById('insights-body');

        if (allIncome.length === 0) {
            insightsBody.innerHTML = '<p class="insights-card__empty">Add some messages to see insights.</p>';
            return;
        }

        let html = '';

        // Biggest income source
        if (allIncome.length > 0) {
            const byPlatform = {};
            for (const item of allIncome) {
                const key = (item.platform || 'Other').trim();
                byPlatform[key] = (byPlatform[key] || 0) + (Number(item.amount) || 0);
            }
            const topPlatform = Object.entries(byPlatform).sort((a, b) => b[1] - a[1])[0];
            html += `<div class="insight-item">
                <span class="insight-item__icon insight-item__icon--green material-icons-round">star</span>
                <span>Your biggest income source is <strong>${topPlatform[0]}</strong> at <strong>${fmt(topPlatform[1])}</strong></span>
            </div>`;
        }

        insightsBody.innerHTML = html;
    }

    // ── Render activity log ──
    function renderHistory() {
        historyList.innerHTML = '';
        if (activityLog.length === 0) {
            historyList.innerHTML = '<p class="history-empty">No messages added yet.</p>';
            return;
        }
        // Show latest first
        for (const entry of [...activityLog].reverse()) {
            const div = document.createElement('div');
            div.className = 'history-item';
            div.innerHTML = `<span class="history-item__dot"></span>
                <span class="history-item__text">
                    <strong>+${entry.income}i / +${entry.expenses}e</strong> parsed
                    <br>${entry.time}
                </span>`;
            historyList.appendChild(div);
        }
    }

    // ── Agent stepper UI ──
    const agentStepper = document.getElementById('agent-stepper');
    function showStepper() {
        agentStepper.style.display = '';
        for (let i = 1; i <= 3; i++) {
            const el = document.getElementById('step-' + i);
            el.classList.remove('agent-step--active', 'agent-step--done');
        }
    }
    function updateStepper(step) {
        for (let i = 1; i <= 3; i++) {
            const el = document.getElementById('step-' + i);
            el.classList.remove('agent-step--active', 'agent-step--done');
            if (i < step) el.classList.add('agent-step--done');
            else if (i === step) el.classList.add('agent-step--active');
        }
    }
    function completeStepper() {
        for (let i = 1; i <= 3; i++) {
            document.getElementById('step-' + i).classList.add('agent-step--done');
        }
        setTimeout(() => { agentStepper.style.display = 'none'; }, 2000);
    }

    // ── Render AI-generated insights (from InsightsAgent) ──
    let lastInsights = loadJSON('returnx_insights', []);
    let lastTaxAnalysis = loadJSON('returnx_tax', {});

    function renderAgentInsights() {
        const insightsBody = document.getElementById('insights-body');

        if (lastInsights.length === 0) {
            // Fallback to basic computed insights
            renderInsights(
                allIncome.reduce((s, i) => s + (Number(i.amount) || 0), 0),
                0
            );
            return;
        }

        const colorMap = { green: '--green', red: '--red', blue: '--blue', amber: '--blue' };
        let html = '';
        for (const insight of lastInsights) {
            const colorClass = colorMap[insight.color] || '--green';
            html += `<div class="insight-item">
                <span class="insight-item__icon insight-item__icon${colorClass} material-icons-round">${insight.icon || 'lightbulb'}</span>
                <span><strong>${insight.title || ''}</strong> ${insight.description || ''}</span>
            </div>`;
        }
        document.getElementById('insights-body').innerHTML = html;

        // Update tax bar with agent-computed values if available
        if (lastTaxAnalysis.tds_estimated) {
            summaryTds.textContent = fmt(lastTaxAnalysis.tds_estimated);
        }
        if (lastTaxAnalysis.taxable_under_44ad) {
            summary44ad.textContent = fmt(lastTaxAnalysis.taxable_under_44ad);
        }
    }

    // ── Add & Analyse button — Agentic Pipeline ──
    addBtn.addEventListener('click', async () => {
        hideError();
        const apiKey = apiKeyIn.value.trim();
        const text   = textarea.value.trim();

        if (!apiKey) {
            if (!apikeyBody.classList.contains('collapse-body--open')) {
                apikeyBody.classList.add('collapse-body--open');
                apikeyArrow.classList.add('collapse-btn__arrow--up');
            }
            apiKeyIn.focus();
            showError('Please paste your Groq API key. <a href="https://console.groq.com/keys" target="_blank">Get free key →</a>');
            return;
        }
        if (!text) {
            textarea.focus();
            showError('Paste some SMS / payment messages first.');
            return;
        }

        // Loading + show stepper
        addBtn.classList.add('add-btn--loading');
        addBtn.disabled = true;
        showStepper();

        try {
            // Build accumulated state for downstream agents
            const accumulated = {
                totalIncome: [...allIncome],
            };

            // Run the full agentic pipeline
            const result = await AgentOrchestrator.run(
                apiKey,
                text,
                accumulated,
                (msg, step, total) => { updateStepper(step); }
            );

            completeStepper();

            // Accumulate parsed transactions
            if (result.income.length > 0) {
                allIncome.push(...result.income);
                saveJSON(KEY_INCOME, allIncome);
            }


            // Store agent outputs
            if (result.insights && result.insights.length > 0) {
                lastInsights = result.insights;
                saveJSON('returnx_insights', lastInsights);
            }
            if (result.taxAnalysis) {
                lastTaxAnalysis = result.taxAnalysis;
                saveJSON('returnx_tax', lastTaxAnalysis);
            }

            // Log entry
            const now = new Date();
            const timeStr = now.toLocaleString('en-IN', {
                day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'
            });
            activityLog.push({
                income: result.income.length,
                expenses: result.expenses.length,
                agents: 3,
                duration: result.pipelineDuration + 's',
                time: timeStr
            });
            saveJSON(KEY_LOG, activityLog);

            // Clear textarea
            textarea.value = '';
            charCount.textContent = '0 chars';

            // Re-render dashboard + agent insights
            renderDashboard();
            renderAgentInsights();

        } catch (err) {
            console.error('[returnX]', err);
            agentStepper.style.display = 'none';
            let msg = err.message || 'Something went wrong.';
            if (msg.includes('401')) msg = 'Invalid API key. Check and try again.';
            else if (msg.includes('429')) msg = 'Rate limit hit. Wait a moment and retry.';
            else if (msg.includes('Failed to fetch')) msg = 'Network error. Check internet.';
            showError(msg);
        } finally {
            addBtn.classList.remove('add-btn--loading');
            addBtn.disabled = false;
        }
    });

    // ── Clear all data ──
    clearAllBtn.addEventListener('click', () => {
        if (!confirm('Clear ALL recorded income and history?')) return;
        allIncome = [];
        activityLog = [];
        lastInsights = [];
        lastTaxAnalysis = {};
        localStorage.removeItem(KEY_INCOME);

        localStorage.removeItem(KEY_LOG);
        localStorage.removeItem('returnx_insights');
        localStorage.removeItem('returnx_tax');
        renderDashboard();
    });

    // ── Initial render ──
    renderDashboard();
    renderAgentInsights();
    console.log('[returnX] Agentic app loaded ✓ | Agents: SmsParser, TaxAdvisor, Insights');

})();
