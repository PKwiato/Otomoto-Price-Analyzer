// Main Frontend Logic

let configData = null;
let charts = {};
let scrapedListings = [];

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await loadConfig();
    setupEventListeners();
});

// Load configuration (makes)
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        configData = await response.json();

        populateMakeSelect();
        // Trigger model population for default make
        await updateModelSelect();
    } catch (error) {
        console.error('Failed to load config:', error);
    }
}

function populateMakeSelect() {
    const makeSelect = document.getElementById('makeSelect');
    makeSelect.innerHTML = '';

    configData.makes.forEach(make => {
        const option = document.createElement('option');
        option.value = make;
        option.textContent = make.toUpperCase();
        if (make === 'bmw') option.selected = true; // Default
        makeSelect.appendChild(option);
    });
}

async function updateModelSelect() {
    const make = document.getElementById('makeSelect').value;
    const modelSelect = document.getElementById('modelSelect');

    // Show loading state
    modelSelect.innerHTML = '<option>Loading models...</option>';
    modelSelect.disabled = true;

    try {
        const response = await fetch(`/api/models/${make}`);
        const models = await response.json();

        modelSelect.innerHTML = '';
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.id;
            option.textContent = model.name;
            modelSelect.appendChild(option);
        });

        // Select a default if it exists (e.g. seria-3 for bmw)
        if (make === 'bmw' && models.some(m => m.id === 'seria-3')) {
            modelSelect.value = 'seria-3';
        }

        modelSelect.disabled = false;
        await updateGenerationSelect();
    } catch (error) {
        console.error('Failed to fetch models:', error);
        modelSelect.innerHTML = '<option value="">Error loading models</option>';
    }
}

async function updateGenerationSelect() {
    const make = document.getElementById('makeSelect').value;
    const model = document.getElementById('modelSelect').value;
    const genSelect = document.getElementById('genSelect');

    if (!model) {
        genSelect.parentElement.style.display = 'none';
        return;
    }

    // Show loading
    genSelect.innerHTML = '<option value="">Loading generations...</option>';
    genSelect.disabled = true;
    genSelect.parentElement.style.display = 'block';

    try {
        const response = await fetch(`/api/generations/${make}/${model}`);
        const gens = await response.json();

        genSelect.innerHTML = '<option value="">All Generations</option>';
        if (gens && gens.length > 0) {
            gens.forEach(gen => {
                const option = document.createElement('option');
                option.textContent = gen.name;
                option.value = gen.id;
                genSelect.appendChild(option);
            });
            genSelect.disabled = false;
            genSelect.parentElement.style.display = 'block';
        } else {
            genSelect.parentElement.style.display = 'none';
        }
    } catch (error) {
        console.error('Failed to fetch generations:', error);
        genSelect.parentElement.style.display = 'none';
    }
}

// Sorting State
let sortState = {
    column: null,
    direction: 'asc' // or 'desc'
};

function setupEventListeners() {
    document.getElementById('makeSelect').addEventListener('change', () => {
        updateModelSelect();
    });

    document.getElementById('modelSelect').addEventListener('change', () => {
        updateGenerationSelect();
    });

    document.getElementById('analyzeBtn').addEventListener('click', runAnalysis);

    // Client-side mapping for polish terms
    const inputs = ['yearFrom', 'yearTo', 'fuelSelect', 'gearboxSelect', 'driveSelect', 'firstOwner', 'accidentFree'];
    inputs.forEach(id => {
        document.getElementById(id).addEventListener('change', () => {
            if (scrapedListings.length > 0) applyFilters();
        });
    });
}

