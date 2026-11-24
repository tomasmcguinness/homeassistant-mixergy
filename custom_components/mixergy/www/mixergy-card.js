import "https://unpkg.com/wired-card@0.8.1/wired-card.js?module";
import "https://unpkg.com/wired-toggle@0.8.0/wired-toggle.js?module";
import {
    LitElement,
    html,
    css
} from "https://unpkg.com/lit-element@2.0.1/lit-element.js?module";

const translations = new Map();

async function loadTranslations(language) {
    const locale = /^[a-zA-Z0-9_-]+$/.test(language) ? language : "en";
    if (translations.has(locale)) {
        return translations.get(locale);
    }
    const response = await fetch(`/mixergy/translations/${locale}.json`);
    if (response.status === 404 && locale !== "en") {
        translations.set(locale, translations.get("en"));
        return translations.get(locale);
    }
    if (!response.ok) {
        throw new Error(`Failed to load Mixergy translations: ${response.status}`);
    }
    const data = await response.json();
    if (locale === "en" && !data.config_panel?.card) {
        throw new Error("Mixergy card translations are missing from en.json");
    }
    const strings = { ...translations.get("en"), ...data.config_panel?.card };
    translations.set(locale, strings);
    return strings;
}

await loadTranslations("en");
const homeAssistant = document.querySelector("home-assistant");
if (homeAssistant?.hass?.language) {
    await loadTranslations(homeAssistant.hass.language);
}

function localize(language, key, values = {}) {
    const strings = translations.get(language) || translations.get("en");
    return strings[key].replace(/\{(\w+)\}/g, (match, name) => values[name] ?? match);
}

class MixergyCard extends LitElement {
    static get properties() {
        return {
            hass: {},
            config: {}
        };
    }

    render() {
        if (!this.hass || !this.config) {
            return html``;
        }

        const language = this.hass.language || "en";
        const entity = this.config.entity_current_charge;
        const state = this.hass.states[entity];
        if (!state) {
            return html`<ha-card header="Mixergy"><div class="message">
                ${localize(language, "entity_not_found", { entity })}
            </div></ha-card>`;
        }

        const percentage = Number(state.state);
        if (state.state.trim() === "" || !Number.isFinite(percentage)) {
            return html`<ha-card header="Mixergy"><div class="message">
                ${localize(language, "entity_unavailable", { entity, state: state.state })}
            </div></ha-card>`;
        }

        return html`
      <ha-card header="Mixergy">
      <div class="content">
          <div class="tank">
        ${html`
        <div class="hot-water" style="height: ${Math.floor(300 * percentage / 100)}px">
        </div>
        <div class="hot-water-percentage">
          ${Math.floor(percentage)}%
        </div>
        `}
        </div>
        </div>
      </ha-card>
    `;
    }

    updated(changedProperties) {
        super.updated(changedProperties);
        const language = this.hass?.language || "en";
        if (!translations.has(language)) {
            loadTranslations(language).then(
                () => this.requestUpdate(),
                (error) => console.error("Mixergy card: failed to load translations", error)
            );
        }
    }

    setConfig(config) {
        const entity = config.entity_current_charge === undefined
            ? "sensor.current_charge"
            : config.entity_current_charge;
        if (!entity) {
            throw new Error(localize(homeAssistant?.hass?.language || "en", "empty_entity"));
        }
        this.config = { ...config, entity_current_charge: entity };
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

      .message {
        padding: 0 16px 16px;
      }
 
      ha-card h1.card-header {
        align-self: start !important;
      }
 
      .tank {
        background-color: #039be5;
        height: 300px;
        width: 120px;
        border-radius: 5px;
        margin-bottom: 20px;
	      display: grid;
      }
 
      .hot-water {
        align-self: flex-end;
        background-color: red;
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

window.customCards = window.customCards || [];
window.customCards.push({
    type: "mixergy-card",
    name: "Mixergy",
    preview: true,
    get description() {
        return localize(homeAssistant?.hass?.language || "en", "description");
    },
    getEntitySuggestion: (hass, entityId) => {
        if (entityId !== "sensor.current_charge") {
            return null;
        }
        return {
            config: {
                type: "custom:mixergy-card",
                entity_current_charge: entityId,
            },
        };
    },
});
