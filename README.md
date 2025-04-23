# 📊 Profit & Breakeven Calculator

A web application built with Streamlit to help businesses analyze their breakeven point, project future financial performance based on detailed costs, and compare different scenarios.

<!-- Optional: Add a screenshot of the running application -->
<!-- ![App Screenshot](link_to_your_screenshot.png) -->

## Features

*   **Breakeven Calculation:** Determines the number of orders and revenue needed per month to cover all costs.
*   **Detailed Cost Inputs:**
    *   **Fixed Costs:** Input monthly marketer payments and average daily ad spend.
    *   **Variable Costs:** Input as a fixed dollar amount per order OR as a percentage of the selling price.
*   **Profit Goal Analysis:** Calculate the required orders and revenue to achieve a specific monthly profit target.
*   **Monthly & Weekly Projections:** Simulate revenue, costs, and profit over a chosen period, incorporating an optional monthly growth rate in orders.
*   **Time to Profitability:** Estimates the week and month when cumulative profit is projected to become positive.
*   **Visualizations:**
    *   Monthly Profit Trend (Bar Chart)
    *   Monthly Revenue Breakdown (Stacked Bar Chart showing Variable Costs, Fixed Costs, and Profit)
    *   Cumulative Profit Trend (Line Chart)
*   **Scenario Comparison:** Save a complete set of inputs and results, then change parameters to see a side-by-side comparison with the saved scenario.
*   **Excel Export:** Download a detailed report containing weekly projections and monthly summaries.

## Technology Stack

*   **Python:** Core programming language.
*   **Streamlit:** Framework for building the interactive web application UI.
*   **Pandas:** Library for data manipulation and creating Excel reports.

## Setup and Installation

Follow these steps to run the application locally:

1.  **Prerequisites:**
    *   Python 3.7+ installed.
    *   Git installed.

2.  **Clone the Repository:**
    ```bash
    git clone https://github.com/YouROS12/profit_calculator.git
    cd profit_calculator
    ```

3.  **Create a Virtual Environment (Recommended):**
    *   **Windows:**
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```
    *   **macOS/Linux:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

4.  **Install Dependencies:**
    Make sure you have a `requirements.txt` file in the project directory (if not, create one using `pip freeze > requirements.txt` after installing the necessary libraries). Then run:
    ```bash
    pip install -r requirements.txt
    ```
    *(Ensure `requirements.txt` includes at least `streamlit`, `pandas`, and `openpyxl`)*

## Usage

1.  **Run the Streamlit App:**
    Make sure your virtual environment is activated. Navigate to the project directory in your terminal and run:
    ```bash
    # IMPORTANT: Replace 'your_app_script.py' with the actual name of your Python script
    # (e.g., vitasana_simulator.py or app.py)
    streamlit run your_app_script.py
    ```

2.  **Access the App:**
    Streamlit will automatically open the application in your default web browser. If not, the terminal will provide a local URL (usually `http://localhost:8500`) that you can open manually.

3.  **Interact:**
    Use the sidebar to input your business parameters (costs, price, goals, etc.). The main panel will update automatically with calculations, projections, charts, and the scenario comparison tool.