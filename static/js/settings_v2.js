/**
 * =====================================================================
 * Settings Module v2 - Simple API Key Management
 * Features: API key management, system configuration, no rotation
 * =====================================================================
 */
(function() {
    'use strict';

    /**
     * =====================================================================
     * Configuration and State
     * =====================================================================
     */
    let apiKeysData = [];
    let systemSettings = {};

    /**
     * =====================================================================
     * Initialize Settings
     * =====================================================================
     */
    function initializeSettings() {
        console.log('🔧 Initializing Settings module v2');
        
        setupEventListeners();
        loadApiKeysStatus();
        loadKeyStats();
        loadSystemSettings();
        
        console.log('✅ Settings module v2 initialized');
    }

    /**
     * =====================================================================
     * Event Listeners
     * =====================================================================
     */
    function setupEventListeners() {
        // Add API key form
        const addKeyForm = document.getElementById('add-api-key-form');
        if (addKeyForm) {
            addKeyForm.addEventListener('submit', handleAddApiKey);
        }
        
        // Refresh keys button
        const refreshBtn = document.getElementById('refresh-keys');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', handleRefreshKeys);
        }
        
        // Test key button
        const testKeyBtn = document.getElementById('test-key');
        if (testKeyBtn) {
            testKeyBtn.addEventListener('click', handleTestKey);
        }
    }

    /**
     * =====================================================================
     * API Key Management
     * =====================================================================
     */
    async function handleAddApiKey(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const keyName = formData.get('key_name');
        const apiKey = formData.get('api_key');
        
        if (!keyName || !apiKey) {
            SurfeApp.ui.showToast('Please provide both key name and API key', 'error');
            return;
        }
        
        if (apiKey.length < 10) {
            SurfeApp.ui.showToast('Invalid API key format', 'error');
            return;
        }
        
        try {
            const response = await SurfeApp.api.post('/api/add-key', {
                key_name: keyName,
                api_key: apiKey
            });
            
            if (response.success) {
                SurfeApp.ui.showToast('API key added successfully', 'success');
                event.target.reset();
                loadApiKeysStatus();
                loadKeyStats();
            } else {
                SurfeApp.ui.showToast(response.message || 'Failed to add API key', 'error');
            }
        } catch (error) {
            console.error('Error adding API key:', error);
            SurfeApp.ui.showToast('Error adding API key', 'error');
        }
    }
    
    async function handleRemoveKey(keyName) {
        if (!confirm(`Are you sure you want to remove the key "${keyName}"?`)) {
            return;
        }
        
        try {
            const response = await SurfeApp.api.post('/api/remove-key', {
                key_name: keyName
            });
            
            if (response.success) {
                SurfeApp.ui.showToast('API key removed successfully', 'success');
                loadApiKeysStatus();
                loadKeyStats();
            } else {
                SurfeApp.ui.showToast(response.message || 'Failed to remove API key', 'error');
            }
        } catch (error) {
            console.error('Error removing API key:', error);
            SurfeApp.ui.showToast('Error removing API key', 'error');
        }
    }
    
    async function handleSelectKey(keyName) {
        try {
            const response = await SurfeApp.api.post('/api/select-key', {
                key_name: keyName
            });
            
            if (response.success) {
                SurfeApp.ui.showToast(`Selected API key: ${keyName}`, 'success');
                loadApiKeysStatus();
                loadKeyStats();
            } else {
                SurfeApp.ui.showToast(response.message || 'Failed to select API key', 'error');
            }
        } catch (error) {
            console.error('Error selecting API key:', error);
            SurfeApp.ui.showToast('Error selecting API key', 'error');
        }
    }
    
    async function handleToggleKey(keyName, enabled) {
        try {
            const endpoint = enabled ? '/api/disable-key' : '/api/enable-key';
            const response = await SurfeApp.api.post(endpoint, {
                key_name: keyName
            });
            
            if (response.success) {
                const action = enabled ? 'disabled' : 'enabled';
                SurfeApp.ui.showToast(`API key ${action} successfully`, 'success');
                loadApiKeysStatus();
                loadKeyStats();
            } else {
                SurfeApp.ui.showToast(response.message || 'Failed to toggle API key', 'error');
            }
        } catch (error) {
            console.error('Error toggling API key:', error);
            SurfeApp.ui.showToast('Error toggling API key', 'error');
        }
    }
    
    async function handleRefreshKeys() {
        try {
            const response = await SurfeApp.api.post('/api/refresh-keys');
            
            if (response.success) {
                SurfeApp.ui.showToast('API keys refreshed from environment', 'success');
                loadApiKeysStatus();
                loadKeyStats();
            } else {
                SurfeApp.ui.showToast(response.message || 'Failed to refresh API keys', 'error');
            }
        } catch (error) {
            console.error('Error refreshing API keys:', error);
            SurfeApp.ui.showToast('Error refreshing API keys', 'error');
        }
    }
    
    async function handleTestKey() {
        try {
            const response = await SurfeApp.api.post('/api/test-key');
            
            if (response.success) {
                SurfeApp.ui.showToast('API key test successful', 'success');
            } else {
                SurfeApp.ui.showToast(response.message || 'API key test failed', 'error');
            }
        } catch (error) {
            console.error('Error testing API key:', error);
            SurfeApp.ui.showToast('Error testing API key', 'error');
        }
    }

    /**
     * =====================================================================
     * Data Loading
     * =====================================================================
     */
    async function loadApiKeysStatus() {
        const container = document.getElementById('api-keys-list');
        if (!container) return;
        
        try {
            const response = await SurfeApp.api.get('/api/config');
            
            if (response && response.keys) {
                displayApiKeys(response.keys, response.selected_key);
                apiKeysData = response.keys;
            } else {
                container.innerHTML = `
                    <div class="text-center text-muted">
                        <i class="fas fa-key fa-2x mb-2"></i>
                        <p>No API keys configured</p>
                        <small>Add keys using the form above or set environment variables</small>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Failed to load API keys:', error);
            container.innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
                    <p>Unable to load API keys</p>
                </div>
            `;
        }
    }
    
    async function loadKeyStats() {
        const statsContainer = document.getElementById('key-stats');
        if (!statsContainer) return;
        
        try {
            const response = await SurfeApp.api.getStats();
            
            if (response) {
                displayKeyStats(response);
            }
        } catch (error) {
            console.error('Failed to load key stats:', error);
            statsContainer.innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
                    <p class="small">Unable to load stats</p>
                </div>
            `;
        }
    }

    async function loadSystemSettings() {
        try {
            const response = await SurfeApp.api.get('/api/config');
            
            if (response) {
                systemSettings = response;
                displaySystemInfo(response);
            }
        } catch (error) {
            console.error('Failed to load system settings:', error);
        }
    }

    /**
     * =====================================================================
     * Display Functions
     * =====================================================================
     */
    function displayApiKeys(keys, selectedKey) {
        const container = document.getElementById('api-keys-list');
        if (!container) return;
        
        if (!keys || keys.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-key fa-2x mb-2"></i>
                    <p>No API keys available</p>
                    <small>Add keys using the form above</small>
                </div>
            `;
            return;
        }
        
        const keysHtml = keys.map(key => {
            const isSelected = key.name === selectedKey;
            const statusBadge = key.enabled ? 
                '<span class="badge bg-success">Enabled</span>' : 
                '<span class="badge bg-secondary">Disabled</span>';
            const selectedBadge = isSelected ? 
                '<span class="badge bg-primary">Selected</span>' : '';
            
            return `
                <div class="key-item border rounded p-3 mb-2 ${isSelected ? 'border-primary' : ''}">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1">${key.name}</h6>
                            <small class="text-muted">Key: ...${key.key_suffix}</small>
                            <div class="mt-1">
                                ${statusBadge}
                                ${selectedBadge}
                                ${key.source ? `<span class="badge bg-info">${key.source}</span>` : ''}
                            </div>
                        </div>
                        <div class="btn-group">
                            ${!isSelected ? `<button class="btn btn-sm btn-outline-primary" onclick="handleSelectKey('${key.name}')">Select</button>` : ''}
                            <button class="btn btn-sm ${key.enabled ? 'btn-outline-warning' : 'btn-outline-success'}" 
                                    onclick="handleToggleKey('${key.name}', ${key.enabled})">
                                ${key.enabled ? 'Disable' : 'Enable'}
                            </button>
                            ${key.source === 'dynamic' ? `<button class="btn btn-sm btn-outline-danger" onclick="handleRemoveKey('${key.name}')">Remove</button>` : ''}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        container.innerHTML = keysHtml;
    }
    
    function displayKeyStats(stats) {
        const statsContainer = document.getElementById('key-stats');
        if (!statsContainer) return;
        
        const statsHtml = `
            <div class="stats-grid">
                <div class="stat-item text-center mb-3">
                    <div class="stat-value text-primary">${stats.total_keys || 0}</div>
                    <div class="stat-label">Total Keys</div>
                </div>
                <div class="stat-item text-center mb-3">
                    <div class="stat-value text-success">${stats.active_keys || 0}</div>
                    <div class="stat-label">Enabled Keys</div>
                </div>
                <div class="stat-item text-center mb-3">
                    <div class="stat-value text-info">${stats.selected_key || 'None'}</div>
                    <div class="stat-label">Selected Key</div>
                </div>
                <div class="stat-item text-center mb-3">
                    <div class="stat-value text-warning">${stats.total_requests || 0}</div>
                    <div class="stat-label">Total Requests</div>
                </div>
            </div>
            
            <div class="mt-3">
                <div class="progress" style="height: 8px;">
                    <div class="progress-bar bg-success" style="width: ${stats.system_health || 0}%"></div>
                </div>
                <small class="text-muted">System Health</small>
            </div>
        `;
        
        statsContainer.innerHTML = statsHtml;
    }
    
    function displaySystemInfo(info) {
        const container = document.getElementById('system-info');
        if (!container) return;
        
        const infoHtml = `
            <div class="row">
                <div class="col-md-6">
                    <h6>Configuration</h6>
                    <ul class="list-unstyled small">
                        <li><strong>Environment:</strong> ${info.environment || 'Development'}</li>
                        <li><strong>Selected Key:</strong> ${info.selected_key || 'None'}</li>
                        <li><strong>Total Keys:</strong> ${info.total_keys || 0}</li>
                    </ul>
                </div>
                <div class="col-md-6">
                    <h6>Status</h6>
                    <ul class="list-unstyled small">
                        <li><strong>System:</strong> <span class="badge bg-success">Active</span></li>
                        <li><strong>Database:</strong> <span class="badge bg-success">Connected</span></li>
                        <li><strong>API:</strong> <span class="badge bg-${info.selected_key ? 'success' : 'warning'}">${info.selected_key ? 'Ready' : 'No Key'}</span></li>
                    </ul>
                </div>
            </div>
        `;
        
        container.innerHTML = infoHtml;
    }

    /**
     * =====================================================================
     * Global Functions for Button Handlers
     * =====================================================================
     */
    window.handleSelectKey = handleSelectKey;
    window.handleToggleKey = handleToggleKey;
    window.handleRemoveKey = handleRemoveKey;

    /**
     * =====================================================================
     * Auto-initialize
     * =====================================================================
     */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeSettings);
    } else {
        initializeSettings();
    }

})();