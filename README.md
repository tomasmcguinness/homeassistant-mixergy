# Home Assistant Mixergy Smart Hot Water Tank Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

Add support for Mixergy's smart water tank into Home Assistant. This integration will return the current temperatures at the the top and bottom of the tank, the tank's current charge, the state of the heating and the energy used by the direct heating element. It also has sensors to report low charge (< 5%) and no change (0%).

![image](https://user-images.githubusercontent.com/302741/130429951-3d47f5c1-39e7-40c7-a160-006615383735.png)

## Support

If you want to support this project, please consider buying me a coffee!

<a href='https://ko-fi.com/G2G11TQK5' target='_blank'><img height='36' style='border:0px;height:36px;' src='https://cdn.ko-fi.com/cdn/kofi2.png?v=3' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>

## Installation

### HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=tomasmcguinness&repository=homeassistant-mixergy&category=integration)

To install via HACS, you must first add the repository and then add the integration.

### Manually

Alternatively, you can copy the contents of the mixergy folder into your custom_components directory.

## Setup

Once installed, the integration will then be available as an integration you can install.

![image](https://user-images.githubusercontent.com/302741/130430354-cbe935cc-fa55-4cec-bcb2-333409e7ebdd.png)

You then need to provide your Mixergy credentials and the serial number of your tank. You can find the serial number physically on the tank, or via [mixergy.io](https://www.mixergy.io/).

![image](https://user-images.githubusercontent.com/302741/130430401-7499d0f8-872c-4062-a743-49d5fd686fcd.png)

## Services

This integration offers two services:

`mixergy.mixergy_set_charge` - This boosts the hot water to the desired percentage.
`mixergy.mixergy_cancel_charge` - This sets the target change to 0, cancelling a boost.
`mixergy.mixergy_set_target_temperature` - Sets the desired hot water temperature.
`mixergy.mixergy_set_holiday_dates` - Set the holiday mode start and end dates.
`mixergy.mixergy_clear_holiday_dates` - Clears the holiday dates, taking the tank out of holiday mode.
`mixergy_set_default_heat_source` - Changes the tank's default heat source.

![image](https://user-images.githubusercontent.com/302741/134326151-7e1583fe-f3b7-482f-82ab-016f2f662cb6.png)

## Lovelace Card

I has created a Love Lace card to give a visual representation of your Mixergy Tank.

![image](https://github.com/user-attachments/assets/fb46e762-0f34-4ed8-a7e2-6a02111e6903)

### Installation

To install this card, start by copying the `www/mixergy-card.js` file into your Home Assistant's `www` folder.

In Home Assistant, go to Settings > Dashboards. Click on the three-dot menu, in the rop right, and choose Resources.

Then click the "Add Resource" button.

Enter the URL as `/local/mixergy-card.js` and select `Javascript Module` as the Resource Type.

Click `Create`. You should then be able to add the Mixergy card into your dashboards.

```
type: custom:mixergy-card
entity_current_charge: sensor.mixergy_current_charge
```

> [!TIP]
> You can only reference this card using YAML at this time. I want to find out how to deploy this card as a HACS package to make installation easier.

## Improvements

This integration is useful as it provides the state of your Mixergy tank via the API, but there are numerous enhancements I would like to make.

* ~~Add the component to HACS~~
* ~~Add to the HACS default repository list (There is a PR open for this)~~
* ~~Add a service to enable the charge to be set, so you can boost via HA~~
* ~~Put better icons into the status~~
* Ensure authentication token expiry is handled correctly. (Been told the token doesn't expire at present)
* ~~Create a nice Lovelace card that provides a visual representation of the tank's state.~~
* Add the Card as a HACS package.
* Get this component merged into the HomeAssistant core?
* Update the Mixergy icon and support dark mode
* ~~Get the Mixergy icon added, to improve the installation~~
* ~~Support *away* by controlling tank's holiday mode~~


