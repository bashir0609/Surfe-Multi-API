(function() {
    'use strict';
    
    // Module namespace
    const PeopleSearch = {
        currentResults: [],
        isSearching: false,
        searchForm: null,
        resultsContainer: null,
        includeDomains: new Set(),
        excludeDomains: new Set()
    };
    
    /**
     * =====================================================================
     * Search Configuration and Form Data - UPDATED WITH AUTHENTIC SURFE DATA
     * =====================================================================
     */
    const searchConfig = {
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
        
        // Official Surfe API Industries
        industries: [
            "3D Technology",
            "Accounting",
            "Advertising",
            "Agriculture", 
            "Artificial Intelligence",
            "Automotive",
            "Banking",
            "Biotechnology",
            "Blockchain",
            "Business Intelligence",
            "Cloud Computing",
            "Consulting",
            "CRM",
            "Cyber Security",
            "E-Commerce",
            "Education",
            "Energy",
            "Engineering",
            "Entertainment",
            "Finance",
            "FinTech",
            "Gaming",
            "Government",
            "Hardware",
            "Health Care",
            "HR",
            "Information Technology",
            "Insurance",
            "Internet",
            "Legal",
            "Machine Learning",
            "Manufacturing",
            "Marketing",
            "Media and Entertainment",
            "Mobile",
            "Non Profit",
            "Real Estate",
            "Retail",
            "SaaS",
            "Sales",
            "Security",
            "Software",
            "Telecommunications"
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
    
    console.log('🔍 People Search v2 - Loaded with authentic Surfe API data');
    console.log('📊 Seniorities:', searchConfig.seniorities);
    console.log('📊 Departments:', searchConfig.departments); 
    console.log('📊 Industries:', searchConfig.industries);
    console.log('📊 Countries:', searchConfig.countries);

    /**
     * =====================================================================
     * Initialize People Search
     * =====================================================================
     */
    PeopleSearch.init = function() {
        console.log('🔍 Initializing People Search module v2');
        
        this.searchForm = document.getElementById('people-search-form');
        this.resultsContainer = document.getElementById('search-results');
        
        if (!this.searchForm || !this.resultsContainer) {
            console.error('Required elements not found for People Search');
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
    PeopleSearch.setupForm = function() {
        // Reset form to clean state
        this.searchForm.reset();
        
        // Setup default values
        const limitSelect = document.getElementById('limit');
        if (limitSelect && !limitSelect.value) {
            limitSelect.value = '10';
        }
        
        const peoplePerCompanySelect = document.getElementById('people-per-company');
        if (peoplePerCompanySelect && !peoplePerCompanySelect.value) {
            peoplePerCompanySelect.value = '1';
        }
    };
    
    PeopleSearch.populateFormOptions = function() {
        // Use centralized autocomplete functionality
        if (window.SurfeApp && window.SurfeApp.autocomplete) {
            return window.SurfeApp.autocomplete.populatePeopleSearchForm();
        } else {
            console.warn('SurfeApp autocomplete not available, using fallback');
            return this.populateFormOptionsFallback();
        }
    };
    
    PeopleSearch.populateFormOptionsFallback = function() {
        console.log('🔄 Using fallback form population...');
        // Fallback for when autocomplete module isn't loaded
        const fallbackData = {
            industries: searchConfig.industries || [],
            seniorities: searchConfig.seniorities || [],
            departments: searchConfig.departments || [],
            countries: searchConfig.countries || []
        };
        
        Object.entries(fallbackData).forEach(([key, options]) => {
            const selectId = key === 'countries' ? 'people-countries' : key;
            this.populateSelectFallback(selectId, options);
            if (key === 'countries') {
                this.populateSelectFallback('company-countries', options);
            }
        });
        
        console.log('✅ Fallback form options populated');
    };
    
    PeopleSearch.populateSelectFallback = function(selectId, options) {
        const select = document.getElementById(selectId);
        if (!select) return;
        
        // Clear existing options except the first one (placeholder)
        while (select.children.length > 1) {
            select.removeChild(select.lastChild);
        }
        
        // Add new options
        options.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option;
            optionElement.textContent = option;
            select.appendChild(optionElement);
        });
    };
    
    // Minimal implementation to avoid errors
    PeopleSearch.setupEventListeners = function() {
        this.searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            console.log('🔍 Search form submitted');
        });
        
        this.setupDomainEventListeners();
    };
    
    PeopleSearch.setupDomainFiltering = function() {
        // Initialize domain counts
        this.updateDomainCounts();
    };
    
    PeopleSearch.setupDomainEventListeners = function() {
        // Minimal implementation
    };
    
    PeopleSearch.updateDomainCounts = function() {
        // Minimal implementation
    };
    
    /**
     * =====================================================================
     * Auto-initialize when DOM is ready
     * =====================================================================
     */
    document.addEventListener('DOMContentLoaded', function() {
        console.log('🚀 DOM loaded, checking for people search form...');
        if (document.getElementById('people-search-form')) {
            console.log('✅ People search form found, initializing...');
            PeopleSearch.init();
        } else {
            console.log('❌ People search form not found');
        }
    });
    
    // Export module for external access
    window.PeopleSearch = PeopleSearch;
    window.searchConfigV2 = searchConfig; // For debugging
    
})();