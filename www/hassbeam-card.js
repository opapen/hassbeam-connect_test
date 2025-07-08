class HassBeamConnectCard extends HTMLElement {
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
      hass.callService("hassbeam_connect", "start_listening", {
        device: device,
        action: action
      });
      this.querySelector("#status").innerText = "Warte auf IR-Event...";
    };

    hass.connection.subscribeEvents((event) => {
      this.querySelector("#status").innerText = `Gespeichert: ${event.data.device} - ${event.data.action}`;
      this.querySelector("#action").value = "";
    }, "hassbeam_connect_saved");
  }

  setConfig() { }
  getCardSize() { return 1; }
}

customElements.define('hassbeam-connect-card', HassBeamConnectCard);
