// Backend API URL
const API_URL = 'http://localhost:8000/api/v1';

// Mock lexicons removed - using Backend API


// Animation on load
window.addEventListener('load', () => {
    const demo = document.getElementById('animationDemo');
    const words = ['nagbasa', 'basa'];
    let i = 0;
    setInterval(() => {
        demo.textContent = words[i % 2] + (i % 2 === 0 ? ' →' : '');
        i++;
    }, 1500);
});

// Page navigation
function showPage(pageId) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Global variables for mismatch handling
let pendingMismatchData = null;

// Main lemmatize function
function lemmatize() {
    const input = document.getElementById('userInput').value.trim();
    const dialect = document.getElementById('dialectSelect').value;

    // Reset force state for new requests unless explicitly set
    if (!window.isRetryingForced) {
        window.lastForceState = false;
    }
    window.isRetryingForced = false;

    if (!input) {
        alert('Please enter some text to lemmatize.');
        return;
    }

    // Get settings
    const mode = document.getElementById('settingsMode').value;
    const outputFormat = document.getElementById('outputFormat') ? document.getElementById('outputFormat').value : 'table';
    const showToken = document.getElementById('chkToken').checked;
    const showPOS = document.getElementById('chkPOS').checked;
    const showType = document.getElementById('chkType').checked;
    const showAffixes = document.getElementById('chkAffixes').checked;
    const showStripped = document.getElementById('chkStripped').checked;
    const showLemma = document.getElementById('chkLemma').checked;

    // Show loading state
    const resultsBody = document.getElementById('resultsBody');
    resultsBody.innerHTML = '<tr><td colspan="5" style="text-align:center;">Processing...</td></tr>';

    // Call Backend API
    fetch(`${API_URL}/lemmatize`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            text: input,
            dialect: dialect, // API requires specific dialect
            mode: mode,
            force: window.lastForceState || false
        })
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Check for dialect mismatch (driven by backend)
            if (data.status === 'error' && data.error_code === 'DIALECT_MISMATCH') {
                // Store data for "Continue" action
                pendingMismatchData = {
                    input,
                    data: null, // No results yet, will re-fetch if forced
                    settings: { mode, outputFormat, showToken, showPOS, showType, showAffixes, showLemma, showStripped },
                    detected: data.detected_dialect,
                    forced: false
                };

                // The backend now provides real confidence scores
                showMismatchModal(dialect, data.detected_dialect, data.confidence_scores);

                // Clear loading state
                resultsBody.innerHTML = '<tr><td colspan="5" style="text-align:center;">Paused (Mismatch Detected)</td></tr>';
                return;
            }

            // Proceed with rendering results (extracted to helper for reuse)
            renderResults(data, { outputFormat, showToken, showPOS, showType, showAffixes, showLemma, showStripped, dialect, input, mode });
        })
        .catch(error => {
            console.error('Error:', error);
            resultsBody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:red;">Error processing text. Ensure backend is running.</td></tr>';
        });
}

