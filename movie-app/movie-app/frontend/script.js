/* ==============================================================================
   MOVIEMATCH - JAVASCRIPT MODULES
   ============================================================================== */

// ===== CONFIG MODULE =====
const CONFIG = {
    API_BASE: "http://localhost:5000",
    DEBOUNCE_DELAY: 300,
    TRENDING_LIMIT: 8,
    SEARCH_LIMIT: 5,
    RECOMMENDATIONS_LIMIT: 5
};

// ==============================================================================
// API SERVICE MODULE - Handle all API calls
// ==============================================================================
const APIService = (() => {
    /**
     * Fetch trending movies from TMDB
     */
    async function getTrendingMovies() {
        try {
            const response = await fetch(`${CONFIG.API_BASE}/tmdb/trending`);
            if (!response.ok) throw new Error("Failed to load trending movies");
            return await response.json();
        } catch (error) {
            console.error("Trending error:", error);
            throw error;
        }
    }

    /**
     * Search TMDB for movies
     */
    async function searchMovies(query) {
        try {
            const response = await fetch(
                `${CONFIG.API_BASE}/tmdb/search?query=${encodeURIComponent(query)}`
            );
            if (!response.ok) throw new Error("Search failed");
            return await response.json();
        } catch (error) {
            console.error("Search error:", error);
            throw error;
        }
    }

    /**
     * Get movie details from TMDB
     */
    async function getMovieDetails(movieId) {
        try {
            const response = await fetch(
                `${CONFIG.API_BASE}/tmdb/details?movie_id=${movieId}`
            );
            if (!response.ok) throw new Error("Failed to load details");
            return await response.json();
        } catch (error) {
            console.error("Details error:", error);
            throw error;
        }
    }

    /**
     * Get recommendations with TMDB data (ML + poster)
     */
    async function getRecommendations(movieName) {
        try {
            const response = await fetch(`${CONFIG.API_BASE}/tmdb/matching`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ movie_name: movieName })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error || "Failed to get recommendations");
            return data;
        } catch (error) {
            console.error("Recommendations error:", error);
            throw error;
        }
    }

    return {
        getTrendingMovies,
        searchMovies,
        getMovieDetails,
        getRecommendations
    };
})();

