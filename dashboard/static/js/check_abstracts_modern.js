document.addEventListener('DOMContentLoaded', function() {
    initServiceCardToggle();
    initSearchFilter();
    initFilterButtons();
    initViewToggle();
    initTableDetailsToggle();
    initSortDropdown();
    initBackToTop();
    initAnalysisToggle();
    updateFilterCounts();
});

function initServiceCardToggle() {
    document.querySelectorAll('.mq-service-header').forEach(header => {
        header.addEventListener('click', function(e) {
            if (e.target.closest('.mq-expand-btn')) return;
            const card = this.closest('.mq-service-card');
            toggleCard(card);
        });
    });
    
    document.querySelectorAll('.mq-expand-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const card = this.closest('.mq-service-card');
            toggleCard(card);
        });
    });
}

function toggleCard(card) {
    const isExpanded = card.classList.contains('expanded');
    card.classList.toggle('expanded');
    const btn = card.querySelector('.mq-expand-btn');
    if (btn) btn.setAttribute('aria-expanded', !isExpanded);
}

function initSearchFilter() {
    const searchInput = document.querySelector('.mq-search-input');
    if (!searchInput) return;
    
    let debounceTimer;
    searchInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            filterServices(this.value.toLowerCase());
            updateFilterCounts();
            updateSearchCounter();
        }, 300);
    });
}

function updateSearchCounter() {
    const searchInput = document.querySelector('.mq-search-input');
    const counter = document.getElementById('mq-search-counter');
    const query = searchInput.value.toLowerCase();
    
    if (!query) {
        counter.classList.remove('visible');
        return;
    }
    
    let matchCount = 0;
    document.querySelectorAll('.mq-service-card').forEach(card => {
        if (card.style.display !== 'none') matchCount++;
    });
    
    counter.textContent = `${matchCount} found`;
    counter.classList.add('visible');
}

function filterServices(query) {
    // Filter cards
    document.querySelectorAll('.mq-service-card').forEach(card => {
        const title = card.querySelector('.mq-service-title')?.textContent.toLowerCase() || '';
        const id = card.querySelector('.mq-service-id')?.textContent.toLowerCase() || '';
        
        if (title.includes(query) || id.includes(query)) {
            card.style.display = '';
            card.style.animation = 'scaleIn 0.3s ease';
        } else {
            card.style.display = 'none';
        }
    });
    
    // Filter table rows
    document.querySelectorAll('.mq-table-row').forEach(row => {
        const title = row.querySelector('.mq-table-title')?.textContent.toLowerCase() || '';
        const id = row.querySelector('.mq-table-id')?.textContent.toLowerCase() || '';
        
        if (title.includes(query) || id.includes(query)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
            // Also hide details row
            const nextRow = row.nextElementSibling;
            if (nextRow && nextRow.classList.contains('mq-table-details-row')) {
                nextRow.style.display = 'none';
            }
        }
    });
}

function initFilterButtons() {
    document.querySelectorAll('.mq-filter-btn[data-filter]').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.mq-filter-btn[data-filter]').forEach(b => {
                b.classList.remove('active');
            });
            this.classList.add('active');
            applyFilter(this.dataset.filter);
        });
    });
    
    // Update filter counts on page load
    updateFilterCounts();
}

function updateFilterCounts() {
    const allCount = document.getElementById('all-count');
    const problemsCount = document.getElementById('problems-count');
    const goodCount = document.getElementById('good-count');
    
    if (!allCount || !problemsCount || !goodCount) return;
    
    const allCards = Array.from(document.querySelectorAll('.mq-service-card'));
    const problemCards = allCards.filter(c => c.classList.contains('has-issues'));
    const goodCards = allCards.filter(c => c.classList.contains('all-good'));
    
    // Count visible items (not filtered by search)
    const visibleCards = allCards.filter(c => c.style.display !== 'none');
    const visibleProblems = visibleCards.filter(c => c.classList.contains('has-issues'));
    const visibleGood = visibleCards.filter(c => c.classList.contains('all-good'));
    
    allCount.textContent = `(${visibleCards.length})`;
    problemsCount.textContent = `(${visibleProblems.length})`;
    goodCount.textContent = `(${visibleGood.length})`;
}

function applyFilter(filter) {
    // Filter cards
    document.querySelectorAll('.mq-service-card').forEach(card => {
        const hasIssues = card.classList.contains('has-issues');
        const allGood = card.classList.contains('all-good');
        
        switch(filter) {
            case 'problems':
                card.style.display = hasIssues ? '' : 'none';
                break;
            case 'good':
                card.style.display = allGood ? '' : 'none';
                break;
            default:
                card.style.display = '';
        }
    });
    
    // Filter table rows
    document.querySelectorAll('.mq-table-row').forEach(row => {
        const hasIssues = row.classList.contains('has-issues');
        const allGood = row.classList.contains('all-good');
        
        let show = true;
        switch(filter) {
            case 'problems':
                show = hasIssues;
                break;
            case 'good':
                show = allGood;
                break;
        }
        
        row.style.display = show ? '' : 'none';
        // Also handle details row
        const nextRow = row.nextElementSibling;
        if (nextRow && nextRow.classList.contains('mq-table-details-row')) {
            if (!show) nextRow.style.display = 'none';
        }
    });
    
    // Update filter counts
    updateFilterCounts();
}

