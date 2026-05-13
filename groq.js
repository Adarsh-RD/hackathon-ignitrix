/* ===== returnX AI — groq.js ===== */

/**
 * Sends raw SMS text to Groq (Llama 3.1 70B) and returns
 * structured { income: [], expenses: [] }.
 *
 * @param {string} apiKey  - Groq API key
 * @param {string} smsText - Raw pasted SMS messages
 * @returns {Promise<{income: Array, expenses: Array}>}
 */
async function parseSmsWithGroq(apiKey, smsText) {

    const SYSTEM_PROMPT = `You are an SMS parser. From the given SMS messages extract two things:
1. INCOME: Any credits from Swiggy, Zomato, Rapido, Ola, Uber, Zepto, Blinkit. Extract platform name, amount, date.
2. EXPENSES: Any debits for petrol, fuel, HPCL, BPCL, IOC, phone recharge, internet, vehicle service, maintenance. Extract category, amount, date.
Return ONLY a JSON object with two arrays: income[] and expenses[]. No extra text.

Each income item: { "platform": "...", "amount": <number>, "date": "..." }
Each expense item: { "category": "...", "amount": <number>, "date": "..." }

If a date is not found, use "unknown".
If no income or expenses found, return empty arrays.`;

    const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`,
        },
        body: JSON.stringify({
            model: 'llama-3.3-70b-versatile',
            messages: [
                { role: 'system', content: SYSTEM_PROMPT },
                { role: 'user',   content: smsText },
            ],
            temperature: 0,
            max_tokens: 2048,
            response_format: { type: 'json_object' },
        }),
    });

    if (!response.ok) {
        const err = await response.text();
        throw new Error(`Groq API error (${response.status}): ${err}`);
    }

    const data = await response.json();
    const raw  = data.choices?.[0]?.message?.content ?? '{}';

    // Parse the JSON from the model response
    let parsed;
    try {
        parsed = JSON.parse(raw);
    } catch {
        // Sometimes the model wraps JSON in markdown — try to extract it
        const match = raw.match(/\{[\s\S]*\}/);
        if (match) {
            parsed = JSON.parse(match[0]);
        } else {
            throw new Error('Could not parse model response as JSON.');
        }
    }

    // Normalise
    const income   = Array.isArray(parsed.income)   ? parsed.income   : [];
    const expenses = Array.isArray(parsed.expenses)  ? parsed.expenses : [];

    return { income, expenses };
}
