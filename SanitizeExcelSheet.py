import pandas as pd
import re

def sanitize_data(text):
    if pd.isna(text):
        return text
        
    # Convert to string if not already
    text = str(text)
    
    # Pattern for GUIDs
    guid_pattern = r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b'
    
    # Pattern for phone numbers (handles various formats)
    phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    
    # Pattern for IP addresses
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    
    # Pattern for server names
    server_pattern = (
        r'\b(?:' +
        r'ar-fsm[A-Za-z0-9-]+|' +
        r'BOSQL[A-Za-z0-9-]+|' +
        r'opersql[A-Za-z0-9-]+|' +
        r'gisdbprd[A-Za-z0-9-]+|' +
        # Azure database pattern
        r'[A-Za-z0-9-]+\.database\.windows\.net|' +
        # Common domain-style server names
        r'(?:srv|server|db|app|web|dev|prod|test|uat|stg|sql)\d*[-.]' +
        r'[A-Za-z0-9-]+\.(com|net|org|local|int|dev|prod|test|stage)|' +
        # Server names with specific prefixes
        r'(?:srv|server|db|app|web|dev|prod|test|uat|stg|sql)\d*-[A-Za-z0-9-]+' +
        r')\b'
    )
    
    # Pattern for email addresses
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Replace each pattern with its placeholder
    text = re.sub(guid_pattern, '[GUID]', text)
    text = re.sub(phone_pattern, '[PhoneNumber]', text)
    text = re.sub(ip_pattern, '[IPAddress]', text)
    text = re.sub(server_pattern, '[ServerName]', text)
    text = re.sub(email_pattern, '[EmailAddress]', text)
    
    return text

def process_excel(input_file, output_file):
    try:
        # Read the Excel file
        df = pd.read_excel(input_file)
        
        # Verify required columns exist
        required_columns = ['TicketID', 'Ticket_Title', 'Ticket_Summary']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Apply sanitization to specified columns
        df['Ticket_Title'] = df['Ticket_Title'].apply(sanitize_data)
        df['Ticket_Summary'] = df['Ticket_Summary'].apply(sanitize_data)
        
        # Save the sanitized data
        df.to_excel(output_file, index=False)
        print(f"Successfully sanitized data and saved to {output_file}")
        
        # Print summary of replacements
        total_rows = len(df)
        affected_titles = df[df['Ticket_Title'].str.contains(r'\[.*?\]', na=False)].shape[0]
        affected_summaries = df[df['Ticket_Summary'].str.contains(r'\[.*?\]', na=False)].shape[0]
        
        print(f"\nProcessing Summary:")
        print(f"Total rows processed: {total_rows}")
        print(f"Tickets with sanitized titles: {affected_titles}")
        print(f"Tickets with sanitized summaries: {affected_summaries}")
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")

# Example usage
if __name__ == "__main__":
    input_file = "JiraTicketExport.xlsx"
    output_file = "JiraTicketExport_sanitized.xlsx"
    process_excel(input_file, output_file)