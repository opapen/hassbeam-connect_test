class IRCodeLoggerCard extends HTMLElement {
  set hass(hass) {
    this.innerHTML = `
      <div style="padding: 16px;">
        <label>Gerät:</label><br/>
        <input id="device" type="text"><br/><br/>
        <label>Aktion:</label><br/>
        <input id="action" type="text"><br/><br/>
        <button id="listen">IR-Code speichern</button>
        <p id="status"></p>
      </div>
    `;

    this.querySelector('#listen').onclick = () => {
      const device = this.querySelector("#device").value;
      const action = this.querySelector("#action").value;
      hass.callService("ir_code_logger", "start_listening", {
        device: device,
        action: action
      });
      this.querySelector("#status").innerText = "Warte auf IR-Event...";
    };

    hass.connection.subscribeEvents((event) => {
      this.querySelector("#status").innerText = `Gespeichert: ${event.data.device} - ${event.data.action}`;
      this.querySelector("#action").value = "";
    }, "ir_code_logger_saved");
  }

  setConfig() { }
  getCardSize() { return 1; }
}

customElements.define('ir-code-logger-card', IRCodeLoggerCard);
