**Project Title: Autolysis - Automated Data Analysis and Storytelling**
-----------------------------------------------------------------------

### **Project Overview**

The **Autolysis** project is an automated data analysis and storytelling tool powered by Python and a language model (GPT-4o-Mini). It accepts a CSV dataset, performs exploratory data analysis, generates insightful visualizations, and narrates a compelling story about the dataset in a Markdown file. This project is designed to work dynamically with any valid CSV file, making it versatile for analyzing diverse datasets.

### **Key Features**

1.  **Automated Data Analysis:**

    -   Generates summary statistics, identifies missing values, and highlights key correlations.
    -   Detects anomalies, clusters, and hierarchies within the data.
    -   Supports advanced analyses such as regression, feature importance, and time-series trends.
2.  **Visualizations:**

    -   Creates 1-3 charts (e.g., heatmaps, scatter plots, bar charts) as PNG images to illustrate insights.
    -   Enhances visualizations with titles, axis labels, and annotations for clarity.
3.  **Narrative Generation:**

    -   Leverages GPT-4o-Mini to craft a story about the dataset, including:
        -   Description of the data.
        -   Summary of the analysis performed.
        -   Insights discovered.
        -   Implications and actionable recommendations.
    -   Outputs the narrative as a `README.md` file.
4.  **Dynamic Prompts and Function Calls:**

    -   Uses the LLM efficiently, sending only necessary summaries, statistics, and key data points.
    -   Employs function calling to optimize analysis and token usage.
5.  **Robust Workflow:**

    -   Works with any valid CSV file without prior knowledge of its structure.
    -   Handles errors gracefully to ensure uninterrupted execution.

### **How It Works**

1.  **Input:**
    -   Run the script by passing a CSV file as an argument:

        bash

        Copy code

        `uv run autolysis.py dataset.csv`

2.  **Analysis and Visualization:**
    -   The script analyzes the dataset and creates relevant visualizations saved as PNG files.
3.  **Storytelling:**
    -   A Markdown file (`README.md`) is generated, narrating the findings and insights.

### **Sample Datasets**

-   `goodreads.csv`: Contains 10,000 books with details such as genres, ratings, and reviews.
-   `happiness.csv`: Data from the World Happiness Report, analyzing factors influencing happiness.
-   `media.csv`: Ratings of movies, TV series, and books provided by the course faculty.

### **Output**

For each dataset, the script generates:

1.  A `README.md` file containing:
    -   A structured narrative with data description, analysis, insights, and implications.
    -   Embedded visualizations.
2.  1-3 PNG visualizations (e.g., heatmaps, bar charts) illustrating key findings.

### **Technologies Used**

-   **Python** for data manipulation, analysis, and visualization.
-   **Pandas** for data processing and summary statistics.
-   **Seaborn** and **Matplotlib** for creating visualizations.
-   **OpenAI GPT-4o-Mini** via AI Proxy for generating narratives and suggesting analyses.

### **Project Goals**

-   Automate data exploration and storytelling for diverse datasets.
-   Generate actionable insights through efficient analysis and visualization.
-   Minimize human intervention by leveraging AI for dynamic decision-making.
