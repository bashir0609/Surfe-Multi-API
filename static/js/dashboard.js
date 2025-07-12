/**
 * =====================================================================
 * Dashboard Module - Handles dashboard functionality and API monitoring
 * Features: Real-time stats, API key health monitoring, auto-refresh
 * =====================================================================
 */

(function() {
    'use strict';
    
    // Module namespace
    const Dashboard = {
        refreshInterval: null,
        isLoading: false,
        autoRefreshEnabled: true,
        refreshIntervalMs: 30000 // 30 seconds
    };
    
    /**
     * =====================================================================
     * Initialize Dashboard
     * =====================================================================
     */
    Dashboard.init = function() {
        console.log('📊 Initializing Dashboard module');
        
        this.setupEventListeners();
        this.loadInitialData();
        // Auto-refresh disabled by default - users can enable it manually
        
        console.log('✅ Dashboard module initialized');
    };
    
    /**
     * =====================================================================
     * Event Listeners
     * =====================================================================
     */
    Dashboard.setupEventListeners = function() {
        // Manual refresh button
        const refreshBtn = document.getElementById('refresh-stats');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshStats());
        }
        
        // Auto-refresh toggle
        const autoRefreshToggle = document.getElementById('auto-refresh-toggle');
        if (autoRefreshToggle) {
            autoRefreshToggle.addEventListener('change', (e) => {
                this.toggleAutoRefresh(e.target.checked);
            });
        }
        
        // Export stats button
        const exportStatsBtn = document.getElementById('export-stats');
        if (exportStatsBtn) {
            exportStatsBtn.addEventListener('click', () => this.exportStats());
        }
        
        // Test API button
        const testApiBtn = document.getElementById('test-api');
        if (testApiBtn) {
            testApiBtn.addEventListener('click', () => this.testApiHealth());
        }
    };
    
    /**
     * =====================================================================
     * Data Loading and Refresh
     * =====================================================================
     */
    Dashboard.loadInitialData = function() {
        this.refreshStats();
    };
    
    Dashboard.refreshStats = function() {
        if (this.isLoading) {
            console.log('📊 Dashboard refresh already in progress');
            return;
        }
        
        this.isLoading = true;
        this.updateRefreshButton(true);
        
        console.log('📊 Refreshing dashboard stats');
        
        Promise.all([
            this.loadApiStats(),
            this.loadHealthCheck()
        ])
        .then(() => {
            this.updateLastRefreshTime();
            SurfeApp.ui.showToast('Dashboard updated successfully', 'success', 2000);
        })
        .catch(error => {
            console.error('❌ Failed to refresh dashboard:', error);
            SurfeApp.ui.showToast('Failed to refresh dashboard', 'error');
        })
        .finally(() => {
            this.isLoading = false;
            this.updateRefreshButton(false);
        });
    };
    
    Dashboard.loadApiStats = function() {
        return SurfeApp.api.getStats()
            .then(stats => {
                this.updateStatsDisplay(stats);
                this.updateKeyDetails(stats.key_details || {});
                return stats;
            })
            .catch(error => {
                console.error('❌ Failed to load API stats:', error);
                this.showStatsError(error);
                throw error;
            });
    };
    
    Dashboard.loadHealthCheck = function() {
        return SurfeApp.api.getHealthCheck()
            .then(health => {
                this.updateHealthDisplay(health);
                return health;
            })
            .catch(error => {
                console.error('❌ Failed to load health check:', error);
                this.showHealthError(error);
                throw error;
            });
    };
    
    /**
     * =====================================================================
     * Stats Display Updates
     * =====================================================================
     */
    Dashboard.updateStatsDisplay = function(stats) {
        if (stats.message && stats.active_keys === 0 && stats.total_keys === 0) {
            // Show "no keys" state
            this.updateStatCard('total-keys', 0);
            this.updateStatCard('active-keys', 0);
            this.updateStatCard('disabled-keys', 0);
            this.updateStatCard('total-requests', 0);
            this.updateStatCard('health-percentage', '0%');
            this.updateHealthBar(0);
            
            // Show helpful message in key details area
            const container = document.getElementById('key-status-cards');
            if (container) {
                container.innerHTML = `
                    <div class="col-12">
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle me-2"></i>
                            ${stats.message}
                            <br><small class="mt-2 d-block">Go to <a href="/settings" class="alert-link">Settings</a> to add your Surfe API keys.</small>
                        </div>
                    </div>
                `;
            }
            return;
        }
        
        // Update main stats cards
        this.updateStatCard('total-keys', stats.total_keys || 0);
        this.updateStatCard('active-keys', stats.active_keys || 0);
        this.updateStatCard('disabled-keys', stats.disabled_keys || 0);
        this.updateStatCard('total-requests', stats.total_requests || 0);
        
        // Update health percentage
        const healthPercentage = stats.success_rate || 0;
        this.updateStatCard('health-percentage', `${healthPercentage.toFixed(1)}%`);
        
        // Update health bar
        this.updateHealthBar(healthPercentage);
        
        // Update last used key
        const lastKeyElement = document.getElementById('last-key-used');
        if (lastKeyElement) {
            lastKeyElement.textContent = stats.last_key_used || 'None';
        }
    };
    
    Dashboard.updateStatCard = function(cardId, value) {
        
        const element = document.getElementById(cardId);
        if (!element) {
            console.error(`❌ Card element ${cardId} not found`);
            return;
        }
        
        // Try different selectors for the value element
        let valueElement = element.querySelector('.stat-value');
        if (!valueElement) {
            valueElement = element; // Fallback to the element itself
        }
        
        if (valueElement) {
            valueElement.textContent = value;
            console.log(`✅ Updated ${cardId} to: ${value}`);
        } else {
            console.error(`❌ Value element not found in ${cardId}`);
        }
    };
    
    Dashboard.updateHealthBar = function(percentage) {
        const healthBar = document.querySelector('.health-fill');
        if (healthBar) {
            healthBar.style.width = `${percentage}%`;
            
            // Update color based on health
            healthBar.className = 'health-fill';
            if (percentage >= 80) {
                healthBar.classList.add('health-excellent');
            } else if (percentage >= 60) {
                healthBar.classList.add('health-good');
            } else if (percentage > 0) {
                healthBar.classList.add('health-warning');
            } else {
                healthBar.classList.add('health-danger');
            }
        }
    };
    
    Dashboard.updateKeyDetails = function(keyDetails) {
        const container = document.getElementById('api-keys-details');
        if (!container) return;
        
        if (!keyDetails || Object.keys(keyDetails).length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted p-4">
                    <i class="fas fa-key fa-2x mb-3"></i>
                    <p>No API keys configured</p>
                </div>
            `;
            return;
        }
        
        const keysHtml = Object.entries(keyDetails)
            .map(([keyId, keyData]) => this.generateKeyCard(keyId, keyData))
            .join('');
        
        container.innerHTML = keysHtml;
    };
    
    Dashboard.generateKeyCard = function(keyId, keyData) {
        const statusClass = keyData.is_disabled ? 'disabled' : 'active';
        const statusIcon = keyData.is_disabled ? 'fas fa-times-circle' : 'fas fa-check-circle';
        const statusText = keyData.is_disabled ? 'Disabled' : 'Active';
        
        return `
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="key-status-card card ${statusClass}">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-3">
                            <div class="key-identifier">${SurfeApp.utils.sanitizeHtml(keyId)}</div>
                            <span class="status-badge status-${statusClass}">
                                <div class="status-indicator"></div>
                                <i class="${statusIcon} me-1"></i>
                                ${statusText}
                            </span>
                        </div>
                        
                        <div class="key-metrics">
                            <div class="metric-item">
                                <span class="metric-value">${SurfeApp.utils.formatNumber(keyData.total_requests || 0)}</span>
                                <span class="metric-label">Total</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-value">${SurfeApp.utils.formatNumber(keyData.successful_requests || 0)}</span>
                                <span class="metric-label">Success</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-value">${SurfeApp.utils.formatNumber(keyData.failed_attempts || 0)}</span>
                                <span class="metric-label">Failed</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-value">${SurfeApp.utils.formatPercentage(keyData.success_rate || 0)}</span>
                                <span class="metric-label">Rate</span>
                            </div>
                        </div>
                        
                        ${keyData.last_used ? `
                            <div class="mt-3">
                                <small class="text-muted">
                                    Last used: ${SurfeApp.utils.formatDate(keyData.last_used)}
                                </small>
                            </div>
                        ` : ''}
                        
                        ${keyData.quota_reset_time ? `
                            <div class="mt-2">
                                <small class="text-warning">
                                    <i class="fas fa-clock me-1"></i>
                                    Cooldown until: ${SurfeApp.utils.formatDate(keyData.quota_reset_time)}
                                </small>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    };
    
    Dashboard.updateHealthDisplay = function(health) {
        const healthContainer = document.getElementById('health-status');
        if (!healthContainer) return;
        
        const status = health.status || 'unknown';
        const simpleSystem = health.simple_system || {};
        
        // Handle case when no keys are configured
        if (status === 'no_keys' || (health.message && health.simple_system && health.simple_system.enabled_keys === 0)) {
            healthContainer.innerHTML = `
                <div class="health-indicator warning">
                    <div class="health-icon">
                        <i class="fas fa-exclamation-triangle"></i>
                    </div>
                    <div class="health-details">
                        <div class="health-status">No API Keys</div>
                        <div class="health-message">Add keys via Settings page</div>
                    </div>
                </div>
            `;
            return;
        }
        
        let statusClass, statusIcon;
        switch (status) {
            case 'healthy':
                statusClass = 'status-active';
                statusIcon = 'fas fa-heart';
                break;
            case 'unhealthy':
                statusClass = 'status-disabled';
                statusIcon = 'fas fa-heart-broken';
                break;
            default:
                statusClass = 'status-warning';
                statusIcon = 'fas fa-question-circle';
        }
        
        healthContainer.innerHTML = `
            <div class="status-badge ${statusClass}">
                <div class="status-indicator"></div>
                <i class="${statusIcon} me-2"></i>
                ${status.charAt(0).toUpperCase() + status.slice(1)}
            </div>
            <small class="text-muted d-block mt-2">
                Last check: ${SurfeApp.utils.formatDate(health.timestamp)}
            </small>
        `;
        
        // Update global health indicator if available
        SurfeApp.ui.updateHealthIndicator(simpleSystem);
    };
    
    /**
     * =====================================================================
     * Error Handling
     * =====================================================================
     */
    Dashboard.showStatsError = function(error) {
        const container = document.getElementById('stats-overview');
        if (container) {
            container.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Failed to load API statistics: ${error.message || error}
                </div>
            `;
        }
    };
    
    Dashboard.showHealthError = function(error) {
        const container = document.getElementById('health-status');
        if (container) {
            container.innerHTML = `
                <div class="status-badge status-disabled">
                    <div class="status-indicator"></div>
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Error
                </div>
                <small class="text-danger d-block mt-2">
                    ${error.message || error}
                </small>
            `;
        }
    };
    
    /**
     * =====================================================================
     * Auto-refresh Management
     * =====================================================================
     */
    Dashboard.startAutoRefresh = function() {
        if (this.autoRefreshEnabled && !this.refreshInterval) {
            this.refreshInterval = setInterval(() => {
                this.refreshStats();
            }, this.refreshIntervalMs);
            
            console.log(`🔄 Started dashboard auto-refresh (${this.refreshIntervalMs}ms)`);
        }
    };
    
    Dashboard.stopAutoRefresh = function() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
            console.log('⏹️ Stopped dashboard auto-refresh');
        }
        // Also stop global health indicator auto-refresh
        SurfeApp.autoRefresh.stop('health-indicator');
    };
    
    Dashboard.toggleAutoRefresh = function(enabled) {
        this.autoRefreshEnabled = enabled;
        
        if (enabled) {
            this.startAutoRefresh();
            SurfeApp.ui.showToast('Auto-refresh enabled', 'info');
        } else {
            this.stopAutoRefresh();
            SurfeApp.ui.showToast('Auto-refresh disabled', 'info');
        }
    };
    
    /**
     * =====================================================================
     * Additional Features
     * =====================================================================
     */
    Dashboard.testApiHealth = function() {
        const testBtn = document.getElementById('test-api');
        if (testBtn) {
            testBtn.disabled = true;
            testBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Testing...';
        }
        
        SurfeApp.api.getHealthCheck()
            .then(health => {
                const status = health.status || 'unknown';
                const message = status === 'healthy' ? 
                    'API is functioning normally' : 
                    'API has issues that need attention';
                
                SurfeApp.ui.showToast(message, status === 'healthy' ? 'success' : 'warning');
            })
            .catch(error => {
                SurfeApp.ui.showToast('API test failed', 'error');
            })
            .finally(() => {
                if (testBtn) {
                    testBtn.disabled = false;
                    testBtn.innerHTML = '<i class="fas fa-stethoscope me-2"></i>Test API';
                }
            });
    };
    
    Dashboard.exportStats = function() {
        Promise.all([
            SurfeApp.api.getStats(),
            SurfeApp.api.getHealthCheck()
        ])
        .then(([stats, health]) => {
            const exportData = {
                timestamp: new Date().toISOString(),
                stats: stats,
                health: health
            };
            
            const timestamp = new Date().toISOString().split('T')[0];
            SurfeApp.export.toJson(exportData, `dashboard_stats_${timestamp}.json`);
        })
        .catch(error => {
            SurfeApp.ui.showToast('Failed to export stats', 'error');
        });
    };
    
    /**
     * =====================================================================
     * UI Helper Functions
     * =====================================================================
     */
    Dashboard.updateRefreshButton = function(isLoading) {
        const refreshBtn = document.getElementById('refresh-stats');
        if (!refreshBtn) return;
        
        if (isLoading) {
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Refreshing...';
        } else {
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Refresh';
        }
    };
    
    Dashboard.updateLastRefreshTime = function() {
        const element = document.getElementById('last-refresh-time');
        if (element) {
            element.textContent = new Date().toLocaleTimeString();
        }
    };
    
    Dashboard.animateValue = function(element, start, end, duration = 1000) {
        const startNum = parseFloat(start) || 0;
        const endNum = parseFloat(end) || 0;
        
        if (startNum === endNum) {
            element.textContent = end;
            return;
        }
        
        const range = endNum - startNum;
        const increment = range / (duration / 16); // 60fps
        let current = startNum;
        
        const timer = setInterval(() => {
            current += increment;
            
            if ((increment > 0 && current >= endNum) || (increment < 0 && current <= endNum)) {
                current = endNum;
                clearInterval(timer);
            }
            
            element.textContent = typeof end === 'string' && end.includes('%') ? 
                `${current.toFixed(1)}%` : 
                Math.round(current);
        }, 16);
    };
    
    /**
     * =====================================================================
     * Cleanup
     * =====================================================================
     */
    Dashboard.destroy = function() {
        this.stopAutoRefresh();
        console.log('📊 Dashboard module destroyed');
    };
    
    /**
     * =====================================================================
     * Auto-initialize when DOM is ready
     * =====================================================================
     */
    document.addEventListener('DOMContentLoaded', function() {
        // Only initialize on dashboard page
        if (document.getElementById('dashboard-container') || 
            document.getElementById('stats-overview')) {
            Dashboard.init();
        }
    });
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', function() {
        Dashboard.destroy();
    });
    
    // Export module for external access
    window.Dashboard = Dashboard;
    
})();
