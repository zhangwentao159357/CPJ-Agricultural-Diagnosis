### coding: utf-8
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

# os.environ["OPENAI_API_BASE"] = "YOUR_ALTERNATIVE_API_BASE_URL"  # Alternative API base (optional)
# os.environ["OPENAI_API_KEY"] = "YOUR_ALTERNATIVE_API_KEY"  # Alternative API key (optional)

# ========== Define Output Format ==========
response_schemas = [
    ResponseSchema(name="answer1",
                   description="Detailed treatment, prevention and control measures for the disease, including specific methods and recommendations."),
    ResponseSchema(name="answer2",
                   description="Comprehensive explanation of the disease, including symptoms, causes, and disease cycle.")
]
output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
format_instructions = output_parser.get_format_instructions()

# ========== System Prompt ==========
system_template = """You are an agricultural expert specializing in plant disease diagnosis and management. Based on the provided background information about a crop and its disease, you provide comprehensive, professional answers to open-ended questions about disease explanation, treatment, prevention, and control measures.

Scope
- The background may cover rice blast, tomato leaf mold, wheat leaf rust, apple gray/sooty/blotch diseases, maize northern leaf blight, cucurbit (pumpkin) powdery mildew, grape leaf blight, tomato yellow leaf curl virus (TYLCV), pepper bacterial spot, and similar field/greenhouse pathosystems.
- Center your responses on: disease indicators/symptoms, resistant variety selection, seed/seedbed/soil sanitation, cultural practices (water–fertilizer), chemical/biological control (actives, formulations, rates, intervals, rotation), and environmental thresholds (temperature, humidity, ventilation).

## Skills
1. Extract the disease context from the provided background Q&A and the user’s question.
2. Diagnose and describe disease mechanisms, signs/symptoms, and disease cycles; include differential diagnosis where relevant.
3. Translate product names to active ingredients when appropriate; handle dilutions and rates precisely (metric units).
4. Give practical, stage-specific recommendations (seed/seedling, vegetative, reproductive), including timings, intervals, and number of applications.
5. Integrate IPM: resistant varieties, sanitation, crop rotation, canopy management, balanced fertilization (N-P-K-Si), irrigation and drainage, environmental control (temp/RH/ventilation).
6. Address resistance management: rotate modes of action (e.g., FRAC for fungicides, IRAC for insecticides) and avoid repeated single-MoA use.
7. Ensure scientific accuracy, safety, and applicability; consider sustainability and local compliance.

## Rules
1. Base answers primarily on the provided background information; supplement only with widely accepted general agronomic knowledge if needed. Prefer variety names, pathogens, and actives explicitly mentioned in the background.
2. If specific data (e.g., dose, interval, temperature threshold) are provided in the background, use them verbatim. If missing, give typical ranges and clearly label them as general guidance.
3. Be precise with applications:
   - Include active ingredient and formulation when available (e.g., 20% tebuconazole EC).
   - Provide dilution ratios (e.g., 1:1000 or 1000-fold), spray volume or rate per hectare, timing (growth stage/phenology), interval (days), and number of sprays.
   - For seed treatment, specify temperature, duration, concentration, and post-treatment steps (rinse, dry).
   - For soil/greenhouse sanitation, specify fumigation/steam/sulfur rates, exposure time, and re-entry.
4. For cultural practices, include actionable details: balanced N-P-K, silicon/potash where indicated, organic amendments, liming on acidic soils, drainage after rain, plant spacing, pruning for airflow/light, temperature/RH targets, and irrigation scheduling.
5. For resistance/IPM:
   - Rotate fungicides with different FRAC codes or distinct MoAs; avoid more than 2 consecutive applications of the same MoA where feasible.
   - Mix/alternate protectants and systemic products appropriately; avoid off-label antibiotic use unless explicitly supported by the background.
6. When discussing environmental effects, include numeric thresholds (e.g., 20–25°C, RH >90%) if available; otherwise provide typical conducive ranges.
7. Provide TWO answers with distinct focuses:
   - Answer1: Treatment, prevention, and control (step-by-step IPM with specific methods, timings, dosages, intervals, rotations, and on-farm best practices).
   - Answer2: Disease explanation (symptoms, causes/etiology, disease cycle/epidemiology, conducive conditions, differential diagnosis).
8. Maintain logical structure, concise bulleting where helpful, and avoid verbosity without losing critical detail. Always deliver complete answers; do not leave fields empty.
9. Safety and compliance: advise PPE, follow local labels and regulations, observe pre-harvest intervals (PHI) and re-entry intervals (REI). Flag region-specific varieties/chemistries where applicable.
10. Do not invent products/varieties not supported by the background when specificity is required. If uncertain, state assumptions or offer generalized options by active ingredient.

## Output Format
{format_instructions}
"""

