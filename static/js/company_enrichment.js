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
        maxBatchSize: 500, // API limit for companies per request
        endpoints: {
            enrich: '/v2/companies/enrich',
            enrichBulk: '/v2/companies/enrich/bulk'
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

        // CSV upload form - using the new consolidated handler
        const csvForm = document.getElementById('csv-upload-form');
        if (csvForm) {
            csvForm.addEventListener('submit', handleCsvUpload);
        }

        // Bulk enrichment form
        const bulkForm = document.getElementById('bulk-enrichment-form');
        if (bulkForm) {
            bulkForm.addEventListener('submit', handleBulkEnrichment);
        }

        // CSV file input change handler for immediate feedback
        const csvFileInput = document.getElementById('csv-file');
        if (csvFileInput) {
            csvFileInput.addEventListener('change', handleCsvFileChange);
        }

        // Domain column selection change
        const domainSelect = document.getElementById('domain-column-select');
        if (domainSelect) {
            domainSelect.addEventListener('change', updateUniqueDomainCount);
        }

        // CSV enrichment button
        const enrichCsvBtn = document.getElementById('enrich-csv-btn');
        if (enrichCsvBtn) {
            enrichCsvBtn.addEventListener('click', handleCsvEnrichment);
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

    /**
     * =====================================================================
     * CSV Upload Handlers - Consolidated Implementation
     * =====================================================================
     */
    async function handleCsvUpload(event) {
        event.preventDefault();
        
        const fileInput = document.getElementById('csv-file');
        const file = fileInput.files[0];
        
        if (!file) {
            SurfeApp.ui.showToast('Please select a CSV file', 'error');
            return;
        }

        await processCsvFile(file);
    }

    async function handleCsvFileChange(event) {
        const file = event.target.files[0];
        if (file) {
            await processCsvFile(file);
        }
    }

    async function processCsvFile(file) {
        try {
            // Validate file first
            const validation = SurfeApp.utils.validateCSVFile(file, config.maxFileSize);
            if (!validation.valid) {
                SurfeApp.ui.showToast(validation.errors.join(', '), 'error');
                return;
            }

            // Parse CSV in browser using shared.js utility
            const parsedRows = await SurfeApp.utils.readCSVFile(file);
            
            if (!parsedRows.length) {
                SurfeApp.ui.showToast('CSV is empty or invalid', 'error');
                return;
            }

            // Store parsed data globally
            window.companyCsvRows = parsedRows;
            
            // Populate dropdown with column options
            populateColumnDropdown(parsedRows);
            
            // Show UI elements
            showCsvControls();
            
            // Update domain count for initial state
            updateUniqueDomainCount();
            
            SurfeApp.ui.showToast('CSV file processed successfully', 'success');
            
        } catch (error) {
            console.error('Error parsing CSV:', error);
            SurfeApp.ui.showToast('Error parsing CSV file', 'error');
        }
    }

    function populateColumnDropdown(parsedRows) {
        const columns = Object.keys(parsedRows[0]);
        const select = document.getElementById('domain-column-select');
        
        if (!select) return;
        
        // Clear existing options
        select.innerHTML = '<option value="">Select domain column</option>';
        
        // Add column options
        columns.forEach(col => {
            const option = document.createElement('option');
            option.value = col;
            option.textContent = col;
            select.appendChild(option);
        });

        // Auto-select if there's a column that looks like a domain
        const domainLikeColumns = columns.filter(col => 
            col.toLowerCase().includes('domain') || 
            col.toLowerCase().includes('website') ||
            col.toLowerCase().includes('url')
        );
        
        if (domainLikeColumns.length > 0) {
            select.value = domainLikeColumns[0];
            updateUniqueDomainCount();
        }
    }

    function showCsvControls() {
        const select = document.getElementById('domain-column-select');
        const enrichBtn = document.getElementById('enrich-csv-btn');
        const countSpan = document.getElementById('unique-domain-count');
        
        if (select) select.style.display = 'block';
        if (enrichBtn) enrichBtn.style.display = 'block';
        if (countSpan) countSpan.style.display = 'inline-block';
    }

    function updateUniqueDomainCount() {
        const select = document.getElementById('domain-column-select');
        const countSpan = document.getElementById('unique-domain-count');
        const parsedRows = window.companyCsvRows;
        
        // Validate required elements exist
        if (!select || !countSpan || !parsedRows) {
            if (countSpan) {
                countSpan.textContent = '';
                countSpan.style.display = 'none';
            }
            return;
        }
        
        const selectedColumn = select.value;
        
        if (!selectedColumn) {
            countSpan.textContent = '';
            countSpan.style.display = 'none';
            return;
        }
        
        // Clean, validate, and deduplicate domains with detailed analysis
        const domainAnalysis = {
            total: 0,
            empty: 0,
            invalid: 0,
            valid: 0,
            samples: []
        };
        
        const validDomains = [];
        const invalidSamples = [];
        
        parsedRows.forEach((row, index) => {
            domainAnalysis.total++;
            const rawDomain = row[selectedColumn];
            
            if (!rawDomain || !rawDomain.trim()) {
                domainAnalysis.empty++;
                return;
            }
            
            const cleanedDomain = SurfeApp.utils.cleanDomain(rawDomain.trim());
            
            if (!cleanedDomain || !SurfeApp.utils.isValidDomain(cleanedDomain)) {
                domainAnalysis.invalid++;
                if (invalidSamples.length < 5) {
                    invalidSamples.push({ row: index + 1, original: rawDomain, cleaned: cleanedDomain });
                }
                return;
            }
            
            // Additional quality checks
            if (cleanedDomain.length > 3 && cleanedDomain.includes('.') && !cleanedDomain.includes(' ')) {
                validDomains.push(cleanedDomain);
                domainAnalysis.valid++;
                if (domainAnalysis.samples.length < 5) {
                    domainAnalysis.samples.push(cleanedDomain);
                }
            } else {
                domainAnalysis.invalid++;
                if (invalidSamples.length < 5) {
                    invalidSamples.push({ row: index + 1, original: rawDomain, cleaned: cleanedDomain, reason: 'Quality check failed' });
                }
            }
        });
        
        const uniqueDomains = Array.from(new Set(validDomains));
        
        // Log detailed analysis
        console.log('Domain Analysis:', domainAnalysis);
        if (invalidSamples.length > 0) {
            console.log('Invalid domain samples:', invalidSamples);
        }
        
        // Add batch warning if needed
        const batchWarning = uniqueDomains.length > config.maxBatchSize ? 
            ` (will be processed in ${Math.ceil(uniqueDomains.length / config.maxBatchSize)} batches)` : '';
        
        const qualityWarning = domainAnalysis.invalid > 0 ? ` - ${domainAnalysis.invalid} invalid domains will be skipped` : '';
        
        countSpan.textContent = `${uniqueDomains.length} unique valid domains${batchWarning}${qualityWarning}`;
        countSpan.style.display = 'inline-block';
        
        // Add warning styling based on quality
        if (domainAnalysis.invalid > domainAnalysis.valid * 0.5) {
            countSpan.className = 'text-danger fw-bold';
        } else if (uniqueDomains.length > config.maxBatchSize || domainAnalysis.invalid > 0) {
            countSpan.className = 'text-warning fw-bold';
        } else {
            countSpan.className = 'text-primary fw-bold';
        }
    }

    async function handleCsvEnrichment() {
        const select = document.getElementById('domain-column-select');
        const parsedRows = window.companyCsvRows;
        
        if (!select || !parsedRows || !select.value) {
            SurfeApp.ui.showToast('Please select a domain column first', 'error');
            return;
        }

        const selectedColumn = select.value;
        
        // Build companies array from CSV data with enhanced validation
        const companies = [];
        const rejectedDomains = [];
        
        parsedRows.forEach((row, index) => {
            const rawDomain = row[selectedColumn];
            if (rawDomain && rawDomain.trim()) {
                const cleanedDomain = SurfeApp.utils.cleanDomain(rawDomain.trim());
                
                // Enhanced domain validation
                if (cleanedDomain && SurfeApp.utils.isValidDomain(cleanedDomain)) {
                    // Additional checks to ensure domain quality
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

        // Log domain processing results
        console.log(`Domain processing results:
        - Total rows: ${parsedRows.length}
        - Valid domains: ${companies.length}
        - Rejected domains: ${rejectedDomains.length}`);
        
        if (rejectedDomains.length > 0) {
            console.log('Sample rejected domains:', rejectedDomains.slice(0, 10));
        }
        
        if (companies.length > 0) {
            console.log('Sample valid domains:', companies.slice(0, 10));
        }

        if (companies.length === 0) {
            SurfeApp.ui.showToast(`No valid domains found in selected column. ${rejectedDomains.length} domains were rejected.`, 'error');
            console.error('All domains rejected:', rejectedDomains);
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
            await performEnrichment(enrichmentData, 'csv');
        }
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
        
        // Validate bulk data
        if (!validateBulkData({ companies })) {
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
        SurfeApp.ui.showLoading(resultsContainer, 'Enriching company data...');

        try {
            // Get selected key from localStorage
            const selectedKey = localStorage.getItem('surfe_selected_key');
            
            console.log('🔑 Company enrichment using selected key:', selectedKey || 'default');
            
            // Use SurfeApp.api.request instead of fetch
            const response = await SurfeApp.api.request(
                'POST',
                config.endpoints.enrich,
                data, { 
                    headers: {
                        'Content-Type': 'application/json', // Add this line
                        'X-Selected-Key': selectedKey || ''
                    }
                }
            );

            // Handle response
            if (response.success && response.data?.enrichmentID) {
                SurfeApp.ui.showToast('Enrichment job started successfully!', 'info');
                pollForResults(response.data.enrichmentID, method);
            } else {
                throw new Error(response.error || 'Failed to start enrichment job');
            }
        } catch (error) {
            console.error('Enrichment error:', error);
            SurfeApp.ui.showError(resultsContainer, `Enrichment failed: ${error.message}`);
            SurfeApp.ui.showToast('Enrichment failed', 'error');
        }
    }

    async function performBatchEnrichment(companies, method) {
        const resultsContainer = document.getElementById('enrichment-results');
        const totalCompanies = companies.length;
        const batches = [];
        
        // Split companies into batches
        for (let i = 0; i < companies.length; i += config.maxBatchSize) {
            batches.push(companies.slice(i, i + config.maxBatchSize));
        }

        SurfeApp.ui.showLoading(
            resultsContainer, 
            `Processing ${totalCompanies} companies in ${batches.length} batches...`
        );

        const allEnrichmentIDs = [];
        let completedBatches = 0;

        try {
            // Process batches sequentially with longer delays
            for (let i = 0; i < batches.length; i++) {
                const batch = batches[i];
                const batchData = { companies: batch };
                
                SurfeApp.ui.showLoading(
                    resultsContainer, 
                    `Processing batch ${i + 1} of ${batches.length} (${batch.length} companies)...`
                );

                // Log the batch data for debugging - show actual domains being sent
                console.log(`Batch ${i + 1} companies:`, batch.map(c => c.domain).slice(0, 5), '...');
                console.log(`Batch ${i + 1} full data sample:`, batch.slice(0, 2));

                const response = await SurfeApp.api.request(
                    'POST',
                    config.endpoints.enrich,
                    batchData, {
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    }
                );

                console.log(`Batch ${i + 1} response:`, response);

                if (response.success && response.data && response.data.enrichmentID) {
                    allEnrichmentIDs.push({
                        id: response.data.enrichmentID,
                        batchIndex: i + 1,
                        companiesCount: batch.length,
                        sampleDomains: batch.slice(0, 3).map(c => c.domain) // Keep sample for debugging
                    });
                    console.log(`Batch ${i + 1} started successfully with ID: ${response.data.enrichmentID}`);
                } else {
                    console.error(`Batch ${i + 1} failed:`, response.error);
                    SurfeApp.ui.showToast(`Batch ${i + 1} failed: ${response.error}`, 'warning');
                }

                // Longer delay between batches to avoid rate limiting
                if (i < batches.length - 1) {
                    const delay = Math.min(3000 + (i * 1000), 10000); // Increasing delay, max 10s
                    SurfeApp.ui.showLoading(
                        resultsContainer, 
                        `Waiting ${delay/1000}s before next batch to avoid rate limits...`
                    );
                    await new Promise(resolve => setTimeout(resolve, delay));
                }
            }

            if (allEnrichmentIDs.length === 0) {
                throw new Error('All batches failed to start');
            }

            SurfeApp.ui.showToast(
                `${allEnrichmentIDs.length} batch jobs started successfully!`, 
                'info'
            );

            // Poll for all batch results with better tracking
            pollForBatchResults(allEnrichmentIDs, method, totalCompanies);

        } catch (error) {
            console.error('Batch enrichment error:', error);
            SurfeApp.ui.showError(resultsContainer, `Batch enrichment failed: ${error.message}`);
            SurfeApp.ui.showToast('Batch enrichment failed', 'error');
        }
    }

    function pollForBatchResults(enrichmentJobs, method, totalCompanies) {
        const resultsContainer = document.getElementById('enrichment-results');
        const allResults = [];
        const completedJobs = new Set();
        let attempts = 0;
        const maxAttempts = 40; // Longer timeout for batch processing
        const interval = 5000; // 5 seconds - longer interval to avoid overwhelming API

        SurfeApp.ui.showLoading(
            resultsContainer, 
            `Monitoring ${enrichmentJobs.length} batch jobs... This may take several minutes.`
        );

        const intervalId = setInterval(async () => {
            if (attempts >= maxAttempts) {
                clearInterval(intervalId);
                
                // Show partial results if we have any
                if (allResults.length > 0) {
                    enrichmentResults = allResults;
                    displayEnrichmentResults(enrichmentResults, method);
                    SurfeApp.ui.showToast(
                        `Partial results: ${allResults.length} of ${totalCompanies} companies processed (some batches timed out)`, 
                        'warning'
                    );
                } else {
                    SurfeApp.ui.showError(resultsContainer, 'All batch enrichment requests timed out.');
                }
                return;
            }

            try {
                // Check status of all pending enrichment jobs
                const pendingJobs = enrichmentJobs.filter(job => !completedJobs.has(job.id));
                
                for (const job of pendingJobs) {
                    try {
                        const statusResponse = await SurfeApp.api.request(
                            'GET', 
                            `/v2/companies/enrich/status/${job.id}`
                        );
                        
                        console.log(`Batch ${job.batchIndex} status:`, statusResponse);
                        
                        if (statusResponse.success && statusResponse.status === 'completed') {
                            completedJobs.add(job.id);
                            const batchResults = statusResponse.data || [];
                            
                            // Log results for debugging
                            console.log(`Batch ${job.batchIndex} completed with ${batchResults.length} results:`, batchResults);
                            
                            // Filter out empty/invalid results
                            const validResults = batchResults.filter(company => 
                                company && (company.name !== 'Unknown Company' && company.name !== '' && company.name)
                            );
                            
                            console.log(`Batch ${job.batchIndex}: ${validResults.length} valid results out of ${batchResults.length} total`);
                            
                            allResults.push(...batchResults); // Include all results, even failed ones for debugging
                            
                            // Update progress
                            SurfeApp.ui.showLoading(
                                resultsContainer, 
                                `Completed batch ${job.batchIndex} (${batchResults.length} companies). Total: ${completedJobs.size}/${enrichmentJobs.length} batches done...`
                            );
                        } else if (statusResponse.status === 'failed') {
                            console.error(`Batch ${job.batchIndex} failed:`, statusResponse);
                            completedJobs.add(job.id); // Mark as completed to stop polling
                            SurfeApp.ui.showToast(`Batch ${job.batchIndex} failed`, 'warning');
                        }
                        
                        // Add small delay between status checks
                        await new Promise(resolve => setTimeout(resolve, 200));
                        
                    } catch (jobError) {
                        console.error(`Error checking batch ${job.batchIndex}:`, jobError);
                        // Don't mark as completed, let it retry
                    }
                }

                // Check if all batches are complete
                if (completedJobs.size === enrichmentJobs.length) {
                    clearInterval(intervalId);
                    enrichmentResults = allResults;
                    
                    // Count successful vs failed enrichments
                    const successfulResults = allResults.filter(company => 
                        company && company.name && company.name !== 'Unknown Company'
                    );
                    
                    displayEnrichmentResults(enrichmentResults, method);
                    
                    SurfeApp.ui.showToast(
                        `Batch enrichment complete! ${successfulResults.length} successful, ${allResults.length - successfulResults.length} failed out of ${totalCompanies} total.`, 
                        successfulResults.length > 0 ? 'success' : 'warning'
                    );
                    
                    console.log(`Final results: ${successfulResults.length} successful, ${allResults.length - successfulResults.length} failed`);
                }

            } catch (error) {
                console.error('Error checking batch status:', error);
                // Continue trying
            }
            
            attempts++;
        }, interval);
    }

    function pollForResults(enrichmentID, method) {
        const resultsContainer = document.getElementById('enrichment-results');
        SurfeApp.ui.showLoading(resultsContainer, 'Processing enrichment... This may take a moment.');

        let attempts = 0;
        const maxAttempts = 15;
        const interval = 2000;

        const intervalId = setInterval(async () => {
            if (attempts >= maxAttempts) {
                clearInterval(intervalId);
                SurfeApp.ui.showError(resultsContainer, 'Enrichment request timed out.');
                return;
            }

            try {
                const statusResponse = await SurfeApp.api.request('GET', `/v2/companies/enrich/status/${enrichmentID}`);
                
                // This is where we follow the backend's structure
                if (statusResponse.success && statusResponse.status === 'completed') {
                    clearInterval(intervalId);
                    // We correctly get the company list from statusResponse.data
                    enrichmentResults = statusResponse.data || []; 
                    displayEnrichmentResults(enrichmentResults, method);
                    SurfeApp.ui.showToast('Enrichment complete!', 'success');
                }
            } catch (error) {
                clearInterval(intervalId);
                SurfeApp.ui.showError(resultsContainer, `Error fetching results: ${error.message}`);
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

    /**
     * =====================================================================
     * Company Card Creation
     * =====================================================================
     */
    function createCompanyCard(company) {
        // Debug logging to see what we're getting
        console.log('Creating card for company:', company);
        
        // --- MAPPING ALL AVAILABLE FIELDS FROM YOUR JSON RESPONSE ---
        const name = company.name || 'Unknown Company';
        const description = company.description || '';
        const industry = company.industry || 'N/A';
        const subIndustry = company.subIndustry || '';
        const location = company.hqAddress || 'N/A';
        const hqCountry = company.hqCountry || 'N/A';
        const linkedIn = company.linkedInURL || '';
        const employeeCount = company.employeeCount || 0;
        const founded = company.founded || 'N/A';

        // Correctly handle array fields by joining them into clean strings
        const website = "https://" + (company.websites && company.websites.length > 0) ? company.websites[0] : '';
        const phones = (company.phones && company.phones.length > 0) ? company.phones.join(' / ') : '';
        const keywords = (company.keywords && company.keywords.length > 0) ? company.keywords.slice(0, 5).join(', ') : ''; // Show first 5 keywords

        // Add debug info for failed enrichments
        const isFailedEnrichment = !company.name || company.name === 'Unknown Company';
        const debugInfo = isFailedEnrichment ? `
            <div class="alert alert-warning mt-2">
                <small><strong>Debug:</strong> ${company.domain || 'No domain'} - Enrichment may have failed or returned no data</small>
            </div>
        ` : '';

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
                                    <h6 class="company-name mb-1">${name}</h6>
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
                            
                            ${debugInfo}
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

    function resetCurrentForm() {
        const activeSection = document.querySelector('.input-section.active');
        if (activeSection) {
            const form = activeSection.querySelector('form');
            if (form) {
                SurfeApp.utils.resetForm(form);
            }
        }
        clearResults();
        
        // Hide CSV controls
        const select = document.getElementById('domain-column-select');
        const enrichBtn = document.getElementById('enrich-csv-btn');
        const countSpan = document.getElementById('unique-domain-count');
        
        if (select) select.style.display = 'none';
        if (enrichBtn) enrichBtn.style.display = 'none';
        if (countSpan) countSpan.style.display = 'none';
        
        // Clear stored CSV data
        window.companyCsvRows = null;
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

        // DEBUG: Log the actual data structure
        console.log('🔍 Company data structure:', enrichmentResults[0]);
        console.log('🔍 Available fields:', Object.keys(enrichmentResults[0]));

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
     * Debug Functions (Global) - for testing domain enrichment
     * =====================================================================
     */
    window.testDomainEnrichment = async function(testDomain = null) {
        // Test with a known good domain or the provided domain
        const domain = testDomain || 'microsoft.com';
        
        console.log(`Testing enrichment with domain: ${domain}`);
        
        const testData = {
            companies: [{ 
                domain: domain,
                externalID: 'test_domain'
            }]
        };
        
        try {
            const response = await SurfeApp.api.request(
                'POST',
                config.endpoints.enrich,
                testData, {
                    headers: {
                        'Content-Type': 'application/json'
                    }
                }
            );
            
            console.log('Test enrichment response:', response);
            
            if (response.success && response.data && response.data.enrichmentID) {
                console.log('Test enrichment started, polling for results...');
                // Poll for results
                const pollTest = setInterval(async () => {
                    try {
                        const statusResponse = await SurfeApp.api.request(
                            'GET', 
                            `/v2/companies/enrich/status/${response.data.enrichmentID}`
                        );
                        
                        console.log('Test status response:', statusResponse);
                        
                        if (statusResponse.success && statusResponse.status === 'completed') {
                            clearInterval(pollTest);
                            console.log('Test completed! Results:', statusResponse.data);
                            SurfeApp.ui.showToast(`Test domain ${domain}: ${statusResponse.data?.length || 0} results`, 'info');
                        }
                    } catch (error) {
                        console.error('Test polling error:', error);
                        clearInterval(pollTest);
                    }
                }, 2000);
                
                // Stop polling after 30 seconds
                setTimeout(() => {
                    clearInterval(pollTest);
                    console.log('Test polling timeout');
                }, 30000);
                
            } else {
                console.error('Test failed:', response.error);
                SurfeApp.ui.showToast(`Test failed: ${response.error}`, 'error');
            }
        } catch (error) {
            console.error('Test error:', error);
            SurfeApp.ui.showToast(`Test error: ${error.message}`, 'error');
        }
    };

    // Test with sample domains from CSV
    window.testCsvDomains = function() {
        const parsedRows = window.companyCsvRows;
        const select = document.getElementById('domain-column-select');
        
        if (!parsedRows || !select || !select.value) {
            console.error('No CSV data or column selected');
            return;
        }
        
        const selectedColumn = select.value;
        const sampleDomains = parsedRows
            .slice(0, 5) // Test first 5 domains
            .map(row => row[selectedColumn])
            .filter(domain => domain && domain.trim())
            .map(domain => SurfeApp.utils.cleanDomain(domain.trim()));
            
        console.log('Testing sample CSV domains:', sampleDomains);
        
        sampleDomains.forEach((domain, index) => {
            setTimeout(() => {
                console.log(`Testing domain ${index + 1}: ${domain}`);
                window.testDomainEnrichment(domain);
            }, index * 5000); // Stagger tests by 5 seconds
        });
    };

    /**
     * =====================================================================
     * Auto-initialize when DOM is ready
     * =====================================================================
     */
    document.addEventListener('DOMContentLoaded', initializeCompanyEnrichment);

})();