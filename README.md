# Home Assistant Mixergy Smart Hot Water Tank Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

Add support for Mixergy's smart water tank into Home Assistant. This integration will return the current temperatures at the the top and bottom of the tank, the tank's current charge, and the state of the heating. It also has sensors to report low charge (< 5%) and no change (0%).

![image](https://user-images.githubusercontent.com/302741/130429951-3d47f5c1-39e7-40c7-a160-006615383735.png)

## Installation

At present, this integration can only be installed manually.

Just copy the mixergy folder into your installation's custom_components folder and restart HomeAssistant. The integration will then be available to install via the Integration page of settings

![image](https://user-images.githubusercontent.com/302741/130430354-cbe935cc-fa55-4cec-bcb2-333409e7ebdd.png)

You then need to provide your Mixergy credentials and the serial number of your tank. 

![image](https://user-images.githubusercontent.com/302741/130430401-7499d0f8-872c-4062-a743-49d5fd686fcd.png)

## Services

This integration adds a new service - mixergy.mixergy_set_charge. It allows you to provide a target percentage, which will get passed to the Mixergy API.

![image](https://user-images.githubusercontent.com/302741/134326151-7e1583fe-f3b7-482f-82ab-016f2f662cb6.png)

## Improvements

This integration is useful as it provides the state of your Mixergy tank via the API, but there are numerous enhancements I plan on making over the coming weeks.

* Add the componets to HACS
* ~~Add a service to enable the charge to be set, so you can boost via HA
* ~~Put better icons into the status
* Ensure authentication token expiry is handled correctly. (Been told the token doesn't expire at present)
* Create a nice Lovelace card that provides a visual representation of the tank's state.
* Maybe get this component merged into the HomeAssistant core
* ~~Get the Mixergy icon added, to improve the installation


