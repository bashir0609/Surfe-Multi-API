/**
 * =====================================================================
 * Company Enrichment Module - Fixed Implementation
 * Features: Manual entry, CSV upload, bulk processing, results display
 * =====================================================================
 */
(function() {
    'use strict';

    let currentInputMethod = 'manual';
    let enrichmentResults = [];

    /**
     * =====================================================================
     * Initialize Company Enrichment
     * =====================================================================
     */
    function initializeCompanyEnrichment() {
        console.log('🚀 Initializing Company Enrichment module');
        
        // Check if SurfeApp is available
        if (typeof SurfeApp === 'undefined') {
            console.error('❌ SurfeApp not found! Please ensure shared.js is loaded first.');
            return;
        }

        setupInputMethodSwitching();
        setupEventListeners();
        setupFormValidation();
        addCustomStyles();
        
        // Initialize with manual input active
        switchInputMethod('manual');
        
        console.log('✅ Company Enrichment module initialized');
    }

    /**
     * =====================================================================
     * Custom Styles
     * =====================================================================
     */
    function addCustomStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .input-method-card {
                border: 2px solid #e9ecef;
                border-radius: 10px;
                padding: 1.5rem;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s ease;
                margin-bottom: 1rem;
                position: relative;
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

            .method-icon {
                font-size: 2rem;
                color: #007bff;
                margin-bottom: 1rem;
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

            .company-card {
                border: none;
                border-radius: 15px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
                transition: all 0.3s ease;
                margin-bottom: 1.5rem;
                overflow: hidden;
                background: white;
            }

            .company-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
            }

            .empty-state {
                text-align: center;
                padding: 4rem 2rem;
                color: #6c757d;
            }

            .empty-icon {
                font-size: 5rem;
                color: #dee2e6;
                margin-bottom: 1.5rem;
                animation: pulse 2s infinite;
            }

            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }

            .metric-item {
                padding: 0.5rem;
                border-radius: 8px;
                background: #f8f9fa;
                margin-bottom: 0.5rem;
            }

            .metric-value {
                font-size: 1.25rem;
                font-weight: 600;
                color: #495057;
            }

            .metric-label {
                font-size: 0.75rem;
                color: #6c757d;
                text-transform: uppercase;
                font-weight: 500;
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * =====================================================================
     * Input Method Switching
     * =====================================================================
     */
    function setupInputMethodSwitching() {
        const methodCards = document.querySelectorAll('.input-method-card');

        methodCards.forEach(card => {
            card.addEventListener('click', function() {
                const method = this.dataset.method;
                switchInputMethod(method);
            });
            
            card.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    const method = this.dataset.method;
                    switchInputMethod(method);
                }
            });
            
            card.setAttribute('tabindex', '0');
            card.style.cursor = 'pointer';
        });
    }

    function switchInputMethod(method) {
        currentInputMethod = method;
        
        // Update active card
        document.querySelectorAll('.input-method-card').forEach(card => {
            card.classList.remove('active');
        });
        const activeCard = document.querySelector(`[data-method="${method}"]`);
        if (activeCard) {
            activeCard.classList.add('active');
        }
        
        // Show corresponding input section
        document.querySelectorAll('.input-section').forEach(section => {
            section.classList.remove('active');
            section.style.display = 'none';
        });
        const activeSection = document.getElementById(`${method}-input`);
        if (activeSection) {
            activeSection.classList.add('active');
            activeSection.style.display = 'block';
        }
        
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

        // CSV file input change handler
        const csvFileInput = document.getElementById('csv-file');
        if (csvFileInput) {
            csvFileInput.addEventListener('change', handleCsvFileChange);
        }

        // Domain column selection change
        const domainSelect = document.getElementById('domain-column-select');
        if (domainSelect) {
            domainSelect.addEventListener('change', updateUniqueDomainCount);
        }

        // Reset buttons
        document.querySelectorAll('#reset-form').forEach(btn => {
            btn.addEventListener('click', resetCurrentForm);
        });
    }

    /**
     * =====================================================================
     * Form Validation
     * =====================================================================
     */
    function setupFormValidation() {
        // Domain validation
        const domainInputs = document.querySelectorAll('input[name="domain"]');
        domainInputs.forEach(input => {
            input.addEventListener('blur', validateDomainField);
        });
    }

    function validateDomainField(event) {
        const input = event.target;
        const domain = input.value.trim();
        
        if (domain && !SurfeApp.utils.isValidDomain(domain)) {
            showFieldError(input, 'Please enter a valid domain (e.g., company.com)');
        } else {
            clearFieldError(input);
        }
    }

    function showFieldError(input, message) {
        clearFieldError(input);
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback d-block';
        errorDiv.textContent = message;
        
        input.classList.add('is-invalid');
        input.parentNode.appendChild(errorDiv);
    }

    function clearFieldError(input) {
        input.classList.remove('is-invalid');
        const errorDiv = input.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    /**
     * =====================================================================
     * Enrichment Handlers
     * =====================================================================
     */
    async function handleManualEnrichment(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        
        // Validate required fields
        const rawDomain = formData.get('domain') || '';
        const cleanedDomain = SurfeApp.utils.cleanDomain(rawDomain);
        
        if (!cleanedDomain || !SurfeApp.utils.isValidDomain(cleanedDomain)) {
            SurfeApp.ui.showToast('Please provide a valid domain (e.g., acme.com)', 'error');
            return;
        }
        
        const company = { domain: cleanedDomain };
        
        // Add optional externalID if provided
        const externalId = formData.get('external-id');
        if (externalId && externalId.trim()) {
            company.externalID = externalId.trim();
        }
        
        const enrichmentData = { companies: [company] };

        await performEnrichment(enrichmentData, 'manual');
    }

    /**
     * =====================================================================
     * CSV Upload Handlers - Single Button Implementation
     * =====================================================================
     */
    async function handleCsvUpload(event) {
        event.preventDefault();
        console.log('🎯 CSV upload form submitted');
        
        const fileInput = document.getElementById('csv-file');
        const file = fileInput.files[0];
        const button = document.getElementById('csv-action-btn');
        
        console.log('📁 File input:', fileInput);
        console.log('📄 Selected file:', file);
        console.log('🔘 Button:', button);
        console.log('📝 Button text:', button ? button.textContent : 'N/A');
        
        // Check if we're in "analyze" mode or "enrich" mode
        if (button && button.textContent.includes('Upload and Analyze')) {
            console.log('🔄 Mode: ANALYZE - Processing CSV file');
            // Analyze mode - process the CSV file
            if (!file) {
                console.error('❌ No file selected');
                SurfeApp.ui.showToast('Please select a CSV file', 'error');
                return;
            }
            await processCsvFile(file);
        } else {
            console.log('🚀 Mode: ENRICH - Processing selected domains');
            // Enrich mode - process the selected domains
            await handleCsvEnrichment();
        }
    }

    async function handleCsvFileChange(event) {
        const file = event.target.files[0];
        if (file) {
            // Reset button to analyze mode when new file is selected
            resetCsvButton();
            // Don't auto-process, wait for user to click button
        } else {
            resetCsvButton();
            hideCsvControls();
        }
    }

    async function processCsvFile(file) {
        try {
            console.log('🔄 Processing CSV file:', file.name);
            
            // Validate file first
            const validation = SurfeApp.utils.validateCSVFile(file, config.maxFileSize);
            if (!validation.valid) {
                console.error('❌ CSV validation failed:', validation.errors);
                SurfeApp.ui.showToast(validation.errors.join(', '), 'error');
                return;
            }

            // Show loading state
            showLoading('Analyzing CSV file...');

            // Parse CSV
            const parsedRows = await SurfeApp.utils.readCSVFile(file);
            console.log('📊 CSV parsed successfully:', parsedRows.length, 'rows');
            console.log('📋 Sample row:', parsedRows[0]);
            
            if (!parsedRows.length) {
                console.error('❌ CSV is empty');
                SurfeApp.ui.showToast('CSV is empty or invalid', 'error');
                showEmpty('CSV file is empty. Please upload a valid CSV file with company data.');
                return;
            }

            // Store parsed data globally
            window.companyCsvRows = parsedRows;
            console.log('💾 Stored CSV data globally');
            
            // Get column headers
            const headers = Object.keys(parsedRows[0]);
            console.log('📋 CSV Headers:', headers);
            
            // Populate dropdown with column options
            populateColumnDropdown(parsedRows);
            console.log('🔧 Populated column dropdown');
            
            // Show UI elements
            showCsvControls();
            console.log('👁️ Showing CSV controls');
            
            // Update domain count for initial state
            updateUniqueDomainCount();
            console.log('🔢 Updated domain count');
            
            // Clear loading state
            clearResults();
            
            SurfeApp.ui.showToast('CSV file processed successfully', 'success');
            console.log('✅ CSV processing complete');
            
        } catch (error) {
            console.error('❌ Error parsing CSV:', error);
            SurfeApp.ui.showToast('Error parsing CSV file: ' + error.message, 'error');
            showError('Error parsing CSV file. Please check the file format and try again.');
        }
    }

    function populateColumnDropdown(parsedRows) {
        console.log('🔧 Populating column dropdown...');
        
        const columns = Object.keys(parsedRows[0]);
        const select = document.getElementById('domain-column-select');
        
        if (!select) {
            console.error('❌ Domain column select element not found');
            return;
        }
        
        console.log('📋 Available columns:', columns);
        
        // Clear existing options
        select.innerHTML = '<option value="">Select domain column</option>';
        
        // Add column options
        columns.forEach(col => {
            const option = document.createElement('option');
            option.value = col;
            option.textContent = col;
            select.appendChild(option);
            console.log('➕ Added column option:', col);
        });

        // Auto-select if there's a column that looks like a domain
        const domainLikeColumns = columns.filter(col => {
            const lower = col.toLowerCase();
            return lower.includes('domain') || 
                   lower.includes('website') ||
                   lower.includes('url') ||
                   lower.includes('company') ||
                   lower === 'domain' ||
                   lower === 'website' ||
                   lower === 'url';
        });
        
        console.log('🎯 Domain-like columns found:', domainLikeColumns);
        
        if (domainLikeColumns.length > 0) {
            select.value = domainLikeColumns[0];
            console.log('✅ Auto-selected column:', domainLikeColumns[0]);
            updateUniqueDomainCount();
        } else {
            console.log('⚠️ No domain-like columns found, user must select manually');
        }
    }

    function showCsvControls() {
        console.log('👁️ Showing CSV controls...');
        
        const domainSection = document.getElementById('domain-selection-section');
        const select = document.getElementById('domain-column-select');
        const countSpan = document.getElementById('unique-domain-count');
        const button = document.getElementById('csv-action-btn');
        
        if (domainSection) {
            domainSection.style.display = 'block';
            console.log('✅ Domain selection section shown');
        } else {
            console.error('❌ Domain selection section not found');
        }
        
        if (select) {
            console.log('✅ Domain select dropdown available');
        } else {
            console.error('❌ Domain select dropdown not found');
        }
        
        // Change button to enrich mode
        if (button) {
            updateCsvButton('enrich');
            console.log('✅ Button updated to enrich mode');
        } else {
            console.error('❌ CSV action button not found');
        }
    }

    function hideCsvControls() {
        const domainSection = document.getElementById('domain-selection-section');
        const button = document.getElementById('csv-action-btn');
        
        if (domainSection) {
            domainSection.style.display = 'none';
        }
        
        // Reset button to upload mode
        if (button) {
            updateCsvButton('upload');
        }
    }

    function updateCsvButton(mode) {
        const button = document.getElementById('csv-action-btn');
        const icon = button.querySelector('i');
        
        if (mode === 'enrich') {
            button.className = 'btn btn-success';
            button.innerHTML = '<i class="fas fa-magic me-2"></i><span class="badge bg-light text-dark me-2">Step 3</span>Enrich Selected Domains';
        } else {
            button.className = 'btn btn-primary';
            button.innerHTML = '<i class="fas fa-upload me-2"></i><span class="badge bg-light text-dark me-2">Step 1</span>Upload and Analyze CSV';
        }
    }

    function resetCsvButton() {
        updateCsvButton('upload');
        hideCsvControls();
    }

    function updateUniqueDomainCount() {
        const select = document.getElementById('domain-column-select');
        const countSpan = document.getElementById('unique-domain-count');
        const parsedRows = window.companyCsvRows;
        
        if (!select || !countSpan || !parsedRows) {
            if (countSpan) {
                countSpan.textContent = '';
            }
            return;
        }
        
        const selectedColumn = select.value;
        
        if (!selectedColumn) {
            countSpan.textContent = '';
            return;
        }
        
        // Clean, validate, and deduplicate domains
        const validDomains = [];
        let invalidCount = 0;
        
        parsedRows.forEach((row) => {
            const rawDomain = row[selectedColumn];
            
            if (!rawDomain || !rawDomain.trim()) {
                return;
            }
            
            const cleanedDomain = SurfeApp.utils.cleanDomain(rawDomain.trim());
            
            if (!cleanedDomain || !SurfeApp.utils.isValidDomain(cleanedDomain)) {
                invalidCount++;
                return;
            }
            
            if (cleanedDomain.length > 3 && cleanedDomain.includes('.') && !cleanedDomain.includes(' ')) {
                validDomains.push(cleanedDomain);
            } else {
                invalidCount++;
            }
        });
        
        const uniqueDomains = Array.from(new Set(validDomains));
        
        // Add batch warning if needed
        const batchWarning = uniqueDomains.length > config.maxBatchSize ? 
            ` (will be processed in ${Math.ceil(uniqueDomains.length / config.maxBatchSize)} batches)` : '';
        
        const qualityWarning = invalidCount > 0 ? ` - ${invalidCount} invalid domains will be skipped` : '';
        
        countSpan.textContent = `${uniqueDomains.length} unique valid domains${batchWarning}${qualityWarning}`;
        
        // Add warning styling based on quality
        if (invalidCount > validDomains.length * 0.5) {
            countSpan.className = 'text-danger fw-bold';
        } else if (uniqueDomains.length > config.maxBatchSize || invalidCount > 0) {
            countSpan.className = 'text-warning fw-bold';
        } else {
            countSpan.className = 'text-primary fw-bold';
        }
    }

    async function handleCsvEnrichment() {
        console.log('🚀 Starting CSV enrichment...');
        
        const select = document.getElementById('domain-column-select');
        const parsedRows = window.companyCsvRows;
        
        if (!select || !parsedRows || !select.value) {
            console.error('❌ Missing requirements:', {
                select: !!select,
                parsedRows: !!parsedRows,
                selectedValue: select?.value
            });
            SurfeApp.ui.showToast('Please select a domain column first', 'error');
            return;
        }

        const selectedColumn = select.value;
        console.log('📋 Selected column:', selectedColumn);
        
        // Build companies array from CSV data
        const companies = [];
        const rejectedDomains = [];
        
        parsedRows.forEach((row, index) => {
            const rawDomain = row[selectedColumn];
            console.log(`Processing row ${index + 1}:`, rawDomain);
            
            if (rawDomain && rawDomain.trim()) {
                const cleanedDomain = SurfeApp.utils.cleanDomain(rawDomain.trim());
                console.log(`Cleaned domain:`, cleanedDomain);
                
                if (cleanedDomain && SurfeApp.utils.isValidDomain(cleanedDomain)) {
                    if (cleanedDomain.length > 3 && cleanedDomain.includes('.') && !cleanedDomain.includes(' ')) {
                        const company = { domain: cleanedDomain };
                        
                        // Add external ID if there's an ID column or use row index
                        if (row.id) {
                            company.externalID = row.id;
                        } else if (row.external_id) {
                            company.externalID = row.external_id;
                        } else {
                            company.externalID = `csv_row_${index + 1}`;
                        }
                        
                        companies.push(company);
                        console.log(`✅ Added company:`, company);
                    } else {
                        rejectedDomains.push({ original: rawDomain, cleaned: cleanedDomain, reason: 'Too short or malformed' });
                    }
                } else {
                    rejectedDomains.push({ original: rawDomain, cleaned: cleanedDomain, reason: 'Invalid domain format' });
                }
            } else {
                rejectedDomains.push({ original: rawDomain || 'empty', cleaned: null, reason: 'Empty or null value' });
            }
        });

        console.log(`📊 Processing results:
        - Total rows: ${parsedRows.length}
        - Valid companies: ${companies.length}
        - Rejected domains: ${rejectedDomains.length}`);
        
        if (rejectedDomains.length > 0) {
            console.log('❌ Rejected domains:', rejectedDomains);
        }

        if (companies.length === 0) {
            SurfeApp.ui.showToast(`No valid domains found in selected column. ${rejectedDomains.length} domains were rejected.`, 'error');
            return;
        }

        if (rejectedDomains.length > 0) {
            SurfeApp.ui.showToast(
                `Processing ${companies.length} valid domains (${rejectedDomains.length} domains were skipped due to formatting issues)`, 
                'warning'
            );
        }

        // Check if we need to batch process
        if (companies.length > config.maxBatchSize) {
            await performBatchEnrichment(companies, 'csv');
        } else {
            const enrichmentData = { companies };
            console.log('📤 Sending enrichment data:', enrichmentData);
            await performEnrichment(enrichmentData, 'csv');
        }
    }

    async function handleBulkEnrichment(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        
        // Parse bulk input
        const rawDomains = SurfeApp.utils.parseTextareaLines(formData.get('domains') || '');
        const externalIds = SurfeApp.utils.parseTextareaLines(formData.get('external_ids') || '');
        
        // Build companies array with cleaned domains
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
        
        // Validate bulk data
        if (companies.length === 0) {
            SurfeApp.ui.showToast('Please provide at least one valid company domain', 'error');
            return;
        }

        // Check if we need to batch process
        if (companies.length > config.maxBatchSize) {
            await performBatchEnrichment(companies, 'bulk');
        } else {
            const enrichmentData = { companies };
            await performEnrichment(enrichmentData, 'bulk');
        }
    }

    /**
     * =====================================================================
     * Enrichment Processing
     * =====================================================================
     */
    async function performEnrichment(data, method) {
        const resultsContainer = document.getElementById('enrichment-results');
        showLoading('Enriching company data...');

        try {
            const response = await SurfeApp.api.enrichCompanies(data);

            if (response.success && response.data && response.data.enrichmentID) {
                SurfeApp.ui.showToast('Enrichment job started successfully!', 'info');
                pollForResults(response.data.enrichmentID, method); 
            } else {
                throw new Error(response.error || 'Failed to start enrichment job.');
            }
        } catch (error) {
            console.error('Enrichment error:', error);
            showError(`Enrichment failed: ${error.message}`);
            SurfeApp.ui.showToast('Enrichment failed', 'error');
        }
    }

    async function checkStatus(enrichmentId) {
        const status = await SurfeApp.api.getCompanyEnrichmentStatus(enrichmentId);  // ← Use centralized API
        return status;
    }

    async function performBatchEnrichment(companies, method) {
        const totalCompanies = companies.length;
        const batches = [];
        
        // Split companies into batches
        for (let i = 0; i < companies.length; i += config.maxBatchSize) {
            batches.push(companies.slice(i, i + config.maxBatchSize));
        }

        showLoading(`Processing ${totalCompanies} companies in ${batches.length} batches...`);

        const allEnrichmentIDs = [];

        try {
            // Process batches sequentially
            for (let i = 0; i < batches.length; i++) {
                const batch = batches[i];
                const batchData = { companies: batch };
                
                showLoading(`Processing batch ${i + 1} of ${batches.length} (${batch.length} companies)...`);

                const response = await SurfeApp.api.enrichCompanies(data);

                if (response.success && response.data && response.data.enrichmentID) {
                    allEnrichmentIDs.push({
                        id: response.data.enrichmentID,
                        batchIndex: i + 1,
                        companiesCount: batch.length
                    });
                    console.log(`Batch ${i + 1} started successfully with ID: ${response.data.enrichmentID}`);
                } else {
                    console.error(`Batch ${i + 1} failed:`, response.error);
                    SurfeApp.ui.showToast(`Batch ${i + 1} failed: ${response.error}`, 'warning');
                }

                // Delay between batches to avoid rate limiting
                if (i < batches.length - 1) {
                    const delay = Math.min(3000 + (i * 1000), 10000);
                    showLoading(`Waiting ${delay/1000}s before next batch to avoid rate limits...`);
                    await new Promise(resolve => setTimeout(resolve, delay));
                }
            }

            if (allEnrichmentIDs.length === 0) {
                throw new Error('All batches failed to start');
            }

            SurfeApp.ui.showToast(`${allEnrichmentIDs.length} batch jobs started successfully!`, 'info');
            pollForBatchResults(allEnrichmentIDs, method, totalCompanies);

        } catch (error) {
            console.error('Batch enrichment error:', error);
            showError(`Batch enrichment failed: ${error.message}`);
            SurfeApp.ui.showToast('Batch enrichment failed', 'error');
        }
    }

    function pollForBatchResults(enrichmentJobs, method, totalCompanies) {
        const allResults = [];
        const completedJobs = new Set();
        let attempts = 0;
        const maxAttempts = 40;
        const interval = 5000;

        showLoading(`Monitoring ${enrichmentJobs.length} batch jobs... This may take several minutes.`);

        const intervalId = setInterval(async () => {
            if (attempts >= maxAttempts) {
                clearInterval(intervalId);
                
                if (allResults.length > 0) {
                    enrichmentResults = allResults;
                    displayEnrichmentResults(enrichmentResults, method);
                    SurfeApp.ui.showToast(
                        `Partial results: ${allResults.length} of ${totalCompanies} companies processed (some batches timed out)`, 
                        'warning'
                    );
                } else {
                    showError('All batch enrichment requests timed out.');
                }
                return;
            }

            try {
                const pendingJobs = enrichmentJobs.filter(job => !completedJobs.has(job.id));
                
                for (const job of pendingJobs) {
                    try {
                        // Use correct Surfe API endpoint pattern
                        const status = await SurfeApp.api.getCompanyEnrichmentStatus(enrichmentId);
                        
                        if (statusResponse.success && statusResponse.status === 'completed') {
                            completedJobs.add(job.id);
                            const batchResults = statusResponse.data || [];
                            
                            allResults.push(...batchResults);
                            
                            showLoading(
                                `Completed batch ${job.batchIndex} (${batchResults.length} companies). Total: ${completedJobs.size}/${enrichmentJobs.length} batches done...`
                            );
                        } else if (statusResponse.status === 'failed') {
                            console.error(`Batch ${job.batchIndex} failed:`, statusResponse);
                            completedJobs.add(job.id);
                            SurfeApp.ui.showToast(`Batch ${job.batchIndex} failed`, 'warning');
                        }
                        
                        await new Promise(resolve => setTimeout(resolve, 200));
                        
                    } catch (jobError) {
                        console.error(`Error checking batch ${job.batchIndex}:`, jobError);
                    }
                }

                // Check if all batches are complete
                if (completedJobs.size === enrichmentJobs.length) {
                    clearInterval(intervalId);
                    enrichmentResults = allResults;
                    
                    const successfulResults = allResults.filter(company => 
                        company && company.name && company.name !== 'Unknown Company'
                    );
                    
                    displayEnrichmentResults(enrichmentResults, method);
                    
                    SurfeApp.ui.showToast(
                        `Batch enrichment complete! ${successfulResults.length} successful, ${allResults.length - successfulResults.length} failed out of ${totalCompanies} total.`, 
                        successfulResults.length > 0 ? 'success' : 'warning'
                    );
                }

            } catch (error) {
                console.error('Error checking batch status:', error);
            }
            
            attempts++;
        }, interval);
    }

    function pollForResults(enrichmentID, method) {
        showLoading('Processing enrichment... This may take a moment.');

        let attempts = 0;
        const maxAttempts = 15;
        const interval = 2000;

        const intervalId = setInterval(async () => {
            if (attempts >= maxAttempts) {
                clearInterval(intervalId);
                showError('Enrichment request timed out.');
                return;
            }

            try {
                // Use the correct Surfe API status endpoint pattern
                const statusEndpoint = `/api/v2/companies/enrich/status/${enrichmentID}`;
                console.log(`🔍 Checking enrichment status: ${statusEndpoint}`);
                
                const statusResponse = await SurfeApp.api.request('GET', statusEndpoint);
                console.log(`📊 Status response:`, statusResponse);
                
                if (statusResponse.success && statusResponse.status === 'completed') {
                    clearInterval(intervalId);
                    enrichmentResults = statusResponse.data || []; 
                    console.log(`✅ Enrichment completed with ${enrichmentResults.length} results`);
                    displayEnrichmentResults(enrichmentResults, method);
                    SurfeApp.ui.showToast('Enrichment complete!', 'success');
                } else if (statusResponse.success && (statusResponse.status === 'pending' || statusResponse.status === 'processing' || statusResponse.status === 'in_progress')) {
                    console.log(`⏳ Enrichment still processing... (${attempts + 1}/${maxAttempts}) - Status: ${statusResponse.status}`);
                } else if (statusResponse.status === 'failed') {
                    clearInterval(intervalId);
                    showError('Enrichment failed. Please try again.');
                } else {
                    console.log('📊 Unexpected status response:', statusResponse);
                }
            } catch (error) {
                console.error('❌ Status check error:', error);
                
                // If it's the last attempt, show error
                if (attempts >= maxAttempts - 1) {
                    clearInterval(intervalId);
                    showError(`Error fetching results: ${error.message}. The enrichment may still be processing in the background.`);
                }
            }
            attempts++;
        }, interval);
    }

    /**
     * =====================================================================
     * Results Display
     * =====================================================================
     */
    function displayEnrichmentResults(results, method) {
        const resultsContainer = document.getElementById('enrichment-results');
        
        if (!results || results.length === 0) {
            showEmpty('No enrichment results found');
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
        const name = company.name || 'Unknown Company';
        const description = company.description || '';
        const industry = company.industry || 'N/A';
        const subIndustry = company.subIndustry || '';
        const location = company.hqAddress || 'N/A';
        const hqCountry = company.hqCountry || 'N/A';
        const linkedIn = company.linkedInURL || '';
        const employeeCount = company.employeeCount || 0;
        const founded = company.founded || 'N/A';

        const website = (company.websites && company.websites.length > 0) ? company.websites[0] : company.domain || '';
        const phones = (company.phones && company.phones.length > 0) ? company.phones.join(' / ') : '';
        const keywords = (company.keywords && company.keywords.length > 0) ? company.keywords.slice(0, 5).join(', ') : '';

        const isFailedEnrichment = !company.name || company.name === 'Unknown Company';

        return `
            <div class="company-card card mb-3 ${isFailedEnrichment ? 'border-warning' : ''}">
                <div class="card-body">
                    <div class="d-flex align-items-start">
                        <div class="company-logo me-3">
                            <i class="fas fa-building fa-2x ${isFailedEnrichment ? 'text-warning' : 'text-primary'}"></i>
                        </div>
                        <div class="flex-grow-1">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <div>
                                    <h6 class="company-name mb-1">${SurfeApp.utils.sanitizeHtml(name)}</h6>
                                    ${company.domain ? `<small class="text-muted">Domain: ${company.domain}</small>` : ''}
                                    <p class="company-industry text-muted mb-1">${industry}${subIndustry ? ` - ${subIndustry}` : ''}</p>
                                    <p class="company-location small text-primary mb-0">
                                        <i class="fas fa-map-marker-alt me-1"></i>${location}${hqCountry !== 'N/A' ? `, ${hqCountry}` : ''}
                                    </p>
                                </div>
                                <div class="company-actions">
                                    ${website ? `<a href="https://${website}" target="_blank" class="btn btn-outline-primary btn-sm me-1" title="Visit Website"><i class="fas fa-external-link-alt"></i></a>` : ''}
                                    ${linkedIn ? `<a href="${linkedIn}" target="_blank" class="btn btn-outline-info btn-sm" title="View LinkedIn"><i class="fab fa-linkedin"></i></a>` : ''}
                                </div>
                            </div>

                            <div class="company-metrics mb-3">
                                <div class="row text-center">
                                    <div class="col-6 col-md-4">
                                        <div class="metric-item">
                                            <div class="metric-value">${employeeCount}</div>
                                            <div class="metric-label">Employees</div>
                                        </div>
                                    </div>
                                    <div class="col-6 col-md-4">
                                        <div class="metric-item">
                                            <div class="metric-value">${founded}</div>
                                            <div class="metric-label">Founded</div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            ${description ? `<p class="small text-muted border-top pt-2 mt-2">${SurfeApp.utils.truncateText ? SurfeApp.utils.truncateText(description, 150) : description}</p>` : ''}

                            <div class="company-details mt-3">
                                ${phones ? `<small class="d-block text-muted"><strong><i class="fas fa-phone me-2"></i>Phones:</strong> ${phones}</small>` : ''}
                                ${keywords ? `<small class="d-block text-muted mt-2"><strong><i class="fas fa-tags me-2"></i>Keywords:</strong> ${keywords}</small>` : ''}
                            </div>
                            
                            ${isFailedEnrichment ? `
                                <div class="alert alert-warning mt-2">
                                    <small><strong>Debug:</strong> ${company.domain || 'No domain'} - Enrichment may have failed or returned no data</small>
                                </div>
                            ` : ''}
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
    function resetCurrentForm() {
        const activeSection = document.querySelector('.input-section.active');
        if (activeSection) {
            const form = activeSection.querySelector('form');
            if (form) {
                form.reset();
                
                // Clear validation errors
                form.querySelectorAll('.is-invalid').forEach(input => {
                    clearFieldError(input);
                });
            }
        }
        clearResults();
        
        // Reset CSV controls
        resetCsvButton();
        
        // Clear stored CSV data
        window.companyCsvRows = null;
    }

    function clearResults() {
        enrichmentResults = [];
        showEmpty('Choose an input method above and provide company data to enrich with comprehensive business information.');
    }

    function showLoading(message) {
        const resultsContainer = document.getElementById('enrichment-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div class="text-center py-5">
                    <div class="spinner-border text-primary mb-3" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="text-muted">${message}</p>
                </div>
            `;
        }
    }

    function showError(message) {
        const resultsContainer = document.getElementById('enrichment-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    <h6><i class="fas fa-exclamation-triangle me-2"></i>Error</h6>
                    <p class="mb-0">${message}</p>
                </div>
            `;
        }
    }

    function showEmpty(message) {
        const resultsContainer = document.getElementById('enrichment-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">
                        <i class="fas fa-building-user"></i>
                    </div>
                    <h5 class="mb-3">Ready for Enrichment</h5>
                    <p class="mb-0">${message}</p>
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
            SurfeApp.utils.exportToCsv(enrichmentResults, filename, 'company_enrichment');
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

    /**
     * =====================================================================
     * Debug Functions (Global)
     * =====================================================================
     */
    window.debugCsvProcessing = function() {
        console.log('🔍 Debug: Checking CSV processing elements...');
        
        const fileInput = document.getElementById('csv-file');
        const domainSection = document.getElementById('domain-selection-section');
        const select = document.getElementById('domain-column-select');
        const button = document.getElementById('csv-action-btn');
        const countSpan = document.getElementById('unique-domain-count');
        
        console.log('📁 File Input:', fileInput);
        console.log('📋 Domain Selection Section:', domainSection);
        console.log('🔽 Domain Select:', select);
        console.log('🔘 CSV Button:', button);
        console.log('📊 Count Span:', countSpan);
        
        if (window.companyCsvRows) {
            console.log('💾 Stored CSV Data:', window.companyCsvRows.length, 'rows');
            console.log('📋 Sample row:', window.companyCsvRows[0]);
            console.log('🏷️ Headers:', Object.keys(window.companyCsvRows[0]));
        } else {
            console.log('❌ No CSV data stored');
        }
    };

    // Test function to simulate CSV processing
    window.testCsvProcessing = function() {
        console.log('🧪 Testing CSV processing with sample data...');
        
        const sampleData = [
            { domain: 'google.com', name: 'Google Inc', external_id: 'company_1' },
            { domain: 'microsoft.com', name: 'Microsoft Corp', external_id: 'company_2' },
            { domain: 'apple.com', name: 'Apple Inc', external_id: 'company_3' }
        ];
        
        window.companyCsvRows = sampleData;
        populateColumnDropdown(sampleData);
        showCsvControls();
        updateUniqueDomainCount();
        
        console.log('✅ Test completed - check if domain selection appeared');
    };

    // Make handleCsvEnrichment accessible globally for debugging
    window.handleCsvEnrichment = handleCsvEnrichment;
    window.testEnrichment = async function() {
        console.log('🧪 Testing enrichment with current CSV data...');
        await handleCsvEnrichment();
    };
    // Check if the script executed and the functions are available
    console.log('Company enrichment debug functions:');
    console.log('debugCsvProcessing:', typeof window.debugCsvProcessing);
    console.log('testCsvProcessing:', typeof window.testCsvProcessing);
    console.log('handleCsvEnrichment:', typeof window.handleCsvEnrichment);
    console.log('testEnrichment:', typeof window.testEnrichment);

    // Run the debug function to see current state
    if (window.debugCsvProcessing) {
        console.log('Running debug...');
        debugCsvProcessing();
    } else {
        console.log('❌ Debug function not found - script may not have loaded');
    }

})();