# miXologist 🍸

## Overview
miXologist is an interactive cocktail recommendation web application that allows users to generate custom cocktail recipes based on their preferred ingredients, drink preferences, and moods. The application features a visually appealing landing page, an intuitive menu for inputting ingredients, and a recommendation page for mood-based cocktail suggestions.

## Features
- **Landing Page**: A beautifully designed welcome page with a hand-drawn aesthetic.
- **Menu Page**: Allows users to input ingredients and receive a tailored cocktail recipe.
- **Mood-Based Recommendation**: Suggests drinks based on the user's mood.
- **Dynamic UI**: Responsive and visually engaging design with interactive elements.

## Technologies Used
- **Frontend**: HTML, CSS (custom styling with Flexbox and absolute positioning)
- **Backend**: Flask (Python-based API for generating cocktail recommendations)
- **API Integration**: Uses OpenAI API for generating cocktail ideas, substitutions, and descriptions

## Installation & Setup
### Prerequisites
- Python 3.x installed
- Flask installed (`pip install flask`)

### Steps to Run the Project
1. Clone this repository:
   ```bash
   git clone https://github.com/ShafeiW/JourneyHacks-2025.git
   cd mixologist
   ```
2. Install dependencies:
   ```bash
   pip install flask openai
   ```
3. Start the Flask backend:
   ```bash
   python app.py
   ```
4. Open `landingpage.html` in a web browser to access the application.

## Project Structure
```
miXologist/
│── assets/              # Contains images, icons, and style assets
│── static/              # CSS, JS, and frontend assets
│── templates/           # HTML files (landingpage.html, index.html, recommendation.html)
│── app.py               # Flask API for cocktail generation
│── README.md            # Project documentation
```

## API Endpoints
- `POST /generate-cocktail`: Generates a cocktail based on user-input ingredients
- `GET /recommend-cocktail-by-mood?mood=happy`: Returns a cocktail suggestion based on mood

## Future Improvements
- Implement user authentication for saving favorite cocktails
- Expand ingredient substitution database
- Add animations and transitions for smoother UI interactions



