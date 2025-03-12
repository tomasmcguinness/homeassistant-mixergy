import "https://unpkg.com/wired-card@0.8.1/wired-card.js?module";
import "https://unpkg.com/wired-toggle@0.8.0/wired-toggle.js?module";
import {
    LitElement,
    html,
    css
} from "https://unpkg.com/lit-element@2.0.1/lit-element.js?module";

class MixergyCard extends LitElement {
    static get properties() {
        return {
            hass: {},
            config: {}
        };
    }

    render() {
        return html`
      <ha-card header="Mixergy">
      <div class="content">
          <div class="tank">
        ${html`
        <div class="hot-water" style="height: ${this.getHeight()}">
        </div>
        <div class="hot-water-percentage">
          ${this.getPercentage()}
        </div>
        `}
        </div>
        </div>
      </ha-card>
    `;
    }

    getPercentage() {
        let entity = this.config.entity_current_charge;
        let state = this.hass.states[entity];
        let percentage = parseFloat(state.state);
        return Math.floor(percentage) + "%";
    }

    getHeight() {
        let entity = this.config.entity_current_charge;
        let state = this.hass.states[entity];
        let percentage = parseFloat(state.state) / 100;
        let height = Math.floor(300 * (1 - percentage));
        return height + "px";
    }

    getOffset() {
        let entity = this.config.entity_current_charge;
        let state = this.hass.states[entity];
        let percentage = parseFloat(state.state) / 100;
        let size = Math.floor(300 - (300 * percentage));
        return size + 1 + "px";
    }

    setConfig(config) {
        if (!config.entity_current_charge) {
            throw new Error("You need to define entities");
        }
        this.config = config;
    }

    // The height of your card. Home Assistant uses this to automatically
    // distribute all cards over the available columns.
    getCardSize() {
        return 5;
    }

    static get styles() {
        return css`
      ha-card {
        display: block;
        font-size: 18px;
      }
 
      .content {
        display: flex;
        flex-direction: column;
        align-items: center;
      }
 
      ha-card h1.card-header {
        align-self: start !important;
      }
 
      .tank {
        background-color: #ff0000;
        height: 300px;
        width: 120px;
        border-radius: 5px;
        margin-bottom: 20px;
	      display: grid;
      }
 
      .hot-water {
        align-self: flex-end;
        background-color: #00008b;
        width: 120px;
        border-radius: 5px;
        align-items: center;
        justify-content: center;
        font-weight: bold;
	      grid-row: 1;
	      grid-column: 1;
      }
 
      .hot-water-percentage {
        align-self: center;
        justify-self: center;
        text-align: center;
        font-weight: bold;
        font-size: large;
        grid-row: 1;
        grid-column: 1;
      }
    `;
    }
}
customElements.define("mixergy-card", MixergyCard);
Advertisement
