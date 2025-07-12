// This object holds the shared data for the application.
const _state = {
    systemStatus: {
        total_keys: 0,
        enabled_keys: 0,
        has_valid_selection: false,
        selected_key: null
    }
};

// A list of functions to call when the state changes.
const listeners = [];

// The main export object.
const appState = {
    /**
     * Allows other parts of the app to get the current status.
     */
    getStatus: () => _state.systemStatus,

    /**
     * Updates the status and notifies all listeners.
     * @param {object} newStatus - The new status object from the API.
     */
    updateStatus: (newStatus) => {
        console.log('🚀 State updated:', newStatus);
        // This line is now correctly using '_state'
        _state.systemStatus = newStatus;
        appState.notifyListeners();
    },

    /**
     * Allows components to register a function to be called on state changes.
     * @param {function} callback - The function to call when state is updated.
     */
    subscribe: (callback) => {
        listeners.push(callback);
    },

    /**
     * Calls all the registered listener functions.
     */
    notifyListeners: () => {
        for (const listener of listeners) {
            listener(_state.systemStatus);
        }
    }
};

// Make the appState object available to other files.
window.appState = appState;