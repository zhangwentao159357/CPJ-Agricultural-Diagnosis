# coding: utf-8
"""
Caption Generation Script
This script generates image captions for agricultural images using Vision-Language Models.

Usage:
    python caption_generation.py --input input.json --output output.json

Features:
    - Generates descriptive captions using VLM with few-shot prompting
    - Describes visual features and disease symptoms without naming crops or diseases
    - Supports base64-encoded images with automatic error handling
"""

import argparse
import os
import base64
import json
import time
import re
from collections import OrderedDict
from tenacity import retry, stop_after_attempt, wait_exponential
from langchain_openai import ChatOpenAI
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

# ========== Configuration ==========
os.environ["OPENAI_API_BASE"] = "YOUR_API_BASE_URL"
os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY"

# ========== Parse Command Line Arguments ==========
parser = argparse.ArgumentParser(description="Generate image captions for agricultural images")
parser.add_argument("--input", type=str, required=True, help="Path to input JSON file")
parser.add_argument("--output", type=str, required=True, help="Path to output JSON file")
args = parser.parse_args()

input_json = args.input
output_json = args.output

# ========== Define Output Format ==========
response_schemas = [
    ResponseSchema(
        name="image_caption",
        description="Description of the plant's visual features and any disease symptoms, including morphology, color, distribution, size, and condition, without naming the plant or disease."
    )
]
output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
format_instructions = output_parser.get_format_instructions()

# ========== System Prompt ==========
system_template = """You are an expert agricultural assistant specializing in describing plant conditions from images.

## Core Task
Describe the visual features of the plant and any disease symptoms in the image, without identifying the plant or disease names.

## Key Requirements
1. Focus on describing the plant's morphology, color, and overall condition.
2. If disease symptoms are present, describe their appearance: color, shape, distribution, size, quantity, and extent.
3. If no disease is visible, state that the plant appears healthy.
4. Assess the severity and stage of any symptoms based on visual cues.
5. Keep the description concise (90-100 words).
6. If uncertain about features, indicate "unable to describe clearly" or "need more images".

## Output Format
{format_instructions}
"""
system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

# ========== Few-shot Examples ==========
examples = [
    {
        "input": "Describe the visual features of the plant and any disease symptoms in the image, including morphology, color, distribution, size, etc., without identifying the plant or disease names.",
        "output": '{"image_caption": "The plant has long, slender leaves with numerous orange-brown pustules scattered on the surface. The leaves show premature browning and some collapse, contrasting with greener plants in the background. The symptoms suggest a fungal infection that reduces plant vigor, with pustules measuring 1-2 mm in diameter. The condition appears moderate, affecting approximately 30% of the leaf area."}'
    },
    {
        "input": "Describe the visual features of the plant and any disease symptoms in the image, including morphology, color, distribution, size, etc., without identifying the plant or disease names.",
        "output": '{"image_caption": "The leaf displays dark-brown, irregular lesions with surrounding yellowing, indicating tissue necrosis. Lesions vary in size from 5-10 mm and are distributed randomly across the leaf surface. The plant shows signs of premature aging, with some areas wilting. The severity is high, covering about 40% of the leaf, and the infection seems advanced."}'
    },
    {
        "input": "Describe the visual features of the plant and any disease symptoms in the image, including morphology, color, distribution, size, etc., without identifying the plant or disease names.",
        "output": '{"image_caption": "The leaf exhibits white, powdery patches that are diffuse and cover portions of the upper surface. The patches have a fuzzy texture and are approximately 5-15 mm in diameter. The plant otherwise appears green and robust, but the symptoms reduce leaf photosynthesis. The infection is at an early stage, affecting around 20% of the leaf."}'
    }
]

# ========== Build Prompt Templates ==========
example_human = HumanMessagePromptTemplate.from_template("{input}")
example_ai = HumanMessagePromptTemplate.from_template("{output}")  # Changed to AIMessagePromptTemplate for accuracy

human_template = "Describe the visual features of the plant and any disease symptoms in the image, including morphology, color, distribution, size, etc., without identifying the plant or disease names."
human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

# Pre-build example messages (for few-shot)
example_messages = []
for example in examples:
    example_messages.append(example_human.format(**example))
    example_messages.append(example_ai.format(**example))

# Build complete prompt (few-shot version)
chat_prompt = ChatPromptTemplate.from_messages(
    [system_message_prompt] + example_messages + [human_message_prompt]
)

