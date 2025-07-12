/**
 * =====================================================================
 * People Enrichment Main Module
 * Handles combinations, forms, and orchestrates the enrichment process
 * =====================================================================
 */
(function() {
    'use strict';

    // Global variables
    let enrichmentResults = [];
    let enrichmentCombinations = [];
    let includeOptions = {};

    /**
     * =====================================================================
     * Initialization
     * =====================================================================
     */
    document.addEventListener('DOMContentLoaded', function() {
        console.log('🚀 Initializing People Enrichment with Combinations');
        
        // Check dependencies
        if (typeof SurfeApp === 'undefined') {
            console.error('❌ SurfeApp not found! Please ensure shared.js is loaded first.');
            showError('SurfeApp is not available. Please refresh the page.');
            return;
        }

        if (typeof PeopleEnrichmentUtils === 'undefined') {
            console.error('❌ PeopleEnrichmentUtils not found! Please ensure people_enrichment_utils.js is loaded first.');
            showError('Utilities not available. Please refresh the page.');
            return;
        }

        initializeModule();
    });

    async function initializeModule() {
        try {
            PeopleEnrichmentUtils.addCustomStyles();
            await loadEnrichmentCombinations();
            setupEventListeners();
            updateIncludeFieldsUI();
            
            // Initialize with manual input active
            PeopleEnrichmentUtils.switchInputMethod('manual');
            
            console.log('✅ People Enrichment module fully initialized');
        } catch (error) {
            console.error('❌ Failed to initialize module:', error);
            showError('Failed to initialize enrichment module. Please refresh the page.');
        }
    }

    /**
     * =====================================================================
     * Load and Display Valid Combinations
     * =====================================================================
     */
    async function loadEnrichmentCombinations() {
        try {
            console.log('📥 Loading enrichment combinations...');
            
            const response = await SurfeApp.api.request('GET', '/v2/people/enrich/combinations');
            
            if (response.success && response.data) {
                enrichmentCombinations = response.data.combinations || [];
                includeOptions = response.data.include_options || {};
                
                console.log('✅ Loaded', enrichmentCombinations.length, 'combinations');
                
                renderCombinations();
                renderIncludeOptions();
                
            } else {
                console.warn('⚠️ Failed to load combinations:', response.error);
                setupFallbackCombinations();
            }
        } catch (error) {
            console.error('❌ Error loading combinations:', error);
            setupFallbackCombinations();
        }
    }

    function setupFallbackCombinations() {
        console.log('📋 Setting up fallback combinations');
        enrichmentCombinations = [
            {
                id: 'linkedin_only',
                name: 'LinkedIn URL Only',
                description: 'Best results - Direct LinkedIn profile enrichment',
                fields: ['linkedinUrl'],
                accuracy: 'Very High',
                success_rate: '95%'
            },
            {
                id: 'email_only',
                name: 'Email Address Only', 
                description: 'High accuracy enrichment using professional email',
                fields: ['email'],
                accuracy: 'High',
                success_rate: '85%'
            },
            {
                id: 'name_company',
                name: 'Name + Company Name',
                description: 'Good results when you have full name and company',
                fields: ['firstName', 'lastName', 'companyName'],
                accuracy: 'High',
                success_rate: '80%'
            }
        ];
        renderCombinations();
    }

    function renderCombinations() {
        const container = document.getElementById('combinations-container');
        if (!container) {
            console.log('📋 No combinations container found, skipping render');
            return;
        }
        
        if (enrichmentCombinations.length === 0) {
            container.innerHTML = '<div class="text-center text-muted p-3">No combinations data available</div>';
            return;
        }

        const combinationsHtml = enrichmentCombinations.map(combo => `
            <div class="combination-card" data-combination="${combo.id}">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <h6 class="mb-0">${combo.name}</h6>
                    <div>
                        <span class="badge accuracy-badge ${getAccuracyBadgeClass(combo.accuracy)} me-1">${combo.accuracy}</span>
                        <span class="badge bg-info">${combo.success_rate}</span>
                    </div>
                </div>
                
                <p class="small text-muted mb-3">${combo.description}</p>
                
                <div class="row mb-3">
                    <div class="col-md-6">
                        <div class="small mb-1"><strong>Required Fields:</strong></div>
                        ${combo.fields.map(field => `<span class="badge bg-danger field-tag">${formatFieldName(field)}</span>`).join('')}
                    </div>
                    ${combo.optional_fields && combo.optional_fields.length > 0 ? `
                    <div class="col-md-6">
                        <div class="small mb-1"><strong>Optional Fields:</strong></div>
                        ${combo.optional_fields.map(field => `<span class="badge bg-success field-tag">${formatFieldName(field)}</span>`).join('')}
                    </div>
                    ` : ''}
                </div>
                
                ${combo.example ? `
                <div class="example-code mb-2">
                    <strong>Example:</strong><br>
                    ${formatExample(combo.example)}
                </div>
                ` : ''}
                
                ${combo.note ? `<div class="small text-info"><i class="fas fa-info-circle me-1"></i>${combo.note}</div>` : ''}
            </div>
        `).join('');

        container.innerHTML = combinationsHtml;
    }

    function renderIncludeOptions() {
        const container = document.getElementById('include-options-container');
        if (!container || !includeOptions || Object.keys(includeOptions).length === 0) {
            console.log('📋 No include options container or data found, skipping render');
            return;
        }

        const optionsHtml = Object.entries(includeOptions).map(([key, option]) => `
            <div class="col-md-6 mb-3">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="include-${key}" name="include-${key}" ${option.default ? 'checked' : ''} ${option.requires_setup ? 'disabled' : ''}>
                    <label class="form-check-label" for="include-${key}">
                        <strong>${formatFieldName(key)}</strong>
                        ${option.requires_setup ? '<span class="badge bg-warning ms-1">Setup Required</span>' : ''}
                    </label>
                    <div class="form-text">${option.description}${option.note ? ` - ${option.note}` : ''}</div>
                </div>
            </div>
        `).join('');

        container.innerHTML = `<div class="row">${optionsHtml}</div>`;
    }

    /**
     * =====================================================================
     * Event Listeners
     * =====================================================================
     */
    function setupEventListeners() {
        console.log('🔧 Setting up event listeners...');

        // Form handlers
        const peopleForm = document.getElementById('people-enrichment-form');
        if (peopleForm) {
            peopleForm.addEventListener('submit', handleManualEnrichment);
        }

        const csvForm = document.getElementById('csv-upload-form');
        if (csvForm) {
            csvForm.addEventListener('submit', handleCsvUpload);
        }

        const csvFileInput = document.getElementById('csv-file');
        if (csvFileInput) {
            csvFileInput.addEventListener('change', handleCsvFileChange);
        }

        const bulkForm = document.getElementById('bulk-enrichment-form');
        if (bulkForm) {
            bulkForm.addEventListener('submit', handleBulkEnrichment);
        }

        // UI controls
        PeopleEnrichmentUtils.setupInputMethodSwitching();

        const resetBtn = document.getElementById('reset-form');
        if (resetBtn) {
            resetBtn.addEventListener('click', function(e) {
                e.preventDefault();
                resetCurrentForm();
            });
        }

        const toggleBtn = document.getElementById('toggle-combinations');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', toggleCombinationsDisplay);
        }

        const validateBtn = document.getElementById('validate-combination');
        if (validateBtn) {
            validateBtn.addEventListener('click', validateCurrentCombination);
        }

        console.log('✅ All event listeners setup complete');
    }

    /**
     * =====================================================================
     * Form Handlers
     * =====================================================================
     */
    async function handleManualEnrichment(event) {
        event.preventDefault();
        console.log('🎯 Manual enrichment with combinations validation');
        
        try {
            const formData = new FormData(event.target);
            
            const rawPerson = {
                firstName: formData.get('first-name') || '',
                lastName: formData.get('last-name') || '',
                companyName: formData.get('company-name') || '',
                companyDomain: formData.get('company-domain') || '',
                linkedinUrl: formData.get('linkedin-url') || '',
                externalID: formData.get('external-id') || ''
            };
            
            const cleanedPerson = PeopleEnrichmentUtils.cleanPersonData(rawPerson);
            const validation = PeopleEnrichmentUtils.validatePersonData(cleanedPerson);
            
            if (!validation.valid) {
                showValidationErrors(validation.errors);
                return;
            }
            
            if (validation.confidence < 60) {
                const proceed = confirm(
                    `This enrichment has ${validation.confidence}% confidence. ` +
                    'Results may be limited. Do you want to proceed?'
                );
                if (!proceed) return;
            }
            
            const enrichmentRequest = {
                include: getIncludeOptions('manual'),
                people: [cleanedPerson]
            };
            
            const webhookUrl = formData.get('webhook-url');
            if (webhookUrl) {
                enrichmentRequest.notificationOptions = { webhookUrl };
            }
            
            await performEnrichment(enrichmentRequest);
            
        } catch (error) {
            console.error('❌ Manual enrichment failed:', error);
            showError(`Enrichment failed: ${error.message}`);
        }
    }

    async function handleCsvUpload(event) {
        event.preventDefault();
        console.log('📁 CSV upload with combinations validation');
        
        try {
            const fileInput = document.getElementById('csv-file');
            const file = fileInput.files[0];
            
            const validation = SurfeApp.utils.validateCSVFile(file, 10 * 1024 * 1024);
            if (!validation.valid) {
                showError(validation.errors.join('\n'));
                return;
            }

            const csvIncludeValidation = validateIncludeOptions('csv');
            if (!csvIncludeValidation.valid) {
                showError(csvIncludeValidation.error);
                return;
            }

            PeopleEnrichmentUtils.showLoading('Reading and parsing CSV file...');

            const parsedData = await SurfeApp.utils.readCSVFile(file);
            console.log('📊 CSV parsed:', parsedData.length, 'rows');

            if (parsedData.length === 0 || parsedData.length > PeopleEnrichmentUtils.API_VALIDATION_RULES.MAX_PEOPLE) {
                showError(parsedData.length === 0 ? 'No valid data found in CSV file.' : `CSV contains ${parsedData.length} people. Maximum allowed is ${PeopleEnrichmentUtils.API_VALIDATION_RULES.MAX_PEOPLE}.`);
                return;
            }

            const people = PeopleEnrichmentUtils.convertCsvToPeople(parsedData);
            const validationResults = PeopleEnrichmentUtils.validateCsvPeople(people);

            if (validationResults.valid.length === 0) {
                showError('No valid records found in CSV.');
                return;
            }

            if (validationResults.invalid.length > 0) {
                const proceed = confirm(
                    `Found ${validationResults.valid.length} valid and ${validationResults.invalid.length} invalid records. ` +
                    'Proceed with valid records only?'
                );
                if (!proceed) {
                    PeopleEnrichmentUtils.clearResults();
                    return;
                }
            }

            const enrichmentRequest = {
                include: getIncludeOptions('csv'),
                people: validationResults.valid
            };

            await performEnrichment(enrichmentRequest);
            
        } catch (error) {
            console.error('❌ CSV upload failed:', error);
            showError(`CSV upload failed: ${error.message}`);
        }
    }

    async function handleBulkEnrichment(event) {
        event.preventDefault();
        console.log('📝 Bulk enrichment with combinations validation');
        
        try {
            const bulkIncludeValidation = validateIncludeOptions('bulk');
            if (!bulkIncludeValidation.valid) {
                showError(bulkIncludeValidation.error);
                return;
            }

            const emailLines = SurfeApp.utils.parseTextareaLines(document.getElementById('bulk-emails')?.value || '');
            const linkedinLines = SurfeApp.utils.parseTextareaLines(document.getElementById('bulk-linkedin')?.value || '');
            const nameLines = SurfeApp.utils.parseTextareaLines(document.getElementById('bulk-names')?.value || '');
            const companyLines = SurfeApp.utils.parseTextareaLines(document.getElementById('bulk-companies')?.value || '');
            
            const people = [];
            const maxEntries = Math.max(emailLines.length, linkedinLines.length, nameLines.length, companyLines.length);
            
            for (let i = 0; i < maxEntries; i++) {
                const person = {};
                
                if (emailLines[i] && SurfeApp.utils.isValidEmail(emailLines[i])) {
                    person.email = emailLines[i];
                }
                
                if (linkedinLines[i] && linkedinLines[i].includes('linkedin')) {
                    let cleanUrl = linkedinLines[i];
                    if (!cleanUrl.startsWith('http')) {
                        cleanUrl = 'https://' + cleanUrl;
                    }
                    if (SurfeApp.utils.isValidUrl(cleanUrl)) {
                        person.linkedinUrl = cleanUrl;
                    }
                }
                
                if (nameLines[i]) {
                    const nameParts = nameLines[i].split(' ');
                    person.firstName = nameParts[0] || '';
                    person.lastName = nameParts.slice(1).join(' ') || '';
                }
                
                if (companyLines[i]) {
                    person.companyName = companyLines[i];
                }
                
                if (Object.keys(person).length > 0) {
                    people.push(person);
                }
            }
            
            if (people.length === 0) {
                showError('Please enter at least one email, LinkedIn URL, name, or company');
                return;
            }

            const validationResults = PeopleEnrichmentUtils.validateBulkPeople(people);
            
            if (validationResults.valid.length === 0) {
                showError('No valid entries found.');
                return;
            }

            if (validationResults.invalid.length > 0) {
                const proceed = confirm(
                    `Found ${validationResults.valid.length} valid and ${validationResults.invalid.length} invalid entries. ` +
                    'Proceed with valid entries only?'
                );
                if (!proceed) return;
            }
            
            const enrichmentData = {
                include: getIncludeOptions('bulk'),
                people: validationResults.valid
            };
            
            await performEnrichment(enrichmentData);
            
        } catch (error) {
            console.error('❌ Bulk enrichment failed:', error);
            showError(`Bulk enrichment failed: ${error.message}`);
        }
    }

    function handleCsvFileChange(event) {
        const file = event.target.files[0];
        if (!file) return;

        const validation = SurfeApp.utils.validateCSVFile(file);
        if (!validation.valid) {
            showError(validation.errors.join('\n'));
            return;
        }

        console.log('📁 CSV file selected:', file.name, 'Size:', PeopleEnrichmentUtils.formatFileSize(file.size));
    }

    
    /**
     * =====================================================================
     * Enrichment Orchestration
     * =====================================================================
     */
    async function performEnrichment(requestData) {
        try {
            const enrichmentID = await PeopleEnrichmentUtils.performEnrichment(requestData);
            
            // Start polling for results
            PeopleEnrichmentUtils.pollForResults(
                enrichmentID,
                (attempts, maxAttempts) => {
                    PeopleEnrichmentUtils.showLoading(`Processing enrichment... (${attempts}/${maxAttempts})`);
                },
                (results) => {
                    enrichmentResults = results || [];
                    PeopleEnrichmentUtils.displayEnrichmentResults(results);
                    SurfeApp.ui.showToast(`Enrichment complete! Processed ${results?.length || 0} results.`, 'success');
                }
            );
            
        } catch (error) {
            // Error handling is done in PeopleEnrichmentUtils.performEnrichment
            console.error('Enrichment orchestration failed:', error);
        }
    }

    /**
     * =====================================================================
     * Utility Functions
     * =====================================================================
     */
    function getIncludeOptions(type) {
        const prefix = type === 'csv' ? 'csv-' : type === 'bulk' ? 'bulk-' : '';
        
        return {
            email: document.getElementById(`${prefix}include-email`)?.checked || false,
            mobile: document.getElementById(`${prefix}include-mobile`)?.checked || false,
            linkedInUrl: document.getElementById(`${prefix}include-linkedin`)?.checked || false,
            jobHistory: document.getElementById(`${prefix}include-job-history`)?.checked || false
        };
    }

    function validateIncludeOptions(type) {
        const include = getIncludeOptions(type);
        const hasAtLeastOneField = Object.values(include).some(value => value === true);
        
        if (!hasAtLeastOneField) {
            return {
                valid: false,
                error: 'Please select at least one field to include in the enrichment results'
            };
        }
        
        return { valid: true };
    }

    function getAccuracyBadgeClass(accuracy) {
        switch (accuracy) {
            case 'Very High': return 'bg-success';
            case 'High': return 'bg-primary';
            case 'Medium': return 'bg-warning text-dark';
            case 'Low': return 'bg-danger';
            default: return 'bg-secondary';
        }
    }

    function formatFieldName(field) {
        return field.replace(/([A-Z])/g, ' $1')
                   .replace(/^./, str => str.toUpperCase())
                   .replace('Linkedin', 'LinkedIn')
                   .replace('Id', 'ID')
                   .trim();
    }

    function formatExample(example) {
        return Object.entries(example)
            .map(([key, value]) => `${formatFieldName(key)}: "${value}"`)
            .join('<br>');
    }

    function toggleCombinationsDisplay() {
        const container = document.getElementById('combinations-container');
        const button = document.getElementById('toggle-combinations');
        
        if (!container || !button) return;
        
        if (container.style.display === 'none') {
            container.style.display = 'block';
            button.innerHTML = '<i class="fas fa-eye-slash me-1"></i>Hide Details';
        } else {
            container.style.display = 'none';
            button.innerHTML = '<i class="fas fa-eye me-1"></i>Show Details';
        }
    }

    function validateCurrentCombination() {
        const formData = new FormData(document.getElementById('people-enrichment-form'));
        const person = {};
        
        for (let [key, value] of formData.entries()) {
            if (value.trim()) {
                const fieldName = convertFormFieldName(key);
                person[fieldName] = value.trim();
            }
        }

        const validationResult = validatePersonCombination(person);
        displayValidationResult(validationResult);
    }

    function validatePersonCombination(person) {
        for (const combo of enrichmentCombinations) {
            if (personMatchesCombination(person, combo)) {
                return {
                    valid: true,
                    combination: combo,
                    message: `✅ Valid combination: ${combo.name} (${combo.accuracy} accuracy, ${combo.success_rate} success rate)`
                };
            }
        }

        return {
            valid: false,
            message: '❌ Current data does not match any valid combination. Please provide more information.',
            suggestions: getSuggestions(person)
        };
    }

    function personMatchesCombination(person, combination) {
        return combination.fields.every(field => {
            const value = person[field];
            if (!value) return false;
            
            if (field === 'email' && !PeopleEnrichmentUtils.API_VALIDATION_RULES.EMAIL_REGEX.test(value)) return false;
            if (field === 'linkedinUrl' && !value.toLowerCase().includes('linkedin.com')) return false;
            if (field === 'companyDomain' && !value.includes('.')) return false;
            
            return true;
        });
    }

    function getSuggestions(person) {
        const suggestions = [];
        
        if (person.linkedinUrl) {
            suggestions.push('LinkedIn URL only is sufficient for high accuracy enrichment');
        } else if (person.email) {
            suggestions.push('Email address only is sufficient for good enrichment');
        } else if (person.firstName && person.lastName) {
            if (!person.companyName && !person.companyDomain) {
                suggestions.push('Add company name or domain to improve accuracy');
            }
        } else {
            suggestions.push('Provide at least first name + last name, or email, or LinkedIn URL');
        }
        
        return suggestions;
    }

    function displayValidationResult(result) {
        const container = document.getElementById('validation-result');
        if (!container) return;
        
        if (result.valid) {
            container.innerHTML = `
                <div class="alert alert-success">
                    <h6>${result.message}</h6>
                    <small>${result.combination.description}</small>
                </div>
            `;
        } else {
            const suggestionsHtml = result.suggestions ? 
                `<ul class="mb-0 mt-2">${result.suggestions.map(s => `<li>${s}</li>`).join('')}</ul>` : '';
            
            container.innerHTML = `
                <div class="alert alert-warning">
                    <h6>${result.message}</h6>
                    ${suggestionsHtml}
                </div>
            `;
        }
        
        container.style.display = 'block';
    }

    function convertFormFieldName(formField) {
        const mapping = {
            'first-name': 'firstName',
            'last-name': 'lastName',
            'company-name': 'companyName',
            'company-domain': 'companyDomain',
            'linkedin-url': 'linkedinUrl',
            'external-id': 'externalID'
        };
        return mapping[formField] || formField;
    }

    function updateIncludeFieldsUI() {
        // Only update if dynamic loading hasn't populated them
        if (Object.keys(includeOptions).length === 0) {
            console.log('📋 Setting up default include options');
        }
    }

    function resetCurrentForm() {
        const activeSection = document.querySelector('.input-section.active');
        if (activeSection) {
            const form = activeSection.querySelector('form');
            if (form) {
                SurfeApp.utils.resetForm(form);
                
                // Reset include checkboxes to default state
                const includeFields = ['email', 'mobile', 'linkedin', 'job-history'];
                const prefix = activeSection.id.replace('-input', '');
                
                includeFields.forEach(field => {
                    const checkbox = document.getElementById(`${prefix === 'manual' ? '' : prefix + '-'}include-${field}`);
                    if (checkbox) {
                        checkbox.checked = ['email', 'mobile'].includes(field);
                    }
                });
                
                // Clear validation displays
                const validationResult = document.getElementById('validation-result');
                if (validationResult) validationResult.style.display = 'none';
            }
        }
        PeopleEnrichmentUtils.clearResults();
    }

    function showError(message) {
        PeopleEnrichmentUtils.showError(message);
    }

    function showValidationErrors(errors) {
        const errorList = errors.map(error => `• ${error}`).join('\n');
        showError(`Validation failed:\n\n${errorList}`);
    }

    /**
     * =====================================================================
     * Global Export Functions
     * =====================================================================
     */
    window.exportResults = function(format) {
        if (!enrichmentResults || enrichmentResults.length === 0) {
            SurfeApp.ui.showToast('No results to export', 'warning');
            return;
        }
        
        const timestamp = new Date().toISOString().split('T')[0];
        const fileName = `people_enrichment_${timestamp}.${format}`;
        
        switch (format.toLowerCase()) {
            case 'csv':
                SurfeApp.utils.exportToCsv(enrichmentResults, fileName, 'people_enrichment');
                break;
                
            case 'json':
                SurfeApp.utils.exportToJson(enrichmentResults, fileName);
                break;
                
            default:
                SurfeApp.ui.showToast('Unsupported export format', 'error');
                return;
        }
        
        console.log(`📁 Exported ${enrichmentResults.length} enrichment results as ${format.toUpperCase()}`);
    };

    window.exportPersonData = function(index) {
        if (!enrichmentResults || !enrichmentResults[index]) {
            SurfeApp.ui.showToast('Person data not found', 'error');
            return;
        }
        
        const person = enrichmentResults[index];
        const fileName = `person_${index + 1}_${Date.now()}.json`;
        
        SurfeApp.utils.exportToJson([person], fileName);
    };

    // Global object for debugging
    window.PeopleEnrichmentComplete = {
        switchInputMethod: PeopleEnrichmentUtils.switchInputMethod,
        validatePersonData: PeopleEnrichmentUtils.validatePersonData,
        validatePersonCombination,
        enrichmentCombinations: () => enrichmentCombinations,
        includeOptions: () => includeOptions,
        getCurrentResults: () => enrichmentResults,
        hasSurfeApp: () => typeof SurfeApp !== 'undefined',
        hasValidCombinations: () => enrichmentCombinations.length > 0,
        hasUtils: () => typeof PeopleEnrichmentUtils !== 'undefined'
    };

    console.log('✅ People Enrichment Main Module with Combinations loaded');

})();