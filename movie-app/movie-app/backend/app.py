"""
================================================================================
MOVIE RECOMMENDATION API - FLASK APPLICATION
================================================================================

PURPOSE:
  This file creates a REST API server that loads a pre-trained ML model and
  serves movie recommendations to frontend clients via HTTP endpoints.

ARCHITECTURE:
  Frontend (HTML/JS) 
    ↓ HTTP Request (JSON)
  Flask API Server ← This file
    ↓ Loads model from pickle
  ML Model (vectors + similarity matrix)
    ↓ Computes recommendations
  JSON Response ← Returns to frontend

KEY CONCEPTS:
  - @app.route(): Decorator that maps URLs to Python functions
  - REST API: Architecture using HTTP verbs (GET, POST, etc.)
  - JSON: Data format for API communication (human-readable)
  - CORS: Allows frontend & backend on different ports to communicate
  - Pickle: Binary format to save/load Python objects quickly

BEST PRACTICES APPLIED:
  1. Global model loading (load once on startup, use many times)
  2. Error handling (try/except blocks)
  3. Separation of concerns (routes, helper functions)
  4. CORS enabled (production needs proper CORS config)

================================================================================
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import requests

# ============================================================================
# FLASK APP INITIALIZATION
# ============================================================================
# Flask(__name__): Creates Flask app instance
# __name__: Makes Flask detect routes in current file
app = Flask(__name__)

# CORS(app): Enable Cross-Origin Resource Sharing
# WHY? Frontend on localhost:8000 needs to call API on localhost:5000
# SECURITY NOTE: '*' allows all origins (OK for learning, restrict in production)
# Example: CORS(app, origins=["http://localhost:8000"]) for production
CORS(app)

# ============================================================================
# TMDB API CONFIGURATION
# ============================================================================
# TMDB: The Movie Database - provides movie metadata, posters, ratings
TMDB_API_KEY = "203f6011b7cb51ac15f09e25b6b78612"
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"  # URL for poster images

# ============================================================================
# GLOBAL MODEL STORAGE
# ============================================================================
# Dictionary to hold model data in memory
# Global = Can be accessed from any function without passing as parameter
# Trade-off: Simple but not ideal for multi-worker setup (use Redis for scale)
model_data = {}

# ============================================================================
# MODEL LOADING FUNCTION
# ============================================================================
def load_model():
    """
    Load the serialized ML model from disk into memory.
    
    WHY LOAD ONCE?
      Training takes 3+ minutes. Loading .pkl takes <1 second.
      Loading at startup = Instant recommendations, happy users.
    
    ALTERNATIVE APPROACH (Advanced):
      - Use model serving platforms (TensorFlow Serving, MLflow)
      - Models in database or cloud storage
      - Version management systems
    
    RETURNS:
      Boolean: True if successful, False if failed
    """
    global model_data
    try:
        # Open pickle file in binary read mode ('rb')
        # Pickle = Binary Python object serialization
        # It's fast but only works with Python (JSON would be cross-language)
        with open('../models/recommendation_model.pkl', 'rb') as f:
            model_data = pickle.load(f)
        print("✓ Model loaded successfully")
        return True
    except Exception as e:
        # Exception: Catch ANY error during file reading
        # Real apps would log this to monitoring system (Sentry, DataDog)
        print(f"✗ Error loading model: {e}")
        return False

# ============================================================================
# FLASK ROUTES (ENDPOINTS)
# ============================================================================
# Route = URL pattern that triggers a function
# Decorator @app.route() connects URL to Python function
# HTTP Methods: GET (read), POST (write), PUT (update), DELETE (remove)

@app.route('/health', methods=['GET'])
def health_check():
    """
    HEALTH CHECK ENDPOINT - DevOps/Monitoring best practice
    
    WHAT IS THIS?
      In production, load balancers and monitoring systems ping /health
      to check if server is alive and ready to serve requests.
    
    RETURNS:
      JSON with status and model readiness
    
    HTTP METHOD: GET (read-only, no data modification)
    
    REAL-WORLD USE:
      - Kubernetes uses /health endpoints to restart dead services
      - Monitoring alerts if /health returns error
      - Load balancers remove server from rotation if unhealthy
    
    Example Response:
      {
        "status": "healthy",
        "model_loaded": true
      }
    """
    return jsonify({
        'status': 'healthy',
        'model_loaded': bool(model_data)
    })

@app.route('/recommend', methods=['POST'])
def recommend_movies():
    """
    PRIMARY ENDPOINT - Get movie recommendations
    
    WHAT IT DOES:
      1. Receives movie name from frontend
      2. Finds similar movies using pre-computed similarity matrix
      3. Returns top 5 recommendations with scores
    
    HTTP METHOD: POST (sends data in request body)
    
    REQUEST FORMAT (JSON):
      {
        "movie_name": "Avatar"
      }
    
    RESPONSE FORMAT (JSON):
      {
        "search_movie": "Avatar",
        "recommendations": [
          {"title": "Avatar: The Way of Water", "similarity_score": 0.85},
          {"title": "Inception", "similarity_score": 0.78},
          ...
        ]
      }
    
    ERROR HANDLING: Returns proper HTTP status codes
      - 400: Bad Request (missing data)
      - 404: Not Found (movie not in database)
      - 500: Server Error (unexpected crash)
    
    REAL-WORLD BEST PRACTICES:
      - Input validation (check data exists and is valid type)
      - Error handling (try/except blocks)
      - Meaningful error messages
      - Proper HTTP status codes (not just returning errors)
    """
    try:
        # Extract JSON from request
        # request.get_json(): Parses JSON body into Python dict
        data = request.get_json()
        movie_name = data.get('movie_name', '').strip()

        # INPUT VALIDATION: Check if movie_name was provided and not empty
        if not movie_name:
            # Status 400 = "Bad Request" (client error, malformed request)
            return jsonify({'error': 'Movie name is required'}), 400

        # Get recommendations using helper function
        recommendations = get_recommendations(movie_name)
        
        # Check if error occurred in helper function
        if 'error' in recommendations:
            # Status 404 = "Not Found" (movie doesn't exist in database)
            return jsonify(recommendations), 404

        # Status 200 = "OK" (success, implicit but good practice to be explicit)
        return jsonify(recommendations), 200

    except Exception as e:
        # Status 500 = "Internal Server Error" (unexpected crash)
        # In production: Log to monitoring system instead of exposing error details
        return jsonify({'error': str(e)}), 500

def get_recommendations(movie_name, num_recommendations=5):
    """
    HELPER FUNCTION - Compute recommendations using similarity matrix
    
    ALGORITHM EXPLAINED:
      1. Find movie index in dataset
      2. Get similarity scores for that movie vs all others (precomputed)
      3. Sort by similarity (highest first)
      4. Return top N (excluding the movie itself)
    
    COMPLEXITY:
      - Time: O(n log n) for sorting (n = number of movies)
      - Space: O(k) for storing k results
      - Precomputed similarity: O(1) lookup (already done during training)
    
    PARAMETERS:
      movie_name (str): Name of movie to find recommendations for
      num_recommendations (int): How many results to return (default 5)
    
    RETURNS:
      dict: Either recommendations or error message
    
    REAL-WORLD IMPROVEMENTS:
      - Cache results (same movie asked often)
      - Use FAISS for 1M+ movies (approximate similarity faster)
      - Add personalization (user history)
    """
    if not model_data:
        return {'error': 'Model not loaded'}

    # Extract model components from global dictionary
    final_ds = model_data['final_ds']
    vectors = model_data['vectors']
    similarity = model_data['similarity']

    # CASE-INSENSITIVE SEARCH: "avatar", "AVATAR", "Avatar" all work
    # .str.lower() converts entire column to lowercase for comparison
    matching_movies = final_ds[final_ds['title'].str.lower() == movie_name.lower()]
    
    if matching_movies.empty:
        return {'error': f'Movie "{movie_name}" not found in database'}

    # Get index of matching movie
    # .index[0] because matching_movies is a Series/DataFrame (need to extract number)
    index = matching_movies.index[0]
    
    # Get similarity scores: This movie vs all others
    # Similarity matrix was precomputed during training (O(1) access)
    distance = similarity[index]
    
    # SORTING EXPLAINED:
    # enumerate(distance): Pairs each score with its movie index
    #   Example: [(0, 0.9), (1, 0.7), (2, 0.85), ...]
    # sorted(..., reverse=True, key=lambda x: x[1]):
    #   - sort by second element (similarity score)
    #   - reverse=True for descending (highest similarity first)
    #   - lambda: Anonymous function for sorting key
    # [1:num_recommendations + 1]: Skip first (the movie itself), take next N
    movie_indices = sorted(
        list(enumerate(distance)),
        reverse=True,
        key=lambda x: x[1]
    )[1:num_recommendations + 1]
    
    # Build response list
    recommendations = []
    for idx, score in movie_indices:
        recommendations.append({
            'title': final_ds.iloc[idx]['title'],
            # Convert to float for JSON serialization (numpy.float64 not JSON-serializable)
            'similarity_score': float(score)
        })

    return {
        'search_movie': final_ds.iloc[index]['title'],
        'recommendations': recommendations
    }

@app.route('/search', methods=['GET'])
def search_movies():
    """
    SEARCH/AUTOCOMPLETE ENDPOINT
    
    WHAT IT DOES:
      Provides movie name suggestions as user types (autocomplete feature)
    
    HTTP METHOD: GET (read-only, no body needed)
    
    QUERY PARAMETERS (in URL)?
      ?q=top        returns movies containing "top"
      ?q=avatar     returns movies containing "avatar"
    
    RESPONSE FORMAT (JSON array):
      ["Top Gun", "Top Gun: Maverick", "Top Story", ...]
    
    FRONTEND USE CASE:
      User types "av" → API returns ["Avatar", "Avatar: The Way of Water", ...]
      Dropdown shows suggestions, user clicks one
    
    REAL-WORLD IMPROVEMENTS:
      - Fuzzy matching (typo tolerance)
      - Ranking by popularity (show better results first)
      - Caching results for common queries
      - Rate limiting (prevent abuse)
    """
    try:
        # Get 'q' parameter from URL: /search?q=top
        # .args.get() for query parameters (vs .json for body data)
        query = request.args.get('q', '').lower()
        
        # Ignore very short queries (too many false positives)
        if not query or len(query) < 2:
            return jsonify([]), 200

        final_ds = model_data['final_ds']
        
        # STRING SEARCH EXPLAINED:
        # .str.contains(): Check if column values contain substring
        # na=False: Treat NaN (missing values) as False
        # Returns boolean array of matching rows
        matching = final_ds[final_ds['title'].str.lower().str.contains(query, na=False)]
        
        # Get top 10 results as list
        results = matching['title'].head(10).tolist()
        
        return jsonify(results), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# TMDB API ENDPOINTS
# ============================================================================

@app.route('/tmdb/trending', methods=['GET'])
def get_trending_movies():
    """
    Get trending movies from TMDB with posters and metadata.
    
    RESPONSE FORMAT:
      {
        "results": [
          {
            "id": 123,
            "title": "Avatar",
            "poster_path": "/path.jpg",
            "poster_url": "https://image.tmdb.org/...",
            "overview": "Movie description",
            "release_date": "2024-01-01",
            "vote_average": 8.5
          },
          ...
        ]
      }
    """
    try:
        url = f"{TMDB_BASE_URL}/trending/movie/week"
        params = {
            "api_key": TMDB_API_KEY,
            "language": "en-US"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Enrich data with full poster URLs
        for movie in data.get('results', []):
            if movie.get('poster_path'):
                movie['poster_url'] = f"{TMDB_IMAGE_BASE}{movie['poster_path']}"
            else:
                movie['poster_url'] = None
        
        return jsonify(data), 200
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f"TMDB API error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/tmdb/search', methods=['GET'])
def search_tmdb():
    """
    Search TMDB for movies by query string - FILTERED TO ML DATABASE.
    
    IMPORTANT:
      - Searches TMDB but ONLY returns movies in the ML training dataset (4806 movies)
      - This prevents "Movie not found" errors when users click results
      - Movies searched are from 2015 TMDB dataset
    
    QUERY PARAMS:
      - query: Movie search term
    
    RESPONSE:
      List of movies with posters and details (only those that exist in ML model)
    """
    try:
        query = request.args.get('query', '').strip()
        
        if not query or len(query) < 2:
            return jsonify({'error': 'Search query must be 2+ characters'}), 400
        
        # Get the ML database movies for filtering
        final_ds = model_data['final_ds']
        ml_movie_titles = set(final_ds['title'].str.lower())
        
        url = f"{TMDB_BASE_URL}/search/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "query": query,
            "language": "en-US"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # FILTER: Only keep movies that exist in our ML training database
        filtered_results = []
        for movie in data.get('results', []):
            title = movie.get('title', '').lower()
            # Check if this exact movie title is in our ML database
            if title in ml_movie_titles:
                if movie.get('poster_path'):
                    movie['poster_url'] = f"{TMDB_IMAGE_BASE}{movie['poster_path']}"
                else:
                    movie['poster_url'] = None
                filtered_results.append(movie)
        
        # Return filtered results (only movies we can recommend for)
        data['results'] = filtered_results
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/tmdb/details', methods=['GET'])
def get_movie_details():
    """
    Get detailed information about a specific movie from TMDB.
    
    QUERY PARAMS:
      - movie_id: TMDB movie ID
    
    RESPONSE:
      Detailed movie information including genres, production companies, etc.
    """
    try:
        movie_id = request.args.get('movie_id', '').strip()
        
        if not movie_id:
            return jsonify({'error': 'movie_id is required'}), 400
        
        url = f"{TMDB_BASE_URL}/movie/{movie_id}"
        params = {
            "api_key": TMDB_API_KEY,
            "language": "en-US"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Enrich with poster URL
        if data.get('poster_path'):
            data['poster_url'] = f"{TMDB_IMAGE_BASE}{data['poster_path']}"
        
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/tmdb/matching', methods=['POST'])
def get_recommendations_with_tmdb():
    """
    Get movie recommendations and enrich with TMDB poster data.
    
    REQUEST:
      {
        "movie_name": "Avatar"
      }
    
    RESPONSE:
      Recommendations with TMDB poster URLs and details
    """
    try:
        data = request.get_json()
        movie_name = data.get('movie_name', '').strip()
        
        if not movie_name:
            return jsonify({'error': 'Movie name is required'}), 400
        
        # Get recommendations from our ML model
        recommendations = get_recommendations(movie_name, num_recommendations=5)
        
        if 'error' in recommendations:
            return jsonify(recommendations), 404
        
        # Now search TMDB for each recommendation to get posters
        enriched_recommendations = []
        for rec in recommendations.get('recommendations', []):
            title = rec['title']
            
            # Search TMDB for this movie
            url = f"{TMDB_BASE_URL}/search/movie"
            params = {
                "api_key": TMDB_API_KEY,
                "query": title,
                "language": "en-US"
            }
            
            try:
                resp = requests.get(url, params=params, timeout=5)
                resp.raise_for_status()
                results = resp.json().get('results', [])
                
                if results:
                    first_match = results[0]
                    rec['tmdb_id'] = first_match.get('id')
                    rec['posters'] = f"{TMDB_IMAGE_BASE}{first_match['poster_path']}" if first_match.get('poster_path') else None
                    rec['overview'] = first_match.get('overview', '')
                    rec['release_date'] = first_match.get('release_date', '')
                    rec['vote_average'] = first_match.get('vote_average', 0)
                else:
                    rec['posters'] = None
                    rec['overview'] = ''
            except:
                rec['posters'] = None
                rec['overview'] = ''
            
            enriched_recommendations.append(rec)
        
        recommendations['recommendations'] = enriched_recommendations
        return jsonify(recommendations), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# This block only runs when script is executed directly (not imported)
# if __name__ == '__main__': prevents running when imported as module

if __name__ == '__main__':
    # Load model before starting server
    if load_model():
        print("Starting Flask API on http://localhost:5000")
        # debug=True: Auto-reload on code changes, detailed error messages
        # host='0.0.0.0': Listen on all network interfaces (not just localhost)
        # port=5000: Standard port for development (change in production)
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("Failed to load model. Exiting.")

"""
================================================================================
FLASK BEST PRACTICES SUMMARY
================================================================================

1. ERROR HANDLING: Always wrap in try/except, return proper status codes
2. VALIDATION: Check input before using it
3. LOGGING: Should go to centralized system (Sentry, ELK Stack, etc.)
4. SECURITY: Don't expose internal errors to users, validate all inputs
5. SCALABILITY: 
   - Current: Single process, single model (fine for learning)
   - Production: Use gunicorn + nginx + multiple workers
   - Enterprise: Use Flask with Kubernetes + load balancing
6. MONITORING:
   - /health endpoint for service checks
   - Metrics: Response time, error rate, etc.
7. DOCUMENTATION:
   - Always document what parameters are needed
   - Always document what response looks like
   - Tools: Swagger/OpenAPI for auto-generated docs

================================================================================
"""