# ========== Initialize VLM Model ==========
model = ChatOpenAI(model="qwen2.5-vl-72b-instruct",
    temperature=0.1,           # Low temperature for deterministic output
    max_tokens=400,            # Shorter output for concise precision
    top_p=0.8,                 # Lower top_p to limit candidate token range
    frequency_penalty=0.3,     # Increase frequency penalty to avoid repetition
    presence_penalty=0.2,      # Light presence penalty to maintain topic focus
    max_retries=3
)

# ========== JSON Repair Function ==========
def extract_and_fix_json(text):
    """Extract and fix JSON format from text"""
    if not isinstance(text, str) or not text.strip():
        return {"image_caption": "No valid response"}

    text = text.strip()

    # First try direct parsing
    try:
        result = json.loads(text)
        if isinstance(result, dict) and "image_caption" in result:
            return {"image_caption": str(result.get("image_caption", ""))}
    except:
        pass

    # Try to find JSON object
    start_idx = text.find('{')
    end_idx = text.rfind('}')

    if start_idx >= 0 and end_idx > start_idx:
        json_str = text[start_idx:end_idx + 1]
        try:
            # Quickly fix common JSON format errors
            json_str = json_str.replace("'", '"')
            json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
            json_str = re.sub(r'([{,])\s*([^"{}\[\]]+?)\s*:', r'\1"\2":', json_str)

            result = json.loads(json_str)
            if isinstance(result, dict):
                return {"image_caption": str(result.get("image_caption", ""))}
        except:
            pass

    # If all attempts fail, return a simple JSON containing the original text
    return {"image_caption": text[:300] + ("..." if len(text) > 300 else "")}

# ========== Retry Decorator for API Calls ==========
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def call_model_with_retry(model, message_content):
    """Call the model with retry mechanism"""
    return model.invoke(message_content)

# ========== Process Answers ==========
def process_response(response_content, idx, total, image_path):
    """Process model response to get caption"""
    try:
        # Try to parse the response
        parsed = output_parser.parse(response_content)
        caption = parsed["image_caption"]
        return caption
    except Exception as e:
        # If standard parsing fails, use the repair function
        print(f"[WARNING] [{idx}/{total}] Standard parsing failed for {image_path}: {e}")
        repaired_json = extract_and_fix_json(response_content)
        return repaired_json["image_caption"]

# ========== Main Processing ==========
# Read JSON
with open(input_json, "r", encoding="utf-8") as f:
    data = json.load(f)

results = []
total = len(data)
processed_count = 0
start_time = time.time()

for idx, entry in enumerate(data, start=1):
    if "image" not in entry:
        continue
    image_path = entry["image"]

    # Read local image and convert to base64
    try:
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"[ERROR] [{idx}/{total}] Failed to read image {image_path}: {e}")
        entry["image_caption"] = f"Read failed: {str(e)}"
        results.append(entry)
        continue

    # Build text messages
    try:
        text_messages = chat_prompt.format_messages(format_instructions=format_instructions)
    except Exception as e:
        error_msg = f"Failed to build prompt: {e}"
        print(f"[ERROR] [{idx}/{total}] {error_msg}")
        entry["image_caption"] = error_msg
        results.append(entry)
        continue

    # Build final message (add image)
    messages = []
    for msg in text_messages:
        if isinstance(msg, HumanMessage):
            # For human messages, add image
            messages.append(HumanMessage(
                content=[
                    {"type": "text", "text": str(msg.content)},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                ]
            ))
        else:
            messages.append(msg)

    # Call model with retry mechanism
    try:
        response = call_model_with_retry(model, messages)
        caption = process_response(response.content, idx, total, image_path)
        processed_count += 1
    except Exception as e:
        caption = f"Processing failed after retries: {str(e)}"
        print(f"[WARNING] [{idx}/{total}] Failed to process {image_path} after retries: {e}")

    # Ensure "image_caption" is the second key-value pair
    new_entry = OrderedDict()
    keys = list(entry.keys())
    if len(keys) > 0:
        new_entry[keys[0]] = entry[keys[0]]
    new_entry["image_caption"] = caption
    for k in keys[1:]:
        new_entry[k] = entry[k]

    results.append(new_entry)

    # Print progress
    print(f"[OK] [{idx}/{total}] Processed {image_path} -> caption length: {len(caption)}")

    # Save intermediate results every 10 images
    if idx % 10 == 0:
        with open(f"temp_{output_json}", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

# ========== Save ==========
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# Calculate and print statistics
end_time = time.time()
total_time = end_time - start_time
avg_time_per_image = total_time / processed_count if processed_count > 0 else 0

print(f"[SUCCESS] Generated {output_json}, processed {processed_count}/{total} images successfully")
print(f"[TIME] Total time: {total_time:.2f} seconds, Average per image: {avg_time_per_image:.2f} seconds")