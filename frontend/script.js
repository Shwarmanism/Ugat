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

// Main lemmatization function
function lemmatize() {
    const input = document.getElementById('userInput').value.trim();
    const dialect = document.getElementById('dialectSelect').value;

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
            mode: mode
        })
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
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
            const detectedDialect = data.dialect.charAt(0).toUpperCase() + data.dialect.slice(1);
            document.getElementById('detectedDialect').textContent = detectedDialect;
            document.getElementById('tokensProcessed').textContent = results.length;
            document.getElementById('totalLemmas').textContent = results.length; // Simplified count
            document.getElementById('irregularWords').textContent = results.filter(r => r.irregular).length;

            if (outputFormat === 'text') {
                document.getElementById('resultsTableContainer').style.display = 'none';
                document.getElementById('resultsText').style.display = 'block';

                let textReport = 'UGAT ANALYSIS REPORT\n';
                textReport += '====================\n';
                textReport += `Dialect: ${detectedDialect}\n`;
                textReport += `Total Tokens: ${results.length}\n`;
                textReport += '--------------------\n\n';

                results.forEach((r, index) => {
                    textReport += `${index + 1}. Token:   ${r.token}\n`;
                    if (showPOS) textReport += `   POS Tag: ${r.pos}\n`;
                    if (showType) textReport += `   Type:    ${r.type}\n`;
                    if (showAffixes) textReport += `   Affixes: ${r.affixes.join(', ') || '-'}\n`;
                    if (showStripped) textReport += `   Stripped: ${r.stripped}\n`;
                    if (showLemma) textReport += `   Lemma:   ${r.lemma}\n`;
                    textReport += '\n';
                });

                document.getElementById('resultsText').textContent = textReport;
            } else {
                document.getElementById('resultsTableContainer').style.display = 'block';
                document.getElementById('resultsText').style.display = 'none';

                // Manage Table Headers
                document.getElementById('thToken').style.display = showToken ? '' : 'none';
                document.getElementById('thPOS').style.display = showPOS ? '' : 'none';
                document.getElementById('thType').style.display = showType ? '' : 'none';
                document.getElementById('thAffixes').style.display = showAffixes ? '' : 'none';
                document.getElementById('thStripped').style.display = showStripped ? '' : 'none';
                document.getElementById('thLemma').style.display = showLemma ? '' : 'none';

                // Populate results table
                resultsBody.innerHTML = '';
                results.forEach(r => {
                    const row = resultsBody.insertRow();
                    let html = '';
                    if (showToken) html += `<td><strong>${r.token}</strong></td>`;
                    if (showPOS) html += `<td>${r.pos}</td>`;
                    if (showType) html += `<td>${r.type}</td>`;
                    if (showAffixes) html += `<td>${r.affixes.join(', ') || '-'}</td>`;
                    if (showStripped) html += `<td>${r.stripped}</td>`;
                    if (showLemma) html += `<td><span class="lemma-highlight">${r.lemma}</span></td>`;
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
            saveToHistory(input, results, detectedDialect);

            // Store for export/logging
            window.lastAnalysisData = {
                settings: {
                    dialect: dialect === 'auto' ? 'hiligaynon' : dialect,
                    mode: mode,
                    outputFormat: outputFormat,
                    showToken: showToken,
                    showPOS: showPOS,
                    showType: showType,
                    showAffixes: showAffixes,
                    showLemma: showLemma,
                    timestamp: new Date().toISOString()
                },
                input: input,
                results: results
            };

            // Log to console as requested
            console.log("--- Ugat Analysis Data ---");
            console.log(window.lastAnalysisData);
            console.log("--------------------------");
        })
        .catch(error => {
            console.error('Error:', error);
            resultsBody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:red;">Error processing text. Ensure backend is running.</td></tr>';
            alert('Error connecting to backend server.');
        });
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
    const selectedDialect = filterSelect ? filterSelect.value : 'all';

    let dialects = ['ilocano', 'cebuano', 'hiligaynon'];

    // If specific dialect selected, only fetch that one
    if (selectedDialect && selectedDialect !== 'all') {
        dialects = [selectedDialect];
    }

    // Parallel fetch for chosen dialects
    const requests = dialects.map(d =>
        fetch(`${API_URL}/lexicon?type=${tab}&dialect=${d}&page_size=1000`)
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
});