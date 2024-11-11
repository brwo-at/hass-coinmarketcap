# CoinMarketCap Integration for Home Assistant

This custom integration allows you to track cryptocurrency prices and your portfolio value using the CoinMarketCap API in Home Assistant.

## Features

- Track prices of multiple cryptocurrencies
- Set custom amounts for each cryptocurrency to calculate portfolio value
- Configurable update interval
- Support for custom/unlisted cryptocurrencies

## Installation

1. Copy the `coinmarketcap` folder to your `custom_components` directory in your Home Assistant configuration directory.
   - If you don't have a `custom_components` directory, you'll need to create one.
2. Restart Home Assistant.

## Configuration

1. In the Home Assistant UI, go to "Configuration" -> "Integrations".
2. Click the "+" button to add a new integration.
3. Search for "CoinMarketCap" and select it.
4. Follow the configuration steps:
   - Enter your CoinMarketCap API key.
   - Select the cryptocurrencies you want to track.
   - (Optional) Add custom cryptocurrencies.
   - Enter the amounts of each cryptocurrency you own.
   - Choose your preferred currency and update interval.

## Usage

After configuration, the integration will create sensors for each tracked cryptocurrency. The sensor state will represent the current value of your holdings in the selected currency.

Sensor attributes include:
- `cryptocurrency`: The symbol of the cryptocurrency
- `amount`: The amount of the cryptocurrency you own
- `price`: The current price of the cryptocurrency

## Troubleshooting

If you encounter any issues:
1. Check the Home Assistant logs for any error messages related to the CoinMarketCap integration.
2. Ensure your CoinMarketCap API key is valid and has the necessary permissions.
3. Verify that your network allows connections to the CoinMarketCap API.

## Contributing

Contributions to improve the integration are welcome. Please feel free to submit pull requests or open issues on the GitHub repository.

## Disclaimer

This integration is not officially affiliated with CoinMarketCap. Use at your own risk. Cryptocurrency prices can be volatile, and this integration should not be used as financial advice.

## License

This project is licensed under the MIT License - see the LICENSE file for details.