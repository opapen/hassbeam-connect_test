console.info("HassBeam Card geladen");

class HassBeamCard extends HTMLElement {
  setConfig(config) {
    this.config = config;
    this.innerHTML = `
      <ha-card header="${config.title || 'HassBeam Card'}">
        <div class="card-content">
          <p>Letztes IR-Event: <span id="ir-event">Wird geladen...</span></p>
        </div>
      </ha-card>
    `;
  }

  set hass(hass) {
    const event = hass.states['sensor.hassbeam_last_ir'];
    const el = this.querySelector('#ir-event');
    if (event && el) {
      el.innerText = event.state;
    } else if (el) {
      el.innerText = "Kein Event verfügbar";
    }
  }

  getCardSize() {
    return 1;
  }
}

customElements.define('hassbeam-card', HassBeamCard);