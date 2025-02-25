import requests
import base64
from datetime import datetime, timedelta
import csv
from transformers import pipeline

# Step 1: Set up personal access token (replace with your token)
personal_access_token = "INSERT-GITHUB-TOKEN-HERE"

# Step 2: Define category (change this to any category you find interesting)
category = "machine learning"

# Step 3: Calculate date one week ago for filtering recent updates
one_week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

# Step 4: Set up headers for authenticated API requests
headers = {
    "Authorization": f"token {personal_access_token}"
}

# Step 5: Fetch trending repositories from GitHub API
url = "https://api.github.com/search/repositories"
params = {
    "q": f"{category} pushed:>{one_week_ago}",  # Repos updated in the last week
    "sort": "stars",                          # Sort by popularity
    "order": "desc",
    "per_page": 10                            # Limit to top 10 repos
}
response = requests.get(url, params=params, headers=headers)
repositories = response.json()["items"]

# Step 6: Initialize summarization pipeline with a free Hugging Face model
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

# Step 7: Collect repository data
repos_data = []
for repo in repositories:
    name = repo["name"]
    url = repo["html_url"]
    full_name = repo["full_name"]
    
    # Fetch README content
    readme_url = f"https://api.github.com/repos/{full_name}/readme"
    readme_response = requests.get(readme_url, headers=headers)
    
    if readme_response.status_code == 200:
        # Decode base64-encoded README content
        readme_content = base64.b64decode(readme_response.json()["content"]).decode("utf-8")
        # Truncate to 2000 characters to keep summarization efficient
        text = readme_content[:2000]
    else:
        # Fallback to description if README is unavailable
        text = repo["description"] or "No description available."
    
    # Generate a one-line summary
    try:
        summary = summarizer(text, max_length=30, min_length=10, do_sample=False)[0]["summary_text"]
    except Exception:
        summary = "Summary generation failed."
    
    # Add data to list
    repos_data.append({"name": name, "url": url, "summary": summary})

# Step 8: Write data to CSV file
with open("trending_repos.csv", "w", newline="") as csvfile:
    fieldnames = ["name", "url", "summary"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for repo in repos_data:
        writer.writerow(repo)

print("Script completed. Check 'trending_repos.csv' for results.")