/**
 * =====================================================================
 * Company Search Module v3 - Clean Implementation with Better Field Sizing
 * Features: Advanced filtering, clean layout, responsive design
 * =====================================================================
 */

(function() {
    'use strict';
    
    // Module namespace
    const CompanySearchV3 = {
        currentResults: [],
        isSearching: false,
        searchForm: null,
        resultsContainer: null,
        domainCounts: {
            include: 0,
            exclude: 0
        },
        csvData: {
            include: null,
            exclude: null
        }
    };

    /**
     * =====================================================================
     * Initialize Company Search V3
     * =====================================================================
     */
    CompanySearchV3.init = function() {
        console.log('🏢 Initializing Company Search module v3');
        
        this.searchForm = document.getElementById('company-search-form');
        this.resultsContainer = document.getElementById('search-results');
        
        if (!this.searchForm || !this.resultsContainer) {
            console.error('Required elements not found for Company Search v3');
            return;
        }
        
        this.setupForm();
        this.setupEventListeners();
        this.populateFormOptions();
        this.setupDomainFiltering();
        
        console.log('✅ Company Search module v3 initialized');
    };

    /**
     * =====================================================================
     * Form Setup and Population
     * =====================================================================
     */
    CompanySearchV3.setupForm = function() {
        this.searchForm.reset();
        
        // Set default values
        const limitSelect = document.getElementById('limit');
        if (limitSelect && !limitSelect.value) {
            limitSelect.value = '10';
        }
    };
    
    CompanySearchV3.populateFormOptions = function() {
        // Use centralized autocomplete functionality
        if (window.SurfeApp && window.SurfeApp.autocomplete) {
            return window.SurfeApp.autocomplete.populateCompanySearchForm();
        } else {
            console.warn('SurfeApp autocomplete not available');
            return false;
        }
    };

    /**
     * =====================================================================
     * Event Listeners
     * =====================================================================
     */
    CompanySearchV3.setupEventListeners = function() {
        // Form submission
        this.searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.performSearch();
        });
        
        // Clear form button
        const clearBtn = document.getElementById('clear-form');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearForm());
        }
        
        // Export buttons
        const exportCsvBtn = document.getElementById('export-csv');
        const exportJsonBtn = document.getElementById('export-json');
        
        if (exportCsvBtn) {
            exportCsvBtn.addEventListener('click', () => this.exportResults('csv'));
        }
        
        if (exportJsonBtn) {
            exportJsonBtn.addEventListener('click', () => this.exportResults('json'));
        }
        
        // Domain filtering events
        this.setupDomainEventListeners();
    };

    /**
     * =====================================================================
     * Domain Filtering Setup
     * =====================================================================
     */
    CompanySearchV3.setupDomainFiltering = function() {
        this.updateDomainCounts();
    };
    
    CompanySearchV3.setupDomainEventListeners = function() {
        // Include domains events
        const includeManual = document.getElementById('domains');
        const includeCsv = document.getElementById('include-domains-csv');
        const includeColumnSelect = document.getElementById('include-domain-column');
        const clearInclude = document.getElementById('clear-include-domains');
        
        if (includeManual) {
            includeManual.addEventListener('input', () => this.updateDomainCounts());
        }
        
        if (includeCsv) {
            includeCsv.addEventListener('change', (e) => this.handleDomainCsvUpload(e, 'include'));
        }
        
        if (includeColumnSelect) {
            includeColumnSelect.addEventListener('change', (e) => this.handleColumnSelection(e, 'include'));
        }
        
        if (clearInclude) {
            clearInclude.addEventListener('click', () => this.clearDomains('include'));
        }
        
        // Exclude domains events
        const excludeManual = document.getElementById('domains-excluded');
        const excludeCsv = document.getElementById('exclude-domains-csv');
        const excludeColumnSelect = document.getElementById('exclude-domain-column');
        const clearExclude = document.getElementById('clear-exclude-domains');
        
        if (excludeManual) {
            excludeManual.addEventListener('input', () => this.updateDomainCounts());
        }
        
        if (excludeCsv) {
            excludeCsv.addEventListener('change', (e) => this.handleDomainCsvUpload(e, 'exclude'));
        }
        
        if (excludeColumnSelect) {
            excludeColumnSelect.addEventListener('change', (e) => this.handleColumnSelection(e, 'exclude'));
        }
        
        if (clearExclude) {
            clearExclude.addEventListener('click', () => this.clearDomains('exclude'));
        }
    };

    /**
     * =====================================================================
     * Domain Management
     * =====================================================================
     */
    CompanySearchV3.updateDomainCounts = function() {
        // Count include domains using domain cleaning
        const includeText = document.getElementById('domains').value;
        const includeDomains = SurfeApp.utils.parseTextareaDomains(includeText);
        this.domainCounts.include = includeDomains.length;
        
        // Count exclude domains using domain cleaning  
        const excludeText = document.getElementById('domains-excluded').value;
        const excludeDomains = SurfeApp.utils.parseTextareaDomains(excludeText);
        this.domainCounts.exclude = excludeDomains.length;
        
        // Update badges
        const includeCountBadge = document.getElementById('include-domains-count');
        const excludeCountBadge = document.getElementById('exclude-domains-count');
        
        if (includeCountBadge) {
            includeCountBadge.textContent = `${this.domainCounts.include} domains`;
        }
        
        if (excludeCountBadge) {
            excludeCountBadge.textContent = `${this.domainCounts.exclude} domains`;
        }
    };
    
    CompanySearchV3.handleDomainCsvUpload = function(event, type) {
        const file = event.target.files[0];
        if (!file) return;
        
        const validation = SurfeApp.utils.validateCSVFile(file, 5 * 1024 * 1024); // 5MB limit
        
        if (!validation.valid) {
            SurfeApp.ui.showToast(validation.errors.join(', '), 'error');
            event.target.value = '';
            return;
        }
        
        // Read file directly as FileReader
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const content = e.target.result;
                
                // Parse CSV content as raw text lines and split by delimiter
                const lines = content.split('\n').filter(line => line.trim().length > 0);
                
                if (lines.length === 0) {
                    SurfeApp.ui.showToast('CSV file is empty or invalid', 'error');
                    return;
                }
                
                // Parse each line as an array of values
                const csvData = lines.map(line => SurfeApp.utils.parseCSVLine(line, ','));
                
                if (csvData.length === 0) {
                    SurfeApp.ui.showToast('CSV file is empty or invalid', 'error');
                    return;
                }
                
                // Store CSV data
                this.csvData[type] = csvData;
                
                // Populate column selector
                const columnSelectId = type === 'include' ? 'include-domain-column' : 'exclude-domain-column';
                const columnSelect = document.getElementById(columnSelectId);
                
                if (columnSelect) {
                    columnSelect.innerHTML = '<option value="">Select column...</option>';
                    
                    // Get column headers (first row)
                    const headers = csvData[0];
                    headers.forEach((header, index) => {
                        const option = document.createElement('option');
                        option.value = index;
                        option.textContent = header.trim();
                        columnSelect.appendChild(option);
                    });
                    
                    SurfeApp.ui.showToast(`CSV loaded with ${csvData.length - 1} rows. Please select domain column.`, 'info');
                }
            } catch (error) {
                console.error('Error parsing CSV file:', error);
                SurfeApp.ui.showToast('Error parsing CSV file', 'error');
            }
        };
        
        reader.onerror = () => {
            SurfeApp.ui.showToast('Error reading CSV file', 'error');
        };
        
        reader.readAsText(file);
        event.target.value = '';
    };
    
    CompanySearchV3.handleColumnSelection = function(event, type) {
        const columnIndex = parseInt(event.target.value);
        const csvData = this.csvData[type];
        
        if (!csvData || isNaN(columnIndex)) {
            return;
        }
        
        // Extract domains from selected column (skip header row)
        const domains = [];
        for (let i = 1; i < csvData.length; i++) {
            const domain = csvData[i][columnIndex];
            if (domain && domain.trim()) {
                domains.push(domain.trim());
            }
        }
        
        if (domains.length === 0) {
            SurfeApp.ui.showToast('No valid domains found in selected column', 'warning');
            return;
        }
        
        // Add domains to textarea
        const textareaId = type === 'include' ? 'domains' : 'domains-excluded';
        const textarea = document.getElementById(textareaId);
        
        if (textarea) {
            const existingContent = textarea.value.trim();
            const newContent = existingContent ? existingContent + '\n' + domains.join('\n') : domains.join('\n');
            textarea.value = newContent;
            this.updateDomainCounts();
            SurfeApp.ui.showToast(`Added ${domains.length} domains from CSV`, 'success');
        }
    };
    
    CompanySearchV3.clearDomains = function(type) {
        const textareaId = type === 'include' ? 'domains' : 'domains-excluded';
        const columnSelectId = type === 'include' ? 'include-domain-column' : 'exclude-domain-column';
        
        // Clear textarea
        const textarea = document.getElementById(textareaId);
        if (textarea) {
            textarea.value = '';
        }
        
        // Clear column selector
        const columnSelect = document.getElementById(columnSelectId);
        if (columnSelect) {
            columnSelect.innerHTML = '<option value="">Select column...</option>';
        }
        
        // Clear stored CSV data
        this.csvData[type] = null;
        
        this.updateDomainCounts();
        SurfeApp.ui.showToast(`${type} domains cleared`, 'info');
    };

    /**
     * =====================================================================
     * Search Functionality
     * =====================================================================
     */
    CompanySearchV3.performSearch = function() {
        if (this.isSearching) return;
        
        this.isSearching = true;
        SurfeApp.utils.updateButtonState(document.querySelector('#company-search-form button[type="submit"]'), true, 'Searching...', 'Search Companies');
        
        const formData = this.collectFormData();

        // Add selected key from localStorage
        const selectedKey = localStorage.getItem('surfe_selected_key');

        console.log('🔍 Performing company search with data:', formData);
        console.log('🔑 Using selected key:', selectedKey || 'default');

        fetch('/api/v2/companies/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Selected-Key': selectedKey || '', // Add this header
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            this.handleSearchResponse(data);
        })
        .catch(error => {
            console.error('Search error:', error);
            SurfeApp.ui.showToast('Search failed. Please try again.', 'error');
            this.displayError('Search request failed');
        })
        .finally(() => {
            this.isSearching = false;
            SurfeApp.utils.updateButtonState(document.querySelector('#company-search-form button[type="submit"]'), false, 'Searching...', 'Search Companies');
        });
    };
    
    CompanySearchV3.collectFormData = function() {
        // Build the authentic Surfe API company search structure
        const requestData = {
            filters: {},
            limit: 10,
            pageToken: ""
        };
        
        // Get form values
        const getInputValue = (id) => {
            const element = document.getElementById(id);
            return element ? element.value.trim() : '';
        };
        
        const getTextareaLines = (id) => {
            const value = getInputValue(id);
            return value ? SurfeApp.utils.parseTextareaLines(value) : [];
        };
        
        const getTextareaDomains = (id) => {
            const value = getInputValue(id);
            return value ? SurfeApp.utils.parseTextareaDomains(value) : [];
        };
        
        // Handle industries array
        const industries = getInputValue('industries');
        if (industries) {
            requestData.filters.industries = [industries];
        }
        
        // Handle countries array (convert to ISO codes if needed)
        const countries = getInputValue('countries');
        if (countries) {
            // For now, pass as-is, but could add country code conversion
            requestData.filters.countries = [countries.toLowerCase()];
        }
        
        // Handle domains and domainsExcluded arrays with proper domain cleaning
        const domains = getTextareaDomains('domains');
        if (domains.length > 0) {
            requestData.filters.domains = domains;
        }
        
        const domainsExcluded = getTextareaDomains('domains-excluded');
        if (domainsExcluded.length > 0) {
            requestData.filters.domainsExcluded = domainsExcluded;
        }
        
        // Handle employee count range
        const employeeMin = getInputValue('employee-min');
        const employeeMax = getInputValue('employee-max');
        if (employeeMin || employeeMax) {
            requestData.filters.employeeCount = {
                from: parseInt(employeeMin) || 1,
                to: parseInt(employeeMax) || 999999999999999
            };
        }
        
        // Handle revenue range
        const revenueMin = getInputValue('revenue-min');
        const revenueMax = getInputValue('revenue-max');
        if (revenueMin || revenueMax) {
            requestData.filters.revenue = {
                from: parseInt(revenueMin) || 1,
                to: parseInt(revenueMax) || 999999999999999
            };
        }
        
        // Handle limit
        const limit = getInputValue('limit');
        if (limit) {
            requestData.limit = parseInt(limit);
        }
        
        // Handle page token
        const pageToken = getInputValue('page-token');
        if (pageToken) {
            requestData.pageToken = pageToken;
        }
        
        return requestData;
    };
    
    CompanySearchV3.handleSearchResponse = function(data) {
        // Correctly access the nested 'companies' array inside the 'data' object
        const companies = data?.data?.companies;

        if (data.success && Array.isArray(companies)) {
            this.currentResults = companies;
            if (companies.length > 0) {
                this.displayResults(companies);
                SurfeApp.ui.showToast(`Found ${companies.length} companies`, 'success');
            } else {
                this.displayNoResults();
                SurfeApp.ui.showToast('No companies found with current filters', 'info');
            }
        } else {
            // Display the error message from the backend
            this.displayError(data.error || 'Search failed');
            SurfeApp.ui.showToast(data.error || 'Search failed', 'error');
        }
    };

    /**
     * =====================================================================
     * Results Display
     * =====================================================================
     */
    CompanySearchV3.displayResults = function(companies) {
        const resultsSection = document.getElementById('results-section');
        SurfeApp.utils.show(resultsSection);
        
        // Debug: Log first company to see what data is available
        if (companies.length > 0) {
            console.log('🔍 Sample company data:', companies[0]);
            console.log('🔍 Available fields:', Object.keys(companies[0]));
        }
        
        let html = `
            <div class="row">
                <div class="col-12 mb-3">
                    <div class="alert alert-success">
                        <i class="fas fa-check-circle me-2"></i>
                        Found <strong>${companies.length}</strong> companies matching your search criteria
                    </div>
                </div>
            </div>
            <div class="row">
        `;
        
        companies.forEach(company => {
            html += this.createCompanyCard(company);
        });
        
        html += '</div>';
        this.resultsContainer.innerHTML = html;
    };
    
    CompanySearchV3.createCompanyCard = function(company) {
        // Handle multiple possible field name formats from API
        const name = SurfeApp.utils.sanitizeHtml(
            company.name || company.companyName || company.company_name || 'Unknown Company'
        );
        
        const domain = SurfeApp.utils.sanitizeHtml(
            company.domain || company.companyDomain || company.company_domain || ''
        );
        
        const website = company.website || company.websiteUrl || company.website_url || '';
        
        const industry = SurfeApp.utils.sanitizeHtml(
            company.industry || company.industries || 'Unknown Industry'
        );
        
        const location = SurfeApp.utils.sanitizeHtml(
            company.location || company.headquarters || company.city || company.country || company.countries || 'Unknown Location'
        );
        
        const employeeCount = (company.employee_count || company.employeeCount || company.employees) ? 
            SurfeApp.utils.formatLargeNumber(company.employee_count || company.employeeCount || company.employees) : 'Unknown';
            
        const revenue = (company.revenue || company.annual_revenue || company.annualRevenue) ? 
            SurfeApp.utils.formatRevenue(company.revenue || company.annual_revenue || company.annualRevenue) : 'Unknown';
            
        const description = company.description ? SurfeApp.utils.truncateText(company.description, 100) : '';
        
        // Additional fields that might be available
        const foundedYear = company.founded_year || company.foundedYear || company.founded || '';
        const fundingStage = company.funding_stage || company.fundingStage || '';
        const phone = company.phone || company.phoneNumber || '';
        const email = company.email || company.contactEmail || '';
        const linkedinUrl = company.linkedin_url || company.linkedinUrl || company.linkedIn || '';
        const technologies = company.technologies || company.tech_stack || [];
        
        return `
            <div class="col-lg-6 col-xl-4 mb-3">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="d-flex align-items-start mb-2">
                            <div class="me-3">
                                <i class="fas fa-building fa-2x text-primary"></i>
                            </div>
                            <div class="flex-grow-1">
                                <h6 class="card-title mb-1">${name}</h6>
                                <p class="text-muted small mb-2">${industry}</p>
                                <p class="text-primary small mb-0">
                                    <i class="fas fa-map-marker-alt me-1"></i>${location}
                                </p>
                            </div>
                        </div>
                        
                        <div class="company-metrics mb-3">
                            <div class="row text-center">
                                <div class="col-6">
                                    <div class="metric-item">
                                        <div class="metric-value small">${employeeCount}</div>
                                        <div class="metric-label">Employees</div>
                                    </div>
                                </div>
                                <div class="col-6">
                                    <div class="metric-item">
                                        <div class="metric-value small">${revenue}</div>
                                        <div class="metric-label">Revenue</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="company-details">
                            ${domain ? `
                                <div class="d-flex align-items-center mb-1">
                                    <i class="fas fa-globe text-muted me-2 small"></i>
                                    <small class="text-truncate">${domain}</small>
                                </div>
                            ` : ''}
                            
                            ${email ? `
                                <div class="d-flex align-items-center mb-1">
                                    <i class="fas fa-envelope text-muted me-2 small"></i>
                                    <small class="text-truncate">${email}</small>
                                </div>
                            ` : ''}
                            
                            ${phone ? `
                                <div class="d-flex align-items-center mb-1">
                                    <i class="fas fa-phone text-muted me-2 small"></i>
                                    <small>${phone}</small>
                                </div>
                            ` : ''}
                            
                            ${foundedYear ? `
                                <div class="d-flex align-items-center mb-1">
                                    <i class="fas fa-calendar text-muted me-2 small"></i>
                                    <small>Founded: ${foundedYear}</small>
                                </div>
                            ` : ''}
                            
                            ${fundingStage ? `
                                <div class="d-flex align-items-center mb-1">
                                    <i class="fas fa-chart-line text-muted me-2 small"></i>
                                    <small>Stage: ${fundingStage}</small>
                                </div>
                            ` : ''}
                            
                            ${Array.isArray(technologies) && technologies.length > 0 ? `
                                <div class="d-flex align-items-center mb-1">
                                    <i class="fas fa-code text-muted me-2 small"></i>
                                    <small>Tech: ${technologies.slice(0, 3).join(', ')}</small>
                                </div>
                            ` : ''}
                        </div>
                        
                        ${description ? `<p class="text-muted small mt-2">${description}</p>` : ''}
                        
                        <div class="mt-3">
                            ${website ? `
                                <a href="${website}" target="_blank" class="btn btn-outline-primary btn-sm me-2">
                                    <i class="fas fa-external-link-alt me-1"></i>Website
                                </a>
                            ` : ''}
                            ${linkedinUrl ? `
                                <a href="${linkedinUrl}" target="_blank" class="btn btn-outline-info btn-sm me-2">
                                    <i class="fab fa-linkedin me-1"></i>LinkedIn
                                </a>
                            ` : ''}
                            ${email ? `
                                <a href="mailto:${email}" class="btn btn-outline-secondary btn-sm">
                                    <i class="fas fa-envelope me-1"></i>Email
                                </a>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
    };
    
    CompanySearchV3.displayNoResults = function() {
        const resultsSection = document.getElementById('results-section');
        SurfeApp.utils.show(resultsSection);
        
        this.resultsContainer.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-search fa-3x text-muted mb-3"></i>
                <h5>No Results Found</h5>
                <p class="text-muted">Try adjusting your search filters or criteria.</p>
            </div>
        `;
    };
    
    CompanySearchV3.displayError = function(message) {
        const resultsSection = document.getElementById('results-section');
        SurfeApp.utils.show(resultsSection);
        
        this.resultsContainer.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>Error:</strong> ${SurfeApp.utils.sanitizeHtml(message)}
            </div>
        `;
    };

    /**
     * =====================================================================
     * Utility Functions
     * =====================================================================
     */
    CompanySearchV3.clearForm = function() {
        SurfeApp.utils.resetForm('company-search-form');
        this.setupForm();
        SurfeApp.utils.hide(document.getElementById('results-section'));
        SurfeApp.ui.showToast('Form cleared', 'info');
    };
    
    CompanySearchV3.exportResults = function(format) {
        if (!this.currentResults || this.currentResults.length === 0) {
            SurfeApp.ui.showToast('No results to export', 'error');
            return;
        }
        
        const timestamp = new Date().toISOString().split('T')[0];
        const filename = `company_search_${timestamp}.${format}`;
        
        if (format === 'csv') {
            SurfeApp.utils.exportToCsv(this.currentResults, filename, 'company');
        } else if (format === 'json') {
            SurfeApp.utils.exportToJson(this.currentResults, filename);
        }
    };

    /**
     * =====================================================================
     * Auto-initialize when DOM is ready
     * =====================================================================
     */
    document.addEventListener('DOMContentLoaded', function() {
        if (document.getElementById('company-search-form')) {
            CompanySearchV3.init();
        }
    });

    // Export for global access
    window.CompanySearchV3 = CompanySearchV3;

})();
