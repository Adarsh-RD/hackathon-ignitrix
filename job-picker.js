/* ===================================================================
 *  returnX AI — job-picker.js (Smart Job Picker — Notification-Based)
 *
 *  TWO INPUT MODES:
 *  1. Paste Notifications — rider pastes raw notification text, AI extracts jobs
 *  2. Simulate Live — demo mode with realistic push notifications
 *
 *  Flow: Notification Text → AI Parse → Extracted Jobs Preview → Compare → Winner
 * =================================================================== */

const JobPicker = {
    extractedJobs: [],  // Jobs extracted from notifications
    currentMode: 'paste',

    // ── Realistic notification templates for simulation ──
    SIMULATED_NOTIFICATIONS: [
        {
            platform: 'Swiggy',
            icon: '🍔',
            color: '#FF5722',
            notifications: [
                'New order available! Earn ₹52 for 3.8 km delivery. Pickup from Meghana Foods (BTM Layout), deliver to Koramangala 5th Block.',
                'Delivery request! ₹38 payout, 2.1 km. Pickup: Dominos Pizza (HSR Layout). Drop: Sector 2, HSR.',
                'High demand zone! Order: ₹67 for 4.5 km. Pickup from Behrouz Biryani, deliver to Indiranagar.',
                'New order! ₹45 for 3.2 km food delivery. Pickup: McDonald\'s (MG Road). Drop: Brigade Road.',
            ]
        },
        {
            platform: 'Zepto',
            icon: '⚡',
            color: '#7B2FF7',
            notifications: [
                'Delivery request! Earn ₹35. Distance: 1.5 km. Grocery order from Zepto Dark Store (Koramangala).',
                'Quick delivery! ₹28 for 1.2 km. Pickup from Zepto Hub (HSR). Small grocery bag.',
                'New order! ₹42 payout, 2.3 km. Zepto Dark Store (Indiranagar) → Customer location.',
                'Instant delivery needed! ₹31 for 1.8 km. Grocery items from Zepto Warehouse.',
            ]
        },
        {
            platform: 'Zomato',
            icon: '🍕',
            color: '#E23744',
            notifications: [
                'Order available! ₹62 payout, 4.1 km. Food pickup from Paradise Biryani (Jayanagar). Deliver to JP Nagar.',
                'New delivery! Earn ₹48 for 3.5 km. Pickup: KFC (Marathahalli). Drop: Whitefield.',
                'Delivery request! ₹55 for 3.9 km. Restaurant: Truffles (Koramangala). Customer: HSR Layout.',
                'Priority order! ₹71 for 5.2 km. Pickup from Empire Restaurant, deliver to Electronic City.',
            ]
        },
        {
            platform: 'Blinkit',
            icon: '🛒',
            color: '#F8C12D',
            notifications: [
                'New delivery! ₹32 for 1.4 km. Grocery order from Blinkit Store (Koramangala 4th Block).',
                'Quick order! Earn ₹25 for 0.9 km. Small essentials order. Pickup: Blinkit Hub.',
                'Delivery available! ₹38 for 1.7 km. Blinkit Dark Store → Customer (BTM Layout).',
            ]
        },
        {
            platform: 'Rapido',
            icon: '🏍️',
            color: '#FFCB05',
            notifications: [
                'Ride request! Earn ₹85 for 6.2 km. Pickup: MG Road Metro. Drop: Whitefield.',
                'New ride! ₹120 for 9.5 km. Pickup from Silk Board. Drop to Electronic City.',
                'Bike taxi request! ₹58 for 4.0 km. HSR Layout to Koramangala.',
            ]
        },
        {
            platform: 'Dunzo',
            icon: '📦',
            color: '#00D09C',
            notifications: [
                'Pickup & drop! Earn ₹55 for 3.8 km. Package pickup from Indiranagar, deliver to MG Road.',
                'New task! ₹42 for 2.5 km. Document delivery from Koramangala to HSR Layout.',
            ]
        },
    ],

    /**
     * Get sample notification text for the paste area
     */
    getSampleNotifications() {
        return `🍔 Swiggy: New order available! Earn ₹52 for 3.8 km delivery. Pickup from Meghana Foods (BTM Layout), deliver to Koramangala 5th Block.

⚡ Zepto: Delivery request! Earn ₹35. Distance: 1.5 km. Grocery order from Zepto Dark Store (Koramangala).

🍕 Zomato: Order available! ₹62 payout, 4.1 km. Food pickup from Paradise Biryani (Jayanagar). Deliver to JP Nagar.`;
    },

    /**
     * Show an error message
     */
    showError(msg) {
        const area = document.getElementById('job-error-area');
        area.innerHTML = `<div class="error-msg">
            <span class="material-icons-round">error_outline</span> ${msg}
        </div>`;
    },

    clearError() {
        document.getElementById('job-error-area').innerHTML = '';
    },

    /**
     * Render extracted jobs as preview cards
     */
    renderExtractedJobs(jobs) {
        this.extractedJobs = jobs;
        const container = document.getElementById('notif-extracted');
        const cardsEl = document.getElementById('notif-extracted-cards');
        const countEl = document.getElementById('notif-extracted-count');

        if (jobs.length === 0) {
            container.style.display = 'none';
            return;
        }

        container.style.display = '';
        countEl.textContent = jobs.length;

        const platformIcons = {
            'Swiggy': '🍔', 'Zomato': '🍕', 'Zepto': '⚡', 'Blinkit': '🛒',
            'BigBasket': '🧺', 'Dunzo': '📦', 'Rapido': '🏍️', 'Uber': '🚗',
            'Ola': '🛺', 'Porter': '🚛',
        };

        const fmt = n => '₹' + Math.round(Number(n)).toLocaleString('en-IN');

        let html = '';
        jobs.forEach((job, i) => {
            const icon = platformIcons[job.platform] || '📱';
            html += `
            <div class="notif-job-card" style="animation-delay:${i * 0.1}s">
                <div class="notif-job-card__icon">${icon}</div>
                <div class="notif-job-card__info">
                    <span class="notif-job-card__platform">${job.platform || 'Unknown'}</span>
                    <span class="notif-job-card__details">
                        ${fmt(job.pay || 0)} · ${job.distance_km || '?'} km · ${job.items || 'Delivery'}
                    </span>
                </div>
                <button class="notif-job-card__remove" data-remove-job="${i}" title="Remove">
                    <span class="material-icons-round">close</span>
                </button>
            </div>`;
        });

        cardsEl.innerHTML = html;

        // Remove job handler
        cardsEl.querySelectorAll('.notif-job-card__remove').forEach(btn => {
            btn.addEventListener('click', () => {
                const idx = parseInt(btn.dataset.removeJob);
                this.extractedJobs.splice(idx, 1);
                this.renderExtractedJobs(this.extractedJobs);
            });
        });
    },

    /**
     * Simulate notifications appearing one by one
     */
    async simulateNotifications() {
        const feedEl = document.getElementById('notif-feed');
        const emptyEl = document.getElementById('notif-feed-empty');
        const simBtn = document.getElementById('notif-simulate-btn');

        // Clear previous
        feedEl.innerHTML = '';
        emptyEl?.remove();
        this.extractedJobs = [];
        this.renderExtractedJobs([]);

        // Disable button
        simBtn.disabled = true;
        simBtn.innerHTML = '<span class="spinner"></span> Receiving notifications...';

        // Pick 2-3 random platforms
        const shuffled = [...this.SIMULATED_NOTIFICATIONS].sort(() => Math.random() - 0.5);
        const selected = shuffled.slice(0, 3);
        const jobs = [];

        for (let i = 0; i < selected.length; i++) {
            const platform = selected[i];
            const notifText = platform.notifications[Math.floor(Math.random() * platform.notifications.length)];

            // Extract pay and distance from the notification text
            const payMatch = notifText.match(/₹(\d+)/);
            const distMatch = notifText.match(/([\d.]+)\s*km/);
            const pay = payMatch ? parseInt(payMatch[1]) : 40;
            const dist = distMatch ? parseFloat(distMatch[1]) : 3.0;
            const itemType = platform.platform === 'Rapido' ? 'Bike ride' :
                            ['Zepto', 'Blinkit', 'BigBasket'].includes(platform.platform) ? 'Grocery delivery' : 'Food delivery';

            jobs.push({
                platform: platform.platform,
                pay: pay,
                distance_km: dist,
                items: itemType,
            });

            // Create notification card with animation
            const notifCard = document.createElement('div');
            notifCard.className = 'notif-card';
            notifCard.style.borderLeftColor = platform.color;
            notifCard.innerHTML = `
                <div class="notif-card__header">
                    <span class="notif-card__icon">${platform.icon}</span>
                    <span class="notif-card__app">${platform.platform}</span>
                    <span class="notif-card__time">just now</span>
                </div>
                <p class="notif-card__body">${notifText}</p>
            `;

            feedEl.prepend(notifCard);

            // Wait between notifications to simulate real-time
            await new Promise(resolve => setTimeout(resolve, 800 + Math.random() * 600));
        }

        // Show extracted jobs
        this.renderExtractedJobs(jobs);

        // Re-enable button
        simBtn.disabled = false;
        simBtn.innerHTML = '<span class="material-icons-round">cell_tower</span> Simulate Again';

        // Scroll to extracted jobs
        document.getElementById('notif-extracted')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    },

    /**
     * Parse notification text via backend API
     */
    async parseNotificationText() {
        const apiKey = document.getElementById('api-key-input')?.value?.trim();
        const notifText = document.getElementById('notif-paste-input')?.value?.trim();

        if (!apiKey) {
            this.showError('Please paste your Groq API key first.');
            return false;
        }
        if (!notifText) {
            this.showError('Paste some notification text first.');
            return false;
        }

        try {
            const response = await fetch('http://localhost:5000/api/parse-notifications', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: apiKey, notification_text: notifText }),
            });

            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                throw new Error(err.error || `Server error (${response.status})`);
            }

            const result = await response.json();
            const jobs = result.jobs || [];

            if (jobs.length < 2) {
                this.showError('Could not extract enough job offers. Try pasting more notification text.');
                return false;
            }

            this.renderExtractedJobs(jobs);
            return true;

        } catch (err) {
            console.error('[JobPicker] Parse error:', err);
            let msg = err.message || 'Something went wrong.';
            if (msg.includes('Failed to fetch')) msg = 'Backend not running. Start the server first.';
            this.showError(msg);
            return false;
        }
    },

    /**
     * Render the comparison results
     */
    renderResults(data) {
        const resultsEl = document.getElementById('job-results');
        const comparisonEl = document.getElementById('job-comparison');

        resultsEl.style.display = '';

        // Winner card
        const rec = data.recommendation || {};
        document.getElementById('job-winner-platform').textContent =
            `🏆 Go with ${rec.best_platform || 'N/A'}!`;
        document.getElementById('job-winner-reason').textContent =
            rec.reason_detailed || rec.reason_short || '—';

        const confidence = rec.confidence || 0;
        const confFill = document.getElementById('job-winner-confidence-fill');
        const confLabel = document.getElementById('job-winner-confidence-label');
        confFill.style.width = '0%';
        confLabel.textContent = `${confidence}% confidence`;

        // Animate confidence bar
        requestAnimationFrame(() => {
            setTimeout(() => {
                confFill.style.width = `${confidence}%`;
            }, 100);
        });

        // Detailed analysis cards
        const analysis = data.analysis || [];
        const bestIndex = rec.best_job_index ?? 0;
        const trafficInfo = data.traffic_info || {};

        // ── Traffic banner → dedicated container ABOVE the map ──
        const trafficContainer = document.getElementById('traffic-container');
        if (trafficContainer) {
            if (trafficInfo.time) {
                const tClr = {'Low':'#059669','Medium':'#D97706','High':'#DC2626','Very High':'#991B1B'};
                trafficContainer.innerHTML = `<div class="traffic-banner">
                    <div class="traffic-banner__head">
                        <span class="material-icons-round">traffic</span>
                        <span>Traffic Analysis</span>
                        <span class="traffic-banner__time">${trafficInfo.time} &middot; ${trafficInfo.period || ''}</span>
                    </div>
                    <div class="traffic-banner__zones">
                        ${(trafficInfo.zones || []).map(z => `
                        <div class="traffic-zone">
                            <span class="traffic-zone__name">${z.name}</span>
                            <div class="traffic-zone__bar"><div class="traffic-zone__fill" style="width:${z.congestion}%;background:${tClr[z.level]||'#D97706'}"></div></div>
                            <span class="traffic-zone__label" style="color:${tClr[z.level]||'#D97706'}">${z.level}</span>
                        </div>`).join('')}
                    </div>
                </div>`;
            } else {
                trafficContainer.innerHTML = '';
            }
        }

        // ── Comparison cards — side by side grid ──
        let html = '';
        analysis.forEach((job, i) => {
            const isWinner = i === bestIndex;
            const fmt = n => '₹' + Math.round(Number(n)).toLocaleString('en-IN');
            const tLevel = job.traffic_level || 'Medium';
            const tClr = {'Low':'#059669','Medium':'#D97706','High':'#DC2626','Very High':'#991B1B'}[tLevel] || '#D97706';
            const tIcon = {'Low':'speed','Medium':'commute','High':'warning','Very High':'dangerous'}[tLevel] || 'commute';
            const delay = job.traffic_delay_mins || 0;

            html += `
            <div class="job-analysis-card ${isWinner ? 'job-analysis-card--winner' : ''}" style="animation-delay:${i * 0.12}s">
                ${isWinner ? '<div class="job-analysis-card__crown"><span class="material-icons-round">emoji_events</span> BEST PICK</div>' : ''}
                <div class="job-analysis-card__head">
                    <h4 class="job-analysis-card__platform">${job.platform || 'Unknown'}</h4>
                    <span class="job-analysis-card__score ${isWinner ? 'job-analysis-card__score--top' : ''}">${job.score || 0}/100</span>
                </div>
                <div class="job-analysis-card__traffic" style="border-left:3px solid ${tClr}">
                    <span class="material-icons-round" style="color:${tClr};font-size:16px">${tIcon}</span>
                    <span style="color:${tClr};font-weight:700;font-size:.78rem">${tLevel} Traffic</span>
                    ${delay > 0 ? `<span class="traffic-delay">+${Math.round(delay)} min delay</span>` : ''}
                </div>
                <div class="job-analysis-card__metrics">
                    <div class="job-metric">
                        <span class="job-metric__label">Pay</span>
                        <span class="job-metric__value job-metric__value--green">${fmt(job.pay || 0)}</span>
                    </div>
                    <div class="job-metric">
                        <span class="job-metric__label">Distance</span>
                        <span class="job-metric__value">${job.distance_km || 0} km</span>
                    </div>
                    <div class="job-metric">
                        <span class="job-metric__label">Fuel Cost</span>
                        <span class="job-metric__value job-metric__value--red">${fmt(job.fuel_cost || 0)}</span>
                    </div>
                    <div class="job-metric">
                        <span class="job-metric__label">Net Profit</span>
                        <span class="job-metric__value job-metric__value--green">${fmt(job.net_profit || 0)}</span>
                    </div>
                    <div class="job-metric">
                        <span class="job-metric__label">Time (traffic)</span>
                        <span class="job-metric__value">${Math.round(job.estimated_time_mins || 0)} min</span>
                    </div>
                    <div class="job-metric">
                        <span class="job-metric__label">₹/Hour</span>
                        <span class="job-metric__value ${isWinner ? 'job-metric__value--highlight' : ''}">${fmt(job.effective_hourly_rate || 0)}</span>
                    </div>
                    <div class="job-metric">
                        <span class="job-metric__label">₹/KM</span>
                        <span class="job-metric__value">${fmt(job.profit_per_km || 0)}</span>
                    </div>
                </div>
                ${(job.pros && job.pros.length > 0) ? `
                <div class="job-analysis-card__pros">
                    ${job.pros.map(p => `<span class="job-tag job-tag--green"><span class="material-icons-round">check_circle</span> ${p}</span>`).join('')}
                </div>` : ''}
                ${(job.cons && job.cons.length > 0) ? `
                <div class="job-analysis-card__cons">
                    ${job.cons.map(c => `<span class="job-tag job-tag--red"><span class="material-icons-round">cancel</span> ${c}</span>`).join('')}
                </div>` : ''}
            </div>`;
        });

        comparisonEl.innerHTML = html;

        // Tip
        const tipEl = document.getElementById('job-tip');
        const tipText = document.getElementById('job-tip-text');
        if (data.tip) {
            tipEl.style.display = '';
            tipText.textContent = data.tip;
        } else {
            tipEl.style.display = 'none';
        }

        // Scroll into view
        resultsEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    },

    /**
     * Initialize all event listeners
     */
    init() {
        const compareBtn = document.getElementById('job-compare-btn');
        const notifInput = document.getElementById('notif-paste-input');
        const charCount = document.getElementById('notif-char-count');
        const sampleBtn = document.getElementById('notif-paste-sample');
        const simBtn = document.getElementById('notif-simulate-btn');

        // ── Mode tabs ──
        document.querySelectorAll('.job-mode-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.job-mode-tab').forEach(t => t.classList.remove('job-mode-tab--active'));
                tab.classList.add('job-mode-tab--active');

                const mode = tab.dataset.mode;
                this.currentMode = mode;

                document.getElementById('job-mode-paste').style.display = mode === 'paste' ? '' : 'none';
                document.getElementById('job-mode-simulate').style.display = mode === 'simulate' ? '' : 'none';

                // Clear results when switching
                document.getElementById('job-results').style.display = 'none';
                this.clearError();
            });
        });

        // ── Char count for paste area ──
        notifInput?.addEventListener('input', () => {
            const len = notifInput.value.length;
            charCount.textContent = len.toLocaleString('en-IN') + ' chars';
        });

        // ── Load sample button ──
        sampleBtn?.addEventListener('click', () => {
            notifInput.value = this.getSampleNotifications();
            charCount.textContent = notifInput.value.length.toLocaleString('en-IN') + ' chars';
            notifInput.focus();
        });

        // ── Simulate button ──
        simBtn?.addEventListener('click', () => {
            this.simulateNotifications();
        });

        // ── Compare button — the main action ──
        compareBtn?.addEventListener('click', async () => {
            this.clearError();

            const apiKey = document.getElementById('api-key-input')?.value?.trim();
            if (!apiKey) {
                this.showError('Please paste your Groq API key first.');
                return;
            }

            // Step 1: If in paste mode and no jobs extracted yet, parse first
            if (this.currentMode === 'paste' && this.extractedJobs.length < 2) {
                compareBtn.classList.add('job-compare-btn--loading');
                compareBtn.querySelector('.job-compare-btn__loader').innerHTML =
                    '<span class="spinner"></span> Extracting jobs from notifications...';
                compareBtn.disabled = true;

                const parsed = await this.parseNotificationText();
                if (!parsed) {
                    compareBtn.classList.remove('job-compare-btn--loading');
                    compareBtn.disabled = false;
                    return;
                }
            }

            // Step 2: Check we have enough jobs
            if (this.extractedJobs.length < 2) {
                this.showError('Need at least 2 job offers to compare. Add more notifications.');
                return;
            }

            // Step 3: Call compare API
            compareBtn.classList.add('job-compare-btn--loading');
            compareBtn.querySelector('.job-compare-btn__loader').innerHTML =
                '<span class="spinner"></span> AI comparing jobs...';
            compareBtn.disabled = true;

            try {
                const response = await fetch('http://localhost:5000/api/compare-jobs', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ api_key: apiKey, jobs: this.extractedJobs }),
                });

                if (!response.ok) {
                    const err = await response.json().catch(() => ({}));
                    throw new Error(err.error || `Server error (${response.status})`);
                }

                const result = await response.json();
                this.renderResults(result);

            } catch (err) {
                console.error('[JobPicker]', err);
                let msg = err.message || 'Something went wrong.';
                if (msg.includes('401')) msg = 'Invalid API key. Check and try again.';
                else if (msg.includes('429')) msg = 'Rate limit hit. Wait a moment and retry.';
                else if (msg.includes('Failed to fetch')) msg = 'Backend not running. Start the server first.';
                this.showError(msg);
            } finally {
                compareBtn.classList.remove('job-compare-btn--loading');
                compareBtn.querySelector('.job-compare-btn__loader').innerHTML =
                    '<span class="spinner"></span> AI Analyzing...';
                compareBtn.disabled = false;
            }
        });
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    JobPicker.init();
    console.log('[returnX] Smart Job Picker loaded ✓ (notification-based)');
});
