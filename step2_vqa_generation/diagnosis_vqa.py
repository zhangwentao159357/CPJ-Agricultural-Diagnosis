# coding: utf-8
import os
import json
import base64
import re
import argparse
from collections import OrderedDict
from langchain_openai import ChatOpenAI
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain_core.messages import HumanMessage, SystemMessage
from retry import retry
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

# ========== API Configuration ==========
os.environ["OPENAI_API_BASE"] = "YOUR_API_BASE_URL"
os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY"

# ========== Define Output Format ==========
response_schemas = [
    ResponseSchema(name="answer1",
                   description="Focus on pest/disease identification: symptoms, severity, and characteristic features. Must include both plant type and disease type."),
    ResponseSchema(name="answer2",
                   description="Focus on crop identification: crop type, variety, and distinctive morphological features. Must include both plant type and disease type.")
]
output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
format_instructions = output_parser.get_format_instructions()

# ========== System Prompt ==========
system_template = """You are an agricultural visual question answering assistant. Based on the provided crop image and its caption, you provide professional and precise answers to the user's questions.

## Skills
1. Identify crop type from image and caption
2. Identify disease/pest type from image and caption
3. Understand user's question thoroughly
4. Analyze image based on the question
5. Extract key information from caption
6. Combine analysis to provide professional answers
7. Provide TWO answers with different focuses

## Rules
1. Base answers solely on image, caption, and question
2. Prioritize scientific accuracy
3. Never return empty answers
4. BOTH answers must include BOTH plant type and disease type
5. Answer1: Focus on PEST/DISEASE identification (symptoms, severity, features)
6. Answer2: Focus on CROP identification (type, variety, morphology)
7. Both answers should be scientifically accurate and detailed

## Output Format
{format_instructions}
"""
system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

# ========== Examples ==========
examples = [
    {
        "input": "Background(image_caption): Apple leaf exhibiting Alternaria blotch. Small, circular brown lesions with yellowish halos are visible on the blade, some starting to coalesce near the margins. Spots appear slightly sunken and surrounded by chlorosis, indicating early to mid infection.\nQuestion: Is this crop diseased?",
        "output": '{"answer1": "This is an apple leaf affected by Alternaria Blotch. Key disease symptoms include small circular brown lesions (2-5mm) with distinctive yellowish halos, some coalescing near leaf margins, accompanied by chlorosis indicating moderate disease severity.", "answer2": "The Alternaria Blotch is affecting an apple (Malus domestica) leaf, which is identified by its ovate shape, serrated margins, and typical apple leaf venation pattern. The leaf appears to be from a mature tree based on size and texture."}'
    },
    {
        "input": "Background(image_caption): Tomato leaf affected by Spider Mites. Fine, pale stippling spreads across the surface, especially along veins, giving a yellow‑bronze, roughened appearance. Leaf edges curl and pucker, and tissue feels dry, with tiny specks and faint webbing likely on the underside.\nQuestion: What disease does this tomato leaf have?",
        "output": '{"answer1": "This is a tomato leaf affected by Spider Mites. Key symptoms include fine pale stippling along veins, yellow-bronze roughened appearance, curled leaf edges, dry tissue texture, and faint webbing on the underside indicating active infestation.", "answer2": "The Spider Mite infestation is affecting a tomato (Solanum lycopersicum) leaf, identified by its compound pinnate structure with serrated leaflets and typical tomato leaf morphology, showing characteristic damage patterns from mite feeding."}'
    },
    {
        "input": "Background(image_caption): Tomato leaf with Late Blight. Irregular, water‑soaked lesions turn dark brown, with pale-green margins that expand rapidly. The affected tissue becomes limp and necrotic, and in humid, cool conditions a delicate white, downy mold appears on the underside along lesion edges.\nQuestion: Is this leaf from a cucumber plant?",
        "output": '{"answer1": "No, this is a tomato leaf affected by Late Blight. Key symptoms include irregular water-soaked lesions turning dark brown with pale-green margins, necrotic tissue, and under humid conditions, white downy mold appears on the underside along lesion edges.", "answer2": "The Late Blight is affecting a tomato (Solanum lycopersicum) leaf, not a cucumber plant. Tomato leaves are identified by their compound pinnate structure with serrated leaflets, distinct from cucumber\'s simple palmate leaves with rounded lobes."}'
    },
    {
        "input": "Background(image_caption): Tomato leaf with Late Blight. Irregular, water‑soaked lesions turn dark brown, with pale-green margins that expand rapidly. The affected tissue becomes limp and necrotic, and in humid, cool conditions a delicate white, downy mold appears on the underside along lesion edges. Infection progresses quickly, causing leaf blighting, petiole collapse, and potential spread to stems and fruit.\nQuestion: Describe the content of this picture.",
        "output": '{"answer1": "This image shows a tomato leaf affected by Late Blight. Key symptoms include irregular water-soaked lesions turning dark brown with pale-green margins, necrotic tissue, white downy mold on the underside in humid conditions, and potential progression to leaf blighting and petiole collapse.", "answer2": "The Late Blight is affecting a tomato (Solanum lycopersicum) leaf, identified by its compound pinnate structure with serrated leaflets. The disease presents with characteristic water-soaked lesions and downy mold, indicating advanced infection that can spread to stems and fruit."}'
    },
    {
        "input": "Background(image_caption): Grape leaf showing Leaf Blight. Numerous small, dark brown spots with yellow halos are scattered across the blade, some coalescing into irregular patches and causing shot-hole tearing. Margins turn necrotic and crisp, with general chlorosis between veins and slight puckering.\nQuestion: Is this apple leaf healthy?",
        "output": '{"answer1": "No, this is not an apple leaf and it is not healthy. This is a grape leaf affected by Leaf Blight, showing symptoms including numerous small dark brown spots with yellow halos, some coalescing into irregular patches, shot-hole tearing, necrotic margins, and general chlorosis between veins.", "answer2": "The Leaf Blight is affecting a grape (Vitis vinifera) leaf, not an apple leaf. Grape leaves are identified by their palmate lobed structure with toothed margins, distinct from apple\'s simple ovate leaves with serrated edges. The disease presents with characteristic spot patterns and chlorosis."}'
    }
]
# ========== Build Prompt Template ==========
example_human = HumanMessagePromptTemplate.from_template("{input}")
example_ai = AIMessagePromptTemplate.from_template("{output}")

human_template = "Background(image_caption): {image_caption}\nQuestion: {question}"
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

# Build zero-shot prompt template (backup)
zero_shot_chat_prompt = ChatPromptTemplate.from_messages(
    [system_message_prompt, human_message_prompt]
)

# ========== Model variable will be initialized in main function ==========
model = None


# ========== JSON Repair Function ==========
def extract_and_fix_json(text):
    """Efficiently extract and repair JSON format from text"""
    if not isinstance(text, str) or not text.strip():
        return {"answer1": "No valid response", "answer2": "No valid response"}

    text = text.strip()

    # First try direct parsing
    try:
        result = json.loads(text)
        if isinstance(result, dict) and "answer1" in result and "answer2" in result:
            return {
                "answer1": str(result.get("answer1", "")),
                "answer2": str(result.get("answer2", ""))
            }
    except:
        pass

    # Try to find JSON object
    start_idx = text.find('{')
    end_idx = text.rfind('}')

    if start_idx >= 0 and end_idx > start_idx:
        json_str = text[start_idx:end_idx + 1]
        try:
            # Quick fix for common JSON format errors
            json_str = json_str.replace("'", '"')
            json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
            json_str = re.sub(r'([{,])\s*([^"{}\[\]]+?)\s*:', r'\1"\2":', json_str)

            result = json.loads(json_str)
            if isinstance(result, dict):
                return {
                    "answer1": str(result.get("answer1", "")),
                    "answer2": str(result.get("answer2", ""))
                }
        except:
            pass

    # If all attempts fail, return simple JSON with original text
    return {
        "answer1": text[:300] + ("..." if len(text) > 300 else ""),
        "answer2": text[:300] + ("..." if len(text) > 300 else "")
    }


