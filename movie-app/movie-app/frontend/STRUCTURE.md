# Frontend Modular Structure

## 📁 File Organization

```
frontend/
├── index.html          # Lean HTML structure only
├── style.css           # All CSS styling (separted)
├── script.js           # All JavaScript modules
└── STRUCTURE.md        # This file
```

## 🏗️ Architecture

### `index.html` (Lean Markup)
- **Size**: ~85 lines
- **Content**: Structure only
- HTML elements with IDs and classes
- No inline CSS or JavaScript
- Links to external CSS and JS files
- Clean, readable, maintainable

### `style.css` (Separated Styling)
- **Size**: ~430 lines
- **Organization**:
  - CSS Variables (colors, spacing)
  - Global styles
  - Component styles (navbar, cards, forms)
  - Responsive design (@media queries)
  - Animations and transitions
- Easily themeable via CSS variables
- Mobile-friendly responsive design

### `script.js` (Modular JavaScript)
- **Size**: ~450 lines
- **Modules**:

#### 1. **CONFIG Module**
- API endpoint configuration
- Constants (debounce delay, page limits)

#### 2. **APIService Module**
- `getTrendingMovies()` - Fetch trending from TMDB
- `searchMovies(query)` - Search autocomplete
- `getMovieDetails(movieId)` - Movie details
- `getRecommendations(movieName)` - ML + TMDB enriched

#### 3. **UIModule Module**
- `getElements()` - DOM element references
- `showError(message)` - Error toast
- `createMovieCard()` - Movie card HTML
- `createResultCard()` - Result card HTML
- `showLoading()`, `showNoResults()` - UI states

#### 4. **NavigationModule Module**
- `showHome()` - Display home page
- `showResults()` - Display results
- Event listener initialization

#### 5. **TrendingModule Module**
- `loadTrending()` - Load and display trending movies

#### 6. **SearchModule Module**
- `init()` - Set up search event listeners
- `handleInput()` - Debounced search input
- `performSearch()` - Autocomplete search
- `handleSearchClick()` - Search button handler

#### 7. **ResultsModule Module**
- `displayResults(data, movieName)` - Render recommendation results

## ✨ Benefits of This Structure

| Aspect | Benefit |
|--------|---------|
| **Separation of Concerns** | HTML = Structure, CSS = Style, JS = Logic |
| **Reusability** | Modules can be reused/extended |
| **Maintainability** | Easy to find and fix bugs |
| **Scalability** | Easy to add new features |
| **Performance** | CSS/JS cached by browser separately |
| **Readability** | Clean code, clear intent |
| **Testing** | Easy to unit test modules |

## 🔄 Module Communication

```
User Interaction (onclick)
    ↓
NavigationModule / SearchModule
    ↓
APIService (fetch data)
    ↓
UIModule (render UI)
    ↓
Display Results
```

## 🚀 How to Extend

### Adding a New Feature:
1. Add new module in `script.js`
2. Add styles to `style.css` 
3. Add HTML elements to `index.html`
4. Call module functions from other modules

### Example: Adding Favorites
```javascript
const FavoritesModule = (() => {
    let favorites = [];
    
    function add(movieId) {
        favorites.push(movieId);
        localStorage.setItem('favorites', JSON.stringify(favorites));
    }
    
    function remove(movieId) {
        favorites = favorites.filter(id => id !== movieId);
        localStorage.setItem('favorites', JSON.stringify(favorites));
    }
    
    return { add, remove };
})();
```

## 📋 Checklist for New Files

When adding to this project:
- [ ] HTML = Structure (no inline CSS/JS)
- [ ] CSS = In style.css (use classes)
- [ ] JS = In script.js modules (with clear naming)
- [ ] Comment your code
- [ ] Use meaningful variable names
- [ ] Keep modules focused (single responsibility)

## 🎯 Best Practices Applied

✅ **Modular Design** - Each module has one responsibility  
✅ **IIFE Pattern** - Modules use Immediately Invoked Function Expressions  
✅ **No Global Pollution** - All functions namespaced in modules  
✅ **DRY Principle** - Don't Repeat Yourself  
✅ **Responsive** - Mobile-first CSS  
✅ **Accessibility** - Semantic HTML  
✅ **Error Handling** - Try/catch blocks  
✅ **Comments** - Explain what, why, how  

## 📱 Responsive Breakpoints

- **Desktop**: 1400px max-width
- **Tablet**: 768px breakpoint
- **Mobile**: Full width with adjusted grid

## 🔗 File Dependencies

```
index.html
├── style.css (linked)
└── script.js (linked)
    └── Fetches from: http://localhost:5000
        ├── /tmdb/trending
        ├── /tmdb/search
        ├── /tmdb/details
        └── /tmdb/matching
```