function expandAllCards() {
    document.querySelectorAll('.mq-service-card').forEach(card => card.classList.add('expanded'));
}

function collapseAllCards() {
    document.querySelectorAll('.mq-service-card').forEach(card => card.classList.remove('expanded'));
}

function initViewToggle() {
    const viewToggleBtns = document.querySelectorAll('.mq-view-btn');
    const cardView = document.getElementById('mq-card-view');
    const tableView = document.getElementById('mq-table-view');
    
    if (!cardView || !tableView || viewToggleBtns.length === 0) return;
    
    // Load saved preference
    const savedView = localStorage.getItem('mq-view-preference') || 'cards';
    if (savedView === 'table') {
        switchToTableView(cardView, tableView, viewToggleBtns);
    }
    
    viewToggleBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const view = this.dataset.view;
            
            if (view === 'cards') {
                switchToCardView(cardView, tableView, viewToggleBtns);
            } else {
                switchToTableView(cardView, tableView, viewToggleBtns);
            }
            
            localStorage.setItem('mq-view-preference', view);
        });
    });
}

function switchToCardView(cardView, tableView, btns) {
    cardView.style.display = '';
    tableView.style.display = 'none';
    btns.forEach(b => {
        b.classList.toggle('active', b.dataset.view === 'cards');
    });
}

function switchToTableView(cardView, tableView, btns) {
    cardView.style.display = 'none';
    tableView.style.display = '';
    tableView.classList.add('active');
    btns.forEach(b => {
        b.classList.toggle('active', b.dataset.view === 'table');
    });
}

function initTableDetailsToggle() {
    document.querySelectorAll('.mq-table-details-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const targetId = this.dataset.target;
            const detailsRow = document.getElementById(targetId);
            
            if (detailsRow) {
                const isVisible = detailsRow.style.display !== 'none';
                detailsRow.style.display = isVisible ? 'none' : 'table-row';
                
                // Rotate chevron
                const icon = this.querySelector('i');
                if (icon) {
                    icon.style.transform = isVisible ? 'rotate(0deg)' : 'rotate(180deg)';
                }
            }
        });
    });
}

// Sorting functionality
function sortServices(sortBy) {
    // Check if we're in table or card view
    const cardView = document.getElementById('mq-card-view');
    const tableView = document.getElementById('mq-table-view');
    const isTableView = tableView.style.display !== 'none';
    
    if (isTableView) {
        sortTable(sortBy);
    } else {
        sortCards(sortBy);
    }
}

function sortCards(sortBy) {
    const cardContainer = document.getElementById('mq-card-view');
    if (!cardContainer) return;
    
    const cards = Array.from(cardContainer.querySelectorAll('.mq-service-card'));
    
    cards.sort((a, b) => {
        let valueA, valueB;
        
        switch(sortBy) {
            case 'title':
                valueA = a.querySelector('.mq-service-title').textContent.toLowerCase();
                valueB = b.querySelector('.mq-service-title').textContent.toLowerCase();
                return valueA.localeCompare(valueB);
            
            case 'quality':
                valueA = parseInt(a.querySelector('.mq-score-percentage')?.textContent) || 0;
                valueB = parseInt(b.querySelector('.mq-score-percentage')?.textContent) || 0;
                return valueB - valueA; // Descending
            
            case 'issues':
                valueA = parseInt(a.dataset.totalIssues) || 0;
                valueB = parseInt(b.dataset.totalIssues) || 0;
                return valueB - valueA; // Descending
            
            case 'layers':
                valueA = parseInt(a.dataset.totalLayers) || 0;
                valueB = parseInt(b.dataset.totalLayers) || 0;
                return valueB - valueA; // Descending
            
            default:
                return 0;
        }
    });
    
    // Re-append sorted cards
    cards.forEach(card => cardContainer.appendChild(card));
}