// Sorting Function
function sortTable(column) {
    // Toggle direction if same column
    if (sortState.column === column) {
        sortState.direction = sortState.direction === 'asc' ? 'desc' : 'asc';
    } else {
        sortState.column = column;
        sortState.direction = 'asc'; // Default new sort to asc
    }

    // Update header visuals
    document.querySelectorAll('th[data-sort]').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
        if (th.dataset.sort === column) {
            th.textContent = th.textContent.split(' ')[0] + (sortState.direction === 'asc' ? ' ▲' : ' ▼');
            th.classList.add(`sort-${sortState.direction}`);
        } else {
            th.textContent = th.textContent.split(' ')[0] + ' ⬍';
        }
    });

    applyFilters(); // Re-render with sort
}

// Analysis with Streaming
async function runAnalysis() {
    const btn = document.getElementById('analyzeBtn');
    const loader = document.getElementById('loader');
    const loadingText = document.getElementById('loadingText');

    btn.disabled = true;
    loader.classList.add('active');
    loadingText.textContent = "Initializing scrape...";

    try {
        const payload = {
            make: document.getElementById('makeSelect').value,
            model: document.getElementById('modelSelect').value,
            generation: document.getElementById('genSelect').value || null,
            year_from: document.getElementById('yearFrom').value,
            year_to: document.getElementById('yearTo').value,
            max_pages: document.getElementById('maxPages').value,

            // Server-side pre-filters
            fuel_type: document.getElementById('fuelSelect').value || null,
            gearbox: document.getElementById('gearboxSelect').value || null,
            drive_type: document.getElementById('driveSelect').value || null,
            first_owner: document.getElementById('firstOwner').checked,
            accident_free: document.getElementById('accidentFree').checked
        };

        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete line in buffer

            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const msg = JSON.parse(line);

                    if (msg.type === 'progress') {
                        loadingText.textContent = msg.message;
                    } else if (msg.type === 'complete') {
                        scrapedListings = msg.data.listings;
                        applyFilters();
                    } else if (msg.type === 'error') {
                        throw new Error(msg.message);
                    }
                } catch (e) {
                    console.error('Error parsing stream:', e);
                }
            }
        }

        document.querySelector('.main-content').scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
        alert('Analysis failed: ' + error.message);
    } finally {
        btn.disabled = false;
        loader.classList.remove('active');
    }
}

// Client-side Filtering & Display
function applyFilters() {
    let results = [...scrapedListings]; // Copy array

    // Filtering logic matching python params
    const yearFrom = parseInt(document.getElementById('yearFrom').value);
    const yearTo = parseInt(document.getElementById('yearTo').value);

    // Mappings
    const fuelMap = {
        'petrol': 'benzyna', 'diesel': 'diesel', 'electric': 'elektryczny', 'hybrid': 'hybryda', 'lpg': 'lpg'
    };
    const gearboxMap = {
        'manual': 'manualna', 'automatic': 'automatyczna'
    };

    results = results.filter(item => {
        const y = parseInt(item.year);
        if (y < yearFrom || y > yearTo) return false;

        // Check params if set
        const fuelFilter = document.getElementById('fuelSelect').value;
        if (fuelFilter) {
            const mapped = fuelMap[fuelFilter] || fuelFilter;
            if (!item.fuel || !item.fuel.toLowerCase().includes(mapped)) return false;
        }

        const gearFilter = document.getElementById('gearboxSelect').value;
        if (gearFilter) {
            const mapped = gearboxMap[gearFilter] || gearFilter;
            if (!item.gearbox || !item.gearbox.toLowerCase().includes(mapped)) return false;
        }

        const driveFilter = document.getElementById('driveSelect').value;
        if (driveFilter) {
            if (!item.drive || !item.drive.toLowerCase().includes(driveFilter)) return false;
        }

        const firstOwner = document.getElementById('firstOwner').checked;
        if (firstOwner && !item.first_owner) return false;

        const accidentFree = document.getElementById('accidentFree').checked;
        if (accidentFree && !item.accident_free) return false;

        return true;
    });

    // Apply Sorting
    if (sortState.column) {
        const col = sortState.column;
        const dir = sortState.direction === 'asc' ? 1 : -1;

        results.sort((a, b) => {
            let valA = a[col];
            let valB = b[col];

            // Handle numeric strings or values
            if (col === 'year' || col === 'price' || col === 'mileage') {
                valA = parseFloat(valA) || 0;
                valB = parseFloat(valB) || 0;
            } else {
                valA = (valA || '').toString().toLowerCase();
                valB = (valB || '').toString().toLowerCase();
            }

            if (valA < valB) return -1 * dir;
            if (valA > valB) return 1 * dir;
            return 0;
        });
    }

    updateUI(results);
}

