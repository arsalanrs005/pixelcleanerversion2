"""
Flask web service for Pixel Cleaner
Deploy this on Render to provide a web API for CSV cleaning
"""

from flask import Flask, request, send_file, jsonify
import subprocess
import os
import tempfile
import uuid

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        'message': 'Pixel Cleaner API',
        'endpoints': {
            '/health': 'Health check endpoint',
            '/clean': 'POST - Clean CSV file (multipart/form-data with "file" field)'
        }
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/clean', methods=['POST'])
def clean_csv():
    """
    Clean CSV endpoint
    Accepts a CSV file via POST request
    Returns cleaned CSV file
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided. Please upload a CSV file with "file" field.'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be a CSV file'}), 400
    
    # Create temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, f'input_{uuid.uuid4().hex}.csv')
        output_path = os.path.join(temp_dir, f'output_{uuid.uuid4().hex}.csv')
        
        # Save uploaded file
        file.save(input_path)
        
        try:
            # Run the pixelcleaner script
            result = subprocess.run(
                ['python3', 'pixelcleaner.py', input_path, output_path],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
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
            
            # Return the cleaned file
            return send_file(
                output_path,
                mimetype='text/csv',
                as_attachment=True,
                download_name='cleaned_output.csv'
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

