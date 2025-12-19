# Configuration Guide

This guide explains how to configure the CPJ framework for your environment.

## API Configuration

Each script in the pipeline requires API configuration. You have two options:

### Option 1: Environment Variables (Recommended)

Create a `.env` file in the project root:

```bash
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_API_KEY=your-api-key-here
```

Then in your scripts:
```python
from dotenv import load_dotenv
load_dotenv()

# API credentials will be loaded automatically
```

### Option 2: Direct Configuration

Edit each script directly:

```python
os.environ["OPENAI_API_BASE"] = "YOUR_API_BASE_URL"
os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY"
```

## Model Configuration

### Recommended Models

The framework was tested with:

**Step 1 - Caption Generation:**
- Qwen2.5-VL-72B-Instruct
- GPT-5-mini
- GPT-4 Vision

**Step 2 - VQA Generation:**
- GPT-5-Nano
- Qwen-VL-Chat

**Step 3 - Answer Selection:**
- GPT-4
- GPT-5-mini

### Configuring Models

In each script, update the model name:

```python
model = ChatOpenAI(
    model="gpt-4",  # Replace with your model
    temperature=0,
    max_retries=3,
    timeout=30,
)
```

### Model-Specific Parameters

**For GPT models:**
```python
model = ChatOpenAI(
    model="gpt-4",
    temperature=0.5,
    max_tokens=400,
    top_p=0.8,
)
```

**For models with reasoning (e.g., GPT-5-Nano):**
```python
model = ChatOpenAI(
    model="gpt-5-nano",
    reasoning_effort="medium",  # or "low", "high"
    verbosity="low",
    max_retries=2,
    timeout=30,
)
```

## Data Paths

Update input/output file paths in each script:

```python
# Step 1
input_json = "path/to/your/input.json"
output_json = "path/to/your/output.json"

# Step 2
input_json = "path/to/step1/output.json"
output_json = "path/to/step2/output.json"

# Step 3
input_file = "path/to/step2/output.json"
output_file = "path/to/final/output.json"
```

## Threshold Configuration

### Caption Quality Threshold (Step 1)

Adjust the quality threshold for caption refinement:

```python
threshold = 8  # Captions scoring below 8/10 will be refined
```

Lower threshold = fewer refinements (faster, potentially lower quality)
Higher threshold = more refinements (slower, higher quality)

### Batch Size (All Steps)

For API rate limiting:

```python
batch_size = 5  # Process 5 items concurrently
```

Adjust based on your API rate limits.

## Alternative API Providers

### Using Alibaba Cloud (Qwen Models)

```python
os.environ["OPENAI_API_BASE"] = "https://dashscope.aliyuncs.com/compatible-mode/v1"
os.environ["OPENAI_API_KEY"] = "your-dashscope-api-key"

model = ChatOpenAI(
    model="qwen2.5-vl-72b-instruct",
    temperature=0.5,
    max_retries=3
)
```

### Using Azure OpenAI

```python
os.environ["OPENAI_API_BASE"] = "https://your-resource.openai.azure.com/"
os.environ["OPENAI_API_KEY"] = "your-azure-api-key"
os.environ["OPENAI_API_VERSION"] = "2023-05-15"
os.environ["OPENAI_API_TYPE"] = "azure"

model = ChatOpenAI(
    model="gpt-4",
    deployment_name="your-deployment-name"
)
```

## Troubleshooting

### API Key Not Found

**Error:** `openai.error.AuthenticationError: No API key provided`

**Solution:** Ensure API credentials are set before importing ChatOpenAI:
```python
import os
os.environ["OPENAI_API_KEY"] = "your-key"

from langchain_openai import ChatOpenAI
```

### Rate Limit Exceeded

**Error:** `openai.error.RateLimitError: Rate limit exceeded`

**Solution:** Reduce batch size or add delays:
```python
batch_size = 3  # Reduce concurrent requests
await asyncio.sleep(2)  # Add delay between batches
```

### Model Not Found

**Error:** `openai.error.InvalidRequestError: Model X does not exist`

**Solution:** Check available models for your API:
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Timeout Errors

**Solution:** Increase timeout:
```python
model = ChatOpenAI(
    model="gpt-4",
    timeout=60,  # Increase from 30 to 60 seconds
    max_retries=5  # Increase retries
)
```

## Best Practices

1. **Use environment variables** for API credentials (never commit keys to git)
2. **Start with small batches** to test configuration
3. **Monitor API usage** to avoid unexpected costs
4. **Save intermediate results** in case of interruptions
5. **Use appropriate models** based on task complexity:
   - Simple tasks: Use smaller/faster models
   - Complex reasoning: Use larger/more capable models

## Example Configuration File

Create `config.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
API_KEY = os.getenv("OPENAI_API_KEY")

# Model Configuration
CAPTION_MODEL = "gpt-5-mini"
VQA_MODEL = "gpt-5-nano"
JUDGE_MODEL = "gpt-4"

# Processing Configuration
CAPTION_THRESHOLD = 8
BATCH_SIZE = 5
TIMEOUT = 30
MAX_RETRIES = 3

# File Paths
DATA_DIR = "data"
OUTPUT_DIR = "output"
```

Then import in your scripts:
```python
from config import *

os.environ["OPENAI_API_BASE"] = API_BASE
os.environ["OPENAI_API_KEY"] = API_KEY

model = ChatOpenAI(
    model=CAPTION_MODEL,
    timeout=TIMEOUT,
    max_retries=MAX_RETRIES
)
```

## Support

For configuration issues, please:
1. Check this guide first
2. Review the script comments
3. Open an issue on GitHub with your (sanitized) configuration
