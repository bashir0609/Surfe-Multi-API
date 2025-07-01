/**
 * =====================================================================
 * Autocompletion Module - Centralized autocomplete functionality
 * Features: Select population, option management, authentic data integration
 * =====================================================================
 */

(function() {
    'use strict';

    /**
     * =====================================================================
     * Autocompletion Namespace
     * =====================================================================
     */
    window.SurfeApp = window.SurfeApp || {};
    window.SurfeApp.autocomplete = {
        /**
         * =====================================================================
         * Core Population Functions
         * =====================================================================
         */

        /**
         * Populate a select element with options
         * @param {string} selectId - The ID of the select element
         * @param {Array} options - Array of option values/objects
         * @param {Object} config - Optional configuration
         */
        populateSelect: function(selectId, options, config = {}) {
            const select = document.getElementById(selectId);
            if (!select) {
                console.warn(`Select element ${selectId} not found`);
                return false;
            }

            const {
                preservePlaceholder = true,
                valueField = null,
                textField = null,
                clearExisting = true
            } = config;

            // Clear existing options (preserve placeholder if requested)
            if (clearExisting) {
                const startIndex = preservePlaceholder ? 1 : 0;
                while (select.children.length > startIndex) {
                    select.removeChild(select.lastChild);
                }
            }

            // Add new options
            options.forEach(option => {
                const optionElement = document.createElement('option');
                
                if (typeof option === 'object' && option !== null) {
                    // Handle object options
                    optionElement.value = valueField ? option[valueField] : option.value || option.code || option.id;
                    optionElement.textContent = textField ? option[textField] : option.text || option.name || option.label;
                } else {
                    // Handle string options
                    optionElement.value = option;
                    optionElement.textContent = option;
                }
                
                select.appendChild(optionElement);
            });

            return true;
        },

        /**
         * Populate a datalist element with options for searchable autocomplete
         * @param {string} datalistId - The ID of the datalist element
         * @param {Array} options - Array of option values/objects
         * @param {Object} config - Optional configuration
         */
        populateDatalist: function(datalistId, options, config = {}) {
            const datalist = document.getElementById(datalistId);
            if (!datalist || !Array.isArray(options)) {
                console.warn(`Cannot populate datalist: element '${datalistId}' not found or options not an array`);
                return false;
            }

            const {
                valueField = null,
                textField = null,
                clearExisting = true
            } = config;

            // Clear existing options
            if (clearExisting) {
                datalist.innerHTML = '';
            }

            // Add new options
            options.forEach(option => {
                const optionElement = document.createElement('option');
                
                if (typeof option === 'object' && option !== null) {
                    // Handle object options
                    optionElement.value = valueField ? option[valueField] : option.value || option.code || option.id;
                    optionElement.textContent = textField ? option[textField] : option.text || option.name || option.label;
                } else {
                    // Handle string options
                    optionElement.value = option;
                    optionElement.textContent = option;
                }
                
                datalist.appendChild(optionElement);
            });

            console.log(`✅ ${datalistId} populated with ${options.length} options`);
            return true;
        },

        /**
         * Populate multiple selects with data from SurfeApp.data
         * @param {Object} selectMappings - Object mapping select IDs to data keys
         */
        populateMultipleSelects: function(selectMappings) {
            if (!window.SurfeApp || !window.SurfeApp.data) {
                console.warn('SurfeApp data not available for autocomplete');
                return;
            }

            const data = window.SurfeApp.data;
            const results = {};

            Object.entries(selectMappings).forEach(([selectId, dataKey]) => {
                if (data[dataKey] && Array.isArray(data[dataKey])) {
                    const success = this.populateSelect(selectId, data[dataKey]);
                    results[selectId] = {
                        success,
                        count: success ? data[dataKey].length : 0
                    };
                } else {
                    console.warn(`Data key '${dataKey}' not found or not an array`);
                    results[selectId] = { success: false, count: 0 };
                }
            });

            return results;
        },

        /**
         * =====================================================================
         * Specialized Population Functions
         * =====================================================================
         */

        /**
         * Populate people search form options with searchable datalists
         */
        populatePeopleSearchForm: function() {
            console.log('🔄 Populating people form options with searchable autocomplete...');
            
            if (!window.SurfeApp || !window.SurfeApp.data) {
                console.warn('SurfeApp data not available for autocomplete');
                return false;
            }

            const data = window.SurfeApp.data;
            const datalistMappings = {
                'industries-list': 'industries',
                'seniorities-list': 'seniorities', 
                'departments-list': 'departments',
                'people-countries-list': 'countries',
                'company-countries-list': 'countries'
            };

            const results = {};
            
            Object.entries(datalistMappings).forEach(([datalistId, dataKey]) => {
                if (data[dataKey] && Array.isArray(data[dataKey])) {
                    const success = this.populateDatalist(datalistId, data[dataKey]);
                    results[datalistId] = {
                        success,
                        count: success ? data[dataKey].length : 0
                    };
                    
                    if (success) {
                        console.log(`✅ ${datalistId} populated with ${data[dataKey].length} options`);
                    } else {
                        console.error(`❌ Failed to populate ${datalistId}`);
                    }
                } else {
                    console.warn(`Data key '${dataKey}' not found or not an array`);
                    results[datalistId] = { success: false, count: 0 };
                }
            });

            console.log('✅ People form autocomplete populated');
            return results;
        },

        /**
         * Populate company search form options with searchable datalists
         */
        populateCompanySearchForm: function() {
            console.log('🔄 Populating company form options with searchable autocomplete...');
            
            if (!window.SurfeApp || !window.SurfeApp.data) {
                console.warn('SurfeApp data not available for autocomplete');
                return false;
            }

            const data = window.SurfeApp.data;
            const results = {};
            
            // Populate with authentic data using datalists
            const datalistMappings = {
                'industries-list': 'industries',
                'countries-list': 'countries'
            };
            
            Object.entries(datalistMappings).forEach(([datalistId, dataKey]) => {
                if (data[dataKey] && Array.isArray(data[dataKey])) {
                    const success = this.populateDatalist(datalistId, data[dataKey]);
                    results[datalistId] = {
                        success,
                        count: success ? data[dataKey].length : 0
                    };
                    
                    if (success) {
                        console.log(`✅ ${datalistId} populated with ${data[dataKey].length} options`);
                    } else {
                        console.error(`❌ Failed to populate ${datalistId}`);
                    }
                } else {
                    console.warn(`Data key '${dataKey}' not found or not an array`);
                    results[datalistId] = { success: false, count: 0 };
                }
            });

            // Populate company sizes (static data) using datalist
            const companySizes = [
                '1-10', '11-50', '51-200', '201-500', '501-1000', 
                '1001-5000', '5001-10000', '10000+'
            ];
            
            const sizeSuccess = this.populateDatalist('company-sizes-list', companySizes);
            results['company-sizes-list'] = { success: sizeSuccess, count: sizeSuccess ? companySizes.length : 0 };
            
            if (sizeSuccess) {
                console.log(`✅ company-sizes populated with ${companySizes.length} options`);
            }

            console.log('✅ Company form options populated with authentic data');
            return results;
        },

        /**
         * Populate enrichment form options (minimal, mainly for countries)
         */
        populateEnrichmentForm: function() {
            console.log('🔄 Populating enrichment form options...');
            
            const selectMappings = {
                'countries': 'countries'
            };

            const results = this.populateMultipleSelects(selectMappings);
            console.log('✅ Enrichment form options populated');
            return results;
        },

        /**
         * =====================================================================
         * Utility Functions
         * =====================================================================
         */

        /**
         * Clear select options (preserve placeholder)
         * @param {string} selectId - The ID of the select element
         * @param {boolean} preservePlaceholder - Whether to keep the first option
         */
        clearSelect: function(selectId, preservePlaceholder = true) {
            const select = document.getElementById(selectId);
            if (!select) return false;

            const startIndex = preservePlaceholder ? 1 : 0;
            while (select.children.length > startIndex) {
                select.removeChild(select.lastChild);
            }
            return true;
        },

        /**
         * Get current value of a select element
         * @param {string} selectId - The ID of the select element
         */
        getSelectValue: function(selectId) {
            const select = document.getElementById(selectId);
            return select ? select.value : null;
        },

        /**
         * Set value of a select element
         * @param {string} selectId - The ID of the select element
         * @param {string} value - The value to set
         */
        setSelectValue: function(selectId, value) {
            const select = document.getElementById(selectId);
            if (select) {
                select.value = value;
                return true;
            }
            return false;
        },

        /**
         * Check if select has options (beyond placeholder)
         * @param {string} selectId - The ID of the select element
         */
        hasOptions: function(selectId) {
            const select = document.getElementById(selectId);
            return select ? select.children.length > 1 : false;
        },

        /**
         * Get all option values from a select
         * @param {string} selectId - The ID of the select element
         * @param {boolean} excludePlaceholder - Whether to exclude the first option
         */
        getSelectOptions: function(selectId, excludePlaceholder = true) {
            const select = document.getElementById(selectId);
            if (!select) return [];

            const options = Array.from(select.options);
            const startIndex = excludePlaceholder ? 1 : 0;
            
            return options.slice(startIndex).map(option => ({
                value: option.value,
                text: option.textContent
            }));
        },

        /**
         * =====================================================================
         * Auto-Detection and Smart Population
         * =====================================================================
         */

        /**
         * Automatically detect and populate forms based on page context
         */
        autoPopulateForms: function() {
            // Detect people search form
            if (document.getElementById('people-search-form')) {
                console.log('🎯 Auto-detected people search form');
                return this.populatePeopleSearchForm();
            }
            
            // Detect company search form
            if (document.getElementById('company-search-form')) {
                console.log('🎯 Auto-detected company search form');
                return this.populateCompanySearchForm();
            }
            
            // Detect enrichment forms
            if (document.querySelector('[id*="enrichment"]')) {
                console.log('🎯 Auto-detected enrichment form');
                return this.populateEnrichmentForm();
            }

            console.log('ℹ️ No forms detected for auto-population');
            return null;
        },

        /**
         * Initialize autocomplete functionality
         */
        init: function() {
            console.log('🎯 Initializing Autocompletion module');
            
            // Wait for SurfeApp data to be available
            if (window.SurfeApp && window.SurfeApp.data) {
                this.autoPopulateForms();
            } else {
                // Wait for data to load
                const checkData = () => {
                    if (window.SurfeApp && window.SurfeApp.data) {
                        this.autoPopulateForms();
                    } else {
                        setTimeout(checkData, 100);
                    }
                };
                checkData();
            }
            
            console.log('✅ Autocompletion module initialized');
        }
    };

    /**
     * =====================================================================
     * Auto-initialize when DOM is ready
     * =====================================================================
     */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            // Initialize after a short delay to ensure SurfeApp.data is loaded
            setTimeout(() => {
                window.SurfeApp.autocomplete.init();
            }, 100);
        });
    } else {
        // DOM already loaded
        setTimeout(() => {
            window.SurfeApp.autocomplete.init();
        }, 100);
    }

})();