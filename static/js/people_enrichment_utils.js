/**
 * =====================================================================
 * People Enrichment Utilities Module
 * Reusable functions for CSV processing, validation, UI helpers, etc.
 * =====================================================================
 */

// FIXED: Immediately define on window object to ensure it's available
window.PeopleEnrichmentUtils = (function() {
    'use strict';

    // API validation rules
    const API_VALIDATION_RULES = {
        MAX_FIELD_LENGTH: 2000,
        MIN_PEOPLE: 1,
        MAX_PEOPLE: 10000,
        EMAIL_REGEX: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
        LINKEDIN_REGEX: /^https?:\/\/(www\.)?linkedin\.com\/in\/[a-zA-Z0-9\-._~:/?#[\]@!$&'()*+,;=%]+$/,
        DOMAIN_REGEX: /^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.([a-zA-Z]{2,}\.?)+$/,
        WEBHOOK_REGEX: /^https?:\/\/.+/
    };

    /**
     * =====================================================================
     * Input Method Management
     * =====================================================================
     */
    function setupInputMethodSwitching() {
        const inputMethodCards = document.querySelectorAll('.input-method-card');
        
        inputMethodCards.forEach((card) => {
            card.removeEventListener('click', handleInputMethodClick);
            card.addEventListener('click', handleInputMethodClick);
            
            card.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    handleInputMethodClick.call(this, e);
                }
            });
            
            card.setAttribute('tabindex', '0');
            card.style.cursor = 'pointer';
        });
    }

    function handleInputMethodClick(event) {
        event.preventDefault();
        event.stopPropagation();
        
        const method = this.dataset.method;
        console.log(`Input method clicked: ${method}`);
        
        if (method) {
            switchInputMethod(method);
        }
    }

    function switchInputMethod(method) {
        console.log(`Switching to input method: ${method}`);
        
        try {
            // Update active card
            const allCards = document.querySelectorAll('.input-method-card');
            allCards.forEach(card => card.classList.remove('active'));
            
            const activeCard = document.querySelector(`[data-method="${method}"]`);
            if (activeCard) {
                activeCard.classList.add('active');
            }
            
            // Show corresponding input section
            const allSections = document.querySelectorAll('.input-section');
            allSections.forEach(section => {
                section.classList.remove('active');
                section.style.display = 'none';
            });
            
            const activeSection = document.getElementById(`${method}-input`);
            if (activeSection) {
                activeSection.classList.add('active');
                activeSection.style.display = 'block';
            }
            
            // Clear results when switching
            clearResults();
            
            console.log(`✅ Successfully switched to ${method} input method`);
            
        } catch (error) {
            console.error('Error switching input method:', error);
        }
    }

    /**
     * =====================================================================
     * CSV Processing Utilities
     * =====================================================================
     */
    function convertCsvToPeople(csvData) {
        const people = [];
        
        csvData.forEach((row, index) => {
            const person = {};
            
            // Map CSV columns to person fields with flexible column name matching
            Object.keys(row).forEach(column => {
                const originalColumn = column;
                const normalizedColumn = column.toLowerCase().trim();
                const value = row[column] ? row[column].trim() : '';
                
                if (!value) return;
                
                console.log(`Processing column: "${originalColumn}" with value: "${value}"`);
                
                if (isFirstNameColumn(originalColumn, normalizedColumn)) {
                    person.firstName = value;
                } else if (isLastNameColumn(originalColumn, normalizedColumn)) {
                    person.lastName = value;
                } else if (isEmailColumn(originalColumn, normalizedColumn)) {
                    person.email = value;
                } else if (isCompanyNameColumn(originalColumn, normalizedColumn)) {
                    person.companyName = value;
                } else if (isCompanyDomainColumn(originalColumn, normalizedColumn)) {
                    person.companyDomain = cleanDomain(value);
                } else if (isLinkedInColumn(originalColumn, normalizedColumn)) {
                    person.linkedinUrl = normalizeLinkedInUrl(value);
                } else if (isExternalIdColumn(originalColumn, normalizedColumn)) {
                    person.externalID = value;
                }
            });

            // Only add person if they have meaningful data
            if (hasMinimumData(person)) {
                people.push(cleanPersonData(person));
            }
        });

        console.log(`📊 Converted ${people.length} people from ${csvData.length} CSV rows`);
        return people;
    }

    function isFirstNameColumn(original, normalized) {
        const patterns = ['firstName', 'FirstName', 'FIRSTNAME', 'first_name', 'firstname', 'first', 'fname', 'given_name', 'givenname'];
        return patterns.includes(original) || patterns.includes(normalized);
    }

    function isLastNameColumn(original, normalized) {
        const patterns = ['lastName', 'LastName', 'LASTNAME', 'last_name', 'lastname', 'last', 'lname', 'surname', 'family_name', 'familyname'];
        return patterns.includes(original) || patterns.includes(normalized);
    }

    function isEmailColumn(original, normalized) {
        const patterns = ['email', 'Email', 'EMAIL', 'email_address', 'emailaddress', 'mail', 'e_mail'];
        return patterns.includes(original) || patterns.includes(normalized);
    }

    function isCompanyNameColumn(original, normalized) {
        const patterns = ['companyName', 'CompanyName', 'COMPANYNAME', 'company_name', 'companyname', 'company', 'organization', 'employer', 'business', 'corp'];
        return patterns.includes(original) || patterns.includes(normalized);
    }

    function isCompanyDomainColumn(original, normalized) {
        const patterns = ['companyDomain', 'CompanyDomain', 'COMPANYDOMAIN', 'company_domain', 'companydomain', 'domain', 'website', 'company_website', 'url'];
        return patterns.includes(original) || patterns.includes(normalized);
    }

    function isLinkedInColumn(original, normalized) {
        const patterns = ['linkedinUrl', 'LinkedinUrl', 'LinkedInUrl', 'LINKEDINURL', 'linkedin_url', 'linkedinurl', 'linkedin', 'linkedin_profile', 'li_url', 'profile_url'];
        return patterns.includes(original) || patterns.includes(normalized);
    }

    function isExternalIdColumn(original, normalized) {
        const patterns = ['externalID', 'ExternalID', 'externalId', 'ExternalId', 'EXTERNALID', 'external_id', 'externalid', 'id', 'user_id', 'customer_id', 'contact_id'];
        return patterns.includes(original) || patterns.includes(normalized);
    }

    function normalizeLinkedInUrl(url) {
        if (!url) return '';
        
        url = url.trim();
        
        // Add https:// if missing
        if (url.includes('linkedin.com/in/') && !url.startsWith('http')) {
            url = 'https://' + url;
        }
        
        // Remove trailing slash
        url = url.replace(/\/$/, '');
        
        return url;
    }

    function cleanDomain(domain) {
        if (!domain) return '';

        // Remove protocol if present
        domain = domain.replace(/^https?:\/\//, '');

        // Remove www. prefix if present
        domain = domain.replace(/^www\./, '');

        // Remove path, query params, and fragment if present
        domain = domain.split('/')[0].split('?')[0].split('#')[0];

        // Remove port if present
        domain = domain.split(':')[0];

        return domain.toLowerCase().trim();
    }

    function hasMinimumData(person) {
        const hasLinkedIn = person.linkedinUrl && person.linkedinUrl.includes('linkedin');
        const hasEmail = person.email && person.email.includes('@');
        const hasNameAndCompany = person.firstName && person.lastName && 
                                (person.companyName || person.companyDomain);
        
        return hasLinkedIn || hasEmail || hasNameAndCompany;
    }

    /**
     * =====================================================================
     * Validation Utilities
     * =====================================================================
     */
    function validatePersonData(person) {
        const errors = [];
        
        // Length validation
        const lengthFields = ['companyDomain', 'companyName', 'linkedinUrl'];
        lengthFields.forEach(field => {
            if (person[field] && person[field].length > API_VALIDATION_RULES.MAX_FIELD_LENGTH) {
                errors.push(`${field} exceeds maximum length of ${API_VALIDATION_RULES.MAX_FIELD_LENGTH} characters`);
            }
        });
        
        // Format validation
        if (person.linkedinUrl && !API_VALIDATION_RULES.LINKEDIN_REGEX.test(person.linkedinUrl)) {
            errors.push('LinkedIn URL must be in format: https://linkedin.com/in/username');
        }
        
        if (person.email && !API_VALIDATION_RULES.EMAIL_REGEX.test(person.email)) {
            errors.push('Invalid email format');
        }
        
        if (person.companyDomain && !isValidDomain(person.companyDomain)) {
            errors.push('Invalid company domain format');
        }
        
        // Combination validation
        const validCombinations = checkValidCombinations(person);
        if (validCombinations.length === 0) {
            errors.push('Data does not match any valid enrichment combination');
        }
        
        return { 
            valid: errors.length === 0, 
            errors, 
            validCombinations,
            confidence: calculateConfidence(person)
        };
    }

    function isValidDomain(domain) {
        const cleanedDomain = cleanDomain(domain);
        const domainRegex = /^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.[a-zA-Z]{2,}$/;
        return domainRegex.test(cleanedDomain);
    }

    function checkValidCombinations(person) {
        const combinations = [];
        
        if (person.linkedinUrl && API_VALIDATION_RULES.LINKEDIN_REGEX.test(person.linkedinUrl)) {
            combinations.push({ type: 'LinkedIn URL', score: 95 });
        }
        
        if (person.email && API_VALIDATION_RULES.EMAIL_REGEX.test(person.email)) {
            combinations.push({ type: 'Email Address', score: 85 });
        }
        
        if (person.firstName && person.lastName && person.companyName) {
            combinations.push({ type: 'Name + Company Name', score: 80 });
        }
        
        if (person.firstName && person.lastName && person.companyDomain) {
            combinations.push({ type: 'Name + Company Domain', score: 75 });
        }
        
        return combinations;
    }

    function calculateConfidence(person) {
        const combinations = checkValidCombinations(person);
        return combinations.length > 0 ? Math.max(...combinations.map(c => c.score)) : 0;
    }

    function validateCsvPeople(people) {
        const results = {
            valid: [],
            invalid: [],
            warnings: []
        };

        people.forEach((person, index) => {
            const validation = validatePersonData(person);
            
            if (validation.valid) {
                results.valid.push(person);
            } else {
                results.invalid.push({ 
                    person, 
                    index, 
                    errors: validation.errors 
                });
            }
            
            if (validation.confidence < 60) {
                results.warnings.push({
                    index,
                    message: `Row ${index + 2}: Low confidence (${validation.confidence}%) - may have limited results`
                });
            }
        });

        return results;
    }

    function validateBulkPeople(people) {
        const results = {
            valid: [],
            invalid: [],
            warnings: []
        };

        people.forEach((person, index) => {
            const validation = validatePersonData(person);
            
            if (validation.valid) {
                results.valid.push(cleanPersonData(person));
            } else {
                results.invalid.push({ 
                    person, 
                    index, 
                    errors: validation.errors 
                });
            }
            
            if (validation.confidence < 60) {
                results.warnings.push({
                    index,
                    message: `Entry ${index + 1}: Low confidence (${validation.confidence}%) - may have limited results`
                });
            }
        });

        return results;
    }

    function cleanPersonData(person) {
        const cleanedPerson = {};
        const apiFields = ['firstName', 'lastName', 'companyDomain', 'companyName', 'linkedinUrl', 'externalID', 'email'];
        
        apiFields.forEach(field => {
            if (person[field] && person[field].trim() !== '') {
                cleanedPerson[field] = person[field].trim();
            }
        });
        
        return cleanedPerson;
    }

    /**
     * =====================================================================
     * API Communication
     * =====================================================================
     */
    async function performEnrichment(requestData) {
        console.log('🚀 Starting enrichment with enhanced error handling');
        showLoading('Submitting enrichment request...');
        
        try {
            const response = await SurfeApp.api.request('POST', '/v2/people/enrich', requestData);
            
            if (response.success && response.data && response.data.enrichmentID) {
                showToast('Enrichment job started successfully!', 'success');
                return response.data.enrichmentID;
            } else {
                throw new Error(response.error || 'Failed to start enrichment job');
            }
            
        } catch (error) {
            console.error('❌ Enrichment failed:', error);
            
            // FIXED: Use structured error data from backend
            if (error.responseData && error.responseData.suggestions) {
                showEnhancedError(
                    error.responseData.error || 'Enrichment Failed',
                    error.responseData.suggestions,
                    error.responseData.details || error.message
                );
            } else {
                // Fallback for unexpected errors
                showEnhancedError(
                    'Enrichment Failed',
                    ['Please check your input data and try again'],
                    error.message
                );
            }
            
            throw error;
        }
    }

    async function pollForResults(enrichmentID, onProgress, onComplete) {
        console.log('🔄 Polling for results:', enrichmentID);
        
        let attempts = 0;
        const maxAttempts = 30;
        const interval = 3000;

        const intervalId = setInterval(async () => {
            if (attempts >= maxAttempts) {
                clearInterval(intervalId);
                showError('Enrichment request timed out. Please try again.');
                return;
            }
            
            try {
                attempts++;
                const statusEndpoint = `/v2/people/enrich/status/${enrichmentID}`;
                
                const statusResponse = await SurfeApp.api.request('GET', statusEndpoint);
                
                if (statusResponse.success && statusResponse.status === 'completed') {
                    clearInterval(intervalId);
                    console.log('✅ Enrichment completed!');
                    
                    if (onComplete) {
                        onComplete(statusResponse.data);
                    }
                    
                } else if (statusResponse.success && statusResponse.status === 'pending') {
                    if (onProgress) {
                        onProgress(attempts, maxAttempts);
                    }
                } else if (statusResponse.success && statusResponse.status === 'failed') {
                    clearInterval(intervalId);
                    showError(`Enrichment failed: ${statusResponse.error || 'Unknown error'}`);
                }
            } catch (error) {
                console.error('Error checking status:', error);
                clearInterval(intervalId);
                showError(`Error fetching results: ${error.message}`);
            }
        }, interval);

        return intervalId;
    }

    /**
     * =====================================================================
     * UI Utilities
     * =====================================================================
     */
    function showLoading(message) {
        if (typeof SurfeApp !== 'undefined' && SurfeApp.ui) {
            SurfeApp.ui.showLoading('enrichment-results', message);
        } else {
            console.log('Loading:', message);
        }
    }

    function showError(message) {
        console.error('Error:', message);
        if (typeof SurfeApp !== 'undefined' && SurfeApp.ui) {
            SurfeApp.ui.showError('enrichment-results', message, 'Enrichment Error');
            SurfeApp.ui.showToast(message, 'error');
        } else {
            alert('Error: ' + message);
        }
    }

    function showToast(message, type) {
        if (typeof SurfeApp !== 'undefined' && SurfeApp.ui) {
            SurfeApp.ui.showToast(message, type);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }

    function showEnhancedError(userMessage, suggestions = [], technicalDetails = '') {
        console.error('Enhanced Error:', userMessage);
        
        const resultsContainer = document.getElementById('enrichment-results');
        if (resultsContainer) {
            let errorHtml = `
                <div class="alert alert-danger border-0 shadow-sm">
                    <div class="d-flex align-items-start">
                        <i class="fas fa-exclamation-triangle me-3 mt-1" style="font-size: 1.5rem; color: #dc3545;"></i>
                        <div class="w-100">
                            <h6 class="mb-2">Enrichment Error</h6>
                            <p class="mb-3">${sanitizeHtml(userMessage)}</p>
            `;
            
            if (suggestions.length > 0) {
                errorHtml += `
                            <div class="mb-3">
                                <strong>Suggested Solutions:</strong>
                                <ul class="mt-2 mb-0">
                                    ${suggestions.map(suggestion => 
                                        `<li>${sanitizeHtml(suggestion)}</li>`
                                    ).join('')}
                                </ul>
                            </div>
                `;
            }
            
            errorHtml += `
                        </div>
                    </div>
                </div>
            `;
            
            resultsContainer.innerHTML = errorHtml;
        }
        
        showToast(userMessage, 'error');
    }

    function sanitizeHtml(str) {
        if (typeof SurfeApp !== 'undefined' && SurfeApp.utils) {
            return SurfeApp.utils.sanitizeHtml(str);
        } else {
            const div = document.createElement('div');
            div.textContent = str;
            return div.innerHTML;
        }
    }

    function clearResults() {
        if (typeof SurfeApp !== 'undefined' && SurfeApp.ui) {
            SurfeApp.ui.showEmpty('enrichment-results', 'Choose an input method above and provide people data for enrichment.', 'fas fa-user-plus');
        } else {
            const container = document.getElementById('enrichment-results');
            if (container) {
                container.innerHTML = `
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
    }

    function displayEnrichmentResults(results) {
        console.log('🎨 Displaying results:', results);
        const resultsContainer = document.getElementById('enrichment-results');
        
        if (!results || results.length === 0) {
            if (typeof SurfeApp !== 'undefined' && SurfeApp.ui) {
                SurfeApp.ui.showEmpty('enrichment-results', 'The enrichment completed but no additional data was found.', 'fas fa-user-times');
            }
            return;
        }

        const enrichedCount = results.filter(person => 
            person.email || person.mobile || person.linkedinUrl || 
            (person.emails && person.emails.length > 0) ||
            (person.mobilePhones && person.mobilePhones.length > 0)
        ).length;

        const resultsHtml = `
            <div class="alert alert-success border-0 shadow-sm mb-4">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <h5 class="mb-2"><i class="fas fa-check-circle me-2"></i>Enrichment Complete</h5>
                        <p class="mb-0">Successfully processed ${results.length} ${results.length === 1 ? 'person' : 'people'}, enriched ${enrichedCount} with additional data.</p>
                    </div>
                    <div class="col-md-4 text-md-end">
                        <div class="btn-group">
                            <button class="btn btn-outline-primary" onclick="exportResults('csv')">
                                <i class="fas fa-download me-1"></i>CSV
                            </button>
                            <button class="btn btn-outline-secondary" onclick="exportResults('json')">
                                <i class="fas fa-download me-1"></i>JSON
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row">
                ${results.map((person, index) => createPersonCard(person, index)).join('')}
            </div>
        `;

        resultsContainer.innerHTML = resultsHtml;
    }

    function createPersonCard(person, index = 0) {
        const firstName = person.firstName || person.first_name || '';
        const lastName = person.lastName || person.last_name || '';
        const fullName = `${firstName} ${lastName}`.trim() || 'Unknown Name';
        const initials = `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase() || '??';
        
        const company = person.companyName || person.company_name || 'N/A';
        const email = person.email || (person.emails && person.emails[0]?.email) || '';
        const mobile = person.mobile || (person.mobilePhones && person.mobilePhones[0]?.mobilePhone) || '';
        const linkedin = person.linkedinUrl || person.linkedin_url || '';
        
        const hasEmail = email && email !== 'N/A';
        const hasMobile = mobile && mobile !== 'N/A';
        const hasLinkedIn = linkedin && linkedin !== 'N/A';
        
        return `
            <div class="col-lg-6 col-xl-4 mb-4">
                <div class="person-card">
                    <div class="person-card-header">
                        <div class="d-flex align-items-center">
                            <div class="person-avatar">${initials}</div>
                            <div class="person-header-content">
                                <h6>${sanitizeHtml(fullName)}</h6>
                                <p class="text-muted mb-0">Professional Contact</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="person-info-grid">
                        <div class="person-info-item">
                            <i class="fas fa-building person-info-icon"></i>
                            <div class="person-info-content">
                                <div class="person-info-label">Company</div>
                                <div class="person-info-value ${company === 'N/A' ? 'empty' : ''}">${sanitizeHtml(company)}</div>
                            </div>
                        </div>
                        
                        <div class="person-info-item">
                            <i class="fas fa-envelope person-info-icon"></i>
                            <div class="person-info-content">
                                <div class="person-info-label">Email Address</div>
                                <div class="person-info-value ${!hasEmail ? 'empty' : ''}">
                                    ${hasEmail ? `<a href="mailto:${email}">${sanitizeHtml(email)}</a>` : 'Not available'}
                                    ${hasEmail ? '<span class="verification-badge verified">Found</span>' : '<span class="verification-badge unverified">N/A</span>'}
                                </div>
                            </div>
                        </div>
                        
                        <div class="person-info-item">
                            <i class="fas fa-mobile-alt person-info-icon"></i>
                            <div class="person-info-content">
                                <div class="person-info-label">Phone Number</div>
                                <div class="person-info-value ${!hasMobile ? 'empty' : ''}">
                                    ${hasMobile ? `<a href="tel:${mobile}">${sanitizeHtml(mobile)}</a>` : 'Not available'}
                                    ${hasMobile ? '<span class="verification-badge verified">Found</span>' : '<span class="verification-badge unverified">N/A</span>'}
                                </div>
                            </div>
                        </div>
                        
                        ${hasLinkedIn ? `
                        <div class="person-info-item">
                            <i class="fab fa-linkedin person-info-icon"></i>
                            <div class="person-info-content">
                                <div class="person-info-label">LinkedIn Profile</div>
                                <div class="person-info-value">
                                    <a href="${linkedin}" target="_blank" class="linkedin-link">View Profile</a>
                                    <span class="verification-badge verified">Available</span>
                                </div>
                            </div>
                        </div>
                        ` : ''}
                    </div>
                    
                    <div class="person-card-actions">
                        <div class="text-muted small">
                            <i class="fas fa-clock me-1"></i>Enriched just now
                        </div>
                        <div>
                            <button class="btn btn-sm btn-outline-primary" onclick="exportPersonData(${index})">
                                <i class="fas fa-download me-1"></i>Export
                            </button>
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
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function addCustomStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .input-method-card {
                transition: all 0.3s ease;
                cursor: pointer;
                border: 2px solid #e9ecef;
                border-radius: 12px;
                padding: 1.5rem;
                text-align: center;
                background: white;
            }

            .input-method-card:hover {
                border-color: #007bff;
                background-color: #f8f9fa;
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            }

            .input-method-card.active {
                border-color: #007bff;
                background: linear-gradient(135deg, #e3f2fd, #f8f9fa);
                box-shadow: 0 4px 15px rgba(0, 123, 255, 0.2);
            }

            .input-section {
                display: none;
                animation: fadeIn 0.3s ease-in;
            }

            .input-section.active {
                display: block;
            }

            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * =====================================================================
     * Public API - FIXED: Return object immediately
     * =====================================================================
     */
    return {
        // Input method management
        setupInputMethodSwitching,
        switchInputMethod,
        
        // CSV processing
        convertCsvToPeople,
        validateCsvPeople,
        
        // Bulk processing
        validateBulkPeople,
        
        // Validation
        validatePersonData,
        cleanPersonData,
        calculateConfidence,
        
        // API communication
        performEnrichment,
        pollForResults,
        
        // UI utilities
        showLoading,
        showError,
        showEnhancedError,
        clearResults,
        displayEnrichmentResults,
        createPersonCard,
        addCustomStyles,
        
        // Utility functions
        formatFileSize,
        
        // Constants
        API_VALIDATION_RULES
    };

})();

// FIXED: Log confirmation that utils are loaded
console.log('✅ PeopleEnrichmentUtils loaded and available on window object');