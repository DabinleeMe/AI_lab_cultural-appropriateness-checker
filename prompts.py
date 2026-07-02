"""
[What is this file for?]
This is a "prompt storage" file that 'Prompting.py' file imports directly.

This file holds the prompt text for all 3 versions (A/B/C). All three are forced
to answer in the exact same JSON shape, so Step 3 can grade A/B/C results with the
same code:

    {"risk": "...", "topic": "...", "intent": "...", "reason": "..."}

This one JSON answer covers these 3 tasks:
  - risk   -> Task 1: risk classification (Expected / Normal / Taboo)
  - topic  -> Task 2: which cultural topic was touched
  - intent -> Task 3: intent/context detection (Intentional / Unintentional / Unclear)
  - reason -> one-sentence explanation (used for Step 5 error analysis)

Ground truth lives in Task1_Global_Advertising_Dataset.csv, in the columns
gt_risk, gt_topic, gt_intent, gt_context.

Note: the 5 few-shot examples used in Prompt C (originally ids 9, 21, 30, 35, 40)
are no longer in the dataset CSV -- they only exist in FEWSHOT_EXAMPLES below.
So there's nothing to exclude at Step 4 evaluation time (they were never in the
dataset to begin with).
"""

# ---------------------------------------------------------------------------
# Everything below is shared material used by all 3 versions (label lists,
# output format, label definitions). Edit this block once and it applies to A/B/C.
# ---------------------------------------------------------------------------

RISK_LABELS = ["Expected", "Normal", "Taboo"]

TOPIC_LABELS = [
    "Religion",
    "Gender",
    "Race/Ethnicity",
    "Language/Wordplay",
    "History/Politics",
    "None",
]

INTENT_LABELS = ["Intentional", "Unintentional", "Unclear"]

# The instruction that forces the model to output ONLY this JSON shape. Used identically by A/B/C.
OUTPUT_SCHEMA_INSTRUCTION = """Respond with ONLY a single valid JSON object. No markdown, no code fences, no extra text before or after.
The JSON object must have exactly these 4 keys:
{
  "risk": one of ["Expected", "Normal", "Taboo"],
  "topic": one of ["Religion", "Gender", "Race/Ethnicity", "Language/Wordplay", "History/Politics", "None"],
  "intent": one of ["Intentional", "Unintentional", "Unclear"],
  "reason": a single sentence (max 30 words) explaining the classification
}"""

# Spells out what each label means. Used in B/C, deliberately left out of A (bare)
# -- the whole point of A is to give label names with no definitions.
TASK_DEFINITIONS = """Definitions:
- risk: How culturally risky is this marketing copy for the target culture?
    Expected = safe, no cultural reference at all, or a well-executed cultural reference with no risk.
    Normal   = the copy engages with a specific cultural/religious/festival theme but does so appropriately -- low risk.
    Taboo    = the copy violates a cultural, religious, gender, or historical norm and would likely cause backlash.
- topic: which single topic is most related to the cultural risk (or "None" if risk is Expected/Normal with no specific topic engaged).
- intent: was the cultural reference/violation likely intentional (a deliberate creative or marketing choice) or unintentional (an oversight, mistranslation, or lack of awareness)? Use "Unclear" only if genuinely ambiguous.
"""

# Placeholder for the actual ad copy and target culture (filled in with real values each time)
USER_TEMPLATE = """Marketing copy: {text}
Target culture: {target_culture}"""


# ---------------------------------------------------------------------------
# VERSION A — Zero-shot (bare)
# No persona, no examples, no label definitions. Just label names + output format.
# No system message at all (None) -- everything is in one user message.
# ---------------------------------------------------------------------------

PROMPT_A_SYSTEM = None  # Version A has no system message, just one user message

PROMPT_A_USER = f"""Classify the marketing copy below.

{OUTPUT_SCHEMA_INSTRUCTION}

{USER_TEMPLATE}"""


# ---------------------------------------------------------------------------
# VERSION B — Persona + Stakes/Pressure
# Gives the model an expert persona, adds a pressure sentence saying "get this
# wrong and the brand loses real money", and explicitly says not to judge from
# a Western default.
# ---------------------------------------------------------------------------

