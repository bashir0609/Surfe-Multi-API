/**
 * =====================================================================
 * Company Search Module - Handles company search functionality
 * Features: Advanced filtering, CSV export, real-time results
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
     * Search Configuration
     * =====================================================================
     */
    const searchConfig = {
        
        companySizes: [
            '1-10', '11-50', '51-200', '201-500', '501-1000', 
            '1001-5000', '5001-10000', '10000+'
        ],
        
        // ISO 3166-1 alpha-2 country codes (common countries)
        countries: [
            { code: "US", name: "United States" },
            { code: "GB", name: "United Kingdom" },
            { code: "CA", name: "Canada" },
            { code: "AU", name: "Australia" },
            { code: "DE", name: "Germany" },
            { code: "FR", name: "France" },
            { code: "NL", name: "Netherlands" },
            { code: "SE", name: "Sweden" },
            { code: "ES", name: "Spain" },
            { code: "IT", name: "Italy" },
            { code: "CH", name: "Switzerland" },
            { code: "IE", name: "Ireland" },
            { code: "DK", name: "Denmark" },
            { code: "NO", name: "Norway" },
            { code: "BE", name: "Belgium" },
            { code: "AT", name: "Austria" },
            { code: "FI", name: "Finland" },
            { code: "PL", name: "Poland" },
            { code: "PT", name: "Portugal" },
            { code: "BR", name: "Brazil" },
            { code: "IN", name: "India" },
            { code: "JP", name: "Japan" },
            { code: "SG", name: "Singapore" },
            { code: "IL", name: "Israel" },
            { code: "ZA", name: "South Africa" },
            { code: "NZ", name: "New Zealand" },
            { code: "MX", name: "Mexico" },
            { code: "AR", name: "Argentina" },
            { code: "CL", name: "Chile" },
            { code: "CO", name: "Colombia" },
            { code: "CN", name: "China" },
            { code: "KR", name: "Korea, Republic of" },
            { code: "TH", name: "Thailand" },
            { code: "MY", name: "Malaysia" },
            { code: "ID", name: "Indonesia" },
            { code: "PH", name: "Philippines" },
            { code: "VN", name: "Viet Nam" },
            { code: "TW", name: "Taiwan, Province of China" },
            { code: "HK", name: "Hong Kong" },
            { code: "AE", name: "United Arab Emirates" },
            { code: "SA", name: "Saudi Arabia" },
            { code: "EG", name: "Egypt" },
            { code: "NG", name: "Nigeria" },
            { code: "KE", name: "Kenya" },
            { code: "MA", name: "Morocco" },
            { code: "TN", name: "Tunisia" },
            { code: "GH", name: "Ghana" },
            { code: "RU", name: "Russian Federation" },
            { code: "UA", name: "Ukraine" },
            { code: "CZ", name: "Czech Republic" },
            { code: "HU", name: "Hungary" },
            { code: "RO", name: "Romania" },
            { code: "BG", name: "Bulgaria" },
            { code: "HR", name: "Croatia" },
            { code: "RS", name: "Serbia" },
            { code: "SK", name: "Slovakia" },
            { code: "SI", name: "Slovenia" },
            { code: "LT", name: "Lithuania" },
            { code: "LV", name: "Latvia" },
            { code: "EE", name: "Estonia" }
        ]
    };
    
    /**
     * =====================================================================
     * Initialize Company Search
     * =====================================================================
     */
    CompanySearch.init = function() {
        console.log('🏢 Initializing Company Search module');
        
        this.searchForm = document.getElementById('company-search-form');
        this.resultsContainer = document.getElementById('search-results');
        
        if (!this.searchForm || !this.resultsContainer) {
            console.error('Required elements not found for Company Search');
            return;
        }
        
        this.setupForm();
        this.setupEventListeners();
        this.populateFormOptions();
        
        console.log('✅ Company Search module initialized');
    };
    
    /**
     * =====================================================================
     * Form Setup and Population
     * =====================================================================
     */
    CompanySearch.setupForm = function() {
        this.searchForm.reset();
        
        const limitSelect = document.getElementById('limit');
        if (limitSelect && !limitSelect.value) {
            limitSelect.value = '10';
        }
    };
    
    CompanySearch.populateFormOptions = function() {
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
        this.populateSelectFallback('industries', searchConfig.industries);
        this.populateSelectFallback('company-sizes', searchConfig.companySizes);
        this.populateSelectFallback('countries', searchConfig.countries.map(c => c.name));
        console.log('✅ Fallback company form options populated');
    };
    
    CompanySearch.populateSelectFallback = function(selectId, options) {
        const select = document.getElementById(selectId);
        if (!select) return;
        
        while (select.children.length > 1) {
            select.removeChild(select.lastChild);
        }
        
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
        
        SurfeApp.ui.showLoading('search-results', 'Searching for companies...');
        
        SurfeApp.api.searchCompanies(searchData)
            .then(response => this.handleSearchSuccess(response))
            .catch(error => this.handleSearchError(error))
            .finally(() => {
                this.isSearching = false;
                this.updateSearchButton(false);
            });
    };
    
    CompanySearch.prepareSearchData = function() {
        const formData = SurfeApp.forms.serializeForm(this.searchForm);
        
        const searchData = {
            filters: {},
            limit: parseInt(formData.limit) || 10
        };
        
        if (formData.industries && formData.industries.length > 0) {
            searchData.filters.industries = Array.isArray(formData.industries) ? 
                formData.industries : [formData.industries];
        }
        
        if (formData['company-sizes'] && formData['company-sizes'].length > 0) {
            searchData.filters.company_sizes = Array.isArray(formData['company-sizes']) ? 
                formData['company-sizes'] : [formData['company-sizes']];
        }
        
        if (formData.countries && formData.countries.length > 0) {
            searchData.filters.countries = Array.isArray(formData.countries) ? 
                formData.countries : [formData.countries];
        }
        
        if (formData['company-names']) {
            const names = formData['company-names'].split(',').map(n => n.trim()).filter(n => n);
            if (names.length > 0) {
                searchData.filters.company_names = names;
            }
        }
        
        if (formData['company-domains']) {
            const domains = formData['company-domains'].split(',').map(d => d.trim()).filter(d => d);
            if (domains.length > 0) {
                searchData.filters.company_domains = domains;
            }
        }
        
        return searchData;
    };
    
    CompanySearch.handleSearchSuccess = function(response) {
        console.log('✅ Company search successful:', response);
        
        if (!response.success || !response.data) {
            throw new Error('Invalid response format');
        }
        
        const companies = response.data.companies || [];
        
        this.currentResults = companies;
        this.displayResults(companies);
        
        SurfeApp.ui.showToast(`Found ${companies.length} companies`, 'success');
        this.updateExportButtons(companies.length > 0);
    };
    
    CompanySearch.handleSearchError = function(error) {
        console.error('❌ Company search failed:', error);
        
        const errorMessage = error.message || 'Search failed. Please try again.';
        
        SurfeApp.ui.showError('search-results', errorMessage, 'Search Failed');
        SurfeApp.ui.showToast(errorMessage, 'error');
        
        this.currentResults = [];
        this.updateExportButtons(false);
    };
    
    /**
     * =====================================================================
     * Results Display
     * =====================================================================
     */
    CompanySearch.displayResults = function(companies) {
        if (!companies || companies.length === 0) {
            SurfeApp.ui.showEmpty(
                'search-results', 
                'No companies found matching your criteria. Try adjusting your filters.',
                'fas fa-building'
            );
            return;
        }
        
        const resultsHtml = this.generateResultsHtml(companies);
        this.resultsContainer.innerHTML = resultsHtml;
        
        this.resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    };
    
    CompanySearch.generateResultsHtml = function(companies) {
        const resultsHeader = `
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h4 class="mb-0">
                    <i class="fas fa-building me-2"></i>
                    Search Results (${SurfeApp.utils.formatNumber(companies.length)})
                </h4>
                <div class="action-buttons">
                    <button id="export-csv" class="btn btn-outline-success export-button">
                        <i class="fas fa-file-csv me-2"></i>Export CSV
                    </button>
                    <button id="export-json" class="btn btn-outline-info export-button">
                        <i class="fas fa-file-code me-2"></i>Export JSON
                    </button>
                </div>
            </div>
        `;
        
        const companyCards = companies.map(company => this.generateCompanyCard(company)).join('');
        
        return resultsHeader + '<div class="row">' + companyCards + '</div>';
    };
    
    CompanySearch.generateCompanyCard = function(company) {
        return `
            <div class="col-lg-6 col-xl-4 mb-4">
                <div class="result-card h-100">
                    <div class="result-header">
                        <h6 class="mb-1">${SurfeApp.utils.sanitizeHtml(company.name || 'Unknown Company')}</h6>
                        <small class="text-muted">${SurfeApp.utils.sanitizeHtml(company.domain || 'No domain')}</small>
                    </div>
                    <div class="result-body">
                        <div class="result-meta">
                            <div class="meta-item">
                                <div class="meta-label">Industry</div>
                                <div class="meta-value">${SurfeApp.utils.sanitizeHtml(company.industry || 'N/A')}</div>
                            </div>
                            <div class="meta-item">
                                <div class="meta-label">Size</div>
                                <div class="meta-value">${SurfeApp.utils.formatNumber(company.employeeCount || 0)} employees</div>
                            </div>
                            <div class="meta-item">
                                <div class="meta-label">Location</div>
                                <div class="meta-value">${SurfeApp.utils.sanitizeHtml(company.location || 'N/A')}</div>
                            </div>
                            <div class="meta-item">
                                <div class="meta-label">Founded</div>
                                <div class="meta-value">${company.founded || 'N/A'}</div>
                            </div>
                            ${company.revenue ? `
                                <div class="meta-item">
                                    <div class="meta-label">Revenue</div>
                                    <div class="meta-value">${SurfeApp.utils.sanitizeHtml(company.revenue)}</div>
                                </div>
                            ` : ''}
                            ${company.website ? `
                                <div class="meta-item">
                                    <div class="meta-label">Website</div>
                                    <div class="meta-value">
                                        <a href="${company.website}" target="_blank" class="text-decoration-none">
                                            <i class="fas fa-external-link-alt me-1"></i>Visit Site
                                        </a>
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                        ${company.description ? `
                            <div class="mt-3">
                                <div class="meta-label">Description</div>
                                <p class="small mb-0">${SurfeApp.utils.sanitizeHtml(company.description.substring(0, 150))}${company.description.length > 150 ? '...' : ''}</p>
                            </div>
                        ` : ''}
                        <div class="mt-3">
                            <span class="badge bg-primary">${SurfeApp.utils.sanitizeHtml(company.industry || 'Unknown')}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    };
    
    /**
     * =====================================================================
     * Export and UI Functions
     * =====================================================================
     */
    CompanySearch.exportResults = function(format) {
        if (!this.currentResults || this.currentResults.length === 0) {
            SurfeApp.ui.showToast('No results to export', 'warning');
            return;
        }
        
        const timestamp = new Date().toISOString().split('T')[0];
        const filename = `company_search_${timestamp}`;
        
        if (format === 'csv') {
            const csvData = this.currentResults.map(company => ({
                'Company Name': company.name || '',
                'Domain': company.domain || '',
                'Industry': company.industry || '',
                'Employee Count': company.employeeCount || '',
                'Location': company.location || '',
                'Founded': company.founded || '',
                'Revenue': company.revenue || '',
                'Website': company.website || '',
                'Description': company.description || ''
            }));
            
            SurfeApp.export.toCsv(csvData, `${filename}.csv`);
        } else if (format === 'json') {
            SurfeApp.export.toJson(this.currentResults, `${filename}.json`);
        }
    };
    
    CompanySearch.updateSearchButton = function(isLoading) {
        const submitBtn = this.searchForm.querySelector('button[type="submit"]');
        if (!submitBtn) return;
        
        if (isLoading) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                Searching...
            `;
        } else {
            submitBtn.disabled = false;
            submitBtn.innerHTML = `
                <i class="fas fa-search me-2"></i>
                Search Companies
            `;
        }
    };
    
    CompanySearch.updateExportButtons = function(enabled) {
        const exportCsvBtn = document.getElementById('export-csv');
        const exportJsonBtn = document.getElementById('export-json');
        
        if (exportCsvBtn) {
            exportCsvBtn.disabled = !enabled;
            exportCsvBtn.addEventListener('click', () => this.exportResults('csv'));
        }
        
        if (exportJsonBtn) {
            exportJsonBtn.disabled = !enabled;
            exportJsonBtn.addEventListener('click', () => this.exportResults('json'));
        }
    };
    
    CompanySearch.resetForm = function() {
        this.searchForm.reset();
        this.setupForm();
        this.resultsContainer.innerHTML = '';
        this.currentResults = [];
        this.updateExportButtons(false);
        
        SurfeApp.ui.showToast('Form reset successfully', 'info');
    };
    
    /**
     * =====================================================================
     * Auto-initialize when DOM is ready
     * =====================================================================
     */
    document.addEventListener('DOMContentLoaded', function() {
        if (document.getElementById('company-search-form')) {
            CompanySearch.init();
        }
    });
    
    // Export module for external access
    window.CompanySearch = CompanySearch;
    
})();
