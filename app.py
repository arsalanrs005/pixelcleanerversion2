"""
Flask web service for Pixel Cleaner
Deploy this on Render to provide a web API for CSV cleaning
"""

from flask import Flask, request, send_file, jsonify, render_template
import subprocess
import os
import tempfile
import uuid
import re
import csv

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/clean', methods=['POST'])
def clean_csv():
    """
    Clean CSV endpoint
    Accepts a CSV file via POST request and optional filename
    Returns cleaned CSV file with user-specified name
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided. Please upload a CSV file with "file" field.'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Accept both .csv and .ai files (since healospixel.ai is actually a CSV)
    if not (file.filename.endswith('.csv') or file.filename.endswith('.ai')):
        return jsonify({'error': 'File must be a CSV file (.csv or .ai)'}), 400
    
    # Check file size before processing
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer
    max_file_size = 500 * 1024 * 1024  # 500MB limit
    warning_size = 50 * 1024 * 1024  # 50MB - warn about potential timeout
    
    if file_size > max_file_size:
        return jsonify({
            'error': f'File too large. Maximum size is 500MB. Your file is {file_size / (1024*1024):.1f}MB. Please split into smaller files or upgrade to Render Starter plan.'
        }), 413
    
    # Get custom filename from form data
    custom_filename = request.form.get('filename', '').strip()
    
    # Sanitize filename - remove any path components and ensure it ends with .csv
    if custom_filename:
        # Remove any directory separators and dangerous characters
        custom_filename = os.path.basename(custom_filename)
        # Remove any non-alphanumeric characters except dots, dashes, and underscores
        custom_filename = re.sub(r'[^a-zA-Z0-9._-]', '', custom_filename)
        # Ensure it ends with .csv
        if not custom_filename.endswith('.csv'):
            custom_filename = custom_filename + '.csv'
    else:
        # Default filename based on input file
        base_name = os.path.splitext(file.filename)[0]
        custom_filename = f'{base_name}_cleaned.csv'
    
    # Create temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, f'input_{uuid.uuid4().hex}.csv')
        output_path = os.path.join(temp_dir, f'output_{uuid.uuid4().hex}.csv')
        
        # Save uploaded file
        file.save(input_path)
        
        try:
            # Run the pixelcleaner script with increased timeout for large files
            # Use longer timeout for very large files
            timeout_seconds = 1800 if file_size > 100 * 1024 * 1024 else 900  # 30 min for >100MB, 15 min otherwise
            
            result = subprocess.run(
                ['python3', 'pixelcleaner.py', input_path, output_path],
                capture_output=True,
                text=True,
                timeout=timeout_seconds
            )
            
            if result.returncode != 0:
                return jsonify({
                    'error': 'Processing failed',
                    'details': result.stderr
                }), 500
            
            # Check if output file was created
            if not os.path.exists(output_path):
                return jsonify({
                    'error': 'Output file was not created',
                    'details': result.stdout
                }), 500
            
            # Read CSV data for preview (maintain exact order from CSV)
            # Skip preview for very large files to save memory and time
            preview_data = []
            output_file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            max_preview_size = 10 * 1024 * 1024  # 10MB - skip preview for files larger than this
            
            # Skip preview entirely for large files to avoid timeout
            if output_file_size < max_preview_size:
                try:
                    with open(output_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        # Get first 50 rows for preview (reduced from 100 to save time)
                        for i, row in enumerate(reader):
                            if i >= 50:  # Limit preview to 50 rows
                                break
                            # Preserve order by appending in sequence
                            preview_data.append(dict(row))  # Ensure it's a new dict to preserve order
                except Exception as e:
                    # If preview fails, continue with file download
                    preview_data = []
            
            # Check if client wants JSON preview (via query parameter)
            if request.args.get('preview') == 'true':
                return jsonify({
                    'success': True,
                    'filename': custom_filename,
                    'preview': preview_data,
                    'total_rows': len(preview_data)
                })
            
            # Return the cleaned file with user-specified filename
            return send_file(
                output_path,
                mimetype='text/csv',
                as_attachment=True,
                download_name=custom_filename
            )
        
        except subprocess.TimeoutExpired:
            return jsonify({'error': 'Processing timed out. File may be too large.'}), 504
        except Exception as e:
            return jsonify({
                'error': 'An error occurred during processing',
                'details': str(e)
            }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