function updateUI(data) {
    if (data.length === 0) {
        // Show empty state
        return;
    }

    // Calculate Stats
    const prices = data.map(i => i.price).filter(p => p > 0);
    const avg = prices.reduce((a, b) => a + b, 0) / prices.length;
    const min = Math.min(...prices);
    const max = Math.max(...prices);

    // Sort for Median
    prices.sort((a, b) => a - b);
    const median = prices[Math.floor(prices.length / 2)];

    // Update Cards
    document.getElementById('statAvg').textContent = Math.round(avg).toLocaleString() + ' PLN';
    document.getElementById('statMedian').textContent = Math.round(median).toLocaleString() + ' PLN';
    document.getElementById('statMin').textContent = Math.round(min).toLocaleString() + ' PLN';
    document.getElementById('statMax').textContent = Math.round(max).toLocaleString() + ' PLN';

    updateCharts(data);
    updateTable(data);
}

function updateCharts(data) {
    const ctxHist = document.getElementById('chartPriceDist').getContext('2d');
    const ctxScatter = document.getElementById('chartPriceMile').getContext('2d');

    // Histogram Logic (Simple bins)
    const validPrices = data.map(d => d.price).filter(p => p > 0);
    const binCount = 20;
    const min = Math.min(...validPrices);
    const max = Math.max(...validPrices);
    const step = (max - min) / binCount;
    const bins = Array(binCount).fill(0);
    const labels = Array(binCount).fill(0).map((_, i) => Math.round(min + i * step));

    validPrices.forEach(p => {
        const idx = Math.min(Math.floor((p - min) / step), binCount - 1);
        bins[idx]++;
    });

    if (charts.hist) charts.hist.destroy();
    charts.hist = new Chart(ctxHist, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Number of Listings',
                data: bins,
                backgroundColor: '#3b82f6',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { grid: { color: '#334155' }, ticks: { color: '#94a3b8' } },
                x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
            }
        }
    });

    // Scatter Plot
    const scatterData = data
        .filter(d => d.price > 0 && d.mileage > 0)
        .map(d => ({ x: d.mileage, y: d.price }));

    if (charts.scatter) charts.scatter.destroy();
    charts.scatter = new Chart(ctxScatter, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Listing',
                data: scatterData,
                backgroundColor: '#8b5cf6'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `Price: ${ctx.parsed.y.toLocaleString()} PLN, Mileage: ${ctx.parsed.x.toLocaleString()} km`
                    }
                }
            },
            scales: {
                y: {
                    title: { display: true, text: 'Price (PLN)', color: '#94a3b8' },
                    grid: { color: '#334155' },
                    ticks: { color: '#94a3b8' }
                },
                x: {
                    title: { display: true, text: 'Mileage (km)', color: '#94a3b8' },
                    grid: { color: '#334155' },
                    ticks: { color: '#94a3b8' }
                }
            }
        }
    });
}

function updateTable(data) {
    const tbody = document.getElementById('tableBody');
    tbody.innerHTML = '';

    data.slice(0, 50).forEach(item => { // Limit to 50 rows for perf
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${item.year}</td>
            <td><a href="${item.link}" target="_blank" class="listing-link">${item.title}</a></td>
            <td>${item.price.toLocaleString()} PLN</td>
            <td>${item.mileage.toLocaleString()} km</td>
            <td>${item.fuel}</td>
            <td>${item.gearbox}</td>
        `;
        tbody.appendChild(tr);
    });
}
