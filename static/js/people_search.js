/**
 * =====================================================================
 * People Search Module v2 - Clean Implementation with Better Field Sizing
 * Features: Advanced filtering, domain handling, responsive layout
 * =====================================================================
 */

(function() {
    'use strict';
    
    // Module namespace
    const PeopleSearchV2 = {
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
     * Initialize People Search V2
     * =====================================================================
     */
    PeopleSearchV2.init = function() {
        console.log('🔍 Initializing People Search module v2');
        
        this.searchForm = document.getElementById('people-search-form');
        this.resultsContainer = document.getElementById('search-results');
        
        if (!this.searchForm || !this.resultsContainer) {
            console.error('Required elements not found for People Search v2');
            return;
        }
        
        this.setupForm();
        this.setupEventListeners();
        this.populateFormOptions();
        this.setupDomainFiltering();
        
        console.log('✅ People Search module v2 initialized');
    };

    /**
     * =====================================================================
     * Form Setup and Population
     * =====================================================================
     */
    PeopleSearchV2.setupForm = function() {
        this.searchForm.reset();
        
        // Set default values
        const limitSelect = document.getElementById('limit');
        if (limitSelect && !limitSelect.value) {
            limitSelect.value = '10';
        }
        
        const peoplePerCompanySelect = document.getElementById('peoplePerCompany');
        if (peoplePerCompanySelect && !peoplePerCompanySelect.value) {
            peoplePerCompanySelect.value = '1';
        }
    };
    
    PeopleSearchV2.populateFormOptions = function() {
        // Use centralized autocomplete functionality
        if (window.SurfeApp && window.SurfeApp.autocomplete) {
            return window.SurfeApp.autocomplete.populatePeopleSearchForm();
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
    PeopleSearchV2.setupEventListeners = function() {
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
    PeopleSearchV2.setupDomainFiltering = function() {
        this.updateDomainCounts();
    };
    
    PeopleSearchV2.setupDomainEventListeners = function() {
        // Include domains events
        const includeManual = document.getElementById('include-domains-manual');
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
        const excludeManual = document.getElementById('exclude-domains-manual');
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
    PeopleSearchV2.updateDomainCounts = function() {
        // Count include domains
        const includeText = document.getElementById('include-domains-manual').value;
        const includeDomains = SurfeApp.utils.parseTextareaLines(includeText);
        this.domainCounts.include = includeDomains.length;
        
        // Count exclude domains
        const excludeText = document.getElementById('exclude-domains-manual').value;
        const excludeDomains = SurfeApp.utils.parseTextareaLines(excludeText);
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
    
    PeopleSearchV2.handleDomainCsvUpload = function(event, type) {
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
    
    PeopleSearchV2.handleColumnSelection = function(event, type) {
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
        const textareaId = type === 'include' ? 'include-domains-manual' : 'exclude-domains-manual';
        const textarea = document.getElementById(textareaId);
        
        if (textarea) {
            const existingContent = textarea.value.trim();
            const newContent = existingContent ? existingContent + '\n' + domains.join('\n') : domains.join('\n');
            textarea.value = newContent;
            this.updateDomainCounts();
            SurfeApp.ui.showToast(`Added ${domains.length} domains from CSV`, 'success');
        }
    };
    
    PeopleSearchV2.clearDomains = function(type) {
        const textareaId = type === 'include' ? 'include-domains-manual' : 'exclude-domains-manual';
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
    PeopleSearchV2.performSearch = function() {
        if (this.isSearching) return;
        
        this.isSearching = true;
        SurfeApp.utils.updateButtonState(document.querySelector('#people-search-form button[type="submit"]'), true, 'Searching...', 'Search People');
        
        const formData = this.collectFormData();

        // Add selected key from localStorage
        const selectedKey = localStorage.getItem('surfe_selected_key');
        if (selectedKey) {
            formData._selectedKey = selectedKey;
        }

        console.log('🔍 Performing people search with data:', formData);

        fetch('/api/v2/people/search', {
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
            SurfeApp.utils.updateButtonState(document.querySelector('#people-search-form button[type="submit"]'), false, 'Searching...', 'Search People');
        });
    };
    
    
    PeopleSearchV2.collectFormData = function() {
        const formData = new FormData(this.searchForm);
        
        // Build authentic Surfe API v2 structure
        const searchRequest = {
            companies: {},
            people: {},
            limit: 10,
            pageToken: null
        };
        
        // Get basic form data
        const formFields = {};
        for (let [key, value] of formData.entries()) {
            if (value && typeof value === 'string' && value.trim()) {
                formFields[key] = value.trim();
            }
        }
        
        // Companies object structure
        const companies = {};
        
        // Handle industries (companies.industries array)
        const industriesInput = document.getElementById('industries');
        if (industriesInput && industriesInput.value.trim()) {
            companies.industries = [industriesInput.value.trim()];
        }
        
        // Handle company countries (companies.countries array)
        const companyCountriesInput = document.getElementById('company-countries');
        if (companyCountriesInput && companyCountriesInput.value.trim()) {
            companies.countries = [companyCountriesInput.value.trim()];
        }
        
        // Handle company names (companies.names array)
        if (formFields['company-names']) {
            const names = SurfeApp.utils.parseTextareaLines(formFields['company-names']);
            if (names.length > 0) {
                companies.names = names;
            }
        }
        
        // Handle domains and domainsExcluded with proper domain cleaning
        const includeDomains = SurfeApp.utils.parseTextareaDomains(
            document.getElementById('include-domains-manual').value
        );
        
        const excludeDomains = SurfeApp.utils.parseTextareaDomains(
            document.getElementById('exclude-domains-manual').value
        );
        
        const uniqueIncludeDomains = [...new Set(includeDomains)];

        if (uniqueIncludeDomains.length > 0) {
            companies.domains = uniqueIncludeDomains;
        }
        
        const uniqueExcludeDomains = [...new Set(excludeDomains)];

        if (uniqueExcludeDomains.length > 0) {
            companies.domainsExcluded = uniqueExcludeDomains;
        }
        
        // Handle employee count range (companies.employeeCount object)
        const empCountFrom = formFields['employee-count-from'];
        const empCountTo = formFields['employee-count-to'];
        if (empCountFrom || empCountTo) {
            companies.employeeCount = {};
            if (empCountFrom) companies.employeeCount.from = parseInt(empCountFrom);
            if (empCountTo) companies.employeeCount.to = parseInt(empCountTo);
        }
        
        // Handle revenue range (companies.revenue object)
        const revenueFrom = formFields['revenue-from'];
        const revenueTo = formFields['revenue-to'];
        if (revenueFrom || revenueTo) {
            companies.revenue = {};
            if (revenueFrom) companies.revenue.from = parseInt(revenueFrom);
            if (revenueTo) companies.revenue.to = parseInt(revenueTo);
        }
        
        // People object structure
        const people = {};
        
        // Handle people countries (people.countries array)
        const peopleCountriesInput = document.getElementById('people-countries');
        if (peopleCountriesInput && peopleCountriesInput.value.trim()) {
            people.countries = [peopleCountriesInput.value.trim()];
        }
        
        // Handle seniorities (people.seniorities array)
        const senioritiesInput = document.getElementById('seniorities');
        if (senioritiesInput && senioritiesInput.value.trim()) {
            people.seniorities = [senioritiesInput.value.trim()];
        }
        
        // Handle departments (people.departments array)
        const departmentsInput = document.getElementById('departments');
        if (departmentsInput && departmentsInput.value.trim()) {
            people.departments = [departmentsInput.value.trim()];
        }
        
        // Handle job titles (people.jobTitles array)
        if (formFields['job-titles']) {
            const jobTitles = SurfeApp.utils.parseTextareaLines(formFields['job-titles']);
            if (jobTitles.length > 0) {
                people.jobTitles = jobTitles;
            }
        }
        
        // Handle limit (1-200, default 10)
        const limitValue = parseInt(formFields['limit']) || 10;
        searchRequest.limit = Math.min(Math.max(limitValue, 1), 200);
        
        // Handle peoplePerCompany (1-5)
        if (formFields['people-per-company']) { // Use the correct key with hyphens
            const peoplePerCompany = parseInt(formFields['people-per-company']);
            if (peoplePerCompany >= 1 && peoplePerCompany <= 5) {
                searchRequest.peoplePerCompany = peoplePerCompany;
            }
        }
        
        // Only include non-empty objects
        if (Object.keys(companies).length > 0) {
            searchRequest.companies = companies;
        }
        
        if (Object.keys(people).length > 0) {
            searchRequest.people = people;
        }
        
        return searchRequest;
    };
    
    PeopleSearchV2.handleSearchResponse = function(data) {
        if (data.success && data.data && data.data.people && data.data.people.length > 0) {
            this.currentResults = data.data.people;
            this.displayResults(data.data.people);
            SurfeApp.ui.showToast(`Found ${data.data.people.length} people`, 'success');
        } else if (data.success && data.data && data.data.people && data.data.people.length === 0) {
            this.displayNoResults();
            SurfeApp.ui.showToast('No people found with current filters', 'info');
        } else {
            this.displayError(data.error || 'Search failed');
            SurfeApp.ui.showToast(data.error || 'Search failed', 'error');
        }
    };

    /**
     * =====================================================================
     * Results Display
     * =====================================================================
     */
    PeopleSearchV2.displayResults = function(people) {
        const resultsSection = document.getElementById('results-section');
        SurfeApp.utils.show(resultsSection);
        
        // Debug: Log first person to see what data is available
        if (people.length > 0) {
            console.log('🔍 Sample person data:', people[0]);
            console.log('🔍 Available fields:', Object.keys(people[0]));
        }
        
        let html = `
            <div class="row">
                <div class="col-12 mb-3">
                    <div class="alert alert-success">
                        <i class="fas fa-check-circle me-2"></i>
                        Found <strong>${people.length}</strong> people matching your search criteria
                    </div>
                </div>
            </div>
            <div class="row">
        `;
        
        people.forEach(person => {
            html += this.createPersonCard(person);
        });
        
        html += '</div>';
        this.resultsContainer.innerHTML = html;
    };
    
    PeopleSearchV2.createPersonCard = function(person) {
        // Handle multiple possible field name formats from API
        const firstName = person.firstName || person.first_name || '';
        const lastName = person.lastName || person.last_name || '';
        const name = SurfeApp.utils.sanitizeHtml(`${firstName} ${lastName}`.trim()) || 'Unknown Name';
        
        const company = SurfeApp.utils.sanitizeHtml(
            person.companyName || person.company_name || person.company || 'Unknown Company'
        );
        
        const title = SurfeApp.utils.sanitizeHtml(
            person.jobTitle || person.job_title || person.title || 'Unknown Title'
        );
        
        const email = SurfeApp.utils.sanitizeHtml(person.email || '');
        const PersonlinkedinUrl = person.linkedInUrl || person.linkedin_url || person.linkedIn || '';
        
        // Additional fields that might be available
        const location = SurfeApp.utils.sanitizeHtml(person.location || person.city || '');
        const country = SurfeApp.utils.sanitizeHtml(person.country || '');
        const seniority = SurfeApp.utils.sanitizeHtml(person.seniorities ? person.seniorities.join(', ') : '');
        const department = SurfeApp.utils.sanitizeHtml(person.departments ? person.departments.join(', ') : '');
        const companyDomain = SurfeApp.utils.sanitizeHtml(person.companyDomain || person.company_domain || '');
        const mobile = SurfeApp.utils.sanitizeHtml(person.mobile || person.phone || '');
        
        return `
            <div class="col-lg-6 col-xl-4 mb-3">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="d-flex align-items-start mb-2">
                            <div class="me-3">
                                <i class="fas fa-user-circle fa-2x text-primary"></i>
                            </div>
                            <div class="flex-grow-1">
                                <h6 class="card-title mb-1">${name}</h6>
                                <p class="text-muted small mb-2">${title}</p>
                                <p class="text-primary small mb-0">
                                    <i class="fas fa-building me-1"></i>${company}
                                </p>
                            </div>
                        </div>
                        
                        <div class="person-details">
                            ${email ? `
                                <div class="d-flex align-items-center mb-1">
                                    <i class="fas fa-envelope text-muted me-2 small"></i>
                                    <small class="text-truncate">${email}</small>
                                </div>
                            ` : ''}
                            
                            ${mobile ? `
                                <div class="d-flex align-items-center mb-1">
                                    <i class="fas fa-phone text-muted me-2 small"></i>
                                    <small>${mobile}</small>
                                </div>
                            ` : ''}
                            
                            ${location || country ? `
                                <div class="d-flex align-items-center mb-1">
                                    <i class="fas fa-map-marker-alt text-muted me-2 small"></i>
                                    <small>${[location, country].filter(Boolean).join(', ')}</small>
                                </div>
                            ` : ''}
                            
                            ${seniority ? `
                                <div class="d-flex align-items-center mb-1">
                                    <i class="fas fa-level-up-alt text-muted me-2 small"></i>
                                    <small>Seniority: ${seniority}</small>
                                </div>
                            ` : ''}
                            
                            ${department ? `
                                <div class="d-flex align-items-center mb-1">
                                    <i class="fas fa-users text-muted me-2 small"></i>
                                    <small>Department: ${department}</small>
                                </div>
                            ` : ''}
                            
                            ${companyDomain ? `
                                <div class="d-flex align-items-center mb-1">
                                    <i class="fas fa-globe text-muted me-2 small"></i>
                                    <small>${companyDomain}</small>
                                </div>
                            ` : ''}
                        </div>
                        
                        <div class="mt-3">
                            ${PersonlinkedinUrl ? `
                                <a href="${PersonlinkedinUrl}" target="_blank" class="btn btn-outline-primary btn-sm me-2">
                                    <i class="fab fa-linkedin me-1"></i>Person linkedin Url
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
    
    PeopleSearchV2.displayNoResults = function() {
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
    
    PeopleSearchV2.displayError = function(message) {
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
    PeopleSearchV2.clearForm = function() {
        SurfeApp.utils.resetForm('people-search-form');
        this.setupForm();
        this.updateDomainCounts();
        SurfeApp.utils.hide(document.getElementById('results-section'));
        SurfeApp.ui.showToast('Form cleared', 'info');
    };
    
    PeopleSearchV2.exportResults = function(format) {
        if (!this.currentResults || this.currentResults.length === 0) {
            SurfeApp.ui.showToast('No results to export', 'error');
            return;
        }

        const timestamp = new Date().toISOString().split('T')[0];
        const filename = `people_search_${timestamp}.${format}`;

        if (format === 'csv') {
            // This now includes the 'people' type
            SurfeApp.utils.exportToCsv(this.currentResults, filename, 'people');
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
        if (document.getElementById('people-search-form')) {
            PeopleSearchV2.init();
        }
    });

    // Export for global access
    window.PeopleSearchV2 = PeopleSearchV2;

})();