PROMPT_B_SYSTEM = """You are a veteran cross-border marketing consultant and cultural anthropologist with 20 years of experience advising global brands on international ad campaigns. You have lived and worked across East Asia, the Middle East, Latin America, and South Asia, and you are known for catching subtle cultural risks that Western-trained reviewers miss.

The stakes are real. If you misjudge this copy, the brand could face a viral backlash, boycotts, forced product recalls, and millions of dollars in losses -- the same kind of fallout as Dolce & Gabbana in China or Pepsi's Kendall Jenner ad. Your assessment will directly decide whether this campaign launches. A wrong call here is not a hypothetical error -- it is a costly real-world failure that damages the brand and your professional reputation.

Do NOT default to Western/American cultural assumptions. Evaluate strictly from the perspective of the target culture provided -- its religious norms, gender norms, historical sensitivities, and language-specific double meanings are the reference point, not your own."""

PROMPT_B_USER = f"""{TASK_DEFINITIONS}
{OUTPUT_SCHEMA_INSTRUCTION}

{USER_TEMPLATE}"""


# ---------------------------------------------------------------------------
# VERSION C — Few-shot + Chain-of-Thought
# Reuses B's persona + stakes system message, and adds (1) a step-by-step
# reasoning instruction and (2) 5 worked examples with the correct answer.
# ---------------------------------------------------------------------------

PROMPT_C_SYSTEM = PROMPT_B_SYSTEM + """

For every new item, think step by step BEFORE giving your final answer:
Step 1: Identify any cultural element referenced in the copy (religion, gender roles, gestures, historical symbols, language/wordplay).
Step 2: Consider how someone from the target culture specifically (not a Western default) would perceive it.
Step 3: Decide the risk level and whether the reference was likely intentional or unintentional.
Show this reasoning under "Step-by-step:", then give the final JSON on its own line, prefixed with "FINAL:"."""

# These 5 items were originally dataset rows with ids 9/21/30/35/40. They no longer
# exist in the dataset -- only here. Each one is pre-written as "reason step by
# step -> arrive at this answer" (a worked few-shot example).
FEWSHOT_EXAMPLES = [
    {
        "id": 30,
        "text": 'Air Max 270 sole features a script-style "Air" logo some readers perceived as resembling the Arabic word "Allah"',
        "target_culture": "Global / Muslim-majority markets",
        "reasoning": (
            "Step 1: The cultural element is a religious one -- a logo design on the sole of a shoe that "
            "resembles Arabic script for a sacred word.\n"
            "Step 2: In Muslim-majority cultures, the word \"Allah\" carries the highest degree of sanctity. "
            "Placing anything resembling it on a shoe sole -- an object that is stepped on and touches the "
            "ground -- is considered deeply disrespectful, regardless of the brand's intent.\n"
            "Step 3: The brand's intent was almost certainly just a stylized \"Air\" logo (unintentional), but "
            "the impact was severe backlash and recall demands from Muslim communities."
        ),
        "final": {"risk": "Taboo", "topic": "Religion", "intent": "Unintentional",
                  "reason": "A shoe-sole logo resembling the sacred word 'Allah' is deeply disrespectful in Muslim-majority cultures, regardless of intent."},
    },
    {
        "id": 21,
        "text": "\"Women belong in the kitchen.\" (International Women's Day tweet, meant as a hook for a female-chef scholarship)",
        "target_culture": "UK",
        "reasoning": (
            "Step 1: The cultural element is a gender-role stereotype stated as a bald claim.\n"
            "Step 2: In UK culture (and most Western markets), this phrase directly invokes a well-known sexist "
            "stereotype about women's domestic role, especially loaded on International Women's Day.\n"
            "Step 3: The brand intended a provocative hook that would be resolved by a scholarship announcement "
            "later in the thread (intentional), but most readers only saw the opening line, so it read as "
            "straightforwardly sexist."
        ),
        "final": {"risk": "Taboo", "topic": "Gender", "intent": "Intentional",
                  "reason": "The line reproduces a sexist stereotype about women's roles; the intended twist was buried and most readers never saw it."},
    },
    {
        "id": 9,
        "text": "\"Finger-lickin' good\" mistranslated into Chinese as roughly \"eat your fingers off\"",
        "target_culture": "China",
        "reasoning": (
            "Step 1: The cultural element is a language/translation issue -- an English idiom translated too literally.\n"
            "Step 2: In Chinese, the literal translation loses the idiomatic 'delicious' meaning and instead reads "
            "as a strange, slightly disturbing command to bite off one's own fingers.\n"
            "Step 3: This was a translation oversight, not a deliberate choice, but it still damaged the brand's "
            "image and became a well-known case of a marketing translation failure."
        ),
        "final": {"risk": "Taboo", "topic": "Language/Wordplay", "intent": "Unintentional",
                  "reason": "A literal translation of an English idiom produced a nonsensical and unsettling phrase in Chinese."},
    },
    {
        "id": 35,
        "text": "Every party starts with a group chat and ends with a pack of Doritos \U0001F60F\U0001F525 #doritos #diwali #houseparty #doritosnachos #crunch #forthebold #friends",
        "target_culture": "India",
        "reasoning": (
            "Step 1: The cultural element is a festival tie-in (Diwali) used purely as a seasonal/social hook, with "
            "no religious symbols, deities, or sacred practices mentioned.\n"
            "Step 2: In India, brands tying seasonal promotions to Diwali as a 'festive/party season' is extremely "
            "common and generally welcomed, since the ad does not touch any specific religious ritual.\n"
            "Step 3: This is a deliberate, low-risk festival tie-in that was well received -- appropriate cultural "
            "engagement rather than a violation."
        ),
        "final": {"risk": "Normal", "topic": "None", "intent": "Intentional",
                  "reason": "A generic Diwali-season party tie-in with no specific religious content is a low-risk, well-received cultural reference."},
    },
    {
        "id": 40,
        "text": "Run through summer with gear that can take the heat.",
        "target_culture": "USA",
        "reasoning": (
            "Step 1: No cultural, religious, gender, or historical element is referenced at all -- purely a generic "
            "seasonal product tagline.\n"
            "Step 2: This copy would read identically safe in virtually any culture; there is nothing "
            "culture-specific to evaluate.\n"
            "Step 3: No risk of any kind."
        ),
        "final": {"risk": "Expected", "topic": "None", "intent": "Intentional",
                  "reason": "Generic seasonal product copy with no cultural reference of any kind."},
    },
]


