"""
================================================================================
MOVIE RECOMMENDATION MODEL - TRAINING & SERIALIZATION
================================================================================

PURPOSE:
  This script trains the ML model ONCE and saves it to disk as a pickle file.
  The saved model is then loaded by app.py for instant recommendations.

WHY SEPARATE TRAINING FROM API?
  - Training is SLOW (takes 2-3 minutes for 5000 movies)
  - Inference is FAST (takes <1ms per recommendation)
  - Separate concerns: Train once, serve many times
  - Production: Models trained offline, API serves thousands of requests

ML PIPELINE FLOW:
  1. Load Data (CSV files)
  2. Data Cleaning & Preprocessing
  3. Feature Engineering (create "tags" column)
  4. Text Vectorization (convert text to numbers)
  5. Similarity Computation (find distances between vectors)
  6. Serialize to Pickle (save for fast loading)

ALGORITHM USED: COSINE SIMILARITY
  - What: Measures angle between vectors in vector space
  - Why: More movies similar = closer vectors = smaller angle = higher similarity
  - Formula: cos(θ) = (A · B) / (||A|| ||B||)
  - Range: 0 (completely different) to 1 (identical)
  - Fast: O(1) lookup after precomputation

ALTERNATIVES FOR SCALE:
  - FAISS (Approximate Nearest Neighbor for 1M+ movies)
  - Elasticsearch (Full-text search + scoring)
  - Deep Learning (embeddings from neural networks)

================================================================================
"""

import pandas as pd
import numpy as np
import ast
import pickle
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.stem.porter import PorterStemmer
import nltk

# NLTK (Natural Language Toolkit) - NLP library
# Download required data files for text processing
# punkt: Tokenizer for splitting text into sentences/words
nltk.download('punkt')

# ============================================================================
# STEMMING EXPLAINED
# ============================================================================
# Problem: "loves", "loving", "loved", "lover" are same concept but different words
# Solution: Stemming converts all to root word "lov"
# 
# Stemming vs Lemmatization:
#   - Stemming: Simple rules, faster, sometimes nonsensical ("lov")
#   - Lemmatization: Dictionary-based, slower, grammatically correct ("love")
# 
# For recommendation: Stemming is usually fine
# 
ps = PorterStemmer()  # Porter stemmer algorithm (industry standard)

# ============================================================================
# DATA LOADING & MERGING
# ============================================================================
def convert(obj):
    """
    CONVERTER FUNCTION 1: Genre & Keywords
    
    PROBLEM:
      CSV stores complex objects as JSON strings:
      "[{"name": "Action"}, {"name": "Adventure"}]"
      
      Python reads this as a STRING, not a list of dicts
    
    SOLUTION:
      - ast.literal_eval(): Safely converts string to Python object
      - Loop through list, extract 'name' field
      - Return clean list of names
    
    EXAMPLE:
      Input:  '[{"name": "Action"}, {"name": "Adventure"}]'
      Output: ["Action", "Adventure"]
    
    WHY NOT JSON.LOADS?
      ✗ json.loads(): Only JSON format
      ✓ ast.literal_eval(): Python literals (safer, more flexible)
    """
    if isinstance(obj, list):  # Already a list, return as-is
        return obj
    genres = []
    for i in ast.literal_eval(obj):  # Convert string to actual list
        genres.append(i['name'])
    return genres

def convert_for_director_crew(obj):
    """
    CONVERTER FUNCTION 2: Extract Director
    
    PROBLEM:
      Crew has many roles (Director, Actor, Producer, etc.)
      We only want the Director
    
    SOLUTION:
      - Loop through crew members
      - Check if job == "Director"
      - Return first director found
    
    WHY FIRST DIRECTOR ONLY?
      - Sometimes multiple directors, but we keep it simple
      - Director is usually main creative force
      - Reduces noise in recommendations
    
    EXAMPLE:
      Input:  [{"name": "James Cameron", "job": "Director"}, 
               {"name": "Producer", "job": "Producer"}]
      Output: ["James Cameron"]
    """
    crew = []
    if isinstance(obj, list):
        data = obj
    else:
        data = ast.literal_eval(obj)
    for i in data:
        if i.get('job') == 'Director':  # Find Director
            crew.append(i.get('name'))
            break  # Only first director
    return crew

def convert_3_actors_only(obj):
    """
    CONVERTER FUNCTION 3: Top 3 Actors
    
    PROBLEM:
      Movies have many actors. Including all creates noise.
    
    SOLUTION:
      - Keep only top 3 cast members (usually main stars)
      - Reduces feature noise
      - Still captures main actors
    
    WHY TOP 3?
      - Balance: Enough to match similar movies, not too many
      - Practical: Main stars are usually public knowledge
      - ML: Too many features cause overfitting
    
    EXAMPLE:
      Input:  [Actor1, Actor2, Actor3, Actor4, Actor5]
      Output: [Actor1, Actor2, Actor3]  (first 3)
    """
    if isinstance(obj, list):
        return obj[:3]  # [:3] means "first 3 elements"
    
    counter = 0
    actors = []
    for i in ast.literal_eval(obj):
        if counter <= 3:
            actors.append(i['name'])
            counter += 1
        else:
            break  # Stop after 3
    return actors

