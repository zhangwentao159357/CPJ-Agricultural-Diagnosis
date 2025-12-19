# CPJ: Caption–Prompt–Judge for Agricultural Pest Diagnosis

<div align="center">

**Training-Free** | **Few-Shot** | **Explainable AI**

[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-orange.svg)](https://www.python.org/)

*Explainable Agricultural Pest Diagnosis via Interpretable Captions and LLM-Judged Refinement*

[📊 Prompts & Evaluation](PROMPTS_AND_EVALUATION.md) | [⚙️ Configuration](CONFIGURATION.md) | [📁 Data Format](DATA_FORMAT.md)

</div>

---

## 🌟 Highlights

<table>
<tr>
<td width="50%">

**🎯 Training-Free**
No costly supervised fine-tuning

**📊 Significant Gains**
+22.7 pp in disease classification

**🔍 Explainable**
Transparent diagnostic reasoning

</td>
<td width="50%">

**⚖️ Human-Validated**
94.2% agreement with experts

**📝 Fully Documented**
Complete prompts & criteria

**🚀 Easy to Use**
Few-shot learning approach

</td>
</tr>
</table>

---

## 💡 What is CPJ?

CPJ (Caption–Prompt–Judge) addresses a critical challenge in agricultural AI: **How can we make crop disease diagnosis both accurate and interpretable?**

Existing methods either:
- Provide only categorical labels ("diseased" / "healthy") without explanation
- Rely on costly supervised fine-tuning for each new disease
- Produce "black-box" predictions that farmers can't trust

**CPJ solves this by:**

1. **📝 Generating interpretable captions** that describe what the model "sees"
2. **🔄 Refining** low-quality captions using LLM-as-a-Judge
3. **🎯 Creating dual answers** from different diagnostic perspectives
4. **⚖️ Selecting** the best answer with transparent scoring

---

## 🏗️ Framework Architecture

<p align="center">
  <img src="docs/framework.png" alt="CPJ Framework" width="100%"/>
  <br/>
  <em>Figure 1: Overview of the CPJ pipeline with three cohesive stages</em>
</p>

### Three-Stage Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│  📝 Step 1: Caption Enhancement                                 │
│  ──────────────────────────────────────────────────────────     │
│  Image → Generate Caption → LLM Judge (score) → Refine if <4.0 │
│                                                                  │
│  Output: "Compound pinnate leaf with scattered necrotic         │
│           lesions (2-5mm) showing chlorotic halos..."           │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  🎯 Step 2: Dual-Answer VQA                                     │
│  ──────────────────────────────────────────────────────────     │
│  Caption + Question → VQA Model → Two Complementary Answers     │
│                                                                  │
│  Answer 1 (Disease Focus): Symptoms, severity, features         │
│  Answer 2 (Crop Focus): Species, morphology, growth stage       │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  ⚖️ Step 3: LLM-as-a-Judge Selection                            │
│  ──────────────────────────────────────────────────────────     │
│  Evaluate both answers (5 criteria × 0-1 points)                │
│  Select higher-scoring answer + Provide reasoning               │
│                                                                  │
│  Selected: 4.7/5.0  |  Unselected: 3.2/5.0                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Key Results

### Performance on CDDMBench

| Metric | GPT-5-Nano + GPT-5-mini Captions | Improvement |
|--------|----------------------------------|-------------|
| **Crop Classification** | 63.38% | **+22.7 pp** over no-caption baseline |
| **Disease Classification** | 33.70% | **+22.7 pp** over no-caption baseline |
| **Knowledge QA Score** | 84.5 / 100 | **+19.5 points** over no-caption baseline |

### LLM-as-a-Judge Validation

We validated our automated evaluation against human experts:

| Validation Metric | Result |
|-------------------|--------|
| **Agreement Rate** | 94.2% |
| **Cohen's Kappa** | 0.88 (strong agreement) |
| **Score Correlation** | r = 0.91 |
| **Sample Size** | 10% random sampling (396 cases) |

**Example Scores:**
- Selected answer: **4.9 / 5.0** ✅
- Unselected answer: **3.6 / 5.0**

This demonstrates that LLM-as-a-Judge is highly reliable for agricultural diagnosis evaluation.

---

## 📦 Dataset

This work uses the **CDDMBench** (Crop Disease Diagnosis Multimodal Benchmark) dataset:

- **Paper**: Xiang Liu, Zhaoxiang Liu, Huan Hu, Zezhou Chen, Kohou Wang, Kai Wang, and Shiguo Lian, "A multimodal benchmark dataset and model for crop disease diagnosis," in *European Conference on Computer Vision (ECCV)*, Springer, 2024, pp. 157–170.
- **GitHub**: [https://github.com/UnicomAI/UnicomBenchmark/tree/main/CDDMBench](https://github.com/UnicomAI/UnicomBenchmark/tree/main/CDDMBench)
- **Test Set**: 3,000 images for diagnosis task, 20 knowledge QA questions

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/CPJ-Agricultural-Diagnosis.git
cd CPJ-Agricultural-Diagnosis

# Install dependencies
pip install -r requirements.txt
```

### Configuration

**Set up your API credentials** in each script:

```python
# Example configuration
os.environ["OPENAI_API_BASE"] = "https://api.openai.com/v1"
os.environ["OPENAI_API_KEY"] = "your-api-key-here"

model = ChatOpenAI(
    model="gpt-4",  # or your preferred model
    temperature=0,
    max_retries=3,
    timeout=30
)
```

See [CONFIGURATION.md](CONFIGURATION.md) for detailed setup instructions.

### Run the Pipeline

```bash
# Step 1: Generate and refine captions
cd step1_caption_generation&enhancement
python caption_judge_optimize.py \
    --input your_images.json \
    --output refined_captions.json \
    --threshold 4.0

# Step 2: Generate dual VQA answers
cd ../step2_vqa_generation
python diagnosis_vqa.py \
    --input ../step1_caption_generation&enhancement/data/refined_captions.json \
    --output data/dual_answers.json \
    --model gpt-4

# Step 3: Select best answer with LLM-as-a-Judge
cd ../step3_answer_selection
python diagnosis_judge.py \
    --input ../step2_vqa_generation/data/dual_answers.json \
    --output data/final_answers.json \
    --evaluation-output data/evaluation_results.json \
    --model gpt-4
```

---

## 📖 Documentation

### 🔥 Core Documents

| Document | Description | Key Content |
|----------|-------------|-------------|
| **[PROMPTS_AND_EVALUATION.md](PROMPTS_AND_EVALUATION.md)** 🔥 | Complete prompt engineering and evaluation details | System prompts, few-shot examples, scoring rubrics, validation results |
| [CONFIGURATION.md](CONFIGURATION.md) | Setup and configuration guide | API setup, model configuration, troubleshooting |
| [DATA_FORMAT.md](DATA_FORMAT.md) | Data format specifications | JSON formats, validation, examples |

### Evaluation System (5-Point Scale)

**Caption Evaluation:**
- **Threshold**: τ = 4.0/5.0
- **Criteria**: Accuracy, Completeness, Detail, Relevance, Clarity
- **Process**: Auto-refine if score < 4.0

**Answer Evaluation:**
- **Dimensions**: Plant Accuracy, Disease Accuracy, Symptom Accuracy, Format Adherence, Completeness
- **Scoring**: Each 0-1, total 0-5
- **Selection**: Higher score + transparent reasoning

**👉 See [PROMPTS_AND_EVALUATION.md](PROMPTS_AND_EVALUATION.md) for complete details, examples, and validation results.**

---

## 🎯 Why CPJ Works

### 1. Interpretable Captions Bridge the Gap

Traditional approaches feed raw images directly to VQA models, losing critical visual information. CPJ's captions make this information explicit:

**❌ Without Caption:**
> Q: "Is this crop diseased?"
> A: "Yes" *(How did the model decide?)*

**✅ With CPJ Caption:**
> Caption: "Compound pinnate leaf with scattered dark brown lesions (2-5mm) showing yellow halos. Approximately 25% coverage..."
> Q: "Is this crop diseased?"
> A: "Yes, this tomato leaf shows bacterial spot. Key symptoms include..."
> *(Clear reasoning path!)*

### 2. Dual Answers Capture Complementary Information

Different diagnostic perspectives ensure nothing is missed:

```
Answer 1 (Disease Focus):
"This tomato leaf is affected by bacterial spot.
Key symptoms: dark brown lesions with yellow halos,
angular shape following leaf veins, 20-30% coverage..."

Answer 2 (Crop Focus):
"This is a tomato (Solanum lycopersicum) leaf
identified by compound pinnate structure with
serrated leaflets, showing bacterial spot symptoms..."
```

### 3. LLM-as-a-Judge Provides Transparent Selection

Every decision is explained with numerical scores:

```json
{
  "selected": "Answer 1",
  "selected_score": 4.7,
  "unselected_score": 3.2,
  "reasoning": "Answer 1 provides more specific symptom
                descriptions and disease stage assessment,
                making it more actionable for treatment"
}
```

---

## 📁 Repository Structure

```
CPJ-Agricultural-Diagnosis/
├── step1_caption_generation&enhancement/  # 📝 Caption generation & refinement
│   ├── caption_generation.py              (Initial caption generation)
│   ├── caption_judge_optimize.py          (Unified caption eval & optimization)
│   └── data/
│       └── refined_captions_sample.json   (Sample refined captions)
│
├── step2_vqa_generation/               # 🎯 Dual-answer generation
│   ├── diagnosis_vqa.py                   (Disease diagnosis task)
│   ├── knowledge_qa_vqa.py                (Knowledge QA task)
│   └── data/
│       └── dual_answers_sample.json       (Sample dual-answer VQA outputs)
│
├── step3_answer_selection/             # ⚖️ LLM-as-a-Judge selection
│   ├── diagnosis_judge.py                 (Diagnosis task judge)
│   ├── knowledge_qa_judge.py              (Knowledge QA task judge)
│   └── data/
│       └── judged_answers_sample.json     (Sample judged answers with scores)
│
├── dataset/                            # CDDMBench images
│   └── README.md                          (Download instructions)
│
├── docs/                               # Documentation images
│   └── framework.png                      (CPJ pipeline diagram)
│
├── PROMPTS_AND_EVALUATION.md          # 🔥 Complete evaluation details
├── CONFIGURATION.md                    # ⚙️ Setup guide
├── DATA_FORMAT.md                      # 📋 Data specifications
├── requirements.txt                    # 📦 Dependencies
├── LICENSE                             # MIT License
└── README.md                           # This file
```

---

## 🔬 Reproducibility

This repository provides everything needed to reproduce our results:

✅ **Complete Prompts**: All system prompts with few-shot examples
✅ **Evaluation Criteria**: Detailed scoring rubrics (5-point scale)
✅ **Human Validation**: Protocol, results, and agreement metrics
✅ **Code**: All three pipeline stages with configuration options
✅ **Data**: Annotated outputs with scores and reasoning
✅ **Documentation**: Setup, data formats, troubleshooting

**Response to Reviewer Concerns:**

> *Reviewer 1*: "How does the model evaluate the accuracy of the 'generated description' and the specific effects of optimizing the process?"

**Answer**: See [PROMPTS_AND_EVALUATION.md](PROMPTS_AND_EVALUATION.md) Section 1 for:
- LLM-as-a-Judge evaluation prompt
- 5-point scoring rubric with examples
- Refinement process for scores < 4.0
- Before/after refinement examples

> *Reviewer 2*: "More concrete description of judging criteria, prompt design, and failure cases would help reproducibility."

**Answer**: See [PROMPTS_AND_EVALUATION.md](PROMPTS_AND_EVALUATION.md) Sections 2-3 for:
- Complete judge system prompts
- Detailed scoring criteria (5 dimensions)
- Few-shot examples with scores
- Common failure patterns and analysis
- Human validation protocol and results

---

## 📧 Contact

- **Wentao Zhang**: 1557085480@qq.com
- **Tao Fang** †: taofang@mmc.edu.mo
- **Lina Lu** †: 3050651@qq.com
- **Lifei Wang**: wanglifei@mmc.edu.mo
- **Weihe Zhong**: whzhong@mmc.edu.mo

*† Co-corresponding authors*

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**⭐ Star this repo if you find it helpful!**

*This repository provides code, data, and comprehensive evaluation criteria for transparent and explainable agricultural pest diagnosis using large language models.*

</div>