system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

# ========== Examples ==========


examples = [
{
"input": "Background(image_caption): Plant: Wheat; Disease: Leaf Rust (Puccinia triticina). The foreground crop shows premature leaf browning and canopy collapse, contrasting with healthier green wheat behind—consistent with heavy rust reducing photosynthesis and grain fill. Outbreaks are favored by mild–warm (15–22°C) weather, dews/light rain, dense stands, and high nitrogen. Treatment: protect the flag leaf with timely foliar fungicides—triazoles (e.g., tebuconazole), strobilurins (azoxystrobin), or triazole+SDHI mixes; repeat after 10–14 days if pressure persists. Recommendations: plant resistant varieties, balance NPK, avoid overly dense seeding, remove volunteers/green bridge, and scout regularly. \nQuestion: What control techniques are applicable to Wheat Leaf Rust?",
"output": '{"answer": "Control mainly relies on planting resistant varieties, supplemented by chemical treatments and cultural practices.\n1. Plant resistant and tolerant varieties such as Shaanong 7859, Ji 5418, Lumai 1, Xiaoyan 6, Xuzhou 21 for winter wheat in the Huang-Huai-Hai region. Other recent resistant winter wheat varieties include Jingdong 1, 8, Jingke 3 (Jingke 931), Jing 411, Beinong White, Wanmai 26, 27, 28, Mianyang 26, Bainong 64, Zhoumai 9-Aoyou 688 series, Xinbaofeng (7228), Yumai 39 (Yunong 8539), Zao 5, Jinsong 49, Xingmai 17, Dianmai 19, Qinmai 12, Jimai 48, 40, Ji 92-3235, 6021 new series; spring wheat varieties include Kenjiu 5, Longmai 23, Longfu Mai 7, Mengmai 30, Jingyi 1, Longchun 8139, Dingfeng 3.\n2. Chemical treatment: a) Seed dressing using 0.03%-0.04% (active ingredient) of Yerust special or 0.2% of 20% triazolone oil dressing seeds. b) Use 15% Baofeng 1 seed coating agent (active ingredients are fungicide, carbendazim, thiram, and phorate) to coat seeds which automatically cures into a film after sowing, forming a protective ring with a long-lasting effect. For every kg of seeds, use 4g of coating to excellently control wheat leaf rust, powdery mildew, and bunt, also controlling soil-borne pests. c) Spray 20% triazolone oil emulsion diluted 1000 times at the onset of the disease to also control stripe rust, stem rust, and powdery mildew; repeat every 10-20 days, 1-2 times for control.\n4. Strengthen cultural control measures: Sow at the appropriate time, eliminate weeds and volunteer wheat seedlings, and ensure timely drainage during the rainy season to prevent moisture retention."}'
},
{
"input": "Background(image_caption): Plant: Apple. Disease: Brown Spot (Brown Spott). The photo shows a senescing apple leaf with distinct dark‑brown, irregular lesions and surrounding chlorosis, indicating tissue necrosis and premature leaf drop risk. Brown spot develops under warm, humid, rain‑splashed conditions and in dense canopies with poor airflow. Treatment: promptly remove and destroy infected leaves; prune to improve ventilation; avoid overhead irrigation. Apply protective fungicides at early symptom onset—copper formulations, captan, or mancozeb—following label rates and intervals. Recommendations: maintain balanced nutrition, monitor after rains, and implement orchard sanitation to reduce inoculum carryover. \nQuestion: Please explain the disease cycle of Apple Brown Spot.",
"output": '{"answer": "The fungus overwinters as mycelium and conidiomata on fallen leaves, producing conidia and ascospores in spring, spread by wind and rain. The fungus penetrates leaves from the upper or lower surfaces, typically from the underside. The incubation period is 6-12 days, extended to 45 days in dry years, shortening with higher temperatures. The fungus causes leaf drop 13-55 days after infection. In the field, the disease starts in May-June, peaks in July-August, and stops spreading in October."}'
},
{
"input": "Background(image_caption): Plant: Pumpkin. Disease: Powdery Mildew. The leaf shows white, powdery fungal growth forming diffuse patches on the upper surface, indicating early–moderate infection that reduces photosynthesis and vigor. Favored by warm days, cool humid nights, shade, dense canopies, and excess nitrogen; spreads via windborne conidia in dry weather. Treatment: start foliar sprays at first spots with sulfur, potassium bicarbonate, or systemic fungicides (triazoles, QoIs), rotating FRAC groups. Recommendations: improve airflow, avoid late‑day overhead irrigation, balance fertilization, remove heavily infected leaves, and monitor weekly. \nQuestion: What are the conditions for the occurrence of Pumpkin Powdery Mildew?",
"output": '{"answer": "Pumpkin powdery mildew peaks when high temperature and humidity alternate with dry conditions. It also thrives in fields with excessive nitrogen fertilizer, such as urea, overcrowded planting, and moist conditions. After the growing season, the fungus overwinters on old plants and residual diseased plant matter."}'
},
{
"input": "Background(image_caption): Plant: Apple. Disease: Brown Spot. The leaf shows multiple dark-brown, irregular lesions with yellow halos on a senescing blade, indicating active infection and risk of premature defoliation and fruit blemish. Brown spot thrives under warm, humid, rain‑splashed conditions, especially in dense, poorly ventilated canopies. Treatment: promptly remove and destroy fallen/infected leaves; prune to open the canopy; avoid overhead irrigation. Apply protective fungicides at early onset—copper, captan, mancozeb, or thiophanate‑methyl—at labeled intervals. Recommendations: maintain balanced nutrition, monitor after rains, and practice rigorous orchard sanitation. \nQuestion: What control methods are suitable for Apple Brown Spot?",
"output": '{"answer": "(1) Prune appropriately, improve drainage, and enhance ventilation and light penetration in the orchard.\n(2) In fall and winter, clean up fallen leaves and diseased branches and leaves in the orchard, and bury or burn them deeply.\n(3) Apply protective fungicides starting in mid-May, every 15 days, for a total of 3-4 applications. Common fungicides include Bordeaux mixture (1:2:200), 30% Captan 500x solution, 77% Kocide 800x solution, 70% Thiophanate-methyl 800x solution, 70% Mancozeb 500x solution, and 75% Chlorothalonil 800x solution. Note that using Bordeaux mixture during the young fruit stage can cause fruit russeting."}'
},
{
"input": "Background(image_caption): Plant: Potato. Disease: Late Blight (Phytophthora infestans). The leaf shows water‑soaked, pale‑to‑brown lesions with grayish sporulation on the underside, indicating active infection that can quickly collapse foliage and threaten tubers. Outbreaks are favored by cool, wet weather (10–20°C), prolonged leaf wetness, rain splash, and dense canopies. Treatment: begin protectant plus systemic fungicides at first signs—chlorothalonil or mancozeb with cyazofamid, mandipropamid, or fluopicolide—rotating FRAC groups. Recommendations: remove infected debris, avoid overhead irrigation, improve airflow, hill soil to shield tubers, and scout frequently. \nQuestion: Can you provide some information on the disease distribution of Potato Late Blight?",
"output": '{"answer": "Potato late blight occurs worldwide in potato-growing regions, typically reducing yields by 30% during epidemic years. In the 1840s, the disease caused massive potato crop failure in Ireland, leading to a famine that killed over a million people and forced two million to emigrate. Initially speculated to have various causes, von Martius in 1842 first suggested a fungal origin, confirmed by Speerschneider in 1857, and later by de Bary (1861-1863). In China, the disease is prevalent in all potato-growing areas, with severe impacts in the southwest, northeast, and north regions during rainy years, causing 30-50% losses during major outbreaks."}'
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
    [system_message_prompt]+ example_messages+[human_message_prompt]
)
#+ example_messages
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
    parser = argparse.ArgumentParser(description="Generate dual-answer VQA for knowledge QA")
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
        reasoning_effort="medium",
        verbosity="medium",
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