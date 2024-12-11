from multiprocessing.spawn import old_main_modules
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import json
import hashlib
import argparse
import requests
import re
import base64
import shutil

CACHE_FILE = "api_cache.json"

# Load or initialize cache
if os.path.exists(CACHE_FILE):
    print("Loading cache from file...")
    with open(CACHE_FILE, "r") as f:
        try:
            CACHE = json.load(f)
            print(f"Cache loaded with {len(CACHE)} entries.")
        except json.JSONDecodeError:
            print("Cache file is corrupted. Initializing a new cache.")
            CACHE = {}
else:
    print("No cache file found. Initializing a new cache.")
    CACHE = {}

def upload_png_files():
    """Read and encode all .png files in the current directory."""
    png_files = [f for f in os.listdir('.') if f.endswith('.png')]
    encoded_files = {}
    for file in png_files:
        with open(file, "rb") as f:
            encoded_files[file] = base64.b64encode(f.read()).decode('utf-8')
    return encoded_files

def save_cache():
    """Save the cache to a file."""
    with open(CACHE_FILE, "w") as f:
        json.dump(CACHE, f, indent=2)
    print("Cache saved successfully.")

def hash_request(data, filename):
    """Generate a hash for the data and filename to use as a cache key."""
    combined_data = {"data": data, "filename": filename}
    return hashlib.md5(json.dumps(combined_data, sort_keys=True).encode()).hexdigest()

def make_openai_request(data,filename):
    """Make a request to OpenAI API with caching."""

    url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
    token = os.environ.get("AIPROXY_TOKEN")
    if not token:
        raise EnvironmentError("AIPROXY_TOKEN environment variable is not set.")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    cache_key = hash_request(data,filename)

    # Check cache
    if cache_key in CACHE:
        print("Using cached response.")
        # print(type(CACHE[cache_key]))
        # print(CACHE[cache_key])
        return CACHE[cache_key]

    # Make API call
    import requests
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        CACHE[cache_key] = result  # Save to cache
        save_cache()  # Persist cache to file
        return result
    else:
        raise RuntimeError(f"OpenAI API request failed: {response.status_code} {response.text}")

def detect_outliers(df):
    """Detect outliers using the IQR method."""
    outlier_info = ""
    for column in df.select_dtypes(include=['number']).columns:
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]
        outlier_info += f"outlier_count for {column} is {len(outliers)}, "
    return outlier_info

def load_data(filename):
    """Load the dataset from a CSV file."""
    encodings = ['utf-8', 'latin1', 'ISO-8859-1']
    for encoding in encodings:
        try:
            return pd.read_csv(filename, encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"Error loading {filename}: Unable to decode file with tried encodings.")

def organize_files_into_folder(folder_name):
    """
    Move all .png and .md files in the current directory into a specified folder.

    Parameters:
    folder_name (str): Name of the folder to create and move files into.
    """
    current_dir = os.getcwd()  # Get the current directory
    target_dir = os.path.join(current_dir, folder_name)

    # Create the target folder if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)

    # List all files in the current directory
    files_to_move = [file for file in os.listdir(current_dir) if file.endswith(('.png', '.md'))]

    # Move each file to the target directory
    for file in files_to_move:
        src_path = os.path.join(current_dir, file)
        dest_path = os.path.join(target_dir, file)
        shutil.move(src_path, dest_path)
        print(f"Moved: {file} -> {folder_name}")

    if not files_to_move:
        print("No .png or .md files found to move.")

def basic_analysis(df):
    """Perform basic analysis on the dataset."""
    df_description = df.describe(include='all').to_markdown()
    insights = {
        "missing_values": df.isnull().sum().to_markdown(),
        "outliers": detect_outliers(df),
        'column': df.columns,
        'data_type': df.dtypes.to_markdown(),
        'numerical_features' : df.select_dtypes(include=['number']).columns,
        'numerical_missing_values' : df[df.select_dtypes(include=['number']).columns].describe().T.isnull().sum().to_markdown(),
        'numerical_unique_values' : df[df.select_dtypes(include=['number']).columns].describe().T.nunique().to_markdown(),
        'categories_features' : df.select_dtypes(include=['object']).columns,
        'categorical_missing_values' : df[df.select_dtypes(include=['object']).columns].describe().T.isnull().sum().to_markdown(),
        'categorical_unique' : df[df.select_dtypes(include=['object']).columns].describe().T.nunique().to_markdown(),
        'sample_data' : df.head(10).to_markdown(),

    }
    return df_description, insights

def sanitize_content(response):
    """Sanitize raw JSON-like content to make it JSON-compliant."""

    # Iterate through the string, considering boundaries
    for i in range(len(response) - 2):  # Avoid accessing out of bounds by subtracting 2
        # print("inside loop")
        if response[i] == '{' or response[i] == '[' or response[i] == '}' or response[i] == ']':
            print("inside first if statement")
            if response[i+1:i+3] == '\\n':  # Check if the next two characters are '\n'
                print('got one')
                # Replace the '\n' part
                response = response[:i+1] + response[i+3:]  # Skip the \n par     

    # Debugging output
    print("Sanitized content:\n", response)

    return response