// ==============================================================================
// UI MODULE - Handle DOM manipulation
// ==============================================================================
const UIModule = (() => {
    /**
     * Get DOM elements
     */
    function getElements() {
        return {
            heroSection: document.getElementById("heroSection"),
            trendingSection: document.getElementById("trendingSection"),
            resultsSection: document.getElementById("resultsSection"),
            searchInput: document.getElementById("searchInput"),
            autocompleteDropdown: document.getElementById("autocompleteDropdown"),
            trendingGrid: document.getElementById("trendingGrid"),
            resultsContent: document.getElementById("resultsContent"),
            resultsTitle: document.getElementById("resultsTitle"),
            resultsSubtitle: document.getElementById("resultsSubtitle"),
            errorMessage: document.getElementById("errorMessage")
        };
    }

    /**
     * Show error message
     */
    function showError(message) {
        const elements = getElements();
        elements.errorMessage.textContent = message;
        elements.errorMessage.classList.add("show");
        setTimeout(() => {
            elements.errorMessage.classList.remove("show");
        }, 5000);
    }

    /**
     * Create movie card HTML
     */
    function createMovieCard(movie) {
        const card = document.createElement("div");
        card.className = "movie-card";
        card.style.cursor = "pointer";
        
        const poster = movie.poster_url || "https://via.placeholder.com/200x300?text=No+Poster";
        const title = movie.title || "Unknown";
        const rating = movie.vote_average ? movie.vote_average.toFixed(1) : "N/A";
        const year = movie.release_date ? movie.release_date.substring(0, 4) : "";

        card.innerHTML = `
            <img src="${poster}" alt="${title}" class="movie-card-image" 
                 onerror="this.src='https://via.placeholder.com/200x300?text=No+Poster'">
            <div class="movie-card-content">
                <div class="movie-card-title">${title}</div>
                <div class="movie-card-info">
                    <div class="rating">${rating}</div>
                </div>
                <div class="movie-card-year">${year}</div>
            </div>
        `;
        
        // Make trending movie cards clickable to search for recommendations
        card.addEventListener("click", () => {
            document.getElementById("searchInput").value = title;
            SearchModule.handleSearchClick();
        });
        
        return card;
    }

    /**
     * Create result card HTML
     */
    function createResultCard(rec) {
        const card = document.createElement("div");
        card.className = "result-card";

        const poster = rec.poster_url || rec.posters || "https://via.placeholder.com/250x350?text=No+Poster";
        const title = rec.title || "Unknown";
        const score = (rec.similarity_score * 100).toFixed(0);
        const rating = rec.vote_average ? rec.vote_average.toFixed(1) : "N/A";
        const releaseDate = rec.release_date ? rec.release_date.substring(0, 4) : "";
        const overview = rec.overview || "No overview available";

        card.innerHTML = `
            <img src="${poster}" alt="${title}" class="result-poster" 
                 onerror="this.src='https://via.placeholder.com/250x350?text=No+Poster'">
            <div class="result-content">
                <div class="result-title">${title}</div>
                <div class="match-score">🎯 ${score}% Match</div>
                <div class="result-meta">
                    <span class="result-rating">${rating}</span>
                    <span>${releaseDate}</span>
                </div>
                <div class="result-overview">${overview}</div>
            </div>
        `;
        return card;
    }

    /**
     * Clear autocomplete dropdown
     */
    function clearAutocomplete() {
        const elements = getElements();
        elements.autocompleteDropdown.innerHTML = "";
        elements.autocompleteDropdown.classList.remove("show");
    }

    /**
     * Create autocomplete item
     */
    function createAutocompleteItem(text, onClick) {
        const item = document.createElement("div");
        item.className = "autocomplete-item";
        item.textContent = text;
        item.onclick = onClick;
        return item;
    }

    /**
     * Show loading state
     */
    function showLoading(message) {
        const elements = getElements();
        elements.resultsContent.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <p>${message}</p>
            </div>
        `;
    }

    /**
     * Show no results message
     */
    function showNoResults() {
        const elements = getElements();
        elements.resultsContent.innerHTML = `
            <div class="no-results">
                <h3>No recommendations found</h3>
                <p>Try searching for a different movie!</p>
            </div>
        `;
    }

    return {
        getElements,
        showError,
        createMovieCard,
        createResultCard,
        clearAutocomplete,
        createAutocompleteItem,
        showLoading,
        showNoResults
    };
})();

// ==============================================================================
// NAVIGATION MODULE - Handle page navigation
// ==============================================================================
const NavigationModule = (() => {
    /**
     * Show home page (hero + trending)
     */
    function showHome() {
        const el = UIModule.getElements();
        el.heroSection.style.display = "block";
        el.trendingSection.classList.remove("hidden");
        el.resultsSection.classList.remove("show");
        el.searchInput.value = "";
        UIModule.clearAutocomplete();
    }

    /**
     * Show results page
     */
    function showResults() {
        const el = UIModule.getElements();
        el.heroSection.style.display = "none";
        el.trendingSection.classList.add("hidden");
        el.resultsSection.classList.add("show");
    }

    // Initialize navigation buttons
    function init() {
        document.querySelectorAll(".back-btn").forEach(btn => {
            btn.addEventListener("click", showHome);
        });

        document.querySelectorAll("[onclick*='showHome']").forEach(el => {
            el.onclick = showHome;
        });
    }

    return { showHome, showResults, init };
})();

// ==============================================================================
// TRENDING MODULE - Load and display trending movies
// ==============================================================================
const TrendingModule = (() => {
    /**
     * Load and display trending movies
     */
    async function loadTrending() {
        try {
            console.log("Loading trending movies...");
            const data = await APIService.getTrendingMovies();
            const elements = UIModule.getElements();
            elements.trendingGrid.innerHTML = "";

            const movies = data.results.slice(0, CONFIG.TRENDING_LIMIT);
            console.log("Got", movies.length, "trending movies");
            
            movies.forEach(movie => {
                const card = UIModule.createMovieCard(movie);
                elements.trendingGrid.appendChild(card);
            });
        } catch (error) {
            console.error("Error loading trending:", error);
            UIModule.showError("Failed to load trending movies");
        }
    }

    return { loadTrending };
})();

// ==============================================================================
// SEARCH MODULE - Handle autocomplete search
// ==============================================================================
const SearchModule = (() => {
    let debounceTimer = null;

    /**
     * Initialize search functionality
     */
    function init() {
        const elements = UIModule.getElements();

        elements.searchInput.addEventListener("input", handleInput);
        elements.searchInput.addEventListener("keypress", handleKeyPress);

        // Close autocomplete when clicking outside
        document.addEventListener("click", (e) => {
            if (!e.target.closest(".search-box")) {
                UIModule.clearAutocomplete();
            }
        });
    }

    /**
     * Handle input with debouncing
     */
    function handleInput(e) {
        clearTimeout(debounceTimer);
        const query = e.target.value.trim();

        if (query.length < 2) {
            UIModule.clearAutocomplete();
            return;
        }

        debounceTimer = setTimeout(() => {
            performSearch(query);
        }, CONFIG.DEBOUNCE_DELAY);
    }

    /**
     * Handle Enter key to search
     */
    function handleKeyPress(e) {
        if (e.key === "Enter") {
            const query = e.target.value.trim();
            if (query) {
                handleSearchClick();
            }
        }
    }

    /**
     * Perform search and show autocomplete
     */
    async function performSearch(query) {
        try {
            console.log("Searching for:", query);
            const data = await APIService.searchMovies(query);
            const elements = UIModule.getElements();
            UIModule.clearAutocomplete();

            const results = data.results.slice(0, CONFIG.SEARCH_LIMIT);
            console.log("Search results:", results);
            
            if (results.length === 0) {
                const item = UIModule.createAutocompleteItem("No movies found", () => {});
                elements.autocompleteDropdown.appendChild(item);
            } else {
                results.forEach(movie => {
                    const item = UIModule.createAutocompleteItem(movie.title, () => {
                        console.log("Selected movie:", movie.title);
                        elements.searchInput.value = movie.title;
                        UIModule.clearAutocomplete();
                    });
                    elements.autocompleteDropdown.appendChild(item);
                });
            }

            elements.autocompleteDropdown.classList.add("show");
            console.log("Autocomplete shown with", results.length, "results");
        } catch (error) {
            console.error("Search error:", error);
            UIModule.showError("Error searching movies");
        }
    }

    /**
     * Handle search button click
     */
    function handleSearchClick() {
        const movieName = document.getElementById("searchInput").value.trim();
        console.log("Search clicked for:", movieName);

        if (!movieName) {
            UIModule.showError("Please enter a movie name");
            return;
        }

        NavigationModule.showResults();
        UIModule.showLoading(`Finding recommendations for "${movieName}"...`);
        performRecommendations(movieName);
    }

    /**
     * Get recommendations
     */
    async function performRecommendations(movieName) {
        try {
            const data = await APIService.getRecommendations(movieName);
            ResultsModule.displayResults(data, movieName);
        } catch (error) {
            console.error("Error:", error);
            UIModule.showError(error.message || "Failed to get recommendations");
            NavigationModule.showHome();
        }
    }

    return { init, handleSearchClick };
})();

// ==============================================================================
// RESULTS MODULE - Display recommendation results
// ==============================================================================
const ResultsModule = (() => {
    /**
     * Display recommendation results
     */
    function displayResults(data, movieName) {
        const recommendations = data.recommendations || [];
        const elements = UIModule.getElements();

        elements.resultsTitle.textContent = `Recommendations for "${movieName}"`;
        elements.resultsSubtitle.textContent =
            `Based on your selected movie, here are ${recommendations.length} similar films`;

        if (recommendations.length === 0) {
            UIModule.showNoResults();
            return;
        }

        const grid = document.createElement("div");
        grid.className = "results-grid";

        recommendations.forEach((rec) => {
            const card = UIModule.createResultCard(rec);
            grid.appendChild(card);
        });

        elements.resultsContent.innerHTML = "";
        elements.resultsContent.appendChild(grid);
    }

    return { displayResults };
})();

// ==============================================================================
// INITIALIZATION
// ==============================================================================
document.addEventListener("DOMContentLoaded", function() {
    // Initialize modules
    NavigationModule.init();
    SearchModule.init();

    // Load trending movies
    TrendingModule.loadTrending();

    // Setup search button
    const searchBtn = document.querySelector(".search-box button");
    if (searchBtn) {
        searchBtn.addEventListener("click", SearchModule.handleSearchClick);
    }
});
