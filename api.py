from flask import Flask, request, jsonify
from tools.google import (
    filter_vet_response,
    google_search_filter,
    google_search_page_filter,
    google_search_video_page_filter,
    get_decoded_body,
    calculate_hash
)

app = Flask(__name__)

@app.route('/filter_vet_response', methods=['POST'])
def api_filter_vet_response():
    """
    API for filter_vet_response
    """
    data = request.get_json()
    response = data.get('response')
    filter_words = data.get('filter_words', [])
    result = filter_vet_response(response, filter_words)
    return jsonify({'filtered_response': result.decode('utf-8') if result else None})

@app.route('/google_search_filter', methods=['POST'])
def api_google_search_filter():
    """
    API for google_search_filter
    """
    data = request.get_json()
    response = data.get('response')
    filter_words = data.get('filter_words', [])
    result = google_search_filter(response, filter_words)
    return jsonify({'filtered_response': result.decode('utf-8') if result else None})

@app.route('/google_search_page_filter', methods=['POST'])
def api_google_search_page_filter():
    """
    API for google_search_page_filter
    """
    data = request.get_json()
    response = data.get('response')
    filter_words = data.get('filter_words', [])
    result = google_search_page_filter(response, filter_words)
    return jsonify({'filtered_response': result.decode('utf-8') if result else None})

@app.route('/google_search_video_page_filter', methods=['POST'])
def api_google_search_video_page_filter():
    """
    API for google_search_video_page_filter
    """
    data = request.get_json()
    response = data.get('response')
    filter_words = data.get('filter_words', [])
    result = google_search_video_page_filter(response, filter_words)
    return jsonify({'filtered_response': result.decode('utf-8') if result else None})

@app.route('/get_decoded_body', methods=['POST'])
def api_get_decoded_body():
    """
    API for get_decoded_body
    """
    data = request.get_json()
    response = data.get('response')
    result = get_decoded_body(response)
    return jsonify({'decoded_body': result.decode('utf-8') if result else None})

@app.route('/calculate_hash', methods=['POST'])
def api_calculate_hash():
    """
    API for calculate_hash
    """
    data = request.get_json()
    content = data.get('content', '')
    result = calculate_hash(content)
    return jsonify({'hash': result})

if __name__ == '__main__':
    app.run(debug=True, port=5000)