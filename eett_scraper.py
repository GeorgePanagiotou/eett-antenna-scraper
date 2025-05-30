#!/usr/bin/env python3
"""
EETT Antenna Data Scraper

A web scraper for extracting antenna installation data from the Greek National 
Telecommunications and Post Commission (EETT) website at https://keraies.eett.gr/

This scraper allows you to search for antenna installations by municipality
and export the results to CSV or Excel format.

Author: George Panagiotou
License: MIT
"""

import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import csv
import sys
import os
from urllib.parse import urljoin
import re
import logging
from typing import List, Dict, Optional


class EETTScraper:
    """
    A scraper for the EETT (Greek Telecommunications Commission) antenna database.
    
    This class provides methods to search for antenna installations by municipality
    and extract detailed information about each installation.
    """
    
    def __init__(self, debug: bool = False):
        """
        Initialize the EETT scraper.
        
        Args:
            debug (bool): Enable debug mode for verbose logging
        """
        self.base_url = "https://keraies.eett.gr/"
        self.search_url = "https://keraies.eett.gr/anazhthsh.php"
        self.session = requests.Session()
        self.debug = debug
        
        # Configure logging
        log_level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Set headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'el-GR,el;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://keraies.eett.gr/anazhthsh.php'
        })
    
    def get_municipality_options(self) -> Dict[str, str]:
        """
        Retrieve available municipality options from the search form.
        
        Returns:
            Dict[str, str]: Dictionary mapping municipality names to their form values
        """
        try:
            response = self.session.get(self.search_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            municipality_select = soup.find('select', {'name': 'municipality'})
            
            if municipality_select:
                options = {}
                for option in municipality_select.find_all('option'):
                    value = option.get('value', '')
                    text = option.get_text(strip=True)
                    if value and text and value != '':
                        options[text] = value
                return options
            return {}
            
        except requests.RequestException as e:
            self.logger.error(f"Error getting municipality options: {e}")
            return {}

    def search_municipality(self, municipality_name: str, max_pages: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Search for antenna data in a specific municipality.
        
        Args:
            municipality_name (str): Name of the municipality to search
            max_pages (Optional[int]): Maximum number of pages to scrape (None for all pages)
        
        Returns:
            List[Dict[str, str]]: List of dictionaries containing antenna data
        """
        self.logger.info(f"Searching for antennas in municipality: {municipality_name}")
        
        # Get municipality options to find the correct value
        municipality_options = self.get_municipality_options()
        municipality_value = self._find_municipality_value(municipality_name, municipality_options)
        
        if not municipality_value:
            self.logger.error(f"Municipality '{municipality_name}' not found")
            self._show_available_municipalities(municipality_options)
            return []
        
        # Get search form structure
        search_data = self._prepare_search_data(municipality_value)
        if not search_data:
            return []
        
        return self._scrape_all_pages(search_data, max_pages)
    
    def _find_municipality_value(self, municipality_name: str, municipality_options: Dict[str, str]) -> Optional[str]:
        """Find the form value for a given municipality name."""
        for name, value in municipality_options.items():
            if municipality_name.lower() in name.lower() or name.lower() in municipality_name.lower():
                self.logger.info(f"Found municipality match: {name} (value: {value})")
                return value
        return None
    
    def _show_available_municipalities(self, municipality_options: Dict[str, str]) -> None:
        """Display available municipality options."""
        self.logger.info("Available municipalities (showing first 10):")
        for name in list(municipality_options.keys())[:10]:
            self.logger.info(f"  - {name}")
    
    def _prepare_search_data(self, municipality_value: str) -> Optional[Dict[str, str]]:
        """Prepare the search form data."""
        try:
            response = self.session.get(self.search_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Get hidden form fields
            hidden_inputs = soup.find_all('input', {'type': 'hidden'})
            self.logger.debug(f"Found {len(hidden_inputs)} hidden form fields")
            
            search_data = {
                'address': '',
                'municipality': municipality_value,
                'siteId': '',
            }
            
            # Add hidden form fields
            for hidden_input in hidden_inputs:
                name = hidden_input.get('name')
                value = hidden_input.get('value', '')
                if name:
                    search_data[name] = value
            
            self.logger.debug(f"Search data prepared: {search_data}")
            return search_data
            
        except requests.RequestException as e:
            self.logger.error(f"Error accessing search page: {e}")
            return None
    
    def _scrape_all_pages(self, search_data: Dict[str, str], max_pages: Optional[int]) -> List[Dict[str, str]]:
        """Scrape all pages of results."""
        all_antennas = []
        page_num = 1
        
        while True:
            if max_pages and page_num > max_pages:
                break
                
            self.logger.info(f"Scraping page {page_num}...")
            
            current_search_data = search_data.copy()
            current_search_data['startPage'] = page_num
            current_search_data['myAction'] = 'search' if page_num == 1 else 'page'
            
            try:
                response = self._make_search_request(current_search_data)
                if not response:
                    break
                
                # Save debug files if in debug mode
                if self.debug and page_num <= 2:
                    self._save_debug_response(response, page_num)
                
                soup = BeautifulSoup(response.content, 'html.parser')
                antennas_on_page = self._parse_results(soup)
                
                if not antennas_on_page:
                    self.logger.warning("No antennas found on this page")
                    if self.debug:
                        self._debug_page_structure(soup)
                    if page_num == 1:
                        self.logger.warning("First page returned no results")
                    break
                
                all_antennas.extend(antennas_on_page)
                self.logger.info(f"Found {len(antennas_on_page)} antennas on page {page_num}")
                
                if not self._has_next_page(soup, page_num):
                    break
                    
                page_num += 1
                time.sleep(1)  # Be respectful to the server
                
            except requests.RequestException as e:
                self.logger.error(f"Error on page {page_num}: {e}")
                break
        
        self.logger.info(f"Total antennas found: {len(all_antennas)}")
        return all_antennas
    
    def _make_search_request(self, search_data: Dict[str, str]) -> Optional[requests.Response]:
        """Make a search request to the server."""
        try:
            response = self.session.post(
                urljoin(self.base_url, "getData.php"),
                data=search_data,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Referer': self.search_url
                }
            )
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            self.logger.error(f"Search request failed: {e}")
            return None
    
    def _save_debug_response(self, response: requests.Response, page_num: int) -> None:
        """Save response HTML for debugging purposes."""
        filename = f'debug_response_page_{page_num}.html'
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(response.text)
            self.logger.debug(f"Saved response HTML to {filename}")
        except IOError as e:
            self.logger.error(f"Failed to save debug file: {e}")
    
    def _parse_results(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Parse results from the HTML response."""
        tables = soup.find_all('table')
        for table in tables:
            antennas = self._parse_table_results(table)
            if antennas:
                self.logger.debug(f"Successfully parsed {len(antennas)} antennas from table")
                return antennas
        return []
    
    def _parse_table_results(self, table) -> List[Dict[str, str]]:
        """Parse antenna data from HTML table."""
        rows = table.find_all('tr')
        if len(rows) < 2:
            return []
        
        # Map table headers to field names
        header_map = self._map_table_headers(rows[0])
        if not self._validate_header_map(header_map):
            return []
        
        self.logger.debug(f"Found antenna table with headers: {header_map}")
        
        # Parse data rows
        antennas = []
        for row in rows[1:]:
            cells = row.find_all('td')
            if len(cells) > max(header_map.values()):
                antenna_data = self._extract_antenna_data(cells, header_map)
                antennas.append(antenna_data)
        
        return antennas
    
    def _map_table_headers(self, header_row) -> Dict[str, int]:
        """Map table headers to column indices."""
        header_cells = header_row.find_all(['th', 'td'])
        header_map = {}
        
        for i, cell in enumerate(header_cells):
            text = cell.get_text(strip=True)
            if 'Κωδ.' in text and 'θέσης' in text:
                header_map['position_code'] = i
            elif 'Κατηγορία' in text:
                header_map['category'] = i
            elif 'Εταιρία' in text:
                header_map['company'] = i
            elif 'Διεύθυνση' in text:
                header_map['address'] = i
            elif 'Δήμος' in text:
                header_map['municipality'] = i
            elif 'Κωδ. Θέσης' in text:
                header_map['sequence'] = i
        
        return header_map
    
    def _validate_header_map(self, header_map: Dict[str, int]) -> bool:
        """Validate that required headers are present."""
        required_headers = ['position_code', 'company', 'address', 'municipality']
        missing_headers = [h for h in required_headers if h not in header_map]
        
        if missing_headers:
            self.logger.debug(f"Missing required headers: {missing_headers}")
            return False
        return True
    
    def _extract_antenna_data(self, cells, header_map: Dict[str, int]) -> Dict[str, str]:
        """Extract antenna data from table cells."""
        return {
            'sequence': cells[header_map.get('sequence', 0)].get_text(strip=True) if 'sequence' in header_map else '',
            'position_code': cells[header_map['position_code']].get_text(strip=True),
            'category': cells[header_map.get('category', 0)].get_text(strip=True) if 'category' in header_map else '',
            'company': cells[header_map['company']].get_text(strip=True),
            'address': cells[header_map['address']].get_text(strip=True),
            'municipality': cells[header_map['municipality']].get_text(strip=True)
        }
    
    def _debug_page_structure(self, soup: BeautifulSoup) -> None:
        """Debug helper to understand page structure."""
        if not self.debug:
            return
            
        self.logger.debug("Analyzing page structure...")
        
        tables = soup.find_all('table')
        self.logger.debug(f"Found {len(tables)} tables")
        
        # Check pagination
        pagination_ul = soup.find('ul', class_='pagination')
        if pagination_ul:
            pagination_items = pagination_ul.find_all('li')
            self.logger.debug(f"Found pagination with {len(pagination_items)} items")
        
        # Check for result indicators
        page_text = soup.get_text().lower()
        indicators = ['αποτελέσματα', 'σφάλμα', 'error', 'κεραία', 'antenna']
        found_indicators = [ind for ind in indicators if ind in page_text]
        if found_indicators:
            self.logger.debug(f"Found content indicators: {found_indicators}")
    
    def _has_next_page(self, soup: BeautifulSoup, current_page_num: int) -> bool:
        """Check if there's a next page available."""
        pagination_ul = soup.find('ul', class_='pagination')
        if not pagination_ul:
            return False
        
        pagination_items = pagination_ul.find_all('li')
        
        # Look for next page indicators
        for li in pagination_items:
            # Check for "Next Page" link
            title = li.get('title', '')
            classes = li.get('class', [])
            
            if ('Επόμενη' in title or 'Next' in title) and 'disabled' not in classes:
                return True
            
            # Check for page numbers greater than current
            a_tag = li.find('a')
            if a_tag:
                text = a_tag.get_text(strip=True)
                onclick = a_tag.get('onclick', '')
                
                if text.isdigit() and int(text) > current_page_num:
                    return True
                
                # Check onclick for page numbers
                match = re.search(r"startPage\.value='?(\d+)'?", onclick)
                if match and int(match.group(1)) > current_page_num:
                    return True
        
        return False
    
    def save_to_csv(self, data: List[Dict[str, str]], filename: str = 'antenna_data.csv') -> None:
        """
        Save the scraped data to a CSV file.
        
        Args:
            data: List of antenna data dictionaries
            filename: Output filename
        """
        if not data:
            self.logger.warning("No data to save")
            return
        
        try:
            fieldnames = ['sequence', 'position_code', 'category', 'company', 'address', 'municipality']
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            self.logger.info(f"Data saved to {filename}")
            
        except IOError as e:
            self.logger.error(f"Error saving CSV file: {e}")
    
    def save_to_excel(self, data: List[Dict[str, str]], filename: str = 'antenna_data.xlsx') -> None:
        """
        Save the scraped data to an Excel file.
        
        Args:
            data: List of antenna data dictionaries
            filename: Output filename
        """
        if not data:
            self.logger.warning("No data to save")
            return
        
        try:
            df = pd.DataFrame(data)
            df.to_excel(filename, index=False)
            self.logger.info(f"Data saved to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving Excel file: {e}")


def main():
    """Main function to run the scraper."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Scrape antenna data from EETT website',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Χαλκιδέων"                    # Scrape all pages for Chalkida
  %(prog)s "Αθηναίων" --max-pages 5       # Scrape first 5 pages for Athens
  %(prog)s --list                         # Show available municipalities
  %(prog)s "Θεσσαλονίκης" --debug         # Enable debug mode
        """
    )
    
    parser.add_argument('municipality', nargs='?', 
                       help='Municipality name to search')
    parser.add_argument('--list', '-l', action='store_true',
                       help='List available municipalities')
    parser.add_argument('--max-pages', type=int, 
                       help='Maximum number of pages to scrape')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode')
    parser.add_argument('--output-dir', default='.',
                       help='Output directory for files (default: current directory)')
    
    args = parser.parse_args()
    
    if args.list:
        scraper = EETTScraper(debug=args.debug)
        print("Available municipalities:")
        options = scraper.get_municipality_options()
        for name in sorted(options.keys()):
            print(f"  - {name}")
        return
    
    if not args.municipality:
        parser.error("Municipality name is required (use --list to see available options)")
    
    # Create output directory if it doesn't exist
    if args.output_dir != '.' and not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    scraper = EETTScraper(debug=args.debug)
    
    try:
        # Search for antennas
        antenna_data = scraper.search_municipality(args.municipality, args.max_pages)
        
        if antenna_data:
            # Generate safe filename
            safe_filename = re.sub(r'[^\w\s-]', '', args.municipality).strip()
            safe_filename = re.sub(r'[-\s]+', '_', safe_filename)
            
            # Create file paths
            csv_filename = os.path.join(args.output_dir, f"antennas_{safe_filename}.csv")
            excel_filename = os.path.join(args.output_dir, f"antennas_{safe_filename}.xlsx")
            
            # Save files
            scraper.save_to_csv(antenna_data, csv_filename)
            scraper.save_to_excel(antenna_data, excel_filename)
            
            # Print summary
            print(f"\n{'='*50}")
            print(f"SCRAPING SUMMARY")
            print(f"{'='*50}")
            print(f"Municipality: {args.municipality}")
            print(f"Total antennas: {len(antenna_data)}")
            print(f"Files saved:")
            print(f"  - {csv_filename}")
            print(f"  - {excel_filename}")
            
            # Show sample data
            if antenna_data:
                print(f"\nSample data (first antenna):")
                print("-" * 30)
                for key, value in antenna_data[0].items():
                    print(f"  {key}: {value}")
                print("-" * 30)
        else:
            print(f"\nNo antenna data found for municipality: {args.municipality}")
            print("\nTroubleshooting suggestions:")
            print("1. Check the municipality name spelling")
            print("2. Use --list to see available municipalities")
            print("3. Try using --debug for more information")
    
    except KeyboardInterrupt:
        print("\nScraping interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
