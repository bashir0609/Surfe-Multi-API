/**
 * =====================================================================
 * People Enrichment Module - COMPLETE FIXED VERSION
 * =====================================================================
 */
(function() {
    'use strict';

    // Global variable to store results
    let enrichmentResults = [];

    /**
     * =====================================================================
     * Initialize People Enrichment
     * =====================================================================
     */
    document.addEventListener('DOMContentLoaded', function() {
        console.log('🚀 Initializing People Enrichment module');
        setupEventListeners();
    });

    /**
     * =====================================================================
     * Event Listeners - THIS WAS MISSING!
     * =====================================================================
     */
    function setupEventListeners() {
        // Prevent form submissions from reloading the page
        const peopleForm = document.getElementById('people-enrichment-form');
        if (peopleForm) {
            peopleForm.addEventListener('submit', handleManualEnrichment);
        }

        const csvForm = document.getElementById('csv-upload-form');
        if (csvForm) {
            csvForm.addEventListener('submit', handleCsvUpload);
        }

        const bulkForm = document.getElementById('bulk-enrichment-form');
        if (bulkForm) {
            bulkForm.addEventListener('submit', handleBulkEnrichment);
        }

        // Input method switching
        document.querySelectorAll('.input-method-card').forEach(card => {
            card.addEventListener('click', function() { 
                switchInputMethod(this.dataset.method); 
            });
        });

        // Reset buttons
        document.querySelectorAll('#reset-form, .reset-form').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault(); // Prevent any default behavior
                resetCurrentForm();
            });
        });

        // Also handle any standalone "Enrich" buttons that might not be in forms
        document.querySelectorAll('button[type="submit"]').forEach(btn => {
            if (btn.textContent.toLowerCase().includes('enrich')) {
                btn.addEventListener('click', function(e) {
                    const form = btn.closest('form');
                    if (form) {
                        e.preventDefault(); // This prevents the page reload!
                        form.dispatchEvent(new Event('submit'));
                    }
                });
            }
        });
    }

    function switchInputMethod(method) {
        document.querySelectorAll('.input-method-card').forEach(c => c.classList.remove('active'));
        document.querySelector(`[data-method="${method}"]`)?.classList.add('active');
        document.querySelectorAll('.input-section').forEach(s => s.classList.remove('active'));
        document.getElementById(`${method}-input`)?.classList.add('active');
        clearResults();
    }

    async function handleManualEnrichment(event) {
        event.preventDefault(); // CRITICAL: Prevent form submission/page reload
        console.log('🎯 Manual enrichment form submitted');
        
        const formData = SurfeApp.forms.serializeForm(event.target);
        const enrichmentData = {
            include: { email: true, mobile: true, linkedInUrl: true },
            people: [{
                firstName: formData['first-name'] || '',
                lastName: formData['last-name'] || '',
                companyName: formData['company-name'] || '',
                linkedinUrl: formData['linkedin-url'] || '',
            }]
        };
        await performEnrichment(enrichmentData);
    }

    async function handleCsvUpload(event) {
        event.preventDefault(); // CRITICAL: Prevent form submission/page reload
        console.log('📁 CSV upload form submitted');
        
        const fileInput = document.getElementById('csv-file');
        const file = fileInput.files[0];
        if (!file) { 
            return SurfeApp.ui.showToast('Please select a CSV file', 'error'); 
        }

        try {
            const peopleData = await SurfeApp.utils.readCSVFile(file);
            const formattedPeople = peopleData.map(row => ({
                firstName: row.first_name || row.firstName,
                lastName: row.last_name || row.lastName,
                companyName: row.company_name || row.companyName,
                linkedinUrl: row.linkedin_url || row.linkedinUrl
            }));
            const enrichmentData = {
                include: { email: true, mobile: true },
                people: formattedPeople
            };
            await performEnrichment(enrichmentData);
        } catch (error) {
            SurfeApp.ui.showError('enrichment-results', 'Failed to read or process CSV file.');
        }
    }

    async function handleBulkEnrichment(event) {
        event.preventDefault(); // CRITICAL: Prevent form submission/page reload
        console.log('📝 Bulk enrichment form submitted');
        
        // Get data from all bulk input fields
        const emailsText = document.querySelector('[placeholder*="email"], #bulk-emails-input, textarea[name*="email"]')?.value || '';
        const linkedinText = document.querySelector('[placeholder*="linkedin"], #bulk-linkedin-input, textarea[name*="linkedin"]')?.value || '';
        const namesText = document.querySelector('[placeholder*="name"], #bulk-names-input, textarea[name*="name"]')?.value || '';
        
        console.log('📊 Bulk input data:', { emailsText, linkedinText, namesText });
        
        const people = [];
        
        // Process names first (most reliable for enrichment)
        if (namesText.trim()) {
            const nameLines = SurfeApp.utils.parseTextareaLines(namesText);
            nameLines.forEach(line => {
                const parts = line.trim().split(' ');
                if (parts.length > 0 && parts[0]) {
                    people.push({
                        firstName: parts[0] || '',
                        lastName: parts.slice(1).join(' ') || ''
                    });
                }
            });
        }
        
        // Process emails - but only if we don't have names, or try to match with names
        if (emailsText.trim()) {
            const emailLines = SurfeApp.utils.parseTextareaLines(emailsText);
            emailLines.forEach((email, index) => {
                if (email.trim() && email.includes('@')) {
                    // If we have corresponding people from names, add email to them
                    if (people[index]) {
                        people[index].email = email.trim();
                    } else {
                        // Otherwise create new person with email only (if supported)
                        // Extract potential name from email
                        const emailPart = email.split('@')[0];
                        const nameParts = emailPart.split(/[._-]/);
                        people.push({
                            firstName: nameParts[0] || 'Unknown',
                            lastName: nameParts[1] || '',
                            email: email.trim()
                        });
                    }
                }
            });
        }
        
        // Process LinkedIn URLs
        if (linkedinText.trim()) {
            const linkedinLines = SurfeApp.utils.parseTextareaLines(linkedinText);
            linkedinLines.forEach((url, index) => {
                if (url.trim() && (url.includes('linkedin.com') || url.includes('linkedin'))) {
                    // Clean up LinkedIn URL
                    let cleanUrl = url.trim();
                    if (!cleanUrl.startsWith('http')) {
                        cleanUrl = 'https://' + cleanUrl;
                    }
                    
                    // If we have corresponding people, add LinkedIn to them
                    if (people[index]) {
                        people[index].linkedinUrl = cleanUrl;
                    } else {
                        // Create new person with LinkedIn URL
                        people.push({
                            linkedinUrl: cleanUrl
                        });
                    }
                }
            });
        }
        
        console.log('👥 Processed people data:', people);
        
        if (people.length === 0) { 
            return SurfeApp.ui.showToast('Please enter at least one name, email, or LinkedIn URL.', 'error'); 
        }
        
        // Validate each person has minimum required data
        const validPeople = people.filter(person => {
            const hasName = person.firstName || person.lastName;
            const hasEmail = person.email;
            const hasLinkedIn = person.linkedinUrl;
            
            // Each person needs at least name OR LinkedIn URL (as per API requirements)
            return hasName || hasLinkedIn;
        });
        
        if (validPeople.length === 0) {
            return SurfeApp.ui.showToast('Each person must have at least a name (first/last) or LinkedIn URL.', 'error');
        }
        
        console.log('✅ Valid people for enrichment:', validPeople);
        
        const enrichmentData = {
            include: { 
                email: true, 
                mobile: true, 
                linkedInUrl: false // Set to false as we might already have LinkedIn URLs
            },
            people: validPeople
        };
        
        console.log('🚀 Final enrichment data:', enrichmentData);
        await performEnrichment(enrichmentData);
    }

    // --- CORE LOGIC (FIXED) ---

    async function performEnrichment(data) {
        console.log('🚀 Starting enrichment with data:', data);
        const resultsContainer = document.getElementById('enrichment-results');
        SurfeApp.ui.showLoading(resultsContainer, 'Submitting enrichment request...');
        
        try {
            // Remove /api prefix since SurfeApp.api.request() adds it automatically
            const endpoint = '/v2/people/enrich';
            console.log('📡 Calling endpoint:', endpoint);
            
            const response = await SurfeApp.api.request('POST', endpoint, data);
            console.log('📥 Enrichment response:', response);
            
            if (response.success && response.data && response.data.enrichmentID) {
                SurfeApp.ui.showToast('Enrichment job started successfully!', 'info');
                pollForResults(response.data.enrichmentID);
            } else {
                throw new Error(response.error || 'Failed to start enrichment job.');
            }
        } catch (error) {
            console.error('❌ Enrichment failed:', error);
            SurfeApp.ui.showError(resultsContainer, `Enrichment failed: ${error.message}`);
        }
    }

    function pollForResults(enrichmentID) {
        console.log('🔄 Starting to poll for results:', enrichmentID);
        const resultsContainer = document.getElementById('enrichment-results');
        SurfeApp.ui.showLoading(resultsContainer, 'Processing enrichment... This may take a moment.');
        
        let attempts = 0;
        const maxAttempts = 20;
        const interval = 2500;

        const intervalId = setInterval(async () => {
            if (attempts >= maxAttempts) {
                clearInterval(intervalId);
                SurfeApp.ui.showError(resultsContainer, 'Enrichment request timed out.');
                return;
            }
            try {
                // Remove /api prefix since SurfeApp.api.request() adds it automatically
                const statusEndpoint = `/v2/people/enrich/status/${enrichmentID}`;
                console.log(`[Attempt ${attempts + 1}] Checking: ${statusEndpoint}`);
                
                const statusResponse = await SurfeApp.api.request('GET', statusEndpoint);
                console.log('Status response:', statusResponse);
                
                if (statusResponse.success && statusResponse.status === 'completed') {
                    clearInterval(intervalId);
                    console.log('✅ Enrichment completed!');
                    
                    enrichmentResults = statusResponse.data || [];
                    displayEnrichmentResults(statusResponse.data);
                    SurfeApp.ui.showToast(`Enrichment complete! Found ${statusResponse.data?.length || 0} results.`, 'success');
                } else if (statusResponse.success && statusResponse.status === 'pending') {
                    console.log('⏳ Still pending...');
                } else {
                    console.warn('Unexpected response:', statusResponse);
                }
            } catch (error) {
                console.error('Error checking status:', error);
                clearInterval(intervalId);
                SurfeApp.ui.showError(resultsContainer, `Error fetching results: ${error.message}`);
            }
            attempts++;
        }, interval);
    }

    /**
     * =====================================================================
     * Results Display (FIXED)
     * =====================================================================
     */
    function displayEnrichmentResults(results) {
        console.log('🎨 Displaying results:', results);
        const resultsContainer = document.getElementById('enrichment-results');
        if (!results || results.length === 0) {
            return SurfeApp.ui.showEmpty(resultsContainer, 'No enrichment results found');
        }

        const resultsHtml = `
            <div class="results-header">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <div>
                        <h4><i class="fas fa-user-plus me-2"></i>Enrichment Results</h4>
                        <p class="text-muted mb-0">${results.length} people enriched successfully</p>
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
        console.log('✅ Results displayed successfully');
    }

    function createPersonCard(person) {
        const firstName = person.firstName || person.first_name || '';
        const lastName = person.lastName || person.last_name || '';
        const name = `${firstName} ${lastName}`.trim() || 'Unknown Name';
        
        const company = person.companyName || person.company_name || person.company || 'N/A';
        const title = person.jobTitle || person.job_title || person.title || 'N/A';
        
        let email = '';
        let emailStatus = '';
        if (typeof person.email === 'string') {
            email = person.email;
        } else if (person.emails && person.emails.length > 0) {
            const emailObj = person.emails[0];
            email = emailObj.email || '';
            emailStatus = emailObj.validationStatus || '';
        }
        
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
                                    ${linkedin ? `<a href="${linkedin}" target="_blank" class="btn btn-outline-info btn-sm" title="View LinkedIn">
                                        <i class="fab fa-linkedin"></i>
                                    </a>` : ''}
                                </div>
                            </div>
                            
                            <div class="person-details">
                                <div class="row">
                                    <div class="col-md-6">
                                        ${email ? `<small class="d-block text-muted" title="Validation: ${emailStatus}">
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

    function resetCurrentForm() {
        console.log('🔄 Resetting current form');
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
            resultsContainer.innerHTML = `<div class="empty-state">...</div>`;
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
            SurfeApp.utils.exportToCsv(enrichmentResults, filename, 'people_enrichment');
        } else if (format === 'json') {
            SurfeApp.utils.exportToJson(enrichmentResults, filename);
        }
    };

    // Make functions available globally if needed
    window.PeopleEnrichment = {
        performEnrichment,
        displayEnrichmentResults,
        clearResults
    };

})();