def _format_fewshot_block() -> str:
    # Combines the 5 FEWSHOT_EXAMPLES above into one long text block formatted as
    # "Marketing copy / Target culture / Step-by-step / FINAL". You won't call this
    # directly -- PROMPT_C_USER_PREFIX below uses it.
    blocks = []
    for ex in FEWSHOT_EXAMPLES:
        final_json = (
            '{"risk": "%s", "topic": "%s", "intent": "%s", "reason": "%s"}'
            % (ex["final"]["risk"], ex["final"]["topic"], ex["final"]["intent"], ex["final"]["reason"])
        )
        blocks.append(
            f"Marketing copy: {ex['text']}\n"
            f"Target culture: {ex['target_culture']}\n"
            f"Step-by-step:\n{ex['reasoning']}\n"
            f"FINAL: {final_json}"
        )
    return "\n\n---\n\n".join(blocks)


PROMPT_C_USER_PREFIX = f"""{TASK_DEFINITIONS}
{OUTPUT_SCHEMA_INSTRUCTION}

Here are {len(FEWSHOT_EXAMPLES)} worked examples:

{_format_fewshot_block()}

---

Now analyze the following new item the same way (Step-by-step, then FINAL: <json>):
"""

PROMPT_C_USER = PROMPT_C_USER_PREFIX + USER_TEMPLATE


# ---------------------------------------------------------------------------
# The function Step 3 actually uses. This is the only thing you need to know --
# everything above is just material this function assembles.
# Usage: from prompts import build_prompt
#        system_prompt, user_prompt = build_prompt("A", text="...", target_culture="Japan")
#        -> pass these two values straight into the Ollama call (skip system_prompt if None)
# ---------------------------------------------------------------------------

def build_prompt(version: str, text: str, target_culture: str):
    """Returns (system_prompt_or_None, user_prompt) for the given version ('A', 'B', or 'C')."""
    filled_user_template = USER_TEMPLATE.format(text=text, target_culture=target_culture)

    if version == "A":
        return None, PROMPT_A_USER.replace(USER_TEMPLATE, filled_user_template)
    elif version == "B":
        return PROMPT_B_SYSTEM, PROMPT_B_USER.replace(USER_TEMPLATE, filled_user_template)
    elif version == "C":
        return PROMPT_C_SYSTEM, PROMPT_C_USER.replace(USER_TEMPLATE, filled_user_template)
    else:
        raise ValueError("version must be 'A', 'B', or 'C'")


if __name__ == "__main__":
    # quick smoke test
    for v in ["A", "B", "C"]:
        sys_p, user_p = build_prompt(v, "Sample ad copy here.", "Japan")
        print(f"=== Version {v} ===")
        print("system:", (sys_p[:80] + "...") if sys_p else None)
        print("user (first 200 chars):", user_p[:200])
        print()