def prepare_data():
    """
    MAIN DATA PREPARATION PIPELINE
    
    STEPS:
      1. Load CSV files
      2. Merge on common key (title)
      3. Select relevant columns
      4. Remove missing values
      5. Convert complex objects to lists
      6. Extract specific fields
      7. Clean text (remove spaces)
      8. Create feature vector (concatenate all features)
      9. Apply stemming (normalize words)
    
    RETURNS:
      DataFrame with cleaned, feature-engineered data ready for ML
    """
    print("Loading CSV files...")
    # pd.read_csv(): Load CSV into DataFrame (like SQL table in Python)
    credits = pd.read_csv('./tmdb_5000_credits.csv')
    movies = pd.read_csv('./tmdb_5000_movies.csv')
    
    print("Merging datasets...")
    # .merge(on="title"): Join two tables on matching 'title' column
    # SQL equivalent: SELECT * FROM movies INNER JOIN credits ON movies.title = credits.title
    data_set = movies.merge(credits, on="title")
    
    print("Selecting relevant columns...")
    # Keep only columns useful for recommendations
    # Ignore: budget, revenue, runtime, release_date (not for similarity)
    movies_df = data_set[['movie_id', 'title', 'keywords', 'genres', 'overview', 'crew', 'cast']].copy()
    
    print("Dropping null values...")
    # .dropna(): Remove rows with missing values
    # Why? ML algorithms can't handle NaN (missing data)
    # Trade-off: Lose some data but keep clean dataset
    movies_df.dropna(inplace=True)
    
    print("Converting genres...")
    # .apply(): Apply function to each row of column
    # convert(): Converts JSON string to Python list
    movies_df['genres'] = movies_df['genres'].apply(convert)
    
    print("Converting keywords...")
    movies_df['keywords'] = movies_df['keywords'].apply(convert)
    
    print("Extracting directors...")
    movies_df['crew'] = data_set['crew'].apply(convert_for_director_crew)
    
    print("Extracting actors...")
    movies_df['cast'] = movies_df['cast'].apply(convert_3_actors_only)
    
    print("Preparing final dataset...")
    final_ds = movies_df[['movie_id', 'title', 'keywords', 'genres', 'crew', 'cast']].copy()
    
    # Remove spaces from names (best practice for text analysis)
    # "James Cameron" → "JamesCameron" (prevents tokenization issues)
    for col in ['keywords', 'genres', 'crew', 'cast']:
        final_ds[col] = final_ds[col].apply(lambda x: [i.replace(' ', '') for i in x])
    
    # CREATE FEATURE VECTOR: Concatenate all features
    # tags = keywords + genres + director + actors
    # Example: ["action", "adventure", "SciFi", "JCameron", "Avatar"]
    # This becomes features for vectorization
    final_ds['tags'] = final_ds['keywords'] + final_ds['genres'] + final_ds['crew'] + final_ds['cast']
    
    # Convert tags list to string (required for vectorizer)
    # " ".join(): ["action", "adventure"] → "action adventure"
    final_ds['tags'] = final_ds['tags'].apply(lambda x: " ".join(x))
    
    # Convert to lowercase (standard preprocessing)
    # Why? "AVATAR" and "avatar" are same movie
    final_ds['tags'] = final_ds['tags'].apply(lambda x: x.lower())
    
    return final_ds

def create_similarity_matrix(final_ds):
    """
    TEXT VECTORIZATION & SIMILARITY COMPUTATION
    
    STEP 1: VECTORIZATION (Text → Numbers)
    ======================================
    Problem: ML algorithms need numbers, not text
    Solution: Convert text to numeric vectors
    
    CountVectorizer (Bag of Words):
      - Creates matrix: rows = movies, columns = words
      - Values: Count of word occurrences
      - Example:
        Movie 1: "action adventure" → [1, 1, 0, 0]  (1 action, 1 adventure)
        Movie 2: "action comedy" → [1, 0, 1, 0]     (1 action, 1 comedy)
      - max_features=5000: Keep only top 5000 most common words
      - stop_words='english': Remove common words (a, the, is) - they add noise
    
    Alternative Methods:
      - TfidfVectorizer: Weights rare words higher (better for text)
      - Word2Vec: Neural embeddings (better for semantic similarity)
      - BERT: Transformer embeddings (state-of-art, slow)
    
    STEP 2: SIMILARITY COMPUTATION (Vectors → Distances)
    =====================================================
    Problem: We have numeric vectors, need to measure similarity
    Solution: Cosine similarity (fast, intuitive)
    
    Cosine Similarity:
      - Measures angle between vectors
      - Range: 0 (perpendicular) to 1 (parallel)
      - Formula: cos(θ) = (A · B) / (||A|| ||B||)
      - Time: O(n²) preprocessing, O(1) lookup
    
    Alternative Metrics:
      - Euclidean Distance: Physical distance (doesn't work well for text)
      - Manhattan Distance: Taxicab distance
      - Jaccard Similarity: Set-based (good for categorical)
    
    RETURNS:
      vectors: Numeric representation (movies × words)
      similarity: Distance matrix (movies × movies)
    """
    print("Creating CountVectorizer...")
    # max_features=5000: Keep top 5000 words (balance between precision & speed)
    #   - Too low (100): Too much information loss
    #   - Too high (50000): Too slow, includes noise
    # stop_words='english': Remove 'the', 'a', 'is', etc.
    cv = CountVectorizer(max_features=5000, stop_words='english')
    
    print("Vectorizing tags...")
    # .fit_transform(): Learn from data AND convert
    # .toarray(): Convert sparse matrix to dense (memory trade-off)
    #   - Sparse: Only store non-zero values (memory efficient)
    #   - Dense: Store all values (faster computation)
    vectors = cv.fit_transform(final_ds['tags']).toarray()
    
    print("Computing cosine similarity...")
    # cosine_similarity(vectors): Returns matrix of all pairwise similarities
    # Shape: (5000, 5000) for 5000 movies
    # Time: ~30 seconds for 5000 movies
    # Can use sklearn.metrics.pairwise.cosine_similarity or scipy.spatial.distance
    similarity = cosine_similarity(vectors)
    
    return vectors, similarity