// Render Results Helper
function renderResults(data, config) {
    const results = [];
    // Flatten nested sentences structure from API
    data.sentences.forEach(sentence => {
        sentence.forEach(tokenData => {
            results.push({
                token: tokenData.token,
                pos: tokenData.pos,
                type: tokenData.type,
                affixes: tokenData.affixes,
                lemma: tokenData.root,
                irregular: tokenData.type === 'irregular',
                stripped: tokenData.stripped || '-'
            });
        });
    });

    // Update summary
    const detectedDialect = (data.dialect || config.dialect).charAt(0).toUpperCase() + (data.dialect || config.dialect).slice(1);
    document.getElementById('detectedDialect').textContent = detectedDialect;
    document.getElementById('tokensProcessed').textContent = results.length;
    document.getElementById('totalLemmas').textContent = results.length; // Simplified count
    document.getElementById('irregularWords').textContent = results.filter(r => r.irregular).length;

    if (config.outputFormat === 'text') {
        document.getElementById('resultsTableContainer').style.display = 'none';
        document.getElementById('resultsText').style.display = 'block';

        let textReport = 'UGAT ANALYSIS REPORT\n';
        textReport += '====================\n';
        textReport += `Dialect: ${detectedDialect}\n`;
        textReport += `Total Tokens: ${results.length}\n`;
        textReport += '--------------------\n\n';

        results.forEach((r, index) => {
            textReport += `${index + 1}. Token:   ${r.token}\n`;
            if (config.showPOS) textReport += `   POS Tag: ${r.pos}\n`;
            if (config.showType) textReport += `   Type:    ${r.type}\n`;
            if (config.showAffixes) textReport += `   Affixes: ${r.affixes.join(', ') || '-'}\n`;
            if (config.showStripped) textReport += `   Stripped: ${r.stripped}\n`;
            if (config.showLemma) textReport += `   Lemma:   ${r.lemma}\n`;
            textReport += '\n';
        });

        document.getElementById('resultsText').textContent = textReport;
    } else {
        document.getElementById('resultsTableContainer').style.display = 'block';
        document.getElementById('resultsText').style.display = 'none';
        const resultsBody = document.getElementById('resultsBody');

        // Manage Table Headers
        document.getElementById('thToken').style.display = config.showToken ? '' : 'none';
        document.getElementById('thPOS').style.display = config.showPOS ? '' : 'none';
        document.getElementById('thType').style.display = config.showType ? '' : 'none';
        document.getElementById('thAffixes').style.display = config.showAffixes ? '' : 'none';
        document.getElementById('thStripped').style.display = config.showStripped ? '' : 'none';
        document.getElementById('thLemma').style.display = config.showLemma ? '' : 'none';

        // Populate results table
        resultsBody.innerHTML = '';
        results.forEach(r => {
            const row = resultsBody.insertRow();
            let html = '';
            if (config.showToken) html += `<td><strong>${r.token}</strong></td>`;
            if (config.showPOS) html += `<td>${r.pos}</td>`;
            if (config.showType) html += `<td>${r.type}</td>`;
            if (config.showAffixes) html += `<td>${r.affixes.join(', ') || '-'}</td>`;
            if (config.showStripped) html += `<td>${r.stripped}</td>`;
            if (config.showLemma) html += `<td><span class="lemma-highlight">${r.lemma}</span></td>`;
            row.innerHTML = html;
        });
    }

    // Populate breakdown
    const breakdownContent = document.getElementById('breakdownContent');
    breakdownContent.innerHTML = '';
    results.forEach(r => {
        if (r.affixes && r.affixes.length > 0) {
            const item = document.createElement('div');
            item.className = 'breakdown-item';
            item.innerHTML = `
            <h3>Word: ${r.token}</h3>
            <div class="breakdown-details">
                <div class="detail-item">
                    <div class="detail-label">Affixes</div>
                    <div class="detail-value">${r.affixes.join(', ')}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Root</div>
                    <div class="detail-value">${r.lemma}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">POS</div>
                    <div class="detail-value">${r.pos}</div>
                </div>
            </div>
        `;
            breakdownContent.appendChild(item);
        }
    });

    // Show success modal
    showSuccessModal(results.length, results.length);

    // Save to history
    saveToHistory(config.input, results, detectedDialect);

    // Store for export/logging
    window.lastAnalysisData = {
        settings: {
            dialect: config.dialect === 'auto' ? 'hiligaynon' : config.dialect,
            mode: config.mode,
            outputFormat: config.outputFormat,
            showToken: config.showToken,
            showPOS: config.showPOS,
            showType: config.showType,
            showAffixes: config.showAffixes,
            showLemma: config.showLemma,
            timestamp: new Date().toISOString()
        },
        input: config.input,
        results: results
    };

    // Log to console as requested
    console.log("--- Ugat Analysis Data ---");
    console.log(window.lastAnalysisData);
    console.log("--------------------------");
}

// Show success modal
function showSuccessModal(tokenCount, lemmaCount) {
    const modal = document.getElementById('successModal');
    document.getElementById('modalTokens').textContent = tokenCount;
    document.getElementById('modalLemmas').textContent = lemmaCount;
    modal.classList.add('show');
}

