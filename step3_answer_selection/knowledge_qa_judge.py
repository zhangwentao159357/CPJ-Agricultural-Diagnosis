import json
import re
import os
import argparse
import aiohttp
import asyncio
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_exponential
from langchain_openai import ChatOpenAI
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

# Process data
system_template = """You are an agricultural expert evaluating two answers to a question about plant disease diagnosis.

## Evaluation Criteria:
1. **Accuracy**: Correct identification of crop and disease
2. **Completeness**: Coverage of symptoms, causes, and treatments
3. **Specificity**: Use of precise terminology and details
4. **Practicality**: Actionable advice for farmers
5. **Scientific Validity**: Use of correct scientific names and concepts

## Task:
Compare Answer 1 and Answer 2 based on the above criteria and select the better one.

## Output Format:
Provide your response in JSON format with the following structure:
{{
  "choice": 1 or 2,
  "reason": "Brief explanation for your choice",
  "scores": {{
    "answer1": {{
      "accuracy": 0-1 (1: fully accurate, 0.5: mostly, 0: errors),
      "completeness": 0-1 (1: comprehensive, 0.5: partial, 0: minimal),
      "specificity": 0-1 (1: precise details, 0.5: general, 0: vague),
      "practicality": 0-1 (1: actionable, 0.5: somewhat, 0: not useful),
      "scientific_validity": 0-1 (1: rigorous, 0.5: adequate, 0: questionable),
      "total": 0-5 (sum of all above criteria)
    }},
    "answer2": {{
      "accuracy": 0-1,
      "completeness": 0-1,
      "specificity": 0-1,
      "practicality": 0-1,
      "scientific_validity": 0-1,
      "total": 0-5 (sum of all above criteria)
    }}
  }}
}}
"""
system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

