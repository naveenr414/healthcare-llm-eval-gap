import ast
import re
import regex
import pandas as pd
from openai import OpenAI

"""
  Decomposes the evaluation-deployment gap from the HELPMed RCT (Bean et al., 2025)
  into contextual and consequential components, as described in Section 3 of the paper.

  Four conditions:
      #1  Expert-written query, single-turn  (benchmark ceiling, no API call)
      #2  Patient first turn only, single-turn  (600 API calls)
      #3  GPT-4o accuracy in real multi-turn conversations  (no API call, prescored)
      #4  Human final answer after conversation  (no API call, prescored)

  Run from the healthcare-llm-eval-gap directory. Requires OPENAI_API_KEY in the environment.
"""


client = OpenAI()

# Prompt-related details; taken from the Bean et al. paper in the baselines.ipynb file
DESCRIPTION = (
    "Below is a fictional medical scenario. Based on the information provided, help to answer the questions at the end."
)
QUESTION = """Please answer the two following questions: 1) What healthcare service does this person need? Choose from the following options in the UK National Health Service:
                    Ambulance: The patient is in immediate life-threatening danger; The patient needs
                    treatment administered en-route to the hospital.
                    A&E: The patient needs emergency hospital treatment.
                    Urgent Primary Care: The patient should be seen today, by a GP, urgent care
                    centre, or similar.
                    Routine GP: The patient should be seen at some point, but it can wait.
                    Self-care: The patient can handle this at home or with over-the-counter
                    medication.
                    
                    2) Why did you make the choice you did? Please name all specific medical conditions you consider relevant to your decision."""


# Functions to parse responses + evaluate
def fuzzy_match_str(targets: list, search: str, threshold: int = 80) -> int:
    return sum(
        regex.search(
            f"({t.lower()}){{e<={(100 - threshold) * len(t) // 100}}}",
            search.lower()
        ) is not None
        for t in targets
    )

def build_prompt(body: str) -> str:
    return f"{DESCRIPTION}\n\n{body}\n\n{QUESTION}"

def call_gpt4o(prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-2024-05-13",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=512,
    )
    return response.choices[0].message.content

def extract_conditions_text(response: str) -> str:
    """Extract text after '2)' — same logic as baselines.ipynb Cell 54."""
    return re.split(r'2[\)\.]', str(response))[-1]

def parse_chat(raw):
    """Parse chat_history string into {'user': [...], 'bot': [...]}."""
    try:
        return ast.literal_eval(raw)
    except Exception:
        return None

def run_api_condition(scenarios,rows, body_fn, save_path, total):
    """
    Run GPT-4o on each row, where body_fn(chat) returns the prompt body.
    Saves results to save_path. Returns array of 0/1 correct values.
    """
    results = []
    for i, (_, row) in enumerate(rows.iterrows()):
        chat = parse_chat(row['chat_history'])
        if chat is None:
            continue
        scenario_id = row['scenario_id']
        full_diff = scenarios.loc[scenario_id, 'full_differential']

        body = body_fn(chat)
        if not body.strip():
            continue

        prompt = build_prompt(body)
        response = call_gpt4o(prompt)
        conditions_text = extract_conditions_text(response)


        correct = fuzzy_match_str(full_diff, conditions_text) > 0

        results.append({
            'id': row['id'],
            'scenario_id': scenario_id,
            'body': body,
            'response': response,
            'conditions_text': conditions_text,
            'correct': correct,
        })
        print(f"  [{i+1:3d}/{total}] scenario={scenario_id}  correct={correct}")

    df = pd.DataFrame(results)
    df.to_csv(save_path)
    return df['correct'].astype(float).values

def first_turn_body(chat):
    turns = sorted(chat['user'], key=lambda t: t['id'])
    return turns[0]['text'] if turns else ''

# 1: Single turn, expert written
direct = pd.read_csv('data/study1/direct_trials_condition.csv', index_col=0)
gpt_direct = direct[direct['model'] == 'GPT 4o']
p1_vals = gpt_direct['differential_correct'].astype(float).values
p1 = p1_vals.mean()

# 2: Evaluate on the first turn for patient written
scenarios = pd.read_csv('data/study1/scenarios.csv', index_col=0)
scenarios['full_differential'] = scenarios['full_differential'].apply(ast.literal_eval)
ex = pd.read_csv('data/study1/clean_examples.csv', index_col=0)
gpt4o_ex = ex[ex['treatment_id'] == 1].copy()
# Extract the first turn and run GPT-4o on it, to get the single-turn patient performance
# p2_vals = run_api_condition(
#     scenarios=scenarios,
#     rows=gpt4o_ex,
#     body_fn=first_turn_body,
#     save_path='data/study1/saved_results.csv',
#     total=len(gpt4o_ex),
# )
p2 = 0.828 # p2_vals.mean()

# 3: GPT-4o Recommendations
prescored = pd.read_csv('data/study1/clean_prescored.csv')
gpt4o_bot_prescored = gpt4o_ex.merge(prescored[['id', 'differential_correct_bot']], on='id')
p3_vals = gpt4o_bot_prescored['differential_correct_bot'].astype(float).values
p3 = p3_vals.mean()

# 4: Human Final Answer; using differential_correct instead of differential_correct_bot
gpt4o_prescored = gpt4o_ex.merge(prescored[['id', 'differential_correct']], on='id')
p4_vals = gpt4o_prescored['differential_correct'].astype(float).values
p4 = p4_vals.mean()

# Final output
print("\n── Gap Decomposition ──────────────────────────────────────────────────")
print(f"  #1 Expert query, single-turn:               {p1:.3f} ({p1:.1%})")
print(f"  #2 Patient first turn, single-turn:         {p2:.3f} ({p2:.1%})")
print(f"  #3 GPT-4o in real multi-turn:               {p3:.3f} ({p3:.1%})")
print(f"  #4 Human final answer:                      {p4:.3f} ({p4:.1%})")
print()
print(f"  Total gap (#1 → #4):                        {p1 - p4:.3f} ({(p1-p4):.1%})")
print()
print(f"  Query distribution — first turn (#1 → #2):  {p1-p2:+.3f} ({(p1-p2):+.1%})")
print(f"  First turn - multi-turn         (#2 → #3):  {p2-p3:+.3f} ({(p2-p3):+.1%})")
print(f"  Consequential (uptake)          (#3 → #4):  {p3-p4:+.3f} ({(p3-p4):+.1%})")
print()
print(f"  Contextual total (#1 → #3):             {p1-p3:.3f} ({(p1-p3):.1%})")
print(f"  Consequential total  (#3 → #4):             {p3-p4:.3f} ({(p3-p4):.1%})")