def ask_llm_for_columns_and_visualizations(df,filename):
    """Ask the LLM to recommend relevant columns and visualizations."""
    prompt = f"""
    You are analyzing a dataset in the current directory with the following columns:
    {', '.join(df.columns)}
    
    Based on the dataset provide just give Python code 
    for visualizations for correlation metrices and outlier boxplot that can help understand the relationships 
    in the data and save it, don't show the plots.  Your response should be in the following format:
    {{
        "columns": ["col1", "col2", "col3"],
        "visualizations": ["code_for_visualization_1", "code_for_visualization_2"]
    }}
    """
    cache_key = hash_request(prompt,filename)
    
    # Check if the prompt response is cached
    if cache_key in CACHE:
        print("Using cached response.")
        content = CACHE[cache_key]["choices"][0]["message"]["content"]
        print(content)
        print("?????????")
        # print(json.loads(content))
        return json.loads(content)

    token = os.getenv("AIPROXY_TOKEN")
    if not token:
        raise EnvironmentError("AIPROXY_TOKEN environment variable is not set.")
    
    url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
    response = requests.post(
        url,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": "Provide Python code for visualizations that can help understand the relationships in the data provided. Provide response in JSON format and don't include any escape characters in your response."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        }
    )
    
    if response.status_code != 200:
        raise RuntimeError(f"Error from LLM API: {response.status_code} {response.text}")
    
    response_data = response.json()
    CACHE[cache_key] = response_data
    save_cache()
    print("Response cached.")

    content = response_data["choices"][0]["message"]["content"]
    print(content)
    print(json.loads(content))
    columns_and_visualizations = json.loads(content)

    return columns_and_visualizations


def run_generated_code(visualization_code):
    """Execute the generated code for visualizations."""
    try:
        exec(visualization_code)
    except Exception as e:
        print(f"Error executing visualization code: {e}")

def generate_visualizations(df, filename):
    """Generate visualizations based on LLM suggestions."""
    # Ask the LLM for relevant columns and visualization code
    columns_and_visualizations = ask_llm_for_columns_and_visualizations(df, filename)

    for key, value in columns_and_visualizations.items():
        print(f"Key: {key}, Value: {value}")

    relevant_columns = columns_and_visualizations.get("columns", [])
    visualization_code_list = columns_and_visualizations.get("visualizations", [])

    # Print the recommended columns
    print(f"Recommended columns for analysis: {', '.join(relevant_columns)}")

    # Apply the code for each visualization
    for code in visualization_code_list:
        # Replace placeholder filename with the actual filename
        updated_code = code.replace('your_dataset.csv', filename)
        print(f"Executing visualization code: {updated_code}")
        
        try:
            # Execute the code
            exec(updated_code.replace(f"df = pd.read_csv('{filename}')", ""), globals(), locals())

        except Exception as e:
            print(f"Error executing visualization code: {e}")


def narrate_story(summary, insights,filename):
    """Generate a story using the OpenAI API."""
    # Upload .png files and attach them to the request
    png_files = upload_png_files()
    print(f"Uploading {len(png_files)} PNG files.")

    prompt = (f"Analyze the dataset based on the following summary statistics and insights:\n\n"
             f"Summary: {json.dumps(summary, indent=2)}\n\n" 
             f"missing_values: {insights['missing_values']}\n\n"
             f"outliers: {insights['outliers']}\n\n"
             f"column: {insights['column']}\n\n"
             f"data_type: {insights['data_type']}\n\n"
             f"numerical_features: {insights['numerical_features']}\n\n"
             f"numerical_missing_values: {insights['numerical_missing_values']}\n\n"
             f"numerical_unique_values: {insights['numerical_unique_values']}\n\n"
             f"categories_features: {insights['categories_features']}\n\n"
             f"categorical_missing_values: {insights['categorical_missing_values']}\n\n"
             f"categorical_unique: {insights['categorical_unique']}\n\n"
             f"sample_data: {insights['sample_data']}\n\n"
             f"Write a detailed overview explaining the key insights, including how outliers might impact the results, "
             f"and suggest potential actions to handle them.")
    
    image_list = []
    for key, value in png_files.items():
        image_dict = {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{value}"
            },
        }
        image_list.append(image_dict)

    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Analyze the dataset based on the following summary statistics and insights and write a detailed overview of the data."},
            {"role": "user", "content": [
                {
                    "type": "text",
                    "text": prompt,
                },
                *image_list  # Unpack and append all dictionaries in `image_list`
            ]}
        ],
        "temperature": 0.5,
    }

    response = make_openai_request(data,filename)
    return response["choices"][0]['message']['content']

def save_outputs(markdown):
    """Save the generated Markdown and plots."""
    with open("README.md", "w") as f:
        f.write(markdown)

def main():
    parser = argparse.ArgumentParser(description="Autolysis: Automated Dataset Analysis")
    parser.add_argument("filename", type=str, help="Input CSV file")
    args = parser.parse_args()
    
    df = load_data(args.filename)
    summary, insights = basic_analysis(df)
    generate_visualizations(df, args.filename)
    markdown = narrate_story(summary, insights, args.filename)
    save_outputs(markdown)
    organize_files_into_folder(args.filename[:-4])

if __name__ == "__main__":
    main()
