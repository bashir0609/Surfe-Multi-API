/**
 * =====================================================================
 * Company Enrichment Module - Handles company enrichment functionality
 * Features: Manual entry, CSV upload, bulk processing, results display
 * =====================================================================
 */
(function() {
    'use strict';

    /**
     * =====================================================================
     * Configuration and State
     * =====================================================================
     */
    const config = {
        maxFileSize: 5 * 1024 * 1024, // 5MB
        supportedFormats: ['.csv'],
        endpoints: {
            enrich: '/api/v2/companies/enrich',
            enrichBulk: '/api/v2/companies/enrich/bulk'
        }
    };

    let currentInputMethod = 'manual';
    let enrichmentResults = [];

    /**
     * =====================================================================
     * Initialize Company Enrichment
     * =====================================================================
     */
    function initializeCompanyEnrichment() {
        console.log('🚀 Initializing Company Enrichment module');
        
        setupInputMethodSwitching();
        setupEventListeners();
        setupFormValidation();
        
        console.log('✅ Company Enrichment module initialized');
    }

    /**
     * =====================================================================
     * Input Method Switching
     * =====================================================================
     */
    function setupInputMethodSwitching() {
        const methodCards = document.querySelectorAll('.input-method-card');
        const inputSections = document.querySelectorAll('.input-section');

        methodCards.forEach(card => {
            card.addEventListener('click', function() {
                const method = this.dataset.method;
                switchInputMethod(method);
            });
        });
    }

    function switchInputMethod(method) {
        currentInputMethod = method;
        
        // Update active card
        document.querySelectorAll('.input-method-card').forEach(card => {
            card.classList.remove('active');
        });
        document.querySelector(`[data-method="${method}"]`).classList.add('active');
        
        // Show corresponding input section
        document.querySelectorAll('.input-section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(`${method}-input`).classList.add('active');
        
        // Clear previous results if switching methods
        clearResults();
    }

    /**
     * =====================================================================
     * Event Listeners
     * =====================================================================
     */
    function setupEventListeners() {
        // Manual enrichment form
        const manualForm = document.getElementById('company-enrichment-form');
        if (manualForm) {
            manualForm.addEventListener('submit', handleManualEnrichment);
        }

        // CSV upload form
        const csvForm = document.getElementById('csv-upload-form');
        if (csvForm) {
            csvForm.addEventListener('submit', handleCsvUpload);
        }

        // Bulk enrichment form
        const bulkForm = document.getElementById('bulk-enrichment-form');
        if (bulkForm) {
            bulkForm.addEventListener('submit', handleBulkEnrichment);
        }

        // Reset buttons
        document.querySelectorAll('#reset-form').forEach(btn => {
            btn.addEventListener('click', resetCurrentForm);
        });

        // File input validation
        const fileInput = document.getElementById('csv-file');
        if (fileInput) {
            fileInput.addEventListener('change', validateFileInput);
        }
    }

    /**
     * =====================================================================
     * Form Validation
     * =====================================================================
     */
    function setupFormValidation() {
        // URL validation
        const urlInputs = document.querySelectorAll('input[type="url"]');
        urlInputs.forEach(input => {
            input.addEventListener('blur', validateUrlField);
        });

        // Domain validation
        const domainInputs = document.querySelectorAll('input[name="domain"]');
        domainInputs.forEach(input => {
            input.addEventListener('blur', validateDomainField);
        });
    }

    function validateUrlField(event) {
        const input = event.target;
        const url = input.value.trim();
        
        if (url && !SurfeApp.utils.isValidUrl(url)) {
            SurfeApp.forms.showFieldError(input, 'Please enter a valid URL');
        } else {
            SurfeApp.forms.clearFieldError(input);
        }
    }

    function validateDomainField(event) {
        const input = event.target;
        const domain = input.value.trim();
        
        if (domain && !SurfeApp.utils.isValidDomain(domain)) {
            SurfeApp.forms.showFieldError(input, 'Please enter a valid domain (e.g., company.com)');
        } else {
            SurfeApp.forms.clearFieldError(input);
        }
    }

    function validateFileInput(event) {
        const file = event.target.files[0];
        if (!file) return;

        const validation = SurfeApp.utils.validateCSVFile(file, config.maxFileSize);
        
        if (!validation.valid) {
            SurfeApp.ui.showToast(validation.errors.join(', '), 'error');
            event.target.value = '';
            return;
        }

        SurfeApp.ui.showToast('File validated successfully', 'success');
    }

    /**
     * =====================================================================
     * Enrichment Handlers
     * =====================================================================
     */
    async function handleManualEnrichment(event) {
        event.preventDefault();
        
        const formData = SurfeApp.forms.serializeForm(event.target);
        
        // Validate required fields
        if (!validateManualForm(formData)) {
            return;
        }

        // Prepare enrichment data using authentic API v2 structure with domain cleaning
        const rawDomain = formData.domain || '';
        const cleanedDomain = SurfeApp.utils.cleanDomain(rawDomain);
        
        if (!cleanedDomain || !SurfeApp.utils.isValidDomain(cleanedDomain)) {
            SurfeApp.ui.showToast('Please provide a valid domain (e.g., acme.com)', 'error');
            return;
        }
        
        const company = { domain: cleanedDomain };
        
        // Add optional externalID if provided
        if (formData['external-id'] && formData['external-id'].trim()) {
            company.externalID = formData['external-id'].trim();
        }
        
        const enrichmentData = { companies: [company] };

        await performEnrichment(enrichmentData, 'manual');
    }

    async function handleCsvUpload(event) {
        event.preventDefault();
        
        const fileInput = document.getElementById('csv-file');
        const file = fileInput.files[0];
        
        if (!file) {
            SurfeApp.ui.showToast('Please select a CSV file', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        await performEnrichmentWithFile(formData, 'csv');
    }

    async function handleBulkEnrichment(event) {
        event.preventDefault();
        
        const formData = SurfeApp.forms.serializeForm(event.target);
        
        // Parse bulk input and build authentic API v2 structure with domain cleaning
        const rawDomains = SurfeApp.utils.parseTextareaLines(formData.domains);
        const externalIds = SurfeApp.utils.parseTextareaLines(formData.external_ids);
        
        // Build companies array with cleaned domain and optional externalID
        const companies = [];
        rawDomains.forEach((rawDomain, index) => {
            if (rawDomain && rawDomain.trim()) {
                const cleanedDomain = SurfeApp.utils.cleanDomain(rawDomain.trim());
                if (cleanedDomain && SurfeApp.utils.isValidDomain(cleanedDomain)) {
                    const company = { domain: cleanedDomain };
                    if (externalIds[index] && externalIds[index].trim()) {
                        company.externalID = externalIds[index].trim();
                    }
                    companies.push(company);
                }
            }
        });
        
        const enrichmentData = { companies };

        // Validate bulk data
        if (!validateBulkData(enrichmentData)) {
            return;
        }

        await performEnrichment(enrichmentData, 'bulk');
    }

    /**
     * =====================================================================
     * Enrichment Processing
     * =====================================================================
     */
    async function performEnrichment(data, method) {
        const resultsContainer = document.getElementById('enrichment-results');
        SurfeApp.ui.showLoading(resultsContainer, 'Enriching company data...');

        try {
            const response = await SurfeApp.api.request(
                'POST',
                config.endpoints.enrich,
                data
            );

            if (response.success) {
                enrichmentResults = response.data.companies || [];
                displayEnrichmentResults(enrichmentResults, method);
                SurfeApp.ui.showToast(
                    `Successfully enriched ${enrichmentResults.length} companies`, 
                    'success'
                );
            } else {
                throw new Error(response.error || 'Enrichment failed');
            }
        } catch (error) {
            console.error('Enrichment error:', error);
            SurfeApp.ui.showError(resultsContainer, `Enrichment failed: ${error.message}`);
            SurfeApp.ui.showToast('Enrichment failed', 'error');
        }
    }

    async function performEnrichmentWithFile(formData, method) {
        const resultsContainer = document.getElementById('enrichment-results');
        SurfeApp.ui.showLoading(resultsContainer, 'Processing CSV and enriching data...');

        try {
            const response = await fetch(config.endpoints.enrichBulk, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                enrichmentResults = result.data.companies || [];
                displayEnrichmentResults(enrichmentResults, method);
                SurfeApp.ui.showToast(
                    `Successfully processed ${enrichmentResults.length} companies from CSV`, 
                    'success'
                );
            } else {
                throw new Error(result.error || 'CSV processing failed');
            }
        } catch (error) {
            console.error('CSV enrichment error:', error);
            SurfeApp.ui.showError(resultsContainer, `CSV processing failed: ${error.message}`);
            SurfeApp.ui.showToast('CSV processing failed', 'error');
        }
    }

    /**
     * =====================================================================
     * Results Display
     * =====================================================================
     */
    function displayEnrichmentResults(results, method) {
        const resultsContainer = document.getElementById('enrichment-results');
        
        if (!results || results.length === 0) {
            SurfeApp.ui.showEmpty(resultsContainer, 'No enrichment results found');
            return;
        }

        const resultsHtml = `
            <div class="results-header">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <div>
                        <h4><i class="fas fa-building-user me-2"></i>Enrichment Results</h4>
                        <p class="text-muted mb-0">${results.length} companies enriched via ${method} input</p>
                    </div>
                    <div class="d-flex gap-2">
                        <button onclick="exportResults('csv')" class="btn btn-outline-success btn-sm">
                            <i class="fas fa-file-csv me-1"></i>Export CSV
                        </button>
                        <button onclick="exportResults('json')" class="btn btn-outline-info btn-sm">
                            <i class="fas fa-file-code me-1"></i>Export JSON
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="enrichment-grid">
                ${results.map(company => createCompanyCard(company)).join('')}
            </div>
        `;

        resultsContainer.innerHTML = resultsHtml;
    }

    function createCompanyCard(company) {
        // Handle multiple possible field name formats from API
        const name = company.name || company.companyName || company.company_name || 'Unknown Company';
        const domain = company.domain || company.companyDomain || company.company_domain || '';
        const website = company.website || company.websiteUrl || company.website_url || '';
        const industry = company.industry || company.industries || '';
        const location = company.location || company.headquarters || company.city || company.country || '';
        const employeeCount = SurfeApp.utils.formatLargeNumber(company.employee_count || company.employeeCount || company.employees);
        const revenue = (company.annual_revenue || company.revenue || company.annualRevenue) ? 
            SurfeApp.utils.formatRevenue(company.annual_revenue || company.revenue || company.annualRevenue) : null;
        
        return `
            <div class="company-card card mb-3">
                <div class="card-body">
                    <div class="d-flex align-items-start">
                        <div class="company-logo me-3">
                            ${company.logo_url ? 
                                `<img src="${company.logo_url}" alt="${company.name} logo" class="company-logo-img">` :
                                `<i class="fas fa-building fa-2x text-primary"></i>`
                            }
                        </div>
                        <div class="flex-grow-1">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <div>
                                    <h6 class="company-name mb-1">${name}</h6>
                                    <p class="company-industry text-muted mb-1">${industry || 'N/A'}</p>
                                    <p class="company-location small text-primary mb-0">
                                        <i class="fas fa-map-marker-alt me-1"></i>${location || 'N/A'}
                                    </p>
                                </div>
                                <div class="company-actions">
                                    ${website ? `<a href="${website}" target="_blank" class="btn btn-outline-primary btn-sm me-1" title="Visit Website">
                                        <i class="fas fa-external-link-alt"></i>
                                    </a>` : ''}
                                    ${company.linkedin_url || company.linkedinUrl || company.linkedIn ? `<a href="${company.linkedin_url || company.linkedinUrl || company.linkedIn}" target="_blank" class="btn btn-outline-info btn-sm" title="View LinkedIn">
                                        <i class="fab fa-linkedin"></i>
                                    </a>` : ''}
                                </div>
                            </div>
                            
                            <div class="company-metrics mb-3">
                                <div class="row">
                                    <div class="col-md-3">
                                        <div class="metric-item">
                                            <div class="metric-value">${employeeCount}</div>
                                            <div class="metric-label">Employees</div>
                                        </div>
                                    </div>
                                    <div class="col-md-3">
                                        <div class="metric-item">
                                            <div class="metric-value">${revenue || 'N/A'}</div>
                                            <div class="metric-label">Revenue</div>
                                        </div>
                                    </div>
                                    <div class="col-md-3">
                                        <div class="metric-item">
                                            <div class="metric-value">${company.founded_year || 'N/A'}</div>
                                            <div class="metric-label">Founded</div>
                                        </div>
                                    </div>
                                    <div class="col-md-3">
                                        <div class="metric-item">
                                            <div class="metric-value">${company.funding_stage || 'N/A'}</div>
                                            <div class="metric-label">Stage</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="company-details">
                                <div class="row">
                                    <div class="col-md-6">
                                        ${domain ? `<small class="d-block text-muted">
                                            <i class="fas fa-globe me-1"></i>Domain: ${domain}
                                        </small>` : ''}
                                        ${company.phone || company.phoneNumber ? `<small class="d-block text-muted">
                                            <i class="fas fa-phone me-1"></i>${company.phone || company.phoneNumber}
                                        </small>` : ''}
                                        ${company.email || company.contactEmail ? `<small class="d-block text-muted">
                                            <i class="fas fa-envelope me-1"></i>${company.email || company.contactEmail}
                                        </small>` : ''}
                                    </div>
                                    <div class="col-md-6">
                                        ${company.technologies ? `<small class="d-block text-muted">
                                            <i class="fas fa-code me-1"></i>Tech: ${Array.isArray(company.technologies) ? company.technologies.slice(0, 3).join(', ') : company.technologies}
                                        </small>` : ''}
                                        ${company.description ? `<small class="d-block text-muted company-description">
                                            <i class="fas fa-info-circle me-1"></i>${SurfeApp.utils.truncateText(company.description, 100)}
                                        </small>` : ''}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * =====================================================================
     * Utility Functions
     * =====================================================================
     */
    function validateManualForm(formData) {
        const hasDomain = formData.domain && formData.domain.trim();

        if (!hasDomain) {
            SurfeApp.ui.showToast('Company domain is required for enrichment', 'error');
            return false;
        }

        return true;
    }

    function validateBulkData(data) {
        const hasCompanies = data.companies && data.companies.length > 0;
        
        if (!hasCompanies) {
            SurfeApp.ui.showToast('Please provide at least one company domain', 'error');
            return false;
        }
        
        // Validate each company has a domain
        for (let company of data.companies) {
            if (!company.domain || !company.domain.trim()) {
                SurfeApp.ui.showToast('All companies must have a valid domain', 'error');
                return false;
            }
        }

        return true;
    }

    // Using shared utility function instead

    // All utility functions moved to shared.js

    function resetCurrentForm() {
        const activeSection = document.querySelector('.input-section.active');
        if (activeSection) {
            const form = activeSection.querySelector('form');
            if (form) {
                SurfeApp.utils.resetForm(form);
            }
        }
        clearResults();
    }

    function clearResults() {
        enrichmentResults = [];
        const resultsContainer = document.getElementById('enrichment-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">
                        <i class="fas fa-building-user"></i>
                    </div>
                    <h5 class="mb-3">Ready for Enrichment</h5>
                    <p class="mb-0">Choose an input method above and provide company data to enrich with comprehensive business information.</p>
                </div>
            `;
        }
    }

    /**
     * =====================================================================
     * Export Functions (Global)
     * =====================================================================
     */
    window.exportResults = function(format) {
        if (!enrichmentResults || enrichmentResults.length === 0) {
            SurfeApp.ui.showToast('No results to export', 'error');
            return;
        }

        const timestamp = new Date().toISOString().split('T')[0];
        const filename = `company_enrichment_${timestamp}.${format}`;

        if (format === 'csv') {
            SurfeApp.utils.exportToCsv(enrichmentResults, filename);
        } else if (format === 'json') {
            SurfeApp.utils.exportToJson(enrichmentResults, filename);
        }
    };

    /**
     * =====================================================================
     * Auto-initialize when DOM is ready
     * =====================================================================
     */
    document.addEventListener('DOMContentLoaded', initializeCompanyEnrichment);

})();