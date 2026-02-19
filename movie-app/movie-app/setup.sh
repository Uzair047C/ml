#!/bin/bash
# Quick setup script for movie recommendation app

echo "🎬 Setting up Movie Recommendation App..."
echo ""

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "❌ Conda not found. Please install Miniconda from https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

echo "✓ Conda found"
echo ""

# Create environment
echo "📦 Creating Conda environment..."
conda env create -f environment.yml -y

echo ""
echo "🚀 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate environment:     conda activate movie-recommender"
echo "2. Copy CSV files to backend: cp ../tmdb_5000_*.csv backend/"
echo "3. Train model:              cd backend && python train_and_save_model.py"
echo "4. Start API:                python app.py"
echo "5. In another terminal:      cd frontend && python -m http.server 8000"
echo "6. Open browser:             http://localhost:8000"
echo ""