function sortTable(sortBy) {
    const table = document.querySelector('.mq-main-table tbody');
    if (!table) return;
    
    // Get all table rows (excluding detail rows)
    const rows = Array.from(table.querySelectorAll('.mq-table-row'));
    
    rows.sort((a, b) => {
        let valueA, valueB;
        
        switch(sortBy) {
            case 'title':
                // Column 3 is service title
                valueA = a.cells[2].textContent.toLowerCase();
                valueB = b.cells[2].textContent.toLowerCase();
                return valueA.localeCompare(valueB);
            
            case 'quality':
                // Quality score is not in table, so use layers count as proxy
                // Column 4 is layer count
                valueA = parseInt(a.cells[3].textContent) || 0;
                valueB = parseInt(b.cells[3].textContent) || 0;
                return valueB - valueA;
            
            case 'issues':
                // Count issues by checking status icons in columns 5-8
                const countIssuesA = countTableRowIssues(a);
                const countIssuesB = countTableRowIssues(b);
                return countIssuesB - countIssuesA;
            
            case 'layers':
                // Column 4 is layer count
                valueA = parseInt(a.cells[3].textContent) || 0;
                valueB = parseInt(b.cells[3].textContent) || 0;
                return valueB - valueA;
            
            default:
                return 0;
        }
    });
    
    // Re-append sorted rows with their detail rows
    rows.forEach((row, index) => {
        table.appendChild(row);
        
        // Find and append corresponding detail row
        const detailId = `table-details-${row.parentElement.children[index].getAttribute('id')?.split('-').pop() || index}`;
        const detailRow = document.getElementById(detailId);
        if (detailRow) {
            table.appendChild(detailRow);
        }
    });
}

function countTableRowIssues(row) {
    let issueCount = 0;
    // Check columns 5-8 for danger icons (issues)
    for (let i = 4; i <= 7; i++) {
        if (row.cells[i] && row.cells[i].querySelector('.mq-status-icon.danger')) {
            issueCount++;
        }
        if (row.cells[i] && row.cells[i].querySelector('.mq-status-icon.warning')) {
            issueCount += 0.5; // Warnings count as half issues
        }
    }
    return issueCount;
}

// Export functionality
function exportToCSV() {
    const cards = document.querySelectorAll('.mq-service-card');
    if (cards.length === 0) {
        alert('No data to export');
        return;
    }
    
    let csv = 'ID,Service Title,Total Layers,Quality Score,Without Abstract,Without Keywords,Short Abstract,Issues\n';
    
    cards.forEach(card => {
        const id = card.querySelector('.mq-service-id').textContent.trim();
        const title = card.querySelector('.mq-service-title').textContent.trim();
        const layers = card.dataset.totalLayers;
        const score = card.querySelector('.mq-score-percentage').textContent.trim();
        const abstract = card.querySelector('[class*="danger"]')?.parentElement?.querySelector('.mq-quality-label')?.textContent === 'Abstract' ? '1' : '0';
        const keywords = card.querySelectorAll('[class*="danger"]').length > 0 ? '1' : '0';
        const shortAbstract = card.querySelectorAll('[class*="warning"]').length > 0 ? '1' : '0';
        const issues = card.dataset.totalIssues;
        
        csv += `"${id}","${title}",${layers},${score},${abstract},${keywords},${shortAbstract},${issues}\n`;
    });
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `metadata-quality-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
}

// Sort dropdown toggle
function initSortDropdown() {
    const sortBtn = document.querySelector('.mq-sort-btn');
    const sortMenu = document.querySelector('.mq-sort-menu');
    
    if (!sortBtn || !sortMenu) return;
    
    sortBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        sortMenu.style.display = sortMenu.style.display === 'none' ? 'block' : 'none';
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.mq-sort-dropdown')) {
            sortMenu.style.display = 'none';
        }
    });
}

// Back to Top Button
function initBackToTop() {
    const backToTopBtn = document.getElementById('mq-back-to-top');
    if (!backToTopBtn) return;
    
    // Show/hide button based on scroll position
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTopBtn.classList.add('visible');
        } else {
            backToTopBtn.classList.remove('visible');
        }
    });
    
    // Scroll to top on click
    backToTopBtn.addEventListener('click', function(e) {
        e.preventDefault();
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

function initAnalysisToggle() {
    const toggleBtn = document.getElementById('mq-toggle-analysis');
    const analysisContent = document.querySelector('.mq-analysis-content');
    
    if (!toggleBtn || !analysisContent) return;
    
    // Retrieve stored preference from localStorage
    const isExpanded = localStorage.getItem('mq-analysis-expanded') !== 'false';
    
    // Set initial state
    if (!isExpanded) {
        analysisContent.classList.add('hidden');
        toggleBtn.classList.add('collapsed');
    } else {
        analysisContent.classList.remove('hidden');
        toggleBtn.classList.remove('collapsed');
    }
    
    // Toggle on button click
    toggleBtn.addEventListener('click', function(e) {
        e.preventDefault();
        
        const isCurrentlyHidden = analysisContent.classList.contains('hidden');
        
        if (isCurrentlyHidden) {
            analysisContent.classList.remove('hidden');
            toggleBtn.classList.remove('collapsed');
            localStorage.setItem('mq-analysis-expanded', 'true');
        } else {
            analysisContent.classList.add('hidden');
            toggleBtn.classList.add('collapsed');
            localStorage.setItem('mq-analysis-expanded', 'false');
        }
    });
    
    // Keyboard shortcut: Alt+A to toggle analysis
    document.addEventListener('keydown', function(e) {
        if ((e.altKey || e.ctrlKey) && e.key === 'a') {
            e.preventDefault();
            toggleBtn.click();
        }
    });
}
