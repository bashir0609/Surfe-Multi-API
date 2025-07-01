/**
 * =====================================================================
 * Company Search Module v2 - With Authentic Surfe API Data
 * Features: Advanced filtering, CSV export, real-time results, authentic autocomplete
 * =====================================================================
 */

(function() {
    'use strict';
    
    // Module namespace
    const CompanySearch = {
        currentResults: [],
        isSearching: false,
        searchForm: null,
        resultsContainer: null
    };
    
    /**
     * =====================================================================
     * Search Configuration - Using Authentic Data from SurfeApp
     * =====================================================================
     */
    const searchConfig = {
        companySizes: [
            '1-10', '11-50', '51-200', '201-500', '501-1000', 
            '1001-5000', '5001-10000', '10000+'
        ]
    };
    
    /**
     * =====================================================================
     * Initialize Company Search
     * =====================================================================
     */
    CompanySearch.init = function() {
        console.log('🏢 Initializing Company Search module v2');
        
        this.searchForm = document.getElementById('company-search-form');
        this.resultsContainer = document.getElementById('search-results');
        
        if (!this.searchForm || !this.resultsContainer) {
            console.error('Required elements not found for Company Search');
            return;
        }
        
        this.setupForm();
        this.setupEventListeners();
        this.populateFormOptionsWithAuthenticData();
        
        console.log('✅ Company Search module v2 initialized');
    };
    
    /**
     * =====================================================================
     * Form Setup and Population with Authentic Data
     * =====================================================================
     */
    CompanySearch.setupForm = function() {
        this.searchForm.reset();
        
        const limitSelect = document.getElementById('limit');
        if (limitSelect && !limitSelect.value) {
            limitSelect.value = '10';
        }
    };
    
    CompanySearch.populateFormOptionsWithAuthenticData = function() {
        // Use centralized autocomplete functionality
        if (window.SurfeApp && window.SurfeApp.autocomplete) {
            return window.SurfeApp.autocomplete.populateCompanySearchForm();
        } else {
            console.warn('SurfeApp autocomplete not available, using fallback');
            return this.populateFormOptionsFallback();
        }
    };
    
    CompanySearch.populateFormOptionsFallback = function() {
        console.log('🔄 Using fallback company form population...');
        
        // Populate company sizes (static)
        const companySizes = searchConfig.companySizes || [
            '1-10', '11-50', '51-200', '201-500', '501-1000', 
            '1001-5000', '5001-10000', '10000+'
        ];
        
        this.populateSelectFallback('company-sizes', companySizes);
        console.log('✅ Fallback company form options populated');
    };
    
    CompanySearch.populateSelectFallback = function(selectId, options) {
        const select = document.getElementById(selectId);
        if (!select) return;
        
        // Clear existing options except the first placeholder
        while (select.children.length > 1) {
            select.removeChild(select.lastChild);
        }
        
        // Add options
        options.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option;
            optionElement.textContent = option;
            select.appendChild(optionElement);
        });
    };
    
    /**
     * =====================================================================
     * Event Listeners
     * =====================================================================
     */
    CompanySearch.setupEventListeners = function() {
        this.searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.performSearch();
        });
        
        const exportCsvBtn = document.getElementById('export-csv');
        const exportJsonBtn = document.getElementById('export-json');
        
        if (exportCsvBtn) {
            exportCsvBtn.addEventListener('click', () => this.exportResults('csv'));
        }
        
        if (exportJsonBtn) {
            exportJsonBtn.addEventListener('click', () => this.exportResults('json'));
        }
        
        const resetBtn = document.getElementById('reset-form');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.resetForm());
        }
    };
    
    /**
     * =====================================================================
     * Search Functionality
     * =====================================================================
     */
    CompanySearch.performSearch = function() {
        if (this.isSearching) {
            SurfeApp.ui.showToast('Search already in progress', 'warning');
            return;
        }
        
        if (!SurfeApp.forms.validateForm(this.searchForm)) {
            SurfeApp.ui.showToast('Please fill in all required fields', 'error');
            return;
        }
        
        this.isSearching = true;
        this.updateSearchButton(true);
        
        const searchData = this.prepareSearchData();
        
        console.log('🏢 Starting company search with data:', searchData);
        
        SurfeApp.api.post('/api/company-search', searchData)
            .then(response => {
                console.log('📊 Company search response:', response);
                
                if (response.success && response.data && response.data.length > 0) {
                    this.currentResults = response.data;
                    this.displayResults(response.data);
                    SurfeApp.ui.showToast(`Found ${response.data.length} companies`, 'success');
                } else {
                    this.displayNoResults();
                    SurfeApp.ui.showToast('No companies found for your search criteria', 'info');
                }
            })
            .catch(error => {
                console.error('❌ Company search error:', error);
                this.displayError(error);
                SurfeApp.ui.showToast('Search failed. Please try again.', 'error');
            })
            .finally(() => {
                this.isSearching = false;
                this.updateSearchButton(false);
            });
    };
    
    CompanySearch.prepareSearchData = function() {
        const formData = new FormData(this.searchForm);
        const data = {};
        
        // Get multi-select values
        const industriesSelect = document.getElementById('industries');
        const sizesSelect = document.getElementById('company-sizes');
        const countriesSelect = document.getElementById('countries');
        
        if (industriesSelect) {
            data.industries = Array.from(industriesSelect.selectedOptions).map(option => option.value).filter(v => v);
        }
        
        if (sizesSelect) {
            data.company_sizes = Array.from(sizesSelect.selectedOptions).map(option => option.value).filter(v => v);
        }
        
        if (countriesSelect) {
            data.countries = Array.from(countriesSelect.selectedOptions).map(option => option.value).filter(v => v);
        }
        
        // Get text inputs
        const companyNames = formData.get('company-names');
        if (companyNames && companyNames.trim()) {
            data.company_names = companyNames.split(',').map(name => name.trim()).filter(name => name);
        }
        
        const companyDomains = formData.get('company-domains');
        if (companyDomains && companyDomains.trim()) {
            data.company_domains = companyDomains.split(',').map(domain => domain.trim()).filter(domain => domain);
        }
        
        data.limit = parseInt(formData.get('limit')) || 10;
        
        return data;
    };
    
    /**
     * =====================================================================
     * Results Display
     * =====================================================================
     */
    CompanySearch.displayResults = function(companies) {
        const resultsHTML = `
            <div class="results-header">
                <h4>
                    <i class="fas fa-building me-2"></i>
                    Search Results (${companies.length} companies)
                </h4>
                <div class="results-actions">
                    <button id="export-csv" class="btn btn-outline-primary btn-sm">
                        <i class="fas fa-download me-1"></i>
                        Export CSV
                    </button>
                    <button id="export-json" class="btn btn-outline-secondary btn-sm">
                        <i class="fas fa-file-code me-1"></i>
                        Export JSON
                    </button>
                </div>
            </div>
            <div class="results-grid">
                ${companies.map(company => this.createCompanyCard(company)).join('')}
            </div>
        `;
        
        this.resultsContainer.innerHTML = resultsHTML;
        this.resultsContainer.classList.remove('hidden');
        this.resultsContainer.classList.add('visible');
        
        // Re-attach export event listeners
        this.setupExportListeners();
        
        // Scroll to results
        this.resultsContainer.scrollIntoView({ behavior: 'smooth' });
    };
    
    CompanySearch.createCompanyCard = function(company) {
        const name = company.name || 'Unknown Company';
        const industry = company.industry || 'Not specified';
        const website = company.website || '';
        const employeeCount = company.employee_count || 'Not specified';
        const location = company.location || 'Not specified';
        const description = company.description || 'No description available';
        
        return `
            <div class="company-card">
                <div class="company-header">
                    <h5 class="company-name">${this.escapeHtml(name)}</h5>
                    ${website ? `<a href="${this.escapeHtml(website)}" target="_blank" class="company-website">
                        <i class="fas fa-external-link-alt"></i>
                    </a>` : ''}
                </div>
                <div class="company-details">
                    <div class="detail-item">
                        <i class="fas fa-industry"></i>
                        <span>${SurfeApp.utils.sanitizeHtml(industry)}</span>
                    </div>
                    <div class="detail-item">
                        <i class="fas fa-users"></i>
                        <span>${SurfeApp.utils.sanitizeHtml(employeeCount.toString())}</span>
                    </div>
                    <div class="detail-item">
                        <i class="fas fa-map-marker-alt"></i>
                        <span>${SurfeApp.utils.sanitizeHtml(location)}</span>
                    </div>
                </div>
                <div class="company-description">
                    <p>${SurfeApp.utils.sanitizeHtml(SurfeApp.utils.truncateText(description, 150))}</p>
                </div>
            </div>
        `;
    };
    
    CompanySearch.displayNoResults = function() {
        this.resultsContainer.innerHTML = `
            <div class="no-results">
                <i class="fas fa-search fa-3x text-muted mb-3"></i>
                <h4>No Companies Found</h4>
                <p class="text-muted">Try adjusting your search criteria or broadening your filters.</p>
            </div>
        `;
        this.resultsContainer.classList.remove('hidden');
        this.resultsContainer.classList.add('visible');
    };
    
    CompanySearch.displayError = function(error) {
        this.resultsContainer.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
                <h4>Search Error</h4>
                <p class="text-muted">${error.message || 'An error occurred while searching for companies.'}</p>
                <button class="btn btn-primary" onclick="location.reload()">
                    <i class="fas fa-refresh me-1"></i>
                    Try Again
                </button>
            </div>
        `;
        this.resultsContainer.classList.remove('hidden');
        this.resultsContainer.classList.add('visible');
    };
    
    /**
     * =====================================================================
     * Utility Functions
     * =====================================================================
     */
    CompanySearch.updateSearchButton = function(searching) {
        const searchBtn = document.querySelector('#company-search-form button[type="submit"]');
        if (searchBtn) {
            if (searching) {
                searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Searching...';
                searchBtn.disabled = true;
            } else {
                searchBtn.innerHTML = '<i class="fas fa-search me-2"></i>Search Companies';
                searchBtn.disabled = false;
            }
        }
    };
    
    CompanySearch.setupExportListeners = function() {
        const exportCsvBtn = document.getElementById('export-csv');
        const exportJsonBtn = document.getElementById('export-json');
        
        if (exportCsvBtn) {
            exportCsvBtn.addEventListener('click', () => this.exportResults('csv'));
        }
        
        if (exportJsonBtn) {
            exportJsonBtn.addEventListener('click', () => this.exportResults('json'));
        }
    };
    
    CompanySearch.exportResults = function(format) {
        if (!this.currentResults || this.currentResults.length === 0) {
            SurfeApp.ui.showToast('No results to export', 'warning');
            return;
        }
        
        const timestamp = new Date().toISOString().split('T')[0];
        const filename = `company-search-${timestamp}.${format}`;
        
        if (format === 'csv') {
            SurfeApp.utils.exportToCsv(this.currentResults, filename);
        } else if (format === 'json') {
            SurfeApp.utils.exportToJson(this.currentResults, filename);
        }
    };
    
    CompanySearch.resetForm = function() {
        this.searchForm.reset();
        this.currentResults = [];
        this.resultsContainer.classList.add('hidden');
        this.resultsContainer.classList.remove('visible');
        this.resultsContainer.innerHTML = '';
        SurfeApp.ui.showToast('Form reset', 'info');
    };
    
    // Utility functions moved to shared.js
    
    /**
     * =====================================================================
     * Export Functions (Global)
     * =====================================================================
     */
    window.CompanySearch = CompanySearch;
    
    /**
     * =====================================================================
     * Auto-initialize when DOM is ready
     * =====================================================================
     */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            CompanySearch.init();
        });
    } else {
        CompanySearch.init();
    }
    
})();