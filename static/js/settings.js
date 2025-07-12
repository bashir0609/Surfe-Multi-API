// Complete settings.html JavaScript - REFACTORED to use shared.js

document.addEventListener('DOMContentLoaded', function () {
    console.log('🔧 Settings page - Complete API management loaded');

    const elements = {
        loadingState: document.getElementById('loading-state'),
        noKeysState: document.getElementById('no-keys-state'),
        keysList: document.getElementById('keys-list'),
        keysTableBody: document.getElementById('keys-table-body'),
        systemStatus: document.getElementById('system-status'),
        refreshKeysBtn: document.getElementById('refresh-keys'),
        reloadKeysBtn: document.getElementById('reload-keys'),
        testApiBtn: document.getElementById('test-api'),
        testResult: document.getElementById('test-result')
    };

    // --- Event Listeners ---
    elements.refreshKeysBtn?.addEventListener('click', refreshApiKeys);
    elements.reloadKeysBtn?.addEventListener('click', loadApiKeys);
    elements.testApiBtn?.addEventListener('click', testSelectedKey);
    document.getElementById('add-key-form')?.addEventListener('submit', handleAddKey);

    // --- Auto-Refresh Toggle ---
    const autoRefreshToggle = document.getElementById('auto-refresh-toggle');
    autoRefreshToggle?.addEventListener('change', function (e) {
        if (e.target.checked) {
            SurfeApp.autoRefresh.start('settings-keys', loadApiKeys, 30000);
        } else {
            SurfeApp.autoRefresh.stop('settings-keys');
        }
    });

    // --- State Management ---
    if (window.appState) {
        window.appState.subscribe(displaySystemStatus);
    }

    // --- Initial Load ---
    loadApiKeys();

    // =================================================================
    //                    FUNCTIONS (FIXED API ENDPOINTS)
    // =================================================================

    async function loadApiKeys() {
        try {
            console.log('Loading API keys...');
            const response = await fetch('/api/settings/config');
            console.log('Response status:', response.status);

            const data = await response.json();
            console.log('Response data:', data);

            if (data.success) {
                // Process the keys
                displayApiKeys(data.data.api_manager);
            } else {
                console.error('Failed to load keys:', data);
                showError('Failed to load API keys: ' + (data.message || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error loading API keys:', error);
            showError('Failed to load API keys: ' + error.message);
        }
    }

    async function handleAddKey(event) {
        event.preventDefault();
        const keyName = document.getElementById('key-name').value.trim();
        const apiKey = document.getElementById('api-key-input').value.trim();
        const addBtn = document.getElementById('add-key-btn');

        if (!apiKey) {
            showError('API key is required');
            return;
        }

        SurfeApp.utils.updateButtonState(addBtn, true, 'Adding...', '<i class="fas fa-plus me-2"></i>Add Key');

        try {
            const payload = { api_key: apiKey };
            if (keyName) payload.key_name = keyName;

            // FIXED: Added /api prefix
            const data = await SurfeApp.api.request('POST', '/settings/keys', payload, {
                headers: { 'X-User-ID': getUserId() }
            });

            if (data.success) {
                showSuccess(`Added API key: ${data.key_name}`);
                document.getElementById('add-key-form').reset();
                loadApiKeys();
            } else {
                showError('Failed to add key: ' + data.error);
            }
        } catch (error) {
            showError('Network error adding key: ' + error.message);
        } finally {
            SurfeApp.utils.updateButtonState(addBtn, false, null, '<i class="fas fa-plus me-2"></i>Add Key');
        }
    }

    async function refreshApiKeys() {
        SurfeApp.utils.updateButtonState(elements.refreshKeysBtn, true, 'Refreshing...', '<i class="fas fa-sync me-2"></i>Refresh Keys');
        try {
            // FIXED: Added /api prefix
            const data = await SurfeApp.api.request('POST', '/settings/refresh', null, {
                headers: { 'X-User-ID': getUserId() }
            });

            if (data.success) {
                showSuccess(data.message);
                loadApiKeys();
            } else {
                showError('Failed to refresh: ' + data.error);
            }
        } catch (error) {
            showError('Network error refreshing keys: ' + error.message);
        } finally {
            SurfeApp.utils.updateButtonState(elements.refreshKeysBtn, false, null, '<i class="fas fa-sync me-2"></i>Refresh Keys');
        }
    }

    function displayApiKeys(apiManager) {
        if (apiManager.total_keys === 0) {
            showNoKeys();
            return;
        }

        showKeys();
        elements.keysTableBody.innerHTML = '';

        if (!apiManager.keys || apiManager.keys.length === 0) {
            elements.keysTableBody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center text-muted p-4">
                        <i class="fas fa-info-circle fa-2x mb-3"></i>
                        <h6>Keys Detected But Not Loaded</h6>
                        <p>Total: <strong>${apiManager.total_keys}</strong>, Enabled: <strong>${apiManager.enabled_keys}</strong></p>
                        <button class="btn btn-sm btn-outline-primary" onclick="location.reload()">
                            <i class="fas fa-refresh me-1"></i>Reload Page
                        </button>
                    </td>
                </tr>`;
            return;
        }

        apiManager.keys.forEach(key => {
            const row = createKeyRow(key);
            elements.keysTableBody.appendChild(row);
        });
    }

    function createKeyRow(key) {
        const row = document.createElement('tr');
        const isDynamic = key.source === 'user' || !key.key_name.startsWith('SURFE_API_KEY_');

        row.innerHTML = `
            <td>
                <code>${key.key_name}</code><br>
                <small class="text-muted">...${key.api_key.slice(-8)}</small>
                ${isDynamic ? '<br><span class="badge bg-info">User</span>' : '<br><span class="badge bg-success">System</span>'}
            </td>
            <td>${key.is_active ? '<span class="badge bg-success">Enabled</span>' : '<span class="badge bg-secondary">Disabled</span>'}</td>
            <td>${key.is_active ? '<span class="badge bg-primary">Selected</span>' : '<span class="badge bg-outline-secondary">Not Selected</span>'}</td>
            <td><small>${key.usage_count || 0} requests</small></td>
            <td>
                <div class="btn-group btn-group-sm" role="group">
                    ${!key.is_active ? `<button class="btn btn-outline-primary select-key" data-key-id="${key.id}">Select</button>` : ''}
                    ${key.is_active ? `<button class="btn btn-outline-warning disable-key" data-key-id="${key.id}">Disable</button>` : `<button class="btn btn-outline-success enable-key" data-key-id="${key.id}">Enable</button>`}
                    <button class="btn btn-outline-danger remove-key" data-key-id="${key.id}">Remove</button>
                </div>
            </td>`;

        row.querySelector('.select-key')?.addEventListener('click', (e) => selectKey(e.target.dataset.keyId));
        row.querySelector('.enable-key')?.addEventListener('click', (e) => updateKeyStatus(e.target.dataset.keyId, true));
        row.querySelector('.disable-key')?.addEventListener('click', (e) => updateKeyStatus(e.target.dataset.keyId, false));
        row.querySelector('.remove-key')?.addEventListener('click', (e) => removeKey(e.target.closest('button').dataset.keyId));

        return row;
    }

    async function selectKey(keyId) {
        try {
            // Change from key_id to api_id
            const data = await SurfeApp.api.request('POST', '/settings/select-api-key', 
                { api_id: keyId },  // <-- Changed from key_id to api_id
                {
                    headers: { 'X-User-ID': getUserId() }
                }
            );
            if (data.success) {
                showSuccess('API key selected successfully');
                loadApiKeys();
            } else {
                showError('Failed to select key: ' + data.error);
            }
        } catch (error) {
            showError('Network error selecting key: ' + error.message);
        }
    }

    async function updateKeyStatus(keyId, isActive) {
        const action = isActive ? 'enable' : 'disable';
        try {
            // FIXED: Added /api prefix
            const data = await SurfeApp.api.request('POST', '/settings/keys/status', 
                { api_id: keyId, is_active: isActive },
                {
                    headers: { 'X-User-ID': getUserId() }
                }
            );
            if (data.success) {
                showSuccess(`API key ${action}d successfully`);
                loadApiKeys();
            } else {
                showError(`Failed to ${action} key: ${data.error}`);
            }
        } catch (error) {
            showError(`Network error trying to ${action} key: ${error.message}`);
        }
    }

    async function removeKey(keyId) {
        if (!confirm('Are you sure you want to remove this API key? This action cannot be undone.')) return;

        try {
            const data = await SurfeApp.api.request('DELETE', '/settings/keys', 
                { api_id: keyId },
                {
                    headers: { 'X-User-ID': getUserId() }
                }
            );
            if (data.success) {
                showSuccess('API key removed successfully');
                loadApiKeys();
            } else {
                showError('Failed to remove key: ' + data.error);
            }
        } catch (error) {
            showError('Network error removing key: ' + error.message);
        }
    }

    async function testSelectedKey() {
        SurfeApp.utils.updateButtonState(elements.testApiBtn, true, 'Testing...', '<i class="fas fa-play me-2"></i>Test Selected Key');
        elements.testResult.style.display = 'none';

        try {
            // FIXED: Added /api prefix
            const data = await SurfeApp.api.request('POST', '/settings/test', null, {
                headers: { 'X-User-ID': getUserId() }
            });
            elements.testResult.innerHTML = data.success ?
                `<div class="alert alert-success"><i class="fas fa-check me-2"></i>${data.message || 'API key is working correctly'}</div>` :
                `<div class="alert alert-danger"><i class="fas fa-times me-2"></i>Test failed: ${data.error || data.message || 'Unknown error'}</div>`;
        } catch (error) {
            elements.testResult.innerHTML = `<div class="alert alert-danger"><i class="fas fa-times me-2"></i>Network error testing API: ${error.message}</div>`;
        } finally {
            elements.testResult.style.display = 'block';
            SurfeApp.utils.updateButtonState(elements.testApiBtn, false, null, '<i class="fas fa-play me-2"></i>Test Selected Key');
        }
    }

    function displaySystemStatus(apiManager) {
        if (!apiManager || !elements.systemStatus) return;

        const { has_valid_selection, total_keys, enabled_keys, selected_key } = apiManager;
        const healthColor = has_valid_selection ? 'success' : 'warning';
        const healthIcon = has_valid_selection ? 'check-circle' : 'exclamation-triangle';

        elements.systemStatus.innerHTML = `
            <div class="text-center">
                <i class="fas fa-${healthIcon} fa-2x text-${healthColor} mb-3"></i>
                <h6>${has_valid_selection ? 'Ready' : 'No Selection'}</h6>
                <div class="row text-center mt-3">
                    <div class="col-6">
                        <div class="border-end">
                            <h5 class="mb-0">${total_keys || 0}</h5>
                            <small class="text-muted">Total Keys</small>
                        </div>
                    </div>
                    <div class="col-6">
                        <h5 class="mb-0">${enabled_keys || 0}</h5>
                        <small class="text-muted">Enabled</small>
                    </div>
                </div>
                ${selected_key ? `<div class="mt-3"><small class="text-muted"><strong>Selected:</strong> ${selected_key}</small></div>` : ''}
            </div>`;
    }

    // UI state functions
    function showLoading() {
        SurfeApp.utils.hide(elements.noKeysState);
        SurfeApp.utils.hide(elements.keysList);
        SurfeApp.utils.show(elements.loadingState);
    }

    function showNoKeys() {
        SurfeApp.utils.hide(elements.loadingState);
        SurfeApp.utils.hide(elements.keysList);
        SurfeApp.utils.show(elements.noKeysState);
    }

    function showKeys() {
        SurfeApp.utils.hide(elements.loadingState);
        SurfeApp.utils.hide(elements.noKeysState);
        SurfeApp.utils.show(elements.keysList);
    }

    // Toast functions
    function showSuccess(message) { SurfeApp.ui.showToast(message, 'success'); }
    function showError(message) { SurfeApp.ui.showToast(message, 'error'); }

    // User ID function
    function getUserId() { return localStorage.getItem('userId') || 'default-user-id'; }
});