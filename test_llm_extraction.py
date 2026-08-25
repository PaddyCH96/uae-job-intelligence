"""Test LLM extraction on mock job descriptions."""

from src.utils.llm import (
    check_ollama_health, get_available_models, extract_skills,
    extract_technologies, extract_sentiment, classify_industry,
    parse_json_array, parse_json_object
)

# 1. Health check
print("=== Ollama Health ===")
healthy = check_ollama_health()
print(f"Healthy: {healthy}")

if healthy:
    models = get_available_models()
    print(f"Available models: {models}")

# 2. Test JSON parsing
print("\n=== JSON Parsing Tests ===")
test1 = parse_json_array('Here are the skills: ["Python", "SQL", "AWS"]')
print(f"Test 1: {test1}")

test2 = parse_json_array('```json\n["Docker", "Kubernetes"]\n```')
print(f"Test 2 (code block): {test2}")

test3 = parse_json_object('{"sentiment_score": 0.5, "sentiment_label": "positive"}')
print(f"Test 3 (object): {test3}")

# 3. Mock job descriptions
mock_jobs = [
    {
        "title": "Senior Python Developer",
        "description": "We are looking for a Senior Python Developer with 5+ years experience in Python, Django, PostgreSQL, and AWS. Must have experience with Docker and CI/CD pipelines. Strong problem-solving skills required."
    },
    {
        "title": "Data Engineer",
        "description": "Seeking a Data Engineer to build and maintain data pipelines using Apache Spark, Airflow, and Snowflake. Experience with SQL, Python, and cloud platforms (AWS/GCP) required. Must understand ETL processes and data warehousing."
    },
    {
        "title": "DevOps Engineer",
        "description": "Looking for a DevOps Engineer experienced in Kubernetes, Docker, Terraform, and Jenkins. Strong Linux administration skills required. Experience with AWS or Azure cloud services preferred."
    },
    {
        "title": "Frontend Developer",
        "description": "Frontend Developer needed with React, TypeScript, and modern CSS. Experience with Next.js, Redux, and RESTful APIs. Must have 3+ years of web development experience."
    },
    {
        "title": "AI/ML Engineer",
        "description": "AI/ML Engineer to develop and deploy machine learning models using Python, TensorFlow, PyTorch, and scikit-learn. Experience with MLOps, Kubernetes, and cloud platforms required."
    }
]

print("\n=== LLM Extraction Tests ===")
for i, job in enumerate(mock_jobs, 1):
    print(f"\n--- Job {i}: {job['title']} ---")
    print(f"Description (first 100 chars): {job['description'][:100]}...")
    
    skills = extract_skills(job["description"])
    print(f"Skills: {skills}")
    
    techs = extract_technologies(job["description"])
    print(f"Technologies: {techs}")

print("\n=== All Tests Complete ===")
