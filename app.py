from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
from urllib.parse import urljoin, urlparse
import time
import random

app = Flask(__name__)

# User agents để tránh bị chặn
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
]

class VirtualBrowser:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.current_url = "https://duckduckgo.com"
        self.history = []
        self.cookies = {}

    def navigate(self, url):
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            response = self.session.get(url, timeout=10)
            self.current_url = response.url
            self.history.append(self.current_url)
            
            return {
                'success': True,
                'content': response.text,
                'url': response.url,
                'status_code': response.status_code
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def search(self, query):
        try:
            search_url = "https://duckduckgo.com/html/"
            params = {
                'q': query,
                'kl': 'us-en'
            }
            
            response = self.session.get(search_url, params=params, timeout=10)
            self.current_url = response.url
            self.history.append(self.current_url)
            
            return {
                'success': True,
                'content': response.text,
                'url': response.url,
                'status_code': response.status_code
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Tạo instance của trình duyệt ảo
browser = VirtualBrowser()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query', '')
    if query:
        result = browser.search(query)
        return jsonify(result)
    return jsonify({'success': False, 'error': 'No query provided'})

@app.route('/navigate', methods=['POST'])
def navigate():
    url = request.form.get('url', '')
    if url:
        result = browser.navigate(url)
        return jsonify(result)
    return jsonify({'success': False, 'error': 'No URL provided'})

@app.route('/get_current_url')
def get_current_url():
    return jsonify({'url': browser.current_url})

@app.route('/history')
def get_history():
    return jsonify({'history': browser.history})

@app.route('/proxy_content', methods=['POST'])
def proxy_content():
    data = request.get_json()
    url = data.get('url', '')
    
    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'})
    
    try:
        # Kiểm tra xem URL có hợp lệ không
        parsed_url = urlparse(url)
        if not parsed_url.netloc:
            return jsonify({'success': False, 'error': 'Invalid URL'})
        
        response = browser.session.get(url, timeout=10)
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'content': response.text,
                'content_type': response.headers.get('content-type', 'text/html')
            })
        else:
            return jsonify({
                'success': False,
                'error': f'HTTP {response.status_code}'
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)