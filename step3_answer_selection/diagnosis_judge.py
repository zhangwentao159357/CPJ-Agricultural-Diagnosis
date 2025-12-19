import json
import time
import re
import os
import argparse
import aiohttp
import asyncio
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_exponential
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser

# Set environment variables
os.environ["OPENAI_API_BASE"] = "YOUR_API_BASE_URL"
os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY"

# System prompt template
system_template = """You are an agricultural expert evaluating two answers to a question about plant disease diagnosis.

## Evaluation Criteria:
1. **Accuracy of Plant Identification**: Correct identification of crop species
2. **Accuracy of Disease/Pest Identification**: Correct identification of disease or pest
3. **Symptom Description Accuracy**: Precise description of disease symptoms
4. **Adherence to Required Format**: Proper structure with plant and disease identification
5. **Completeness and Professionalism**: Comprehensive and scientifically sound response

## Task:
Compare Answer 1 and Answer 2 based on the above criteria and select the better one.

## Output Format:
Provide your response in JSON format with the following structure:
{{
  "choice": 1 or 2,
  "reason": "Brief explanation for your choice",
  "scores": {{
    "answer1": {{
      "plant_accuracy": 0-1 (1: precise species, 0.5: genus, 0: wrong),
      "disease_accuracy": 0-1 (1: specific disease, 0.5: disease type, 0: wrong),
      "symptom_accuracy": 0-1 (1: detailed symptoms, 0.5: general, 0: inaccurate),
      "format_adherence": 0-1 (1: both plant and disease, 0.5: one missing, 0: neither),
      "completeness": 0-1 (1: comprehensive, 0.5: partial, 0: minimal),
      "total": 0-5 (sum of all above criteria)
    }},
    "answer2": {{
      "plant_accuracy": 0-1,
      "disease_accuracy": 0-1,
      "symptom_accuracy": 0-1,
      "format_adherence": 0-1,
      "completeness": 0-1,
      "total": 0-5 (sum of all above criteria)
    }}
  }}
}}
"""
system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

# Few-shot examples
examples = [
    {
        "input": "Question: What disease is affecting this plant?\nImage Caption: Apple leaf exhibiting signs of Alternaria blotch with circular brown lesions and yellowish halos.\nAnswer 1: This is an apple leaf with Alternaria blotch. Symptoms include circular brown spots with yellow halos.\nAnswer 2: This leaf might be diseased. It has some spots on it, possibly caused by a fungus.",
        "output": '{"choice": 1, "reason": "Answer 1 correctly identifies both the plant (apple) and disease (Alternaria blotch) with specific symptoms. Answer 2 is vague and lacks specific identification.", "scores": {"answer1": {"plant_accuracy": 1.0, "disease_accuracy": 1.0, "symptom_accuracy": 0.9, "format_adherence": 1.0, "completeness": 0.9, "total": 4.8}, "answer2": {"plant_accuracy": 0.2, "disease_accuracy": 0.3, "symptom_accuracy": 0.4, "format_adherence": 0.3, "completeness": 0.4, "total": 1.6}}}'
    },
    {
        "input": "Question: What is wrong with this tomato?\nImage Caption: Tomato fruit showing symptoms of blossom-end rot with dark, sunken lesions at the blossom end.\nAnswer 1: This is a tomato suffering from blossom-end rot, a physiological disorder caused by calcium deficiency.\nAnswer 2: This tomato has late blight with large, dark, sunken lesions typical of this fungal disease.",
        "output": '{"choice": 1, "reason": "Answer 1 correctly identifies blossom-end rot and explains it\'s a physiological disorder. Answer 2 is wrong, misidentifying it as late blight which has different symptoms.", "scores": {"answer1": {"plant_accuracy": 1.0, "disease_accuracy": 1.0, "symptom_accuracy": 0.9, "format_adherence": 1.0, "completeness": 0.9, "total": 4.8}, "answer2": {"plant_accuracy": 1.0, "disease_accuracy": 0.2, "symptom_accuracy": 0.5, "format_adherence": 0.8, "completeness": 0.6, "total": 3.1}}}'
    },
    {
        "input": "Question: Is this corn disease dangerous to the crop yield?\nImage Caption: Corn leaf severely infected with Northern Corn Leaf Blight with long, grayish-tan lesions.\nAnswer 1: This is corn with Northern Corn Leaf Blight. Yes, severe infections can significantly reduce photosynthesis and yield.\nAnswer 2: This is a maize leaf affected by a fungal pathogen that can potentially impact yield.",
        "output": '{"choice": 1, "reason": "Both answers recognize the threat to yield, but Answer 1 provides the specific disease name and a more detailed explanation of the impact mechanism.", "scores": {"answer1": {"plant_accuracy": 1.0, "disease_accuracy": 1.0, "symptom_accuracy": 0.9, "format_adherence": 1.0, "completeness": 0.9, "total": 4.8}, "answer2": {"plant_accuracy": 1.0, "disease_accuracy": 0.6, "symptom_accuracy": 0.7, "format_adherence": 0.8, "completeness": 0.7, "total": 3.8}}}'
    }
]

# Build example messages
example_messages = []
for example in examples:
    example_messages.append(HumanMessage(content=example["input"]))
    example_messages.append(AIMessage(content=example["output"]))

# Template for current evaluation input
human_template = """Question: {question}
Image Caption: {image_caption}
Answer 1: {answer1}
Answer 2: {answer2}"""
human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

# Build complete prompt
chat_prompt = ChatPromptTemplate.from_messages(
    [system_message_prompt] +
    example_messages +
    [human_message_prompt]
)

# ========== Chain variable will be initialized in main function ==========
chain = None


def load_data(file_path):
    """Load data from JSON file"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def evaluate_answers_batch(batch_data):
    """Batch evaluate answers"""
    tasks = []
    for data in batch_data:
        task = chain.ainvoke({
            "question": data["question"],
            "image_caption": data["image_caption"],
            "answer1": data["answer1"],
            "answer2": data["answer2"]
        })
        tasks.append(task)

    return await asyncio.gather(*tasks, return_exceptions=True)


def parse_evaluation_response(response):
    """Parse evaluation response with scoring information"""
    try:
        # Try to extract JSON part
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            result = json.loads(json_str)

            # Check if there's a choice
            if "choice" in result and result["choice"] in [1, 2]:
                choice = result["choice"]
                reason = result.get("reason", "No reason provided")

                # Process data
                answer1_score = 0
                answer2_score = 0

                if "scores" in result:
                    scores = result["scores"]
                    answer1_score = sum(scores.get("answer1", {}).values()) if isinstance(scores.get("answer1"), dict) else 0
                    answer2_score = sum(scores.get("answer2", {}).values()) if isinstance(scores.get("answer2"), dict) else 0

                return choice, reason, answer1_score, answer2_score
    except json.JSONDecodeError:
        pass

    # Try to extract JSON part
    choice_match = re.search(r'(?i)choice.*?[12]|(?i)select.*?[12]|[12](?=\D*$)', response)
    if choice_match:
        choice_text = choice_match.group()
        if '1' in choice_text:
            return 1, "Extracted from text response", 0, 0
        elif '2' in choice_text:
            return 2, "Extracted from text response", 0, 0

    # If uncertain, default to first answer
    return 1, "Default selection - could not determine choice", 0, 0


async def process_data_async(input_data, batch_size=5):
    """Process data asynchronously and select best answer"""
    processed_data = []
    evaluation_results = []

    # Prepare batch data
    batched_data = []
    for i, item in enumerate(input_data):
        answer1 = item.get("generation_answer1", "")
        answer2 = item.get("generation_answer2", "")

        if isinstance(answer1, dict):
            answer1 = json.dumps(answer1, ensure_ascii=False)
        if isinstance(answer2, dict):
            answer2 = json.dumps(answer2, ensure_ascii=False)

        batched_data.append({
            "index": i,
            "question": item.get("question", ""),
            "image_caption": item.get("image_caption", ""),
            "answer1": answer1,
            "answer2": answer2,
            "original_item": item
        })

    # Process data
    for i in tqdm(range(0, len(batched_data), batch_size), desc="Processing batches"):
        batch = batched_data[i:i + batch_size]

        responses = await evaluate_answers_batch(batch)

        for j, response in enumerate(responses):
            data_index = i + j
            if data_index >= len(batched_data):
                break

            data = batched_data[data_index]
            original_item = data["original_item"]

            if isinstance(response, Exception):
                print(f"API call error: {response}")
                choice, reason, score1, score2 = 1, f"Error: {str(response)}", 0, 0
            else:
                choice, reason, score1, score2 = parse_evaluation_response(response)

            # Record evaluation result
            eval_result = {
                "id": original_item.get("id", len(evaluation_results)),
                "question": original_item.get("question", ""),
                "choice": choice,
                "reason": reason,
                "answer1_score": score1,
                "answer2_score": score2,
                "answer1_preview": data["answer1"][:200] + "..." if len(data["answer1"]) > 200 else data["answer1"],
                "answer2_preview": data["answer2"][:200] + "..." if len(data["answer2"]) > 200 else data["answer2"]
            }
            evaluation_results.append(eval_result)

            # Create new item, keep original fields
            new_item = original_item.copy()

            # Set selected answer and score
            if choice == 1:
                new_item["generation_answer"] = data["answer1"]
                new_item["selected_answer"] = "answer1"
                new_item["selected_score"] = score1
                new_item["unselected_score"] = score2
            else:
                new_item["generation_answer"] = data["answer2"]
                new_item["selected_answer"] = "answer2"
                new_item["selected_score"] = score2
                new_item["unselected_score"] = score1

            # Keep evaluation reason
            new_item["evaluation_reason"] = reason

            # Delete original two answer fields
            if "generation_answer1" in new_item:
                del new_item["generation_answer1"]
            if "generation_answer2" in new_item:
                del new_item["generation_answer2"]

            processed_data.append(new_item)

        # Add delay between batches to avoid API limits
        await asyncio.sleep(1)

    return processed_data, evaluation_results


# Main function
async def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Judge and select best answer for disease diagnosis")
    parser.add_argument("--input", type=str, required=True, help="Input JSON file path")
    parser.add_argument("--output", type=str, required=True, help="Output JSON file path")
    parser.add_argument("--evaluation-output", type=str, default="evaluation_results.json",
                       help="Evaluation results output file path")
    parser.add_argument("--model", type=str, default="gpt-4", help="Model name to use (default: gpt-4)")
    args = parser.parse_args()

    input_file = args.input
    output_file = args.output
    evaluation_file = args.evaluation_output
    model_name = args.model

    # Initialize chain
    global chain
    chain = chat_prompt | ChatOpenAI(model=model_name, temperature=0) | StrOutputParser()

    # Load data
    data = load_data(input_file)

    # Process data asynchronously
    processed_data, evaluation_results = await process_data_async(data)

    # Save results
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, indent=4, ensure_ascii=False)

    with open(evaluation_file, 'w', encoding='utf-8') as f:
        json.dump(evaluation_results, f, indent=4, ensure_ascii=False)

    print(f"Processing complete! Results saved to {output_file}")
    print(f"Evaluation details saved to {evaluation_file}")

    # Print statistics
    choices = [result["choice"] for result in evaluation_results]
    choice1_count = choices.count(1)
    choice2_count = choices.count(2)

    print(f"\nEvaluation Statistics:")
    print(f"Selected Answer 1: {choice1_count}  times ({choice1_count / len(choices) * 100:.1f}%)")
    print(f"Selected Answer 2: {choice2_count}  times ({choice2_count / len(choices) * 100:.1f}%)")


if __name__ == "__main__":
    asyncio.run(main())