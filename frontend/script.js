// Mock lexicons and rules for demonstration
const mockLexicon = {
    tagalog: {
        roots: ['basa', 'lakad', 'bata', 'saya', 'labas', 'laro', 'kain', 'inom', 'punta'],
        irregular: {
            'pumunta': 'punta',
            'kumain': 'kain',
            'uminom': 'inom'
        },
        affixes: {
            prefixes: ['nag', 'mag', 'um', 'ma', 'ka', 'pa', 'na'],
            suffixes: ['an', 'in', 'han'],
            infixes: ['um', 'in']
        }
    },
    cebuano: {
        roots: ['kaon', 'bugas', 'tubig', 'balay'],
        irregular: {},
        affixes: {
            prefixes: ['nag', 'mag', 'mi', 'mo'],
            suffixes: ['an', 'on'],
            infixes: ['um']
        }
    },
    ilocano: {
        roots: ['pan', 'merkado', 'balay', 'danum'],
        irregular: {},
        affixes: {
            prefixes: ['nag', 'ag', 'um', 'ma'],
            suffixes: ['an', 'en'],
            infixes: ['um', 'in']
        }
    }
};

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

    // Mock processing
    const tokens = input.toLowerCase().replace(/[.,!?]/g, '').split(/\s+/);
    const results = tokens.map(token => processToken(token, dialect));

    // Update summary
    const detectedDialect = dialect === 'auto' ? 'Tagalog' : dialect.charAt(0).toUpperCase() + dialect.slice(1);
    document.getElementById('detectedDialect').textContent = detectedDialect;
    document.getElementById('tokensProcessed').textContent = tokens.length;
    document.getElementById('totalLemmas').textContent = results.length;
    document.getElementById('irregularWords').textContent = results.filter(r => r.irregular).length;

    // Populate results table
    const tbody = document.getElementById('resultsBody');
    tbody.innerHTML = '';
    results.forEach(r => {
        const row = tbody.insertRow();
        row.innerHTML = `
            <td><strong>${r.token}</strong></td>
            <td>${r.pos}</td>
            <td>${r.affixes.join(', ') || 'none'}</td>
            <td>${r.candidates.join(', ')}</td>
            <td><span class="lemma-highlight">${r.lemma}</span></td>
        `;
    });

    // Populate breakdown
    const breakdownContent = document.getElementById('breakdownContent');
    breakdownContent.innerHTML = '';
    results.forEach(r => {
        if (r.affixes.length > 0) {
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
                    <div class="detail-item">
                        <div class="detail-label">Rule Applied</div>
                        <div class="detail-value">${r.rule}</div>
                    </div>
                </div>
            `;
            breakdownContent.appendChild(item);
        }
    });

    // Show success modal
    showSuccessModal(tokens.length, results.length);

    // Save to history
    saveToHistory(input, results, detectedDialect);
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

// Process individual token
function processToken(token, dialect) {
    // Determine dialect lexicon
    const dialectKey = dialect === 'auto' ? 'tagalog' : dialect;
    const lexicon = mockLexicon[dialectKey] || mockLexicon.tagalog;
    
    let lemma = token;
    let affixes = [];
    let candidates = [];
    let irregular = false;

    // Check irregular
    if (lexicon.irregular[token]) {
        lemma = lexicon.irregular[token];
        irregular = true;
        candidates.push(lemma);
    } else {
        // Strip prefixes
        for (let prefix of lexicon.affixes.prefixes) {
            if (token.startsWith(prefix)) {
                affixes.push(prefix + '-');
                lemma = token.substring(prefix.length);
                break;
            }
        }

        // Strip suffixes
        for (let suffix of lexicon.affixes.suffixes) {
            if (lemma.endsWith(suffix)) {
                affixes.push('-' + suffix);
                lemma = lemma.substring(0, lemma.length - suffix.length);
                break;
            }
        }

        candidates.push(lemma);

        // Check if in lexicon, if not, use original token
        if (!lexicon.roots.includes(lemma)) {
            candidates.push(token);
            // Keep the lemma as processed, or fallback to token if preferred
        }
    }

    return {
        token,
        lemma,
        pos: 'Verb', // Mock POS - in real system, this would be determined by POS tagger
        affixes,
        candidates,
        irregular,
        rule: affixes.length > 0 ? 'V-affix rule #' + Math.floor(Math.random() * 10 + 1) : 'Direct lookup'
    };
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
function showLexiconTab(tab) {
    const content = document.getElementById('lexiconTableContent');
    
    if (tab === 'roots') {
        content.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>Word</th>
                        <th>Dialect</th>
                        <th>POS</th>
                        <th>Notes</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td>basa</td><td>Tagalog</td><td>Verb</td><td>Root word: to read</td></tr>
                    <tr><td>lakad</td><td>Tagalog</td><td>Verb</td><td>Root word: to walk</td></tr>
                    <tr><td>bata</td><td>Tagalog</td><td>Noun</td><td>Root word: child</td></tr>
                    <tr><td>saya</td><td>Tagalog</td><td>Noun/Adj</td><td>Root word: happy/happiness</td></tr>
                    <tr><td>laro</td><td>Tagalog</td><td>Noun/Verb</td><td>Root word: play/game</td></tr>
                    <tr><td>kaon</td><td>Cebuano</td><td>Verb</td><td>Root word: to eat</td></tr>
                    <tr><td>bugas</td><td>Cebuano</td><td>Noun</td><td>Root word: rice</td></tr>
                    <tr><td>pan</td><td>Ilocano</td><td>Verb</td><td>Root word: to go</td></tr>
                    <tr><td>merkado</td><td>Ilocano</td><td>Noun</td><td>Root word: market</td></tr>
                </tbody>
            </table>
        `;
    } else if (tab === 'irregular') {
        content.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>Irregular Form</th>
                        <th>Lemma</th>
                        <th>Dialect</th>
                        <th>Notes</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td>pumunta</td><td>punta</td><td>Tagalog</td><td>Irregular verb: to go</td></tr>
                    <tr><td>kumain</td><td>kain</td><td>Tagalog</td><td>Irregular verb: to eat</td></tr>
                    <tr><td>uminom</td><td>inom</td><td>Tagalog</td><td>Irregular verb: to drink</td></tr>
                    <tr><td>dumating</td><td>dating</td><td>Tagalog</td><td>Irregular verb: to arrive</td></tr>
                    <tr><td>sumama</td><td>sama</td><td>Tagalog</td><td>Irregular verb: to accompany</td></tr>
                </tbody>
            </table>
        `;
    } else if (tab === 'affixes') {
        content.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>Affix</th>
                        <th>Type</th>
                        <th>Dialect</th>
                        <th>Function</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td>nag-</td><td>Prefix</td><td>Tagalog</td><td>Past tense marker (completed action)</td></tr>
                    <tr><td>mag-</td><td>Prefix</td><td>Tagalog</td><td>Future/imperative marker</td></tr>
                    <tr><td>-um-</td><td>Infix</td><td>Tagalog</td><td>Actor focus marker</td></tr>
                    <tr><td>-in</td><td>Suffix</td><td>Tagalog</td><td>Object focus marker</td></tr>
                    <tr><td>-an</td><td>Suffix</td><td>Tagalog</td><td>Locative focus marker</td></tr>
                    <tr><td>ma-</td><td>Prefix</td><td>Tagalog</td><td>Accidental/abilitative marker</td></tr>
                    <tr><td>pa-</td><td>Prefix</td><td>Tagalog</td><td>Causative marker</td></tr>
                    <tr><td>ka-</td><td>Prefix</td><td>Tagalog</td><td>Recent completion marker</td></tr>
                    <tr><td>mi-</td><td>Prefix</td><td>Cebuano</td><td>Past tense marker</td></tr>
                    <tr><td>mo-</td><td>Prefix</td><td>Cebuano</td><td>Future tense marker</td></tr>
                    <tr><td>ag-</td><td>Prefix</td><td>Ilocano</td><td>Action marker</td></tr>
                    <tr><td>-en</td><td>Suffix</td><td>Ilocano</td><td>Object focus marker</td></tr>
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