// Close success modal and scroll to results
function closeSuccessModal() {
    const modal = document.getElementById('successModal');
    modal.classList.remove('show');

    // Show results section
    document.getElementById('resultsSection').style.display = 'block';

    // Scroll to results
    setTimeout(() => {
        document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
    }, 300);
}



// Save to history
function saveToHistory(text, results, dialect) {
    const lemmas = [...new Set(results.map(r => r.lemma))].join(', ');
    const historyContent = document.getElementById('historyContent');

    const item = document.createElement('div');
    item.className = 'history-item';
    item.innerHTML = `
        <div class="history-text">"${text}"</div>
        <div class="history-meta">→ lemmas: ${lemmas} (${dialect}) • Just now</div>
    `;

    historyContent.insertBefore(item, historyContent.firstChild);
}

// Lexicon tab switching
async function showLexiconTab(tab) {
    window.currentLexiconTab = tab; // Store state
    const content = document.getElementById('lexiconTableContent');
    content.innerHTML = '<div style="text-align:center; padding: 2rem;">Loading lexicon data...</div>';

    // Get selected dialect filter
    const filterSelect = document.getElementById('lexiconDialectFilter');
    const selectedDialect = filterSelect ? filterSelect.value : 'ilocano';

    let dialects = ['ilocano', 'cebuano', 'hiligaynon'];

    // If specific dialect selected, only fetch that one
    if (selectedDialect && selectedDialect !== 'all') {
        dialects = [selectedDialect];
    }

    // Parallel fetch for chosen dialects
    const requests = dialects.map(d =>
        fetch(`${API_URL}/lexicon?type=${tab}&dialect=${d}&page_size=5000`)
            .then(res => {
                if (!res.ok) throw new Error(`Failed to fetch ${d}`);
                return res.json();
            })
            .then(data => ({ dialect: d, items: data.items }))
            .catch(err => ({ dialect: d, items: [], error: err }))
    );

    try {
        const results = await Promise.all(requests);
        let allItems = [];

        // Aggregate results
        results.forEach(r => {
            if (r.items) {
                r.items.forEach(item => {
                    item._dialect = r.dialect; // Tag with dialect
                    allItems.push(item);
                });
            }
        });

        // Sort by term
        allItems.sort((a, b) => a.term.localeCompare(b.term));

        // Create table inside scroll container
        let tableHtml = '<div class="table-scroll-container"><table>';

        if (tab === 'roots') {
            tableHtml += `
                <thead>
                    <tr>
                        <th>Word</th>
                        <th>Dialect</th>
                        <th>POS</th>
                    </tr>
                </thead>
                <tbody>`;

            if (allItems.length === 0) {
                tableHtml += '<tr><td colspan="3" style="text-align:center;">No data found.</td></tr>';
            } else {
                allItems.forEach(item => {
                    const pos = typeof item.details === 'string' ? item.details : (item.details.pos || JSON.stringify(item.details));
                    tableHtml += `
                        <tr>
                            <td>${item.term}</td>
                            <td style="text-transform: capitalize;">${item._dialect}</td>
                            <td>${pos}</td>
                        </tr>`;
                });
            }

        } else if (tab === 'irregular') {
            tableHtml += `
                <thead>
                    <tr>
                        <th>Word</th>
                        <th>Equivalent</th>
                        <th>POS</th>
                    </tr>
                </thead>
                <tbody>`;

            if (allItems.length === 0) {
                tableHtml += '<tr><td colspan="3" style="text-align:center;">No data found.</td></tr>';
            } else {
                allItems.forEach(item => {
                    const equiv = item.details.equivalent || '-';
                    const pos = item.details.pos || '-';
                    tableHtml += `
                        <tr>
                            <td>${item.term}</td>
                            <td>${equiv}</td>
                            <td>${pos}</td>
                        </tr>`;
                });
            }

        } else if (tab === 'affixes') {
            tableHtml += `
                <thead>
                    <tr>
                        <th>Affix</th>
                        <th>Type</th>
                        <th>Dialect</th>
                    </tr>
                </thead>
                <tbody>`;

            if (allItems.length === 0) {
                tableHtml += '<tr><td colspan="3" style="text-align:center;">No data found.</td></tr>';
            } else {
                allItems.forEach(item => {
                    const type = item.metadata.affix_type || '-';
                    tableHtml += `
                        <tr>
                            <td>${item.term}</td>
                            <td>${type}</td>
                            <td style="text-transform: capitalize;">${item._dialect}</td>
                        </tr>`;
                });
            }
        }

        tableHtml += '</tbody></table></div>'; // Close scroll container
        content.innerHTML = tableHtml;

    } catch (error) {
        console.error('Error fetching lexicon:', error);
        content.innerHTML = `<div style="text-align:center; color:red; padding: 2rem;">Error loading data: ${error.message}</div>`;
    }
}

// Search functionality for lexicon
document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('lexiconSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function (e) {
            const query = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('#lexiconTableContent tbody tr');

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(query) ? '' : 'none';
            });
        });
    }

    // Dialect Filter Event Listener
    const dialectFilter = document.getElementById('lexiconDialectFilter');
    if (dialectFilter) {
        dialectFilter.addEventListener('change', function () {
            // Re-fetch/render current active tab with new filter
            if (window.currentLexiconTab) {
                showLexiconTab(window.currentLexiconTab);
            } else {
                showLexiconTab('roots');
            }
        });
    }

    // Auto-load Ilocano root words on page load
    showLexiconTab('roots');
});

// --- Mismatch Modal Helper Functions ---

function showMismatchModal(currentDialect, suggestedDialect, probabilities) {
    const modal = document.getElementById('mismatchModal');

    // Update Text
    document.getElementById('selectedDialectDisplay').textContent = capitalize(currentDialect);

    // Update Action Buttons
    document.getElementById('btnSuggestedName').textContent = capitalize(suggestedDialect);
    document.getElementById('btnCurrentName').textContent = capitalize(currentDialect);

    // Visualization
    const container = document.getElementById('confidenceContainer');
    container.innerHTML = '';

    // Sort probabilities
    const sorted = Object.entries(probabilities || {}).sort(([, a], [, b]) => b - a);

    sorted.forEach(([d, score]) => {
        const percentage = Math.round(score); // Backend already sends 0-100
        const isSuggested = d === suggestedDialect;

        const item = document.createElement('div');
        item.className = `confidence-item ${isSuggested ? 'suggested' : ''}`;
        item.innerHTML = `
            <div class="conf-row">
                <span>${capitalize(d)}</span>
                <span>${percentage}%</span>
            </div>
            <div class="conf-bar-bg">
                <div class="conf-bar-fill" style="width: 0%"></div>
            </div>
        `;
        container.appendChild(item);

        // Animate bar
        setTimeout(() => {
            item.querySelector('.conf-bar-fill').style.width = `${percentage}%`;
        }, 100);
    });

    modal.classList.add('show');
}

function keepCurrentDialect() {
    if (pendingMismatchData) {
        // Set flags to force the next request
        window.lastForceState = true;
        window.isRetryingForced = true;

        // Re-run processing (this time it will force)
        lemmatize();

        // Clear pending
        pendingMismatchData = null;
    }
    closeMismatchModal();
}

function switchToSuggested() {
    if (pendingMismatchData) {
        const newDialect = pendingMismatchData.detected;

        // Update UI
        document.getElementById('dialectSelect').value = newDialect;

        // Re-run processing with new dialect
        closeMismatchModal();
        setTimeout(lemmatize, 100); // Small delay to allow UI update

        pendingMismatchData = null;
    }
}

function cancelProcessing() {
    pendingMismatchData = null;
    closeMismatchModal();
    // Clear loading state
    document.getElementById('resultsBody').innerHTML = '';
}

function closeMismatchModal() {
    document.getElementById('mismatchModal').classList.remove('show');
}

function capitalize(s) {
    if (!s) return '';
    return s.charAt(0).toUpperCase() + s.slice(1);
}
