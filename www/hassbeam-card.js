/**
 * Hassbeam Connect Card for Home Assistant
 * Automatically captures IR codes from remote controls
 */

// IIFE um sicherzustellen, dass die Karte nur einmal registriert wird
(function() {
  'use strict';
  
  // Prüfen ob bereits registriert
  if (window.customCards && window.customCards.find(card => card.type === "hassbeam-connect-card")) {
    console.info("Hassbeam Connect Card bereits registriert");
    return;
  }
  
  // Automatische Karten-Registrierung
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "hassbeam-connect-card",
    name: "Hassbeam Connect Card",
    description: "Capture IR codes from remote controls using HassBeam device",
    preview: true,
    documentationURL: "https://github.com/BasilBerg/hassbeam-connect"
  });
  
  console.info("✅ Hassbeam Connect Card registriert");

})();

class HassBeamConnectCard extends HTMLElement {
  constructor() {
    super();
    this._initialized = false;
    this._eventListener = null;
  }

  static getConfigElement() {
    return document.createElement("hassbeam-connect-card-config");
  }

  static getStubConfig() {
    return {
      type: "custom:hassbeam-connect-card",
      name: "Hassbeam Connect"
    };
  }

  connectedCallback() {
    console.log("Hassbeam Connect Card connected");
  }

  disconnectedCallback() {
    if (this._eventListener && this._hass) {
      this._hass.connection.unsubscribeEvents(this._eventListener);
    }
  }

  set hass(hass) {
    this._hass = hass;
    
    if (!this._initialized) {
      this._initialize();
      this._setupEventListeners();
      this._initialized = true;
    }
  }

  _initialize() {
    this.innerHTML = `
      <ha-card header="Hassbeam Connect - IR Code Capture">
        <div class="card-content">
          <div class="input-group">
            <label for="device">Gerät (Device):</label>
            <input id="device" type="text" placeholder="z.B. TV, AC, Soundbar" />
          </div>
          
          <div class="input-group">
            <label for="action">Aktion (Action):</label>
            <input id="action" type="text" placeholder="z.B. power, volume_up, ch1" />
          </div>
          
          <div class="button-group">
            <button id="listen" class="primary">IR-Code speichern</button>
            <button id="clear" class="secondary">Felder leeren</button>
          </div>
          
          <div id="status" class="status-message"></div>
        </div>
      </ha-card>
      
      <style>
        ha-card {
          padding: 16px;
        }
        
        .input-group {
          margin-bottom: 16px;
        }
        
        .input-group label {
          display: block;
          margin-bottom: 4px;
          font-weight: 500;
        }
        
        .input-group input {
          width: 100%;
          padding: 8px;
          border: 1px solid var(--divider-color);
          border-radius: 4px;
          font-size: 14px;
        }
        
        .button-group {
          display: flex;
          gap: 8px;
          margin-bottom: 16px;
        }
        
        button {
          padding: 10px 16px;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
          flex: 1;
        }
        
        button.primary {
          background-color: var(--primary-color);
          color: var(--text-primary-color);
        }
        
        button.secondary {
          background-color: var(--secondary-background-color);
          color: var(--primary-text-color);
          border: 1px solid var(--divider-color);
        }
        
        button:hover {
          opacity: 0.8;
        }
        
        button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        
        .status-message {
          padding: 8px;
          border-radius: 4px;
          font-size: 14px;
          min-height: 20px;
        }
        
        .status-message.waiting {
          background-color: var(--info-color);
          color: white;
        }
        
        .status-message.success {
          background-color: var(--success-color);
          color: white;
        }
        
        .status-message.error {
          background-color: var(--error-color);
          color: white;
        }
      </style>
    `;
  }

  _setupEventListeners() {
    const listenButton = this.querySelector('#listen');
    const clearButton = this.querySelector('#clear');
    const deviceInput = this.querySelector('#device');
    const actionInput = this.querySelector('#action');
    const statusDiv = this.querySelector('#status');

    // Listen button click
    listenButton.onclick = () => {
      const device = deviceInput.value.trim();
      const action = actionInput.value.trim();
      
      if (!device || !action) {
        this._showStatus('Bitte geben Sie Gerät und Aktion ein', 'error');
        return;
      }
      
      // Disable button while listening
      listenButton.disabled = true;
      listenButton.textContent = 'Warte auf IR-Signal...';
      
      // Call the service
      this._hass.callService("hassbeam_connect", "start_listening", {
        device: device,
        action: action
      }).then(() => {
        this._showStatus(`Warte auf IR-Event für ${device}.${action}...`, 'waiting');
      }).catch((error) => {
        this._showStatus(`Fehler: ${error.message}`, 'error');
        this._resetButton(listenButton);
      });
    };

    // Clear button click
    clearButton.onclick = () => {
      deviceInput.value = '';
      actionInput.value = '';
      statusDiv.textContent = '';
      statusDiv.className = 'status-message';
      this._resetButton(listenButton);
    };

    // Listen for success events
    if (this._eventListener) {
      this._hass.connection.unsubscribeEvents(this._eventListener);
    }
    
    this._eventListener = this._hass.connection.subscribeEvents((event) => {
      const { device, action } = event.data;
      this._showStatus(`✅ Gespeichert: ${device} - ${action}`, 'success');
      actionInput.value = ''; // Clear action for next capture
      this._resetButton(listenButton);
    }, "hassbeam_connect_saved");
  }

  _showStatus(message, type = '') {
    const statusDiv = this.querySelector('#status');
    statusDiv.textContent = message;
    statusDiv.className = `status-message ${type}`;
  }

  _resetButton(button) {
    button.disabled = false;
    button.textContent = 'IR-Code speichern';
  }

  setConfig(config) {
    // No configuration needed
  }

  getCardSize() {
    return 3;
  }
}

customElements.define('hassbeam-connect-card', HassBeamConnectCard);
