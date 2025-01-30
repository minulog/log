import os
import re
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Define a function to parse Apache/Nginx log format
def parse_log_line(line):
    # This is a basic regex for Apache/Nginx combined log format
    log_pattern = r'(?P<ip_address>\S+) - - \[(?P<datetime>.*?)\] "(?P<method>\S+) (?P<url>\S+) \S+" (?P<response_code>\d{3}) (?P<bytes_sent>\d+) "(?P<referrer>.*?)" "(?P<user_agent>.*?)"'
    match = re.match(log_pattern, line)
    if match:
        return match.groupdict()
    return None

# Function to search for a log in a single file
def search_log_file(file_path, search_terms, website, result_list):
    with open(file_path, 'r') as log_file:
        for line_number, line in enumerate(log_file, 1):
            parsed_line = parse_log_line(line)
            if parsed_line:
                # If the website is provided, we also match the URL or referrer
                if (website and (website in parsed_line['url'] or website in parsed_line['referrer'])) or not website:
                    if any(re.search(term, str(parsed_line), re.IGNORECASE) for term in search_terms):
                        result_list.append((file_path, line_number, parsed_line))

# Function to handle search across multiple log files in parallel
def search_logs_in_directory(directory, search_terms, website, output_file):
    result_list = []
    
    with ThreadPoolExecutor() as executor:
        futures = []
        
        # Loop through all files in the directory
        for filename in os.listdir(directory):
            if filename.endswith(".log"):  # Only look for .log files
                file_path = os.path.join(directory, filename)
                futures.append(executor.submit(search_log_file, file_path, search_terms, website, result_list))
        
        # Wait for all threads to finish
        for future in futures:
            future.result()

    # Output the results to the specified output file
    with open(output_file, 'w') as f:
        for file_path, line_number, log_data in result_list:
            f.write(f"File: {file_path} Line: {line_number}\n")
            f.write(f"IP Address: {log_data['ip_address']} | URL: {log_data['url']} | Response Code: {log_data['response_code']}\n")
            f.write(f"Method: {log_data['method']} | User-Agent: {log_data['user_agent']}\n")
            f.write("-" * 80 + "\n")

    print(f"Search complete. Results saved to {output_file}")

# Main function to handle command-line arguments and initiate search
def main():
    # Setup command-line argument parser
    parser = argparse.ArgumentParser(description="Powerful Website Log Finder Tool")
    parser.add_argument("directory", help="Directory path containing the log files")
    parser.add_argument("search_terms", nargs='+', help="Search terms (e.g., error, 404, user-agent)")
    parser.add_argument("--website", help="Website URL to filter (e.g., 'example.com')")
    parser.add_argument("--output", default="search_results.txt", help="Output file to save results (default: search_results.txt)")
    
    args = parser.parse_args()

    # Validate the directory path
    if not os.path.isdir(args.directory):
        print(f"Invalid directory: {args.directory}")
        return
    
    # Run the log search
    search_logs_in_directory(args.directory, args.search_terms, args.website, args.output)

if __name__ == "__main__":
    main()
