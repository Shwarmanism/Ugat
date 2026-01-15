
//Page Nav and UI
window.addEventListener('load', () => {
    const demo = document.getElementById('animationDemo');
    if (demo) {
        const words = ['nagbasa', 'basa'];
        let i = 0;
        setInterval(() => {
            demo.textContent = words[i % 2] + (i % 2 === 0 ? ' →' : '');
            i++;
        }, 1500);
    }
    
    // Initialize default lexicon view
    showLexiconTab('roots');
});


function showPage(pageId) {
    // 1. Remove 'active' class from all pages
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    
    // 2. Add 'active' class to the clicked page
    const target = document.getElementById(pageId);
    if (target) {
        target.classList.add('active');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
        console.error(`Page ID '${pageId}' not found in HTML.`);
    }

   
    document.querySelectorAll('.nav-links a').forEach(link => {
        link.classList.remove('active');
        if(link.getAttribute('onclick') && link.getAttribute('onclick').includes(pageId)) {
            link.classList.add('active');
        }
    });
}

//Backend Connection

async function lemmatize() {
    const input = document.getElementById('userInput').value.trim();
    const dialect = document.getElementById('dialectSelect').value;

    if (!input) {
        alert('Please enter some text to lemmatize.');
        return;
    }

    // A. Construct JSON Payload
    const payload = {
        input_text: input,
        dialect: dialect,
        settings: {
            show_details: {
                // Check if these checkboxes exist, otherwise default to true/false
                pos_tags: document.getElementById('showPOS') ? document.getElementById('showPOS').checked : true,
                candidates: document.getElementById('showCandidates') ? document.getElementById('showCandidates').checked : true,
                rules: document.getElementById('showRules') ? document.getElementById('showRules').checked : true,
                lexicon_match: document.getElementById('showLexicon') ? document.getElementById('showLexicon').checked : true
            },
            preprocessing: {
                remove_punctuation: document.getElementById('removePunctuation') ? document.getElementById('removePunctuation').checked : true,
                normalize_caps: document.getElementById('normalizeCaps') ? document.getElementById('normalizeCaps').checked : true,
                remove_numbers: document.getElementById('removeNumbers') ? document.getElementById('removeNumbers').checked : false
            },
            output_format: document.getElementById('outputFormat') ? document.getElementById('outputFormat').value : 'json'
        }
    };

    console.log("Sending Payload:", payload);

    try {
        // B. Loading State
        const btn = document.querySelector('.btn-center .btn') || document.querySelector('button[onclick="lemmatize()"]');
        const originalText = btn ? btn.innerText : 'Lemmatize';
        if(btn) {
            btn.innerText = "Processing...";
            btn.disabled = true;
        }

        // C. Connect to Backend
        const response = await fetch('http://localhost:8000/api/lemmatize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();
        console.log("Received Data:", data);
        console.log(JSON.stringify(data, null, 2));

        // D. Update UI with Real Data
        updateUIWithBackendData(data, dialect, input);

    } catch (error) {
        console.error('Error:', error);
        alert('Failed to connect to backend. Is "uvicorn main:app" running?');
    } finally {
        // Reset Button
        const btn = document.querySelector('.btn-center .btn') || document.querySelector('button[onclick="lemmatize()"]');
        if(btn) {
            btn.innerText = "Lemmatize";
            btn.disabled = false;
        }
    }
}

// UI update (Filling Tables and Results)

function updateUIWithBackendData(data, selectedDialect, originalInput) {
    // 1. Update Summary Stats
    const detectedDialect = selectedDialect === 'auto' ? (data.detected_dialect || 'Hiligaynon') : selectedDialect;
    
    // Helper to safely set text content
    const setText = (id, val) => { const el = document.getElementById(id); if(el) el.textContent = val; };
    
    setText('detectedDialect', detectedDialect.charAt(0).toUpperCase() + detectedDialect.slice(1));
    setText('tokensProcessed', data.stats.tokens);
    setText('totalLemmas', data.stats.lemmas);
    setText('irregularWords', data.stats.irregulars);

    // 2. Populate Results Table
    const tbody = document.getElementById('resultsBody');
    if (tbody) {
        tbody.innerHTML = '';
        data.results.forEach(r => {
            const row = tbody.insertRow();
            
            // Handle arrays vs strings
            const affixes = Array.isArray(r.affixes) ? r.affixes.join(', ') : (r.affixes || '-');
            const candidates = Array.isArray(r.candidates) ? r.candidates.join(', ') : (r.candidates || '-');
            const lemma = r.lemma || r.root || 'unk';
            const pos = r.pos || 'Verb'; // Default to verb if missing

            row.innerHTML = `
                <td><strong>${r.token}</strong></td>
                <td>${pos}</td>
                <td>${affixes}</td>
                <td>${candidates}</td>
                <td><span class="lemma-highlight">${lemma}</span></td>
            `;
        });
    }

    // 3. Populate Breakdown Cards
    const breakdownContent = document.getElementById('breakdownContent');
    if (breakdownContent) {
        breakdownContent.innerHTML = '';
        data.results.forEach(r => {
            // Show breakdown if it has affixes OR is irregular
            if ((r.affixes && r.affixes.length > 0) || r.is_irregular) {
                const item = document.createElement('div');
                item.className = 'breakdown-item';
                
                const affixesStr = Array.isArray(r.affixes) ? r.affixes.join(', ') : (r.affixes || 'None');
                const ruleStr = r.is_irregular ? 'Irregular Lookup' : 'Affix Stripping';
                
                item.innerHTML = `
                    <h3>Word: ${r.token}</h3>
                    <div class="breakdown-details">
                        <div class="detail-item">
                            <div class="detail-label">Affixes</div>
                            <div class="detail-value">${affixesStr}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Root</div>
                            <div class="detail-value">${r.lemma}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">POS</div>
                            <div class="detail-value">${r.pos || 'Verb'}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Rule Applied</div>
                            <div class="detail-value">${ruleStr}</div>
                        </div>
                    </div>
                `;
                breakdownContent.appendChild(item);
            }
        });
    }

    // 4. Show Success Modal
    showSuccessModal(data.stats.tokens, data.stats.lemmas);

    // 5. Save to History (Using your original DOM-based approach)
    saveToHistory(originalInput, data.results, detectedDialect);
}

// History

function saveToHistory(text, results, dialect) {
    const historyContent = document.getElementById('historyContent');
    if (!historyContent) return;

    // Create a simple comma-separated list of lemmas
    const lemmas = [...new Set(results.map(r => r.lemma))].join(', ');
    
    const item = document.createElement('div');
    item.className = 'history-item';
    
    // This HTML structure matches your CSS for history items
    item.innerHTML = `
        <div class="history-text">"${text}"</div>
        <div class="history-meta">→ lemmas: ${lemmas} (${dialect}) • Just now</div>
    `;
    
    // Insert at the top
    historyContent.insertBefore(item, historyContent.firstChild);
}

function showSuccessModal(tokenCount, lemmaCount) {
    const modal = document.getElementById('successModal');
    if (modal) {
        const tCount = document.getElementById('modalTokens');
        const lCount = document.getElementById('modalLemmas');
        if(tCount) tCount.textContent = tokenCount;
        if(lCount) lCount.textContent = lemmaCount;
        
        // Your original code used .add('show'), assuming CSS handles the display
        modal.classList.add('show');
        // Fallback in case your CSS relies on display:flex
        modal.style.display = 'flex'; 
    }
}

function closeSuccessModal() {
    const modal = document.getElementById('successModal');
    if (modal) {
        modal.classList.remove('show');
        modal.style.display = 'none';
    }
    
    // Show results section
    const resultsSection = document.getElementById('resultsSection');
    if (resultsSection) {
        resultsSection.style.display = 'block';
        setTimeout(() => {
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        }, 300);
    }
}

// Lexicon Tabs

function showLexiconTab(tab) {
    // Highlight the active button
    const buttons = document.querySelectorAll('.tab-btn');
    buttons.forEach(btn => {
        if(btn.innerText.toLowerCase().includes(tab) || btn.getAttribute('onclick').includes(tab)) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    const content = document.getElementById('lexiconTableContent');
    if (!content) return;

    // Your static table HTML
    if (tab === 'roots') {
        content.innerHTML = `
            <table>
                <thead>
                    <tr><th>Word</th><th>Dialect</th><th>POS</th><th>Notes</th></tr>
                </thead>
                <tbody>
                    <tr><td>basa</td><td>Hiligaynon</td><td>Verb</td><td>Root word: to read</td></tr>
                    <tr><td>lakad</td><td>Hiligaynon</td><td>Verb</td><td>Root word: to walk</td></tr>
                    <tr><td>bata</td><td>Hiligaynon</td><td>Noun</td><td>Root word: child</td></tr>
                    <tr><td>kaon</td><td>Cebuano</td><td>Verb</td><td>Root word: to eat</td></tr>
                    <tr><td>pan</td><td>Ilocano</td><td>Verb</td><td>Root word: to go</td></tr>
                </tbody>
            </table>
        `;
    } else if (tab === 'irregular') {
        content.innerHTML = `
            <table>
                <thead>
                    <tr><th>Irregular Form</th><th>Lemma</th><th>Dialect</th><th>Notes</th></tr>
                </thead>
                <tbody>
                    <tr><td>pumunta</td><td>punta</td><td>Hiligaynon</td><td>Irregular verb: to go</td></tr>
                    <tr><td>kumain</td><td>kain</td><td>Hiligaynon</td><td>Irregular verb: to eat</td></tr>
                    <tr><td>uminom</td><td>inom</td><td>Hiligaynon</td><td>Irregular verb: to drink</td></tr>
                </tbody>
            </table>
        `;
    } else if (tab === 'affixes') {
        content.innerHTML = `
            <table>
                <thead>
                    <tr><th>Affix</th><th>Type</th><th>Dialect</th><th>Function</th></tr>
                </thead>
                <tbody>
                    <tr><td>nag-</td><td>Prefix</td><td>Hiligaynon</td><td>Past tense marker</td></tr>
                    <tr><td>-um-</td><td>Infix</td><td>Hiligaynon</td><td>Actor focus marker</td></tr>
                    <tr><td>mi-</td><td>Prefix</td><td>Cebuano</td><td>Past tense marker</td></tr>
                    <tr><td>ag-</td><td>Prefix</td><td>Ilocano</td><td>Action marker</td></tr>
                </tbody>
            </table>
        `;
    }
}

// Search functionality for lexicon
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('lexiconSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const query = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('#lexiconTableContent tbody tr');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(query) ? '' : 'none';
            });
        });
    }
});