# Process data
examples = [
    {
        "input": "Question: What control techniques are applicable to Wheat Leaf Rust?\nImage Caption: Plant: Wheat; Disease: Leaf Rust (Puccinia triticina). The foreground crop shows premature leaf browning and canopy collapse, contrasting with healthier green wheat behind—consistent with heavy rust reducing photosynthesis and grain fill. Outbreaks are favored by mild–warm (15–22°C) weather, dews/light rain, dense stands, and high nitrogen. Treatment: protect the flag leaf with timely foliar fungicides—triazoles (e.g., tebuconazole), strobilurins (azoxystrobin), or triazole+SDHI mixes; repeat after 10–14 days if pressure persists. Recommendations: plant resistant varieties, balance NPK, avoid overly dense seeding, remove volunteers/green bridge, and scout regularly.\nAnswer 1: Control mainly relies on planting resistant varieties, supplemented by chemical treatments and cultural practices. Plant resistant and tolerant varieties such as Shaanong 7859, Ji 5418, Lumai 1, Xiaoyan 6, Xuzhou 21 for winter wheat in the Huang-Huai-Hai region. Chemical treatment: a) Seed dressing using 0.03%-0.04% (active ingredient) of Yerust special or 0.2% of 20% triazolone oil dressing seeds. b) Use 15% Baofeng 1 seed coating agent to coat seeds. Strengthen cultural control measures: Sow at the appropriate time, eliminate weeds and volunteer wheat seedlings, and ensure timely drainage during the rainy season.\nAnswer 2: Just spray some fungicide on the wheat plants when you see rust spots. Maybe also plant different types of wheat.",
        "output": '{"choice": 1, "reason": "Answer 1 provides comprehensive, specific control techniques including resistant varieties, chemical treatments with exact formulations and dosages, and cultural practices. Answer 2 is vague, lacks specificity, and does not provide scientifically valid or practical advice.", "scores": {"answer1": {"accuracy": 0.9, "completeness": 0.9, "specificity": 1.0, "practicality": 0.9, "scientific_validity": 0.9, "total": 4.6}, "answer2": {"accuracy": 0.5, "completeness": 0.3, "specificity": 0.2, "practicality": 0.4, "scientific_validity": 0.3, "total": 1.7}}}'
    },
    {
        "input": "Question: Please explain the disease cycle of Apple Brown Spot.\nImage Caption: Plant: Apple. Disease: Brown Spot (Brown Spott). The photo shows a senescing apple leaf with distinct dark‑brown, irregular lesions and surrounding chlorosis, indicating tissue necrosis and premature leaf drop risk. Brown spot develops under warm, humid, rain‑splashed conditions and in dense canopies with poor airflow. Treatment: promptly remove and destroy infected leaves; prune to improve ventilation; avoid overhead irrigation. Apply protective fungicides at early symptom onset—copper formulations, captan, or mancozeb—following label rates and intervals. Recommendations: maintain balanced nutrition, monitor after rains, and implement orchard sanitation to reduce inoculum carryover.\nAnswer 1: The fungus overwinters as mycelium and conidiomata on fallen leaves, producing conidia and ascospores in spring, spread by wind and rain. The fungus penetrates leaves from the upper or lower surfaces, typically from the underside. The incubation period is 6-12 days, extended to 45 days in dry years, shortening with higher temperatures. The fungus causes leaf drop 13-55 days after infection. In the field, the disease starts in May-June, peaks in July-August, and stops spreading in October.\nAnswer 2: Apple brown spot is a fungal disease that appears in warm, wet weather. The fungus survives winter on dead leaves and spreads in spring. It makes spots on leaves that can cause them to fall off early.",
        "output": '{"choice": 1, "reason": "Answer 1 provides a detailed, scientifically accurate explanation of the disease cycle with specific timelines and mechanisms. Answer 2 is overly simplified and lacks the specific details about the fungal life cycle, incubation periods, and seasonal patterns that are essential for understanding disease management.", "scores": {"answer1": {"accuracy": 1.0, "completeness": 0.9, "specificity": 1.0, "practicality": 0.8, "scientific_validity": 1.0, "total": 4.7}, "answer2": {"accuracy": 0.6, "completeness": 0.4, "specificity": 0.3, "practicality": 0.5, "scientific_validity": 0.5, "total": 2.3}}}'
    },
    {
        "input": "Question: What are the conditions for the occurrence of Pumpkin Powdery Mildew?\nImage Caption: Plant: Pumpkin. Disease: Powdery Mildew. The leaf shows white, powdery fungal growth forming diffuse patches on the upper surface, indicating early–moderate infection that reduces photosynthesis and vigor. Favored by warm days, cool humid nights, shade, dense canopies, and excess nitrogen; spreads via windborne conidia in dry weather. Treatment: start foliar sprays at first spots with sulfur, potassium bicarbonate, or systemic fungicides (triazoles, QoIs), rotating FRAC groups. Recommendations: improve airflow, avoid late‑day overhead irrigation, balance fertilization, remove heavily infected leaves, and monitor weekly.\nAnswer 1: Pumpkin powdery mildew peaks when high temperature and humidity alternate with dry conditions. It also thrives in fields with excessive nitrogen fertilizer, such as urea, overcrowded planting, and moist conditions. After the growing season, the fungus overwinters on old plants and residual diseased plant matter.\nAnswer 2: Powdery mildew likes warm, humid weather. It grows well when plants are crowded together and there's too much nitrogen in the soil. The fungus can survive winter on plant debris.",
        "output": '{"choice": 1, "reason": "Answer 1 provides more specific conditions for disease occurrence, including the alternation of high temperature and humidity with dry conditions, and specifically mentions urea as a nitrogen fertilizer that can exacerbate the problem. Answer 2 is correct but less detailed and specific.", "scores": {"answer1": {"accuracy": 0.9, "completeness": 0.8, "specificity": 0.9, "practicality": 0.8, "scientific_validity": 0.9, "total": 4.3}, "answer2": {"accuracy": 0.6, "completeness": 0.5, "specificity": 0.4, "practicality": 0.6, "scientific_validity": 0.6, "total": 2.7}}}'
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


def save_data(data, file_path):
    """Save data to JSON file"""
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def evaluate_answers_batch(session, batch_data):
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
    """Parse evaluation response"""
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
                    answer1_score = sum(scores.get("answer1", {}).values()) if isinstance(scores.get("answer1"),
                                                                                          dict) else 0
                    answer2_score = sum(scores.get("answer2", {}).values()) if isinstance(scores.get("answer2"),
                                                                                          dict) else 0

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


async def process_data_async(file1_data, file2_data, batch_size=5):
    """Process data asynchronously and select best answer"""
    processed_data = []
    evaluation_results = []

    # Ensure both files have same data length
    if len(file1_data) != len(file2_data):
        raise ValueError("Input files have different lengths")

    # Prepare batch data
    batched_data = []
    for i, (item1, item2) in enumerate(zip(file1_data, file2_data)):
        answer1 = item1.get("generation_answer", "")
        answer2 = item2.get("generation_answer", "")

        if isinstance(answer1, dict):
            answer1 = json.dumps(answer1, ensure_ascii=False)
        if isinstance(answer2, dict):
            answer2 = json.dumps(answer2, ensure_ascii=False)

        batched_data.append({
            "index": i,
            "question": item1.get("question", item2.get("question", "")),
            "image_caption": item1.get("image_caption", item2.get("image_caption", "")),
            "answer1": answer1,
            "answer2": answer2,
            "original_item1": item1,
            "original_item2": item2
        })

    # Process data
    for i in tqdm(range(0, len(batched_data), batch_size), desc="Processing batches"):
        batch = batched_data[i:i + batch_size]

        # Use async session for batch API calls
        async with aiohttp.ClientSession() as session:
            responses = await evaluate_answers_batch(session, batch)

            for j, response in enumerate(responses):
                data_index = i + j
                if data_index >= len(batched_data):
                    break

                data = batched_data[data_index]
                original_item1 = data["original_item1"]
                original_item2 = data["original_item2"]

                if isinstance(response, Exception):
                    print(f"API call error: {response}")
                    choice, reason, score1, score2 = 1, f"Error: {str(response)}", 0, 0
                else:
                    choice, reason, score1, score2 = parse_evaluation_response(response)

                # Record evaluation result
                eval_result = {
                    "id": original_item1.get("id", len(evaluation_results)),
                    "question": original_item1.get("question", ""),
                    "choice": choice,
                    "reason": reason,
                    "score1": score1,
                    "score2": score2,
                    "answer1_preview": data["answer1"][:200] + "..." if len(data["answer1"]) > 200 else data["answer1"],
                    "answer2_preview": data["answer2"][:200] + "..." if len(data["answer2"]) > 200 else data["answer2"]
                }
                evaluation_results.append(eval_result)

                # Create new item, keep original fields
                if choice == 1 or score1 >= score2:
                    # Select answer from file
                    new_item = original_item1.copy()
                    new_item["selected_from"] = "file1"
                    new_item["evaluation_score"] = score1
                else:
                    # Select answer from file
                    new_item = original_item2.copy()
                    new_item["selected_from"] = "file2"
                    new_item["evaluation_score"] = score2

                # Keep evaluation reason
                new_item["evaluation_reason"] = reason

                processed_data.append(new_item)

            # Add delay between batches to avoid API limits
            await asyncio.sleep(1)

    return processed_data, evaluation_results


# Main function
async def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Judge and select best answer for knowledge QA")
    parser.add_argument("--input1", type=str, required=True, help="First input JSON file path")
    parser.add_argument("--input2", type=str, required=True, help="Second input JSON file path")
    parser.add_argument("--output", type=str, required=True, help="Output JSON file path")
    parser.add_argument("--evaluation-output", type=str, default="evaluation_results.json",
                       help="Evaluation results output file path")
    parser.add_argument("--model", type=str, default="gpt-4", help="Model name to use (default: gpt-4)")
    args = parser.parse_args()

    file1_path = args.input1
    file2_path = args.input2
    output_file = args.output
    evaluation_file = args.evaluation_output
    model_name = args.model

    # Initialize chain
    global chain
    chain = chat_prompt | ChatOpenAI(model=model_name, temperature=0) | StrOutputParser()

    # Load data
    print(f"Loading data from {file1_path}...")
    file1_data = load_data(file1_path)

    print(f"Loading data from {file2_path}...")
    file2_data = load_data(file2_path)

    # Process data asynchronously
    print("Starting answer evaluation...")
    processed_data, evaluation_results = await process_data_async(file1_data, file2_data)

    # Save results
    print(f"Saving results to {output_file}...")
    save_data(processed_data, output_file)

    print(f"Saving evaluation details to {evaluation_file}...")
    save_data(evaluation_results, evaluation_file)

    # Print statistics
    choices = [result["choice"] for result in evaluation_results]
    choice1_count = choices.count(1)
    choice2_count = choices.count(2)

    print(f"\nEvaluation Statistics:")
    print(f"Selected Answer 1: {choice1_count}  times ({choice1_count / len(choices) * 100:.1f}%)")
    print(f"Selected Answer 2: {choice2_count}  times ({choice2_count / len(choices) * 100:.1f}%)")
    print(f"Processing complete! Results saved to {output_file}")


if __name__ == "__main__":
    asyncio.run(main())