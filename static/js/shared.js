/**
 * =====================================================================
 * Surfe API Project - Shared JavaScript Utilities
 * Handles global functionality, API calls, and common UI patterns
 * =====================================================================
 */

// Global application namespace
window.SurfeApp = window.SurfeApp || {};

/**
 * =====================================================================
 * Configuration and Constants
 * =====================================================================
 */
SurfeApp.config = {
    apiBaseUrl: '/api',
    requestTimeout: 30000,
    maxAttempts: 1,
    requestDelay: 1000,

    // UI Constants
    animationDuration: 300,
    debounceDelay: 500,

    // Pagination
    defaultPageSize: 10,
    maxPageSize: 100
};

/**
 * =====================================================================
 * Utility Functions
 * =====================================================================
 */
SurfeApp.utils = {

    /**
     * Debounce function to limit API calls
     */
    debounce: function (func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Format numbers with proper locale support
     */
    formatNumber: function (num) {
        if (num === null || num === undefined) return 'N/A';
        if (typeof num !== 'number') return num;
        return new Intl.NumberFormat().format(num);
    },

    /**
     * Format percentages
     */
    formatPercentage: function (num, decimals = 1) {
        if (num === null || num === undefined) return 'N/A';
        if (typeof num !== 'number') return num;
        return `${num.toFixed(decimals)}%`;
    },

    /**
     * Format dates in a user-friendly way
     */
    formatDate: function (dateString) {
        if (!dateString) return 'N/A';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        } catch (e) {
            return dateString;
        }
    },

    /**
     * Safe JSON parsing
     */
    safeJsonParse: function (str, defaultValue = null) {
        try {
            return JSON.parse(str);
        } catch (e) {
            console.warn('Failed to parse JSON:', str);
            return defaultValue;
        }
    },

    /**
     * Generate unique IDs
     */
    generateId: function (prefix = 'id') {
        return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    },

    /**
     * Sanitize HTML to prevent XSS
     */
    sanitizeHtml: function (str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    /**
     * Parse textarea input into clean array of lines
     */
    parseTextareaLines: function (text) {
        if (!text) return [];
        return text.split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 0);
    },

    /**
     * Parse textarea input into clean array of domains
     */
    parseTextareaDomains: function (text) {
        if (!text) return [];
        return text.split('\n')
            .map(line => this.cleanDomain(line.trim()))
            .filter(domain => domain.length > 0 && this.isValidDomain(domain));
    },

    /**
     * Validate URL format
     */
    isValidUrl: function (url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    },

    /**
     * Validate email format
     */
    isValidEmail: function (email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    },

    /**
     * Clean and validate domain format
     */
    cleanDomain: function (domain) {
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
    },

    /**
     * Validate domain format
     */
    isValidDomain: function (domain) {
        const cleanedDomain = this.cleanDomain(domain);
        const domainRegex = /^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.[a-zA-Z]{2,}$/;
        return domainRegex.test(cleanedDomain);
    },

    /**
     * Format large numbers (e.g., employee count)
     */
    formatLargeNumber: function (count) {
        if (!count) return 'N/A';
        if (count < 1000) return count.toString();
        if (count < 1000000) return `${(count / 1000).toFixed(1)}K`;
        return `${(count / 1000000).toFixed(1)}M`;
    },

    /**
     * Format revenue/financial amounts
     */
    formatRevenue: function (revenue) {
        if (!revenue) return null;
        if (typeof revenue === 'string') return revenue;
        if (revenue < 1000000) return `$${(revenue / 1000).toFixed(0)}K`;
        if (revenue < 1000000000) return `$${(revenue / 1000000).toFixed(1)}M`;
        return `$${(revenue / 1000000000).toFixed(1)}B`;
    },

    /**
     * Truncate text to specified length
     */
    truncateText: function (text, maxLength) {
        if (!text || text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    },

    /**
     * Reset form and clear validation errors
     */
    resetForm: function (formSelector) {
        const form = document.querySelector(formSelector);
        if (form) {
            form.reset();
            // Clear validation errors
            form.querySelectorAll('.is-invalid').forEach(input => {
                input.classList.remove('is-invalid');
            });
            form.querySelectorAll('.invalid-feedback').forEach(feedback => {
                feedback.remove();
            });
        }
    },

    /**
     * Update button loading state
     */
    updateButtonState: function (button, isLoading, loadingText = 'Loading...', normalText = 'Submit') {
        if (!button) return;

        if (isLoading) {
            button.disabled = true;
            button.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                ${loadingText}
            `;
        } else {
            button.disabled = false;
            button.innerHTML = normalText;
        }
    },

    /**
     * Show element using CSS class
     */
    show: function (element) {
        if (!element) return;
        element.classList.remove('hidden');
        element.classList.add('visible');
    },

    /**
     * Hide element using CSS class
     */
    hide: function (element) {
        if (!element) return;
        element.classList.add('hidden');
        element.classList.remove('visible');
    },

    /**
     * Toggle element visibility using CSS class
     */
    toggle: function (element) {
        if (!element) return;
        if (element.classList.contains('hidden')) {
            this.show(element);
        } else {
            this.hide(element);
        }
    },

    /**
     * =====================================================================
     * CSV Utility Functions
     * =====================================================================
     */

    /**
     * Export data to CSV file
     */
    exportToCsv: function (data, filename = 'export.csv', type = 'people') {
        if (!data || data.length === 0) {
            SurfeApp.ui.showToast('No data to export', 'warning');
            return;
        }

        const csvContent = this.convertToCSV(data, type);
        this.downloadFile(csvContent, filename, 'text/csv');

        SurfeApp.ui.showToast(`Results exported as ${filename}`, 'success');
    },

    /**
     * Export data to JSON file
     */
    exportToJson: function (data, filename = 'export.json') {
        if (!data || data.length === 0) {
            SurfeApp.ui.showToast('No data to export', 'warning');
            return;
        }

        const jsonContent = JSON.stringify(data, null, 2);
        this.downloadFile(jsonContent, filename, 'application/json');

        SurfeApp.ui.showToast(`Results exported as ${filename}`, 'success');
    },

    // In SurfeApp.utils
    csvHeaderMaps: {
        // ======== People Search CSV Headers ========
        people: {
            'firstName': 'First Name',
            'lastName': 'Last Name',
            'jobTitle': 'Job Title',
            'linkedInUrl': 'LinkedIn URL',
            'companyName': 'Company Name',
            'companyDomain': 'companyDomain',
            'country': 'Country',
            'departments': 'Departments', // This will be comma-separated
            'seniorities': 'Seniorities' // This will be comma-separated
        },

        // ======== People Enrichment CSV Headers ========
        people_enrichment: {
            'firstName': 'First Name',
            'lastName': 'Last Name',
            'jobTitle': 'Job Title',
            'linkedInUrl': 'LinkedIn URL',
            'location': 'Location',
            'country': 'Country',
            'emails.0.email': 'Email',
            'emails.0.validationStatus': 'Email Status',
            'mobilePhones.0.mobilePhone': 'Mobile Phone 1',
            'mobilePhones.1.mobilePhone': 'Mobile Phone 2',
            'mobilePhones.2.mobilePhone': 'Mobile Phone 3',
            'mobilePhones.0.confidenceScore': 'Phone 1 Confidence',
            'mobilePhones.1.confidenceScore': 'Phone 2 Confidence',
            'mobilePhones.2.confidenceScore': 'Phone 3 Confidence',
            'companyName': 'Company Name',
            'companyDomain': 'companyDomain',
            'departments': 'Departments',
            'seniorities': 'Seniorities',
            'jobHistory.0.jobTitle': 'Previous Job Title',
            'jobHistory.0.companyName': 'Previous Company',
            'jobHistory.0.startDate': 'Previous Job Start',
            'jobHistory.0.endDate': 'Previous Job End',
            'externalID': 'External ID',
            'status': 'Status'
        },

        // ======== Company Search CSV Headers ========
        company: {
            'name': 'Company Name',
            'domain': 'Domain',
            'employeeCount': 'Employee Count',
            'revenue': 'Revenue',
            'industries': 'Industries',
            'countries': 'Countries',
            'companyDomains': 'companyDomain'
        },

        // ======== Company Enrichment CSV Headers ========
        company_enrichment: {
            'name': 'Company Name',
            'linkedInURL': 'Company LinkedIn URL',
            'description': 'Description',
            'industry': 'Industry',
            'subIndustry': 'Sub-Industry',
            'employeeCount': 'Employee Count',
            'founded': 'Founded Year',
            'revenue': 'Revenue',
            'keywords': 'Keywords',
            'hqAddress': 'HQ Address',
            'hqCountry': 'HQ Country',
            'companyDomains':  'companyDomain',
            'websites': 'Website',
            'phones.0': 'Phone 1',
            'phones.1': 'Phone 2',
            'phones.2': 'Phone 3',
            'followersCountLinkedi': 'LinkedIn Followers',
            'isPublic': 'Is Public',
            'parentOrganization.name': 'Parent Organization',
            'parentOrganization.website': 'Parent Organization Website',
            'ipo.date': 'IPO Date',
            'ipo.sharePrice': 'IPO Share Price',
            'ipo.sharePriceCurrency': 'IPO Currency',
            'stocks.0.ticker': 'Stock Ticker',
            'stocks.0.exchange': 'Stock Exchange',
            'fundingRounds.0.name': 'Last Funding Round',
            'fundingRounds.0.amount': 'Last Funding Amount',
            'fundingRounds.0.amountCurrency': 'Funding Currency',
            'fundingRounds.0.announcedDate': 'Last Funding Date',
            'digitalPresence.0.name': 'Digital Presence Site',
            'digitalPresence.0.url': 'Digital Presence URL',
            'externalID': 'External ID',
            'status': 'Company Status'
        }
    },

        // Add this helper function to SurfeApp.utils
        getNestedValue: function (obj, path) {
        // Handle arrays that should be joined (removed 'phones' from this list)
        if (['keywords', 'websites', 'industries', 'countries', 'departments', 'seniorities'].includes(path) && Array.isArray(obj[path])) {
            return obj[path].join(', ');
        }

        // Handle array index access (e.g., 'phones.0', 'emails.0.email')
        if (path.includes('.')) {
            return path.split('.').reduce((acc, part) => {
                if (acc === null || acc === undefined) return '';

                if (!isNaN(part)) {
                    const index = parseInt(part);
                    return Array.isArray(acc) && acc[index] ? acc[index] : '';
                }

                return acc[part];
            }, obj);
        }

        // Simple property access
        const value = obj[path];
        return value === undefined || value === null ? '' : value;
    },

    // Replace the old convertToCSV with this one
    convertToCSV: function (data, type) {
        if (!Array.isArray(data) || data.length === 0) return '';

        const headerMap = this.csvHeaderMaps[type];
        if (!headerMap) {
            console.error('Invalid CSV export type:', type);
            return '';
        }

        const orderedPaths = Object.keys(headerMap);
        const csvRows = [];

        // Filter out paths that have no data in any row
        const pathsWithData = orderedPaths.filter(path => {
            return data.some(item => {
                const value = this.getNestedValue(item, path);
                return value !== '' && value !== null && value !== undefined;
            });
        });

        // Create header row only for paths with data
        const headerRow = pathsWithData.map(path => this.escapeCSVField(headerMap[path])).join(',');
        csvRows.push(headerRow);

        // Create data rows only for paths with data
        data.forEach(item => {
            const row = pathsWithData.map(path => {
                const value = this.getNestedValue(item, path);
                return this.escapeCSVField(value);
            });
            csvRows.push(row.join(','));
        });

        return csvRows.join('\n');
    },

    /**
     * Escape CSV field content
     */
    escapeCSVField: function (field) {
        if (field === null || field === undefined) return '';

        const fieldStr = String(field);

        // If field contains comma, newline, or quotes, wrap in quotes and escape internal quotes
        if (fieldStr.includes(',') || fieldStr.includes('\n') || fieldStr.includes('"')) {
            return '"' + fieldStr.replace(/"/g, '""') + '"';
        }

        return fieldStr;
    },

    /**
     * formatCSVValue function updated by gemini to handle csv array of email objects
     */

    formatCSVValue: function (value, key) { // Note: The 'key' parameter is new
        if (value === null || value === undefined) {
            return '';
        }

        if (Array.isArray(value)) {
            // If the key is 'keywords', join the array with commas.
            if (key === 'keywords') {
                return value.join(', ');
            }

            // For other arrays, return the first item.
            // (Emails & Phones are handled before this function is called).
            if (value.length > 0) {
                return String(value[0]);
            }
            return '';
        }

        // Handle all other types as before
        if (typeof value === 'object') {
            return ''; // Avoids outputting [object Object]
        }

        return String(value);
    },


    /**
     * Parse CSV content to array of objects
     */
    parseCSV: function (csvContent, options = {}) {
        const {
            headers = null,
            delimiter = ',',
            skipEmptyLines = true,
            trimValues = true
        } = options;

        if (!csvContent) return [];

        const lines = csvContent.split('\n');
        if (lines.length === 0) return [];

        // Remove empty lines if requested
        const filteredLines = skipEmptyLines ?
            lines.filter(line => line.trim().length > 0) : lines;

        if (filteredLines.length === 0) return [];

        // Parse header row
        const headerRow = headers || this.parseCSVLine(filteredLines[0], delimiter);
        const dataStartIndex = headers ? 0 : 1;

        // Parse data rows
        const result = [];
        for (let i = dataStartIndex; i < filteredLines.length; i++) {
            const values = this.parseCSVLine(filteredLines[i], delimiter);
            const row = {};

            headerRow.forEach((header, index) => {
                let value = values[index] || '';
                if (trimValues) value = value.trim();
                row[header] = value;
            });

            result.push(row);
        }

        return result;
    },

    /**
     * Parse a single CSV line considering quoted fields
     */
    parseCSVLine: function (line, delimiter = ',') {
        const result = [];
        let current = '';
        let inQuotes = false;
        let i = 0;

        while (i < line.length) {
            const char = line[i];

            if (char === '"') {
                if (inQuotes && line[i + 1] === '"') {
                    // Escaped quote
                    current += '"';
                    i += 2;
                    continue;
                } else {
                    // Toggle quote state
                    inQuotes = !inQuotes;
                }
            } else if (char === delimiter && !inQuotes) {
                // Field separator
                result.push(current);
                current = '';
                i++;
                continue;
            } else {
                current += char;
            }

            i++;
        }

        // Add the last field
        result.push(current);

        return result;
    },

    /**
     * Download file with given content
     */
    downloadFile: function (content, filename, mimeType = 'text/plain') {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);

        const downloadLink = document.createElement('a');
        downloadLink.href = url;
        downloadLink.download = filename;
        downloadLink.style.display = 'none';

        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);

        // Clean up the URL object
        URL.revokeObjectURL(url);
    },

    /**
     * Validate CSV file input
     */
    validateCSVFile: function (file, maxSize = 5 * 1024 * 1024) {
        const errors = [];

        if (!file) {
            errors.push('No file selected');
            return { valid: false, errors };
        }

        // Check file type
        if (!file.name.toLowerCase().endsWith('.csv')) {
            errors.push('File must be a CSV file (.csv)');
        }

        // Check file size
        if (file.size > maxSize) {
            const maxSizeMB = Math.round(maxSize / (1024 * 1024));
            errors.push(`File size must be less than ${maxSizeMB}MB`);
        }

        // Check if file is empty
        if (file.size === 0) {
            errors.push('File cannot be empty');
        }

        return {
            valid: errors.length === 0,
            errors: errors
        };
    },

    /**
     * Read CSV file and return parsed data
     */
    readCSVFile: function (file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();

            reader.onload = function (e) {
                try {
                    const csvContent = e.target.result;
                    const parsedData = SurfeApp.utils.parseCSV(csvContent);
                    resolve(parsedData);
                } catch (error) {
                    reject(new Error(`Failed to parse CSV: ${error.message}`));
                }
            };

            reader.onerror = function () {
                reject(new Error('Failed to read file'));
            };

            reader.readAsText(file);
        });
    }
};

/**
 * =====================================================================
 * API Client with Error Handling
 * =====================================================================
 */
SurfeApp.api = {

    /**
     * Make API request with single attempt
     */
    request: async function (method, endpoint, data = null, options = {}) {
        const config = {
            // 1. First, spread any miscellaneous options passed in
            ...options,

            // 2. Then, explicitly define the method and headers to ensure they are correct
            method: method.toUpperCase(),
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                // 3. Finally, add any custom headers from the options
                ...options.headers
            }
        };

        if (data && (method.toUpperCase() === 'POST' || method.toUpperCase() === 'PUT')) {
            config.body = JSON.stringify(data);
        }

        const url = `${SurfeApp.config.apiBaseUrl}${endpoint}`;

        console.log(`🔍 API Request: ${method.toUpperCase()} ${url}`, data);

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), SurfeApp.config.requestTimeout);
            config.signal = controller.signal;

            const response = await fetch(url, config);
            clearTimeout(timeoutId);

            console.log(`📡 API Response: ${response.status} for ${url}`);

            // FIXED: Parse response body before throwing error
            let responseData;
            try {
                responseData = await response.json();
            } catch (e) {
                responseData = { error: `HTTP ${response.status}`, message: response.statusText };
            }

            if (!response.ok) {
                // FIXED: Create error with structured data attached
                const error = new Error(responseData.error || responseData.message || `HTTP ${response.status}`);
                error.status = response.status;
                error.responseData = responseData; // Attach the structured error data
                throw error;
            }

            console.log(`✅ API Success: ${url}`, responseData);
            return responseData;

        } catch (error) {
            console.error(`❌ API Error:`, error);
            throw error;
        }
    },

    /**
     * Parse error response
     */
    parseErrorResponse: async function (response) {
        try {
            return await response.json();
        } catch (e) {
            return {
                error: `HTTP ${response.status}`,
                message: response.statusText || 'Unknown error'
            };
        }
    },

    /**
     * Specific API methods - FIXED VERSION
     */
    searchPeople: function (searchData) {
        return this.request('POST', '/v2/people/search', searchData);  // ✅ Removed /api
    },

    searchCompanies: function (searchData) {
        return this.request('POST', '/v2/companies/search', searchData);  // ✅ Removed /api
    },

    getHealthCheck: function () {
        return this.request('GET', '/health');  // ✅ Keep as is (no /api in Flask)
    },

    getStats: function () {
        return this.request('GET', '/stats');  // ✅ Removed /api
    },

    // People enrichment methods
    enrichPeople: function (enrichData) {
        return this.request('POST', '/v2/people/enrich', enrichData);  // ✅ Removed /api
    },

    enrichPeopleBulk: function (enrichData) {
        return this.request('POST', '/v2/people/enrich/bulk', enrichData);  // ✅ Removed /api
    },

    getPeopleEnrichmentStatus: function (enrichmentId) {
        return this.request('GET', `/v2/people/enrich/status/${enrichmentId}`);  // ✅ Added /status + removed /api
    },

    // Company enrichment methods  
    enrichCompanies: function (enrichData) {
        return this.request('POST', '/v2/companies/enrich', enrichData);  // ✅ Already correct
    },

    enrichCompaniesBulk: function (enrichData) {
        return this.request('POST', '/v2/companies/enrich/bulk', enrichData);  // ✅ Already correct
    },

    getCompanyEnrichmentStatus: function (enrichmentId) {
        return this.request('GET', `/v2/companies/enrich/status/${enrichmentId}`);  // ✅ Added /status
    },

    // Settings API methods
    getSettingsConfig: function () {
        return this.request('GET', '/settings/config');  // ✅ Removed /api
    },

    addApiKey: function (keyData) {
        return this.request('POST', '/settings/keys', keyData);  // ✅ Removed /api
    },

    removeApiKey: function (keyData) {
        return this.request('DELETE', '/settings/keys', keyData);  // ✅ Removed /api
    },

    updateKeyStatus: function (statusData) {
        return this.request('POST', '/settings/keys/status', statusData);  // ✅ Removed /api
    },

    selectApiKey: function (keyData) {
        return this.request('POST', '/settings/select', keyData);  // ✅ Removed /api
    },

    testApiKey: function (testData) {
        return this.request('POST', '/settings/test', testData);  // ✅ Removed /api
    },

    refreshApiKeys: function () {
        return this.request('POST', '/settings/refresh');  // ✅ Removed /api
    },

    // Diagnostics
    getPerformanceMetrics: function () {
        return this.request('GET', '/api/diagnostics/performance');  // ✅ Keep as is (no /api in Flask)
    }
};

/**
 * =====================================================================
 * UI Management and Loading States
 * =====================================================================
 */
SurfeApp.ui = {

    /**
     * Show loading spinner
     */
    showLoading: function (containerId, message = 'Loading...') {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div class="loading-text mt-3">${SurfeApp.utils.sanitizeHtml(message)}</div>
            </div>
        `;
    },

    /**
     * Hide loading and show content
     */
    hideLoading: function (containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const spinner = container.querySelector('.loading-spinner');
        if (spinner) {
            spinner.remove();
        }
    },

    /**
     * Show error message
     */
    showError: function (containerId, error, title = 'Error') {
        const container = document.getElementById(containerId);
        if (!container) return;

        const errorMessage = typeof error === 'object' ?
            (error.message || error.error || 'Unknown error occurred') :
            error;

        container.innerHTML = `
            <div class="error-state">
                <div class="error-icon">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <h5 class="mb-3">${SurfeApp.utils.sanitizeHtml(title)}</h5>
                <p class="mb-3">${SurfeApp.utils.sanitizeHtml(errorMessage)}</p>
                <button class="btn btn-outline-primary" onclick="location.reload()">
                    <i class="fas fa-sync me-2"></i>Try Again
                </button>
            </div>
        `;
    },

    /**
     * Show empty state
     */
    showEmpty: function (containerId, message = 'No data available', icon = 'fas fa-inbox') {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">
                    <i class="${icon}"></i>
                </div>
                <h5 class="mb-3">No Results Found</h5>
                <p class="mb-0">${SurfeApp.utils.sanitizeHtml(message)}</p>
            </div>
        `;
    },

    /**
     * Show toast notification
     */
    showToast: function (message, type = 'info', duration = 5000) {
        const toastContainer = this.getOrCreateToastContainer();
        const toastId = SurfeApp.utils.generateId('toast');

        const bgClass = type === 'error' ? 'bg-danger' :
            type === 'success' ? 'bg-success' :
                type === 'warning' ? 'bg-warning' : 'bg-info';

        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white ${bgClass} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        toast.id = toastId;

        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${SurfeApp.utils.sanitizeHtml(message)}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        toastContainer.appendChild(toast);

        // Initialize Bootstrap toast
        const bsToast = new bootstrap.Toast(toast, { delay: duration });
        bsToast.show();

        // Clean up after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    },

    /**
     * Get or create toast container
     */
    getOrCreateToastContainer: function () {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '1055';
            document.body.appendChild(container);
        }
        return container;
    },

    /**
    * Update health indicator
    */
    updateHealthIndicator: function (stats) {
        const healthElement = document.getElementById('health-indicator');
        if (!healthElement || !stats) return;

        // Logic is now based on whether a valid key is selected.
        const isReady = stats.has_valid_selection;
        const enabledKeys = stats.enabled_keys || 0;
        const totalKeys = stats.total_keys || 0;

        let statusClass, statusText, statusIcon;

        if (isReady) {
            statusClass = 'status-active';
            statusText = 'Ready';
            statusIcon = 'fas fa-check-circle';
        } else if (totalKeys > 0) {
            statusClass = 'status-warning';
            statusText = 'Needs Selection';
            statusIcon = 'fas fa-exclamation-triangle';
        } else {
            statusClass = 'status-disabled';
            statusText = 'No Keys';
            statusIcon = 'fas fa-times-circle';
        }

        healthElement.innerHTML = `
            <div class="status-badge ${statusClass}">
                <div class="status-indicator"></div>
                <i class="${statusIcon} me-1"></i>
                ${statusText}
            </div>
            <small class="text-muted d-block mt-1">
                ${enabledKeys}/${totalKeys} keys enabled
            </small>
        `;
    }
};

/**
 * =====================================================================
 * Form Handling and Validation
 * =====================================================================
 */
SurfeApp.forms = {

    /**
     * Serialize form data to object
     */
    serializeForm: function (formElement) {
        const formData = new FormData(formElement);
        const data = {};

        for (let [key, value] of formData.entries()) {
            // Handle multi-select fields
            if (data[key]) {
                if (Array.isArray(data[key])) {
                    data[key].push(value);
                } else {
                    data[key] = [data[key], value];
                }
            } else {
                data[key] = value;
            }
        }

        return data;
    },

    /**
     * Validate required fields
     */
    validateForm: function (formElement) {
        const requiredFields = formElement.querySelectorAll('[required]');
        let isValid = true;

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                this.showFieldError(field, 'This field is required');
                isValid = false;
            } else {
                this.clearFieldError(field);
            }
        });

        return isValid;
    },

    /**
     * Show field error
     */
    showFieldError: function (field, message) {
        field.classList.add('is-invalid');

        let feedback = field.parentNode.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            field.parentNode.appendChild(feedback);
        }
        feedback.textContent = message;
    },

    /**
     * Clear field error
     */
    clearFieldError: function (field) {
        field.classList.remove('is-invalid');
        const feedback = field.parentNode.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.remove();
        }
    }
};

/**
 * =====================================================================
 * Export and Download Utilities
 * =====================================================================
 */
SurfeApp.export = {

    /**
     * Export data to CSV
     */
    toCsv: function (data, filename = 'export.csv') {
        if (!data || data.length === 0) {
            SurfeApp.ui.showToast('No data to export', 'warning');
            return;
        }

        // Get headers from first object
        const headers = Object.keys(data[0]);

        // Create CSV content
        const csvContent = [
            headers.join(','),
            ...data.map(row =>
                headers.map(header => {
                    const value = row[header] || '';
                    // Escape quotes and wrap in quotes if contains comma
                    const escaped = String(value).replace(/"/g, '""');
                    return escaped.includes(',') || escaped.includes('\n') ?
                        `"${escaped}"` : escaped;
                }).join(',')
            )
        ].join('\n');

        this.downloadFile(csvContent, filename, 'text/csv');
    },

    /**
     * Export data to JSON
     */
    toJson: function (data, filename = 'export.json') {
        if (!data) {
            SurfeApp.ui.showToast('No data to export', 'warning');
            return;
        }

        const jsonContent = JSON.stringify(data, null, 2);
        this.downloadFile(jsonContent, filename, 'application/json');
    },

    /**
     * Download file
     */
    downloadFile: function (content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        SurfeApp.ui.showToast(`Downloaded ${filename}`, 'success');
    }
};

/**
 * =====================================================================
 * Auto-refresh and Real-time Updates
 * =====================================================================
 */
SurfeApp.autoRefresh = {
    intervals: new Map(),

    /**
     * Start auto-refresh for a function
     */
    start: function (key, func, interval = 30000) {
        this.stop(key); // Clear existing interval

        const intervalId = setInterval(func, interval);
        this.intervals.set(key, intervalId);

        console.log(`🔄 Started auto-refresh for ${key} (${interval}ms)`);
    },

    /**
     * Stop auto-refresh
     */
    stop: function (key) {
        const intervalId = this.intervals.get(key);
        if (intervalId) {
            clearInterval(intervalId);
            this.intervals.delete(key);
            console.log(`⏹️ Stopped auto-refresh for ${key}`);
        }
    },

    /**
     * Stop all auto-refresh
     */
    stopAll: function () {
        this.intervals.forEach((intervalId, key) => {
            clearInterval(intervalId);
            console.log(`⏹️ Stopped auto-refresh for ${key}`);
        });
        this.intervals.clear();
    }
};

/**
 * =====================================================================
 * Authentic Surfe API Data
 * =====================================================================
 */
SurfeApp.data = {
    // Official Surfe API Seniority levels
    seniorities: [
        "Board Member",
        "C-Level",
        "Director",
        "Founder",
        "Head",
        "Manager",
        "Other",
        "Owner",
        "Partner",
        "VP"
    ],

    // Official Surfe API Departments
    departments: [
        "Accounting and Finance",
        "Board",
        "Business Support",
        "Customer Relations",
        "Design",
        "Editorial Personnel",
        "Engineering",
        "Founder/Owner",
        "Healthcare",
        "HR",
        "Legal",
        "Management",
        "Manufacturing",
        "Marketing and Advertising",
        "Operations",
        "Other",
        "PR and Communications",
        "Procurement",
        "Product",
        "Quality Control",
        "R&D",
        "Sales",
        "Security",
        "Supply Chain"
    ],

    // Complete Official Surfe API Industries (from authentic API documentation)
    industries: [
        "Call Center", "Collection Agency", "Courier Service", "Debt Collections", "Delivery", "Document Preparation", "Extermination Service", "Facilities Support Services", "Housekeeping Service", "Office Administration", "Packaging Services", "Physical Security", "Staffing Agency", "Trade Shows", "Virtual Workforce", "Ad Network", "Advertising", "Advertising Platforms", "Affiliate Marketing", "Mobile Advertising", "Outdoor Advertising", "SEM", "Social Media Advertising", "Video Advertising", "3D Technology", "Accounting", "Accounting Services", "Bookkeeping", "Compliance", "CPA", "Financial Services", "Payroll", "Agriculture", "Agricultural Biotechnology", "Agtech", "Animal Feed", "Aquaculture", "Farming", "Fertilizers", "Food Production", "Forestry", "Livestock", "Agriculture Machinery", "Agriculture", "Artificial Intelligence", "Automotive", "Automotive Parts", "Autonomous Vehicles", "Car Rental", "Electric Vehicles", "Motorcycles", "Ridesharing", "Used Cars", "Aviation", "Airlines", "Aircraft Manufacturing", "Airport Operations", "Commercial Aviation", "General Aviation", "Aviation Software", "Banking", "Commercial Banking", "Credit Cards", "Investment Banking", "Mortgage Banking", "Private Banking", "Retail Banking", "Biotechnology", "Bioengineering", "Bioinformatics", "Biomedicine", "Biopharmaceuticals", "Clinical Research", "Drug Discovery", "Gene Therapy", "Genomics", "Medical Devices", "Pharmaceuticals", "Precision Medicine", "Blockchain", "Cryptocurrency", "DeFi", "Digital Assets", "NFT", "Smart Contracts", "Building Materials", "Cement", "Construction", "Construction Equipment", "Heavy Equipment", "Home Improvement", "Infrastructure", "Roofing", "Business Intelligence", "Analytics", "Big Data", "Data Science", "Data Visualization", "Market Research", "Predictive Analytics", "Call Center", "CRM", "Customer Service", "Help Desk", "Live Chat", "Support", "Telecommunications", "Chemical", "Chemical Manufacturing", "Petrochemicals", "Plastics", "Specialty Chemicals", "Cloud Computing", "Cloud Infrastructure", "Cloud Services", "DevOps", "Infrastructure as a Service", "Platform as a Service", "Software as a Service", "Consulting", "Business Consulting", "IT Consulting", "Management Consulting", "Strategy Consulting", "Consumer Electronics", "Audio Equipment", "Computer Hardware", "Gaming Hardware", "Mobile Devices", "Smart Home", "Wearable Technology", "Consumer Goods", "Apparel", "Beauty", "Cosmetics", "Fashion", "Fast Moving Consumer Goods", "Home and Garden", "Jewelry", "Luxury Goods", "Personal Care", "Sporting Goods", "Toys", "CRM", "Customer Relationship Management", "Lead Generation", "Sales Automation", "Sales Software", "Cyber Security", "Application Security", "Cloud Security", "Data Protection", "Identity Management", "Network Security", "Privacy", "Security Software", "Database", "Data Management", "Data Storage", "NoSQL", "SQL", "E-Commerce", "Marketplace", "Online Retail", "Payment Processing", "Shopping", "Education", "E-Learning", "EdTech", "Higher Education", "K-12 Education", "Language Learning", "Online Education", "Training", "Tutoring", "Energy", "Clean Energy", "Electricity", "Energy Storage", "Natural Gas", "Nuclear Energy", "Oil and Gas", "Renewable Energy", "Solar Energy", "Wind Energy", "Engineering", "Aerospace Engineering", "Chemical Engineering", "Civil Engineering", "Electrical Engineering", "Environmental Engineering", "Mechanical Engineering", "Software Engineering", "Structural Engineering", "Entertainment", "Broadcasting", "Content Creation", "Film Production", "Gaming", "Media", "Music", "Publishing", "Streaming", "Television", "Video Production", "Environmental", "Carbon Credits", "Climate Technology", "Environmental Consulting", "Pollution Control", "Recycling", "Sustainability", "Waste Management", "Water Treatment", "Finance", "Asset Management", "Capital Markets", "Corporate Finance", "Financial Planning", "Financial Technology", "Investment Management", "Private Equity", "Venture Capital", "Wealth Management", "FinTech", "Digital Banking", "Digital Payments", "Financial Software", "InsurTech", "LendTech", "Open Banking", "Payment Processing", "Personal Finance", "RegTech", "WealthTech", "Food and Beverage", "Beverages", "Food Manufacturing", "Food Processing", "Food Service", "Restaurants", "Gaming", "Casino", "Esports", "Game Development", "Gaming Hardware", "Mobile Gaming", "Online Gaming", "Video Games", "Government", "Defense", "Federal Government", "Local Government", "Military", "Public Administration", "Public Safety", "State Government", "Hardware", "Computer Hardware", "Electronics Manufacturing", "Semiconductor", "Health Care", "Biotechnology", "Digital Health", "Health Insurance", "Healthcare IT", "Healthcare Services", "Hospitals", "Medical Devices", "Mental Health", "Pharmaceuticals", "Telemedicine", "Wellness", "HR", "Benefits Administration", "Compensation", "Employee Engagement", "Human Resources", "Payroll", "Performance Management", "Recruiting", "Talent Acquisition", "Talent Management", "Workforce Management", "Information Technology", "Enterprise Software", "IT Services", "Software Development", "Technology Consulting", "Insurance", "Auto Insurance", "Health Insurance", "Life Insurance", "Property Insurance", "Reinsurance", "Internet", "Content Delivery Networks", "Domain Names", "Internet Infrastructure", "Internet Service Providers", "Web Hosting", "Web Services", "Legal", "Corporate Law", "Family Law", "Immigration Law", "Intellectual Property", "Legal Services", "Legal Technology", "Litigation", "Patent Law", "Logistics", "Freight", "Last Mile Delivery", "Shipping", "Supply Chain", "Transportation", "Warehousing", "Machine Learning", "Artificial Intelligence", "Computer Vision", "Deep Learning", "Natural Language Processing", "Neural Networks", "Robotics", "Manufacturing", "Aerospace Manufacturing", "Automotive Manufacturing", "Chemical Manufacturing", "Electronics Manufacturing", "Food Manufacturing", "Industrial Manufacturing", "Textile Manufacturing", "Marketing", "Content Marketing", "Digital Marketing", "Email Marketing", "Marketing Automation", "Performance Marketing", "Search Engine Marketing", "Social Media Marketing", "Media and Entertainment", "Broadcasting", "Digital Media", "Film", "Music", "News", "Publishing", "Radio", "Social Media", "Television", "Video Streaming", "Mining", "Coal Mining", "Gold Mining", "Metal Mining", "Oil and Gas Extraction", "Mobile", "Mobile Apps", "Mobile Commerce", "Mobile Development", "Mobile Gaming", "Mobile Marketing", "Mobile Payments", "Mobile Software", "Non Profit", "Charity", "Foundation", "NGO", "Social Impact", "Non-Profit", "Oil and Gas", "Energy", "Natural Gas", "Oil Exploration", "Oil Refining", "Petroleum", "Personal Care", "Beauty", "Cosmetics", "Skincare", "Wellness", "Pharmaceuticals", "Biotech", "Clinical Trials", "Drug Development", "Medical Research", "Pharmaceuticals", "Real Estate", "Commercial Real Estate", "Property Management", "Real Estate Development", "Real Estate Investment", "Real Estate Technology", "Residential Real Estate", "Restaurants", "Casual Dining", "Fast Food", "Fine Dining", "Food Delivery", "Food Service", "Quick Service Restaurant", "Retail", "Department Stores", "Discount Stores", "Fashion Retail", "Grocery", "Luxury Retail", "Online Retail", "Specialty Retail", "SaaS", "B2B Software", "Business Software", "Cloud Software", "Enterprise SaaS", "Software as a Service", "Vertical SaaS", "Sales", "Inside Sales", "Outside Sales", "Sales Development", "Sales Enablement", "Sales Operations", "Telesales", "Security", "Cybersecurity", "Information Security", "Network Security", "Physical Security", "Software", "Application Software", "Business Software", "Consumer Software", "Enterprise Software", "Mobile Software", "Open Source Software", "Software Development", "System Software", "Sports", "Fantasy Sports", "Fitness", "Professional Sports", "Sports Analytics", "Sports Media", "Sports Technology", "Telecommunications", "5G", "Broadband", "Mobile Networks", "Network Infrastructure", "Telecom Equipment", "Telecom Services", "Wireless", "Transportation", "Autonomous Vehicles", "Logistics", "Mass Transportation", "Public Transportation", "Ridesharing", "Shipping", "Transportation Technology", "Travel", "Airlines", "Hospitality", "Hotels", "Online Travel", "Tourism", "Travel Technology", "Vacation Rentals", "Utilities", "Electric Utilities", "Gas Utilities", "Public Utilities", "Renewable Utilities", "Water Utilities", "Video Streaming", "Content Streaming", "Live Streaming", "Video on Demand", "Video Technology", "Virtual Reality", "Augmented Reality", "Mixed Reality", "VR/AR", "Warehousing", "Distribution", "Fulfillment", "Inventory Management", "Logistics", "Supply Chain", "Warehouse Automation", "Web Development", "Frontend Development", "Full Stack Development", "Web Design", "Web Services", "Website Development"
    ],

    // ISO 3166-1 country names
    countries: [
        "United States",
        "United Kingdom",
        "Canada",
        "Australia",
        "Germany",
        "France",
        "Netherlands",
        "Sweden",
        "Spain",
        "Italy",
        "Switzerland",
        "Ireland",
        "Denmark",
        "Norway",
        "Belgium",
        "Austria",
        "Finland",
        "Poland",
        "Portugal",
        "Brazil",
        "India",
        "Japan",
        "Singapore",
        "Israel",
        "South Africa",
        "New Zealand",
        "Mexico",
        "Argentina",
        "Chile",
        "Colombia",
        "China",
        "Korea, Republic of",
        "Thailand",
        "Malaysia",
        "Indonesia",
        "Philippines",
        "Viet Nam",
        "Taiwan, Province of China",
        "Hong Kong",
        "United Arab Emirates",
        "Saudi Arabia",
        "Egypt",
        "Nigeria",
        "Kenya",
        "Morocco",
        "Tunisia",
        "Ghana"
    ]
};

/**
 * =====================================================================
 * Page Lifecycle Management
 * =====================================================================
 */
// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    console.log('🚀 SurfeApp initialized');
    console.log('📊 Authentic Data Loaded:');
    console.log('  • Industries:', SurfeApp.data.industries.length);
    console.log('  • Seniorities:', SurfeApp.data.seniorities.length);
    console.log('  • Departments:', SurfeApp.data.departments.length);
    console.log('  • Countries:', SurfeApp.data.countries.length);

    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Set up global error handler
    window.addEventListener('unhandledrejection', function (event) {
        console.error('Unhandled promise rejection:', event.reason);
        SurfeApp.ui.showToast('An unexpected error occurred', 'error');
    });


    // =================================================================
    //  NEW CODE BLOCK TO ADD
    // =================================================================
    // Connect the global health indicator to the state manager
    if (window.appState && document.getElementById('health-indicator')) {
        // 1. Subscribe to any future state changes
        window.appState.subscribe(SurfeApp.ui.updateHealthIndicator);

        // 2. Fetch the initial state when the page first loads
        // FIXED: Corrected the endpoint path
        SurfeApp.api.request('GET', '/settings/config', null, {
            headers: { 'X-User-ID': localStorage.getItem('userId') || 'default-user-id' }
        })
        .then(data => {
            if (data.success && data.data.api_manager) {
                // Update the central state, which will automatically update the indicator
                window.appState.updateStatus(data.data.api_manager);
            }
        })
        .catch(err => {
            console.error("Failed to load initial health status:", err);
            // If the initial fetch fails, show an error in the indicator
            const indicator = document.getElementById('health-indicator');
            if(indicator) {
                indicator.innerHTML = `
                    <div class="status-badge status-disabled">
                        <i class="fas fa-times-circle me-1"></i>Error
                    </div>`;
            }
        });
    }
    // =================================================================
    //  END OF NEW CODE BLOCK
    // =================================================================
});

// Clean up on page unload and visibility change
window.addEventListener('beforeunload', function () {
    SurfeApp.autoRefresh.stopAll();
});

// Stop auto-refresh when tab becomes hidden to save resources
document.addEventListener('visibilitychange', function () {
    if (document.hidden) {
        SurfeApp.autoRefresh.stopAll();
        console.log('⏸️ Page hidden - stopped all auto-refresh');
    }
    // Note: Auto-refresh is disabled by default and won't restart automatically
});

// Export for use in other scripts
window.SurfeApp = SurfeApp;