def save_model(final_ds, vectors, similarity):
    """
    SERIALIZATION: Save Model to Disk
    
    WHY SAVE THE MODEL?
      - Training takes 3+ minutes
      - Loading from disk takes <1 second
      - Better UX: API starts instantly
      - Reproducibility: Same model always loaded
    
    PICKLE FORMAT:
      - Binary Python serialization
      - Fast loading
      - Only Python (not language-agnostic like JSON)
      - Security risk if loading untrusted files (pickle execution)
    
    ALTERNATIVE FORMATS:
      - ONNX: Cross-platform, cross-language
      - Protocol Buffers: Google format
      - hdf5: Scientific data format
      - PMML: XML for statistical models
    
    WHAT WE SAVE:
      - final_ds: Movie metadata (title, movie_id)
      - vectors: TF-IDF vectors (used for new predictions)
      - similarity: Precomputed similarity matrix (fast lookups)
    
    WHY NOT SAVE countervectorizer?
      - We don't need it at inference time
      - Similarity is already computed
      - Save space: ~150MB instead of ~200MB
    
    PRODUCTION CONSIDERATIONS:
      - Model versioning (v1.0, v1.1, v2.0)
      - Model validation (test before deployment)
      - A/B testing (compare models)
      - Model monitoring (track accuracy over time)
    """
    model_data = {
        'final_ds': final_ds[['movie_id', 'title']],  # Keep only necessary columns
        'vectors': vectors,
        'similarity': similarity
    }
    
    # 'wb': Write in Binary mode
    # pickle.dump(): Serialize Python object to file
    with open('../models/recommendation_model.pkl', 'wb') as f:
        pickle.dump(model_data, f)
    
    print(f"✓ Model saved successfully!")
    print(f"  - Dataset size: {final_ds.shape[0]} movies")
    print(f"  - Features: {vectors.shape[1]}")

if __name__ == '__main__':
    """
    MAIN EXECUTION
    
    __name__ == '__main__': Only runs when script is executed directly
    (not when imported as module)
    
    Flow:
      1. Load & prepare data (2 min)
      2. Train model (2 min)
      3. Save to disk (10 sec)
      ✓ Ready for API!
    """
    try:
        print("=" * 60)
        print("Movie Recommendation Model Training & Serialization")
        print("=" * 60)
        
        final_ds = prepare_data()
        vectors, similarity = create_similarity_matrix(final_ds)
        save_model(final_ds, vectors, similarity)
        
        print("=" * 60)
        print("✓ Training complete! Model ready for the API.")
        print("=" * 60)
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

"""
================================================================================
ML CONCEPTS GLOSSARY
================================================================================

VECTORIZATION:
  Converting text into numeric format that ML algorithms can process
  Example: "action adventure" → [0.5, 0.3, 0.0, 0.1, ...]

TF-IDF (Term Frequency-Inverse Document Frequency):
  Weight words by how unique/important they are
  Common words (the, is) get low weight, unique words high weight

COSINE SIMILARITY:
  Measures how close two vectors are (0 = different, 1 = identical)
  Based on angle between vectors, not distance

PICKLE:
  Python's native serialization format (save/load Python objects)
  Fast but not portable to other languages

STEMMING:
  Reduce words to root form ("loves" → "lov", "running" → "runn")
  Simple rules, sometimes creates nonsensical stems

FEATURE ENGINEERING:
  Creating new variables from raw data to improve ML model
  Example: tags = genres + keywords + director + actors

N-GRAM:
  Sequence of N words ("new york" = 2-gram, "new york city" = 3-gram)
  Captures word relationships

SPARSE MATRIX:
  Matrix optimized for lots of zeros (efficient storage)
  Text vectorization creates sparse matrices

================================================================================
"""
