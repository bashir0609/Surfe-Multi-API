/**
 * =====================================================================
 * People Enrichment Module - Handles people enrichment functionality
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
            enrich: '/api/v2/people/enrich',
            enrichBulk: '/api/v2/people/enrich/bulk'
        }
    };

    let currentInputMethod = 'manual';
    let enrichmentResults = [];

    /**
     * =====================================================================
     * Initialize People Enrichment
     * =====================================================================
     */
    function initializePeopleEnrichment() {
        console.log('🚀 Initializing People Enrichment module');
        
        setupInputMethodSwitching();
        setupEventListeners();
        setupFormValidation();
        
        console.log('✅ People Enrichment module initialized');
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
        const manualForm = document.getElementById('people-enrichment-form');
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
        // Real-time validation for email fields
        const emailInputs = document.querySelectorAll('input[type="email"]');
        emailInputs.forEach(input => {
            input.addEventListener('blur', validateEmailField);
        });

        // URL validation
        const urlInputs = document.querySelectorAll('input[type="url"]');
        urlInputs.forEach(input => {
            input.addEventListener('blur', validateUrlField);
        });
    }

    function validateEmailField(event) {
        const input = event.target;
        const email = input.value.trim();
        
        if (email && !SurfeApp.utils.isValidEmail(email)) {
            SurfeApp.forms.showFieldError(input, 'Please enter a valid email address');
        } else {
            SurfeApp.forms.clearFieldError(input);
        }
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

        // Prepare enrichment data according to Surfe API v2 format
        const includeConfig = {
            email: document.getElementById('include-email').checked,
            linkedInUrl: document.getElementById('include-linkedin').checked,
            mobile: document.getElementById('include-mobile').checked
        };
        
        // Validate that at least one field is included (required by API)
        if (!includeConfig.email && !includeConfig.linkedInUrl && !includeConfig.mobile) {
            SurfeApp.ui.showToast('At least one field must be selected in "Data to Include"', 'error');
            return;
        }
        
        // Clean company domain if provided
        let companyDomain = formData['company-domain'] || '';
        if (companyDomain) {
            companyDomain = SurfeApp.utils.cleanDomain(companyDomain);
            if (!SurfeApp.utils.isValidDomain(companyDomain)) {
                SurfeApp.ui.showToast('Please provide a valid company domain (e.g., acme.com)', 'error');
                return;
            }
        }
        
        const enrichmentData = {
            include: includeConfig,
            people: [{
                firstName: formData['first-name'] || '',
                lastName: formData['last-name'] || '',
                companyName: formData['company-name'] || '',
                companyDomain: companyDomain,
                linkedinUrl: formData['linkedin-url'] || '',
                externalID: formData['external-id'] || ''
            }]
        };
        
        // Add notificationOptions if webhook URL is provided
        const webhookUrl = formData['webhook-url'];
        if (webhookUrl && webhookUrl.trim()) {
            enrichmentData.notificationOptions = {
                webhookUrl: webhookUrl.trim()
            };
        }

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
        
        // Parse bulk input according to Surfe API v2 format
        const includeConfig = {
            email: document.getElementById('include-email').checked,
            linkedInUrl: document.getElementById('include-linkedin').checked,
            mobile: document.getElementById('include-mobile').checked
        };
        
        // Validate that at least one field is included (required by API)
        if (!includeConfig.email && !includeConfig.linkedInUrl && !includeConfig.mobile) {
            SurfeApp.ui.showToast('At least one field must be selected in "Data to Include"', 'error');
            return;
        }
        
        const enrichmentData = {
            include: includeConfig,
            people: []
        };

        // Parse names into people objects
        const names = SurfeApp.utils.parseTextareaLines(formData.names);
        const emails = SurfeApp.utils.parseTextareaLines(formData.emails);
        const linkedinUrls = SurfeApp.utils.parseTextareaLines(formData.linkedin_urls);

        // Create people objects with available data
        const maxLength = Math.max(names.length, emails.length, linkedinUrls.length);
        for (let i = 0; i < maxLength; i++) {
            const person = {};
            
            // Parse name if available
            if (names[i]) {
                const nameParts = names[i].trim().split(' ');
                person.firstName = nameParts[0] || '';
                person.lastName = nameParts.slice(1).join(' ') || '';
            }
            
            // Add other fields if available
            if (emails[i]) person.email = emails[i].trim();
            if (linkedinUrls[i]) person.linkedinUrl = linkedinUrls[i].trim();
            
            // Add external ID based on index
            person.externalID = `bulk-${i + 1}`;
            
            enrichmentData.people.push(person);
        }

        // Validate array size (1-10000 people according to API spec)
        if (enrichmentData.people.length === 0) {
            SurfeApp.ui.showToast('At least one person is required for enrichment', 'error');
            return;
        }
        
        if (enrichmentData.people.length > 10000) {
            SurfeApp.ui.showToast('Maximum 10,000 people allowed per enrichment request', 'error');
            return;
        }

        // Add notificationOptions if webhook URL is provided
        const webhookUrl = formData['webhook-url'];
        if (webhookUrl && webhookUrl.trim()) {
            enrichmentData.notificationOptions = {
                webhookUrl: webhookUrl.trim()
            };
        }

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
        SurfeApp.ui.showLoading(resultsContainer, 'Enriching people data...');

        try {
            const response = await SurfeApp.api.request(
                'POST',
                config.endpoints.enrich,
                data
            );

            if (response.success) {
                enrichmentResults = response.data.people || [];
                displayEnrichmentResults(enrichmentResults, method);
                SurfeApp.ui.showToast(
                    `Successfully enriched ${enrichmentResults.length} people`, 
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
                enrichmentResults = result.data.people || [];
                displayEnrichmentResults(enrichmentResults, method);
                SurfeApp.ui.showToast(
                    `Successfully processed ${enrichmentResults.length} people from CSV`, 
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
                        <h4><i class="fas fa-user-plus me-2"></i>Enrichment Results</h4>
                        <p class="text-muted mb-0">${results.length} people enriched via ${method} input</p>
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
                ${results.map(person => createPersonCard(person)).join('')}
            </div>
        `;

        resultsContainer.innerHTML = resultsHtml;
    }

    function createPersonCard(person) {
        // Handle multiple possible field name formats from API
        const firstName = person.firstName || person.first_name || '';
        const lastName = person.lastName || person.last_name || '';
        const name = `${firstName} ${lastName}`.trim() || 'Unknown Name';
        
        const company = person.companyName || person.company_name || person.company || 'N/A';
        const title = person.jobTitle || person.job_title || person.title || 'N/A';
        const email = person.email || '';
        const linkedin = person.linkedinUrl || person.linkedin_url || person.linkedIn || '';
        const mobile = person.mobile || person.phone || '';
        const location = person.location || person.city || '';
        const country = person.country || '';
        const seniority = person.seniority || '';
        const department = person.department || '';
        const companyDomain = person.companyDomain || person.company_domain || '';
        
        return `
            <div class="person-card card mb-3">
                <div class="card-body">
                    <div class="d-flex align-items-start">
                        <div class="person-avatar me-3">
                            <i class="fas fa-user-circle fa-2x text-primary"></i>
                        </div>
                        <div class="flex-grow-1">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <div>
                                    <h6 class="person-name mb-1">${name}</h6>
                                    <p class="person-title text-muted mb-1">${title}</p>
                                    <p class="person-company small text-primary mb-0">
                                        <i class="fas fa-building me-1"></i>${company}
                                    </p>
                                </div>
                                <div class="person-actions">
                                    ${email ? `<a href="mailto:${email}" class="btn btn-outline-primary btn-sm me-1" title="Send Email">
                                        <i class="fas fa-envelope"></i>
                                    </a>` : ''}
                                    ${linkedin ? `<a href="${linkedin}" target="_blank" class="btn btn-outline-info btn-sm" title="View LinkedIn">
                                        <i class="fab fa-linkedin"></i>
                                    </a>` : ''}
                                </div>
                            </div>
                            
                            <div class="person-details">
                                <div class="row">
                                    <div class="col-md-6">
                                        ${email ? `<small class="d-block text-muted">
                                            <i class="fas fa-envelope me-1"></i>${email}
                                        </small>` : ''}
                                        ${mobile ? `<small class="d-block text-muted">
                                            <i class="fas fa-phone me-1"></i>${mobile}
                                        </small>` : ''}
                                        ${location || country ? `<small class="d-block text-muted">
                                            <i class="fas fa-map-marker-alt me-1"></i>${[location, country].filter(Boolean).join(', ')}
                                        </small>` : ''}
                                        ${companyDomain ? `<small class="d-block text-muted">
                                            <i class="fas fa-globe me-1"></i>${companyDomain}
                                        </small>` : ''}
                                    </div>
                                    <div class="col-md-6">
                                        ${seniority ? `<small class="d-block text-muted">
                                            <i class="fas fa-level-up-alt me-1"></i>Seniority: ${seniority}
                                        </small>` : ''}
                                        ${department ? `<small class="d-block text-muted">
                                            <i class="fas fa-users me-1"></i>Department: ${department}
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
        // According to Surfe API v2 spec, each person needs sufficient identifying data
        // Better find rates achieved by providing as much information as possible
        const hasName = formData['first-name'] || formData['last-name'];
        const hasCompanyInfo = formData['company-name'] || formData['company-domain'];
        const hasLinkedIn = formData['linkedin-url'];

        // Need at least name OR linkedIn URL (company info alone isn't sufficient for person enrichment)
        if (!hasName && !hasLinkedIn) {
            SurfeApp.ui.showToast('Please provide at least a name (first/last) OR LinkedIn URL for person identification', 'error');
            return false;
        }

        // Validate field lengths according to Surfe API v2 specification
        const fieldLimits = {
            'company-domain': 2000,
            'company-name': 2000,
            'linkedin-url': 2000
        };

        for (const [field, maxLength] of Object.entries(fieldLimits)) {
            const value = formData[field];
            if (value && value.length > maxLength) {
                SurfeApp.ui.showToast(`${field.replace('-', ' ')} must be ${maxLength} characters or less`, 'error');
                return false;
            }
        }

        // Validate webhook URL format if provided
        const webhookUrl = formData['webhook-url'];
        if (webhookUrl && webhookUrl.trim()) {
            if (!webhookUrl.match(/^https?:\/\/.+/i)) {
                SurfeApp.ui.showToast('Webhook URL must be a valid HTTP or HTTPS URL', 'error');
                return false;
            }
        }

        return true;
    }

    function validateBulkData(data) {
        const hasEmails = data.emails && data.emails.length > 0;
        const hasLinkedIn = data.linkedin_urls && data.linkedin_urls.length > 0;
        const hasNames = data.people && data.people.length > 0;

        if (!hasEmails && !hasLinkedIn && !hasNames) {
            SurfeApp.ui.showToast('Please provide at least one type of bulk data', 'error');
            return false;
        }

        return true;
    }

    function parseNamesInput(text) {
        if (!text) return [];
        const lines = SurfeApp.utils.parseTextareaLines(text);
        return lines.map(name => {
            const parts = name.split(' ');
            return {
                first_name: parts[0] || '',
                last_name: parts.slice(1).join(' ') || ''
            };
        });
    }

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
                        <i class="fas fa-user-plus"></i>
                    </div>
                    <h5 class="mb-3">Ready for Enrichment</h5>
                    <p class="mb-0">Choose an input method above and provide people data to enrich with professional information.</p>
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
        const filename = `people_enrichment_${timestamp}.${format}`;

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
    document.addEventListener('DOMContentLoaded', initializePeopleEnrichment);

})();