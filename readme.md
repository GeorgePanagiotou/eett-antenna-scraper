# EETT Antenna Scraper

A Python web scraper for extracting antenna data from the Greek National Telecommunications and Post Commission (EETT) website.

## Description

This tool scrapes antenna installation data from the official EETT database at https://keraies.eett.gr/. It can search for antennas by municipality and export the results to CSV and Excel formats.

## Features

- Search for antennas by municipality name
- Pagination support for large datasets
- Export to both CSV and Excel formats
- Comprehensive error handling and debugging
- Respectful scraping with built-in delays
- Greek language support

## Installation

1. Clone this repository:
```bash
git clone https://github.com/GeorgePanagiotou/eett-antenna-scraper.git
cd eett-antenna-scraper
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Search for antennas in a specific municipality:
```bash
python eett_scraper.py "Αθηναίων"
```

### Advanced Usage

Limit the number of pages to scrape:
```bash
python eett_scraper.py "Χαλκιδέων" 5
```

List available municipalities:
```bash
python eett_scraper.py --list
```

### Command Line Arguments

- `municipality_name`: Name of the municipality to search (required)
- `max_pages`: Maximum number of pages to scrape (optional)
- `--list` or `-l`: List all available municipalities

## Output

The scraper generates two files:
- `antennas_{municipality_name}.csv`: CSV format
- `antennas_{municipality_name}.xlsx`: Excel format

### Data Fields

Each antenna record includes:
- `sequence`: Sequential number
- `position_code`: Unique position code
- `category`: Antenna category
- `company`: Operating company
- `address`: Installation address
- `municipality`: Municipality name

## Examples

```bash
# Search for antennas in Athens
python eett_scraper.py "Αθηναίων"

# Search first 3 pages in Thessaloniki
python eett_scraper.py "Θεσσαλονίκης" 3

# List all available municipalities
python eett_scraper.py --list
```

## Requirements

- Python 3.6+
- requests
- pandas
- beautifulsoup4
- openpyxl (for Excel export)

## Legal and Ethical Considerations

- This scraper respects the EETT website's terms of service
- Built-in delays prevent server overload
- Data is publicly available on the EETT website
- Use responsibly and in accordance with Greek law

## Troubleshooting

### Common Issues

1. **No data found**: 
   - Check municipality name spelling
   - Use `--list` to see available municipalities
   - Verify website accessibility

2. **Connection errors**:
   - Check internet connection
   - Website may be temporarily unavailable

3. **Parsing errors**:
   - Website structure may have changed
   - Check debug output files for analysis

### Debug Mode

The scraper automatically saves debug HTML files for the first two pages to help with troubleshooting.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for educational and research purposes. Users are responsible for ensuring their use complies with applicable laws and the website's terms of service.

## Changelog

### Version 1.0.0
- Initial release
- Basic municipality search functionality
- CSV and Excel export
- Pagination support
- Error handling and debugging features

## Support

If you encounter any issues or have questions, please open an issue on GitHub.
