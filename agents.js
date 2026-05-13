/* ===================================================================
 *  returnX AI — agents.js  (100% client-side, no backend needed)
 *
 *  Three-agent pipeline running directly against the Groq API:
 *    Agent 1 — SmsParserAgent   : extracts income transactions
 *    Agent 2 — TaxAdvisorAgent  : computes tax liability
 *    Agent 3 — InsightsAgent    : generates actionable insights
 * =================================================================== */

const AgentOrchestrator = {

    // ── Shared Groq chat helper ──────────────────────────────────────
    async _chat(apiKey, systemPrompt, userContent, json = true) {
        const body = {
            model: 'llama-3.3-70b-versatile',
            messages: [
                { role: 'system', content: systemPrompt },
                { role: 'user',   content: userContent  },
            ],
            temperature: 0,
            max_tokens: 2048,
        };
        if (json) body.response_format = { type: 'json_object' };

        const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type':  'application/json',
                'Authorization': `Bearer ${apiKey}`,
            },
            body: JSON.stringify(body),
        });

        if (!res.ok) {
            const txt = await res.text();
            throw new Error(`Groq API error (${res.status}): ${txt}`);
        }

        const data = await res.json();
        const raw  = data.choices?.[0]?.message?.content ?? (json ? '{}' : '');

        if (!json) return raw.trim();

        try {
            return JSON.parse(raw);
        } catch {
            const match = raw.match(/\{[\s\S]*\}/);
            if (match) return JSON.parse(match[0]);
            throw new Error('Could not parse model response as JSON.');
        }
    },

    // ── Agent 1: SMS Parser ──────────────────────────────────────────
    async runSmsParser(apiKey, smsText) {
        const SYSTEM = `You are an SMS parser for Indian gig workers (Swiggy, Zomato, Rapido, Ola, Uber, Zepto, Blinkit, Dunzo, etc.).
Extract INCOME only: any payment/credit received from these platforms.
Return ONLY a JSON object:
{
  "income": [{ "platform": "...", "amount": <number>, "date": "..." }]
}
If no income found, return { "income": [] }.
If date is not mentioned, use "unknown". Do NOT include expenses.`;

        const parsed = await this._chat(apiKey, SYSTEM, smsText);
        return Array.isArray(parsed.income) ? parsed.income : [];
    },

    // ── Agent 2: Tax Advisor ─────────────────────────────────────────
    async runTaxAdvisor(apiKey, income) {
        const totalInc = income.reduce((s, i) => s + (Number(i.amount) || 0), 0);

        const SYSTEM = `You are an Indian tax advisor specialising in gig workers.
Given total income, compute:
- tds_estimated: 1% of total income (TDS deducted by platforms)
- taxable_under_44ad: 6% of total income (presumptive tax under Sec 44AD)
- tax_slab: which income tax slab the income falls into
- advice: one actionable tax-saving tip (1-2 sentences)
Return ONLY JSON: { "tds_estimated": <n>, "taxable_under_44ad": <n>, "tax_slab": "...", "advice": "..." }`;

        return await this._chat(apiKey, SYSTEM, `Total annual income so far: ₹${Math.round(totalInc)}`);
    },

    // ── Agent 3: Insights ────────────────────────────────────────────
    async runInsights(apiKey, income, taxAnalysis) {
        const totalInc = income.reduce((s, i) => s + (Number(i.amount) || 0), 0);

        // Build platform summary
        const byPlatform = {};
        for (const item of income) {
            const k = (item.platform || 'Other').trim();
            byPlatform[k] = (byPlatform[k] || 0) + (Number(item.amount) || 0);
        }
        const platformSummary = Object.entries(byPlatform)
            .map(([p, a]) => `${p}: ₹${Math.round(a)}`).join(', ');

        const SYSTEM = `You are a financial coach for Indian gig delivery workers.
Generate 3 concise, actionable insights about the worker's income.
Return ONLY JSON:
{
  "insights": [
    { "icon": "<material-icon-name>", "color": "green|amber|blue", "title": "...", "description": "..." },
    ...
  ]
}`;

        const userMsg = `Total income: ₹${Math.round(totalInc)}
Platform breakdown: ${platformSummary || 'N/A'}
Tax info: TDS ₹${Math.round(taxAnalysis.tds_estimated || 0)}, Taxable under 44AD: ₹${Math.round(taxAnalysis.taxable_under_44ad || 0)}`;

        const parsed = await this._chat(apiKey, SYSTEM, userMsg);
        return Array.isArray(parsed.insights) ? parsed.insights : [];
    },

    // ── Main orchestrator ────────────────────────────────────────────
    async run(apiKey, smsText, accumulated, onStep) {
        const t0 = Date.now();

        // Step 1 — SMS Parser
        onStep?.('SmsParser running…', 1, 3);
        const income = await this.runSmsParser(apiKey, smsText);

        // Step 2 — Tax Advisor
        onStep?.('TaxAdvisor running…', 2, 3);
        const allIncome = [...(accumulated.totalIncome || []), ...income];
        const taxAnalysis = await this.runTaxAdvisor(apiKey, allIncome);

        // Step 3 — Insights
        onStep?.('Insights running…', 3, 3);
        const insights = await this.runInsights(apiKey, allIncome, taxAnalysis);

        const duration = ((Date.now() - t0) / 1000).toFixed(1);

        return {
            income,
            expenses:         [],           // removed — no expense tracking
            taxAnalysis,
            insights,
            agentLog:         [],
            pipelineDuration: duration,
        };
    },
};
