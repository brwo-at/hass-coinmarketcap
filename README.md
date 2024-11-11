# CoinMarketCap Integration for Home Assistant

This custom integration allows you to track cryptocurrency prices from CoinMarketCap in your Home Assistant instance.

## Features

- Track multiple cryptocurrencies
- Customizable update interval
- Support for different fiat currencies
- Calculate total value based on owned coin amounts
- Add custom cryptocurrencies not in the predefined list

## Installation

### Option 1: HACS (Recommended)

1. Make sure you have [HACS](https://hacs.xyz/) installed in your Home Assistant instance.
2. Add this repository to HACS:
   [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=brwo-at&repository=hass-coinmarketcap&category=integration)
3. Search for "CoinMarketCap" in the Integrations tab of HACS and install it.
4. Restart Home Assistant.

### Option 2: Manual Installation

1. Copy the `coinmarketcap` folder from this repository to your `config/custom_components` directory.
2. Restart Home Assistant.

## Configuration

1. In Home Assistant, go to Configuration -> Integrations.
2. Click the "+" button to add a new integration.
3. Search for "CoinMarketCap" and select it.
4. Follow the configuration steps:
   - Enter your CoinMarketCap API key
   - Select the cryptocurrencies you want to track
   - Enter the amounts of each cryptocurrency you own (optional)
   - Choose your preferred fiat currency
   - Set the update interval

## API Key

This integration requires a CoinMarketCap API key. You can obtain one for free at [https://coinmarketcap.com/api/](https://coinmarketcap.com/api/).

Please note that the free API has usage limits. Check CoinMarketCap's documentation for details.

## Sensors

For each configured cryptocurrency, the integration will create a sensor with the following attributes:
- State: Current value of your holdings in the selected fiat currency
- Attributes:
  - `cryptocurrency`: Symbol of the cryptocurrency
  - `amount`: Amount of the cryptocurrency you own
  - `price`: Current price of the cryptocurrency in the selected fiat currency

## Localization

This integration supports both English and German languages. The language will be automatically selected based on your Home Assistant configuration.

## Support

If you encounter any issues or have suggestions for improvements, please open an issue on the [GitHub repository](https://github.com/brwo-at/hass-coinmarketcap/issues).

## Disclaimer

This integration is not officially associated with CoinMarketCap. Use at your own risk.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.