# ========== API Call Function with Retry ==========
@retry(exceptions=Exception, tries=2, delay=1)
def get_model_response(messages):
    """Call model and process response"""
    try:
        response = model.invoke(messages)
        return str(response.content) if response.content else ""
    except Exception as e:
        print(f"API call failed: {str(e)}")
        raise


# ========== Process Answers ==========
def process_answers(messages, idx, total, image_path):
    """Process model response and get two answers"""
    try:
        response_content = get_model_response(messages)

        # Check if response is empty
        if not response_content or response_content.strip() == "":
            return "No response generated", "No response generated"

        # Try to parse response
        try:
            parsed = output_parser.parse(response_content)
            answer1 = str(parsed.get("answer1", ""))
            answer2 = str(parsed.get("answer2", ""))
            return answer1, answer2
        except Exception as e:
            # If standard parsing fails, use repair function
            repaired_json = extract_and_fix_json(response_content)
            return repaired_json["answer1"], repaired_json["answer2"]
    except Exception as e:
        error_msg = f"API call failed: {str(e)}"
        print(f"[ERROR] [{idx}/{total}] {error_msg}")
        return error_msg, error_msg


# ========== Main Processing Flow ==========
def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Generate dual-answer VQA for disease diagnosis")
    parser.add_argument("--input", type=str, required=True, help="Input JSON file path")
    parser.add_argument("--output", type=str, required=True, help="Output JSON file path")
    parser.add_argument("--model", type=str, default="gpt-4", help="Model name to use (default: gpt-4)")
    args = parser.parse_args()

    input_json = args.input
    output_json = args.output
    model_name = args.model

    # Update model configuration
    global model
    model = ChatOpenAI(
        model=model_name,
        reasoning_effort="minimal",
        verbosity="low",
        max_retries=2,
        timeout=30,
    )

    # Read JSON
    try:
        with open(input_json, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to read input file: {e}")
        return

    results = []
    total = len(data)

    for idx, entry in enumerate(data, start=1):
        if "image" not in entry or "question" not in entry or "image_caption" not in entry:
            # Keep original entry but add answer fields
            entry["generation_answer1"] = "Missing required fields"
            entry["generation_answer2"] = "Missing required fields"
            results.append(entry)
            print(f"[WARNING] [{idx}/{total}] Skipped, missing required fields")
            continue

        image_path = entry["image"]
        question = str(entry["question"])
        image_caption = str(entry["image_caption"])

        # Read local image and convert to base64
        try:
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            error_msg = f"Failed to read image {image_path}: {e}"
            print(f"[ERROR] [{idx}/{total}] {error_msg}")
            entry["generation_answer1"] = error_msg
            entry["generation_answer2"] = error_msg
            results.append(entry)
            continue

        # Build text messages (using few-shot version)
        try:
            text_messages = chat_prompt.format_messages(
                image_caption=image_caption,
                question=question,
                format_instructions=format_instructions
            )
        except Exception as e:
            error_msg = f"Failed to build prompt: {e}"
            print(f"[ERROR] [{idx}/{total}] {error_msg}")
            entry["generation_answer1"] = error_msg
            entry["generation_answer2"] = error_msg
            results.append(entry)
            continue

        # Build final messages (add image)
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

        # Call API to get two answers
        answer1, answer2 = process_answers(messages, idx, total, image_path)

        # Keep original fields unchanged, add two answer fields
        new_entry = OrderedDict(entry)
        new_entry["generation_answer1"] = answer1
        new_entry["generation_answer2"] = answer2
        results.append(new_entry)

        print(f"[SUCCESS] [{idx}/{total}] {os.path.basename(image_path)}")
        if answer1:
            print(f"   Answer 1: {answer1[:80]}{'...' if len(answer1) > 80 else ''}")
        if answer2:
            print(f"   Answer 2: {answer2[:80]}{'...' if len(answer2) > 80 else ''}")

    # ========== Save Final Results ==========
    try:
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"[SUCCESS] Generated {output_json}, processed {len(results)}  records")
    except Exception as e:
        print(f"[ERROR] Failed to save results: {e}")


if __name__ == "__main__":
    main()