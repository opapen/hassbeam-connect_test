class HassbeamConnectCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.isListening = false;
  }

  setConfig(config) {
    if (!config) {
      throw new Error('Invalid configuration');
    }
    this.config = config;
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
    this.updateUI();
  }

  render() {
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          padding: 16px;
        }
        
        .card {
          background: var(--card-background-color, #fff);
          border-radius: var(--ha-card-border-radius, 12px);
          box-shadow: var(--ha-card-box-shadow, none);
          border: var(--ha-card-border-width, 1px) solid var(--divider-color);
          padding: 16px;
        }
        
        .header {
          display: flex;
          align-items: center;
          margin-bottom: 16px;
        }
        
        .icon {
          width: 24px;
          height: 24px;
          margin-right: 8px;
          color: var(--primary-color);
        }
        
        .title {
          font-size: 20px;
          font-weight: 500;
          color: var(--primary-text-color);
        }
        
        .form-group {
          margin-bottom: 16px;
        }
        
        .form-group label {
          display: block;
          margin-bottom: 4px;
          font-weight: 500;
          color: var(--primary-text-color);
        }
        
        .form-group input {
          width: 100%;
          padding: 8px 12px;
          border: 1px solid var(--divider-color);
          border-radius: 8px;
          font-size: 14px;
          background: var(--card-background-color);
          color: var(--primary-text-color);
          box-sizing: border-box;
        }
        
        .form-group input:focus {
          outline: none;
          border-color: var(--primary-color);
          box-shadow: 0 0 0 2px rgba(var(--rgb-primary-color), 0.2);
        }
        
        .button-group {
          display: flex;
          gap: 8px;
          margin-top: 16px;
        }
        
        .btn {
          flex: 1;
          padding: 12px 16px;
          border: none;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
        }
        
        .btn-primary {
          background: var(--primary-color);
          color: var(--text-primary-color);
        }
        
        .btn-primary:hover {
          opacity: 0.9;
        }
        
        .btn-primary:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        
        .btn-secondary {
          background: var(--secondary-background-color);
          color: var(--primary-text-color);
          border: 1px solid var(--divider-color);
        }
        
        .btn-secondary:hover {
          background: var(--divider-color);
        }
        
        .status {
          margin-top: 16px;
          padding: 12px;
          border-radius: 8px;
          font-size: 14px;
          text-align: center;
        }
        
        .status.listening {
          background: #e3f2fd;
          color: #1976d2;
          border: 1px solid #bbdefb;
        }
        
        .status.success {
          background: #e8f5e8;
          color: #2e7d32;
          border: 1px solid #c8e6c9;
        }
        
        .status.error {
          background: #ffebee;
          color: #c62828;
          border: 1px solid #ffcdd2;
        }
        
        .status.info {
          background: var(--secondary-background-color);
          color: var(--primary-text-color);
          border: 1px solid var(--divider-color);
        }
        
        .pulse {
          animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.5; }
          100% { opacity: 1; }
        }
        
        .recent-codes {
          margin-top: 24px;
          padding-top: 16px;
          border-top: 1px solid var(--divider-color);
        }
        
        .recent-codes h3 {
          margin: 0 0 12px 0;
          font-size: 16px;
          color: var(--primary-text-color);
        }
        
        .code-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 0;
          border-bottom: 1px solid var(--divider-color);
        }
        
        .code-item:last-child {
          border-bottom: none;
        }
        
        .code-info {
          flex: 1;
        }
        
        .code-device {
          font-weight: 500;
          color: var(--primary-text-color);
        }
        
        .code-action {
          font-size: 12px;
          color: var(--secondary-text-color);
        }
        
        .code-time {
          font-size: 12px;
          color: var(--secondary-text-color);
        }
      </style>
      
      <div class="card">
        <div class="header">
          <svg class="icon" viewBox="0 0 24 24">
            <path fill="currentColor" d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4M12,6A6,6 0 0,0 6,12A6,6 0 0,0 12,18A6,6 0 0,0 18,12A6,6 0 0,0 12,6M12,8A4,4 0 0,1 16,12A4,4 0 0,1 12,16A4,4 0 0,1 8,12A4,4 0 0,1 12,8Z"/>
          </svg>
          <span class="title">Hassbeam Connect</span>
        </div>
        
        <div class="form-group">
          <label for="device">Gerät:</label>
          <input type="text" id="device" placeholder="z.B. TV, Soundbar, Klimaanlage" />
        </div>
        
        <div class="form-group">
          <label for="action">Aktion:</label>
          <input type="text" id="action" placeholder="z.B. power, volume_up, channel_1" />
        </div>
        
        <div class="button-group">
          <button class="btn btn-primary" id="startBtn">
            🎯 IR-Code aufnehmen
          </button>
          <button class="btn btn-secondary" id="refreshBtn">
            🔄 Aktualisieren
          </button>
        </div>
        
        <div id="status" class="status info" style="display: none;">
          Bereit zum Aufnehmen
        </div>
        
        <div class="recent-codes">
          <h3>Zuletzt aufgenommene Codes</h3>
          <div id="recentCodes">
            <div class="code-item">
              <div class="code-info">
                <div class="code-device">Noch keine Codes aufgenommen</div>
                <div class="code-action">Verwenden Sie die Aufnahmefunktion oben</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
    
    this.setupEventListeners();
  }

  setupEventListeners() {
    const startBtn = this.shadowRoot.getElementById('startBtn');
    const refreshBtn = this.shadowRoot.getElementById('refreshBtn');
    const deviceInput = this.shadowRoot.getElementById('device');
    const actionInput = this.shadowRoot.getElementById('action');

    startBtn.addEventListener('click', () => this.startListening());
    refreshBtn.addEventListener('click', () => this.refresh());
    
    // Enter key support
    [deviceInput, actionInput].forEach(input => {
      input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          this.startListening();
        }
      });
    });

    // Listen for events
    if (this._hass) {
      this._hass.connection.subscribeEvents((event) => {
        if (event.event_type === 'hassbeam_connect_saved') {
          this.onCodeSaved(event.data);
        } else if (event.event_type === 'hassbeam_connect_codes_retrieved') {
          this.onCodesRetrieved(event.data.codes);
        }
      }, ['hassbeam_connect_saved', 'hassbeam_connect_codes_retrieved']);
    }
    
    // Load recent codes on startup
    setTimeout(() => this.loadRecentCodes(), 1000);
  }

  startListening() {
    const device = this.shadowRoot.getElementById('device').value.trim();
    const action = this.shadowRoot.getElementById('action').value.trim();
    
    if (!device || !action) {
      this.showStatus('Bitte geben Sie Gerät und Aktion ein', 'error');
      return;
    }

    this.isListening = true;
    this.updateUI();
    
    // Call the Home Assistant service
    this._hass.callService('hassbeam_connect', 'start_listening', {
      device: device,
      action: action
    }).then(() => {
      this.showStatus(`🎯 Warte auf IR-Signal für "${device} - ${action}"...`, 'listening');
    }).catch((error) => {
      this.isListening = false;
      this.updateUI();
      this.showStatus(`Fehler: ${error.message}`, 'error');
    });
  }

  onCodeSaved(data) {
    this.isListening = false;
    this.updateUI();
    this.showStatus(`✅ IR-Code für "${data.device} - ${data.action}" erfolgreich gespeichert!`, 'success');
    
    // Clear inputs
    this.shadowRoot.getElementById('device').value = '';
    this.shadowRoot.getElementById('action').value = '';
    
    // Refresh the recent codes list
    setTimeout(() => this.loadRecentCodes(), 500);
  }

  refresh() {
    this.loadRecentCodes();
    this.showStatus('Aktualisiert', 'info');
  }

  loadRecentCodes() {
    if (!this._hass) return;
    
    // Call the service to get recent codes
    this._hass.callService('hassbeam_connect', 'get_recent_codes', {
      limit: 5
    }).catch((error) => {
      console.warn('Could not load recent codes:', error);
      this.showMockCodes();
    });
  }

  onCodesRetrieved(codes) {
    const recentCodesDiv = this.shadowRoot.getElementById('recentCodes');
    
    if (!codes || codes.length === 0) {
      recentCodesDiv.innerHTML = `
        <div class="code-item">
          <div class="code-info">
            <div class="code-device">Noch keine Codes aufgenommen</div>
            <div class="code-action">Verwenden Sie die Aufnahmefunktion oben</div>
          </div>
        </div>
      `;
    } else {
      recentCodesDiv.innerHTML = codes.map(code => `
        <div class="code-item">
          <div class="code-info">
            <div class="code-device">${code.device}</div>
            <div class="code-action">${code.action}</div>
          </div>
          <div class="code-time">${this.formatTime(code.created_at)}</div>
        </div>
      `).join('');
    }
  }

  showMockCodes() {
    const recentCodesDiv = this.shadowRoot.getElementById('recentCodes');
    recentCodesDiv.innerHTML = `
      <div class="code-item">
        <div class="code-info">
          <div class="code-device">Service nicht verfügbar</div>
          <div class="code-action">Integration überprüfen</div>
        </div>
      </div>
    `;
  }

  formatTime(timestamp) {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString('de-DE', { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    } catch {
      return 'Kürzlich';
    }
  }

  showStatus(message, type) {
    const statusDiv = this.shadowRoot.getElementById('status');
    statusDiv.textContent = message;
    statusDiv.className = `status ${type}`;
    statusDiv.style.display = 'block';
    
    if (type === 'listening') {
      statusDiv.classList.add('pulse');
    } else {
      statusDiv.classList.remove('pulse');
    }
    
    // Auto-hide info and success messages
    if (type === 'info' || type === 'success') {
      setTimeout(() => {
        statusDiv.style.display = 'none';
      }, 3000);
    }
  }

  updateUI() {
    const startBtn = this.shadowRoot.getElementById('startBtn');
    const deviceInput = this.shadowRoot.getElementById('device');
    const actionInput = this.shadowRoot.getElementById('action');
    
    if (this.isListening) {
      startBtn.textContent = '⏳ Warte auf IR-Signal...';
      startBtn.disabled = true;
      deviceInput.disabled = true;
      actionInput.disabled = true;
    } else {
      startBtn.textContent = '🎯 IR-Code aufnehmen';
      startBtn.disabled = false;
      deviceInput.disabled = false;
      actionInput.disabled = false;
    }
  }

  getCardSize() {
    return 4;
  }

  static getConfigElement() {
    return document.createElement('hassbeam-connect-card-editor');
  }

  static getStubConfig() {
    return {};
  }
}

// Card Editor (optional, for UI configuration)
class HassbeamConnectCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = config;
    this.render();
  }

  render() {
    this.innerHTML = `
      <div style="padding: 16px;">
        <h3>Hassbeam Connect Karte</h3>
        <p>Diese Karte benötigt keine Konfiguration.</p>
        <p>Stellen Sie sicher, dass die Hassbeam Connect Integration installiert und konfiguriert ist.</p>
      </div>
    `;
  }

  get value() {
    return this._config;
  }
}

// Register the custom elements
customElements.define('hassbeam-connect-card', HassbeamConnectCard);
customElements.define('hassbeam-connect-card-editor', HassbeamConnectCardEditor);

// Register with the card picker
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'hassbeam-connect-card',
  name: 'Hassbeam Connect Karte',
  description: 'Karte zum Aufnehmen von IR-Codes mit Hassbeam Connect',
  preview: true,
  documentationURL: 'https://github.com/BasilBerg/hassbeam-connect'
});

console.info('Hassbeam Connect Card loaded successfully');
