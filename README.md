# Multilingual Mental Health Support Chatbot (PRJ_495)

An AI-powered, **non-clinical** emotional-support chatbot aligned with UN SDG 3 (Good Health and Well-being). It offers supportive conversation, coping suggestions and helpline information in multiple languages. It does **not** diagnose, prescribe, or replace a mental-health professional.

> If you or someone you know is in crisis, contact a local emergency service or a helpline right away. In India: Tele-MANAS 14416 or Kiran 1800-599-0019 (verify numbers before relying on them).

## Status

| Part | Status |
|---|---|
| Dataset preparation (cleaning, translation, safety examples) | Done |
| Fine-tuning of the language model (QLoRA) and first evaluation | Done |
| Backend: login, chat, saved chats, helplines, thought of the day, mood journal, safety plan, feedback, guided programs | Done (automated tests pass) |
| Rule-based crisis check and output guard | Done (phrase lists need native-speaker review for Telugu, Tamil, Kannada) |
| Website (React): chat, history, language selector, Get help, breathing, journal, safety plan, programs | Built |
| Voice input and spoken replies (browser speech) | Built (quality varies by browser, language and installed voices) |
| Fine-tuned model connected to the backend | Via a GPU laptop or Colab model server |
| Crisis classifier (second fine-tuned model) | Planned |
| Deployment (hosted backend, database and website) | Planned |
| Camera / facial analysis | Not included: weak reliability and privacy concerns (see docs/scope-and-ethics.md) |

## How it works (target design)

```
User (React website)
   |
Main backend (FastAPI + database)
   1. login check (JWT)
   2. crisis check on the text
        -> crisis detected: fixed message + helpline numbers (model NOT called)
   3. language routing: English/Spanish -> fine-tuned model,
                        Hindi/Telugu/Tamil/Kannada -> hosted LLM API (fallback)
   4. output guard: replies that sound like a diagnosis are replaced by a safe message
   5. save conversation
   |
Model server (GPU): Qwen2.5-3B-Instruct + fine-tuned LoRA adapter
```

## Features

- Multilingual supportive chat (English, Hindi, Telugu, Tamil, Kannada, Spanish), typed or spoken
- Always-visible Get help now button with helplines, and crisis replies that bypass the model
- Personal safety plan, shown next to the helplines if a crisis is detected
- Mood journal with a daily rating, note and weekly bar chart
- Guided programs (5 days to calmer exams, 5 days to better sleep habits)
- Thought of the day and a guided breathing exercise
- Saved conversations, thumbs up/down on replies, and download of a chat as text
- Delete a conversation, or the whole account with all its data

## Fine-tuning summary

- Base model: `Qwen/Qwen2.5-3B-Instruct`, 4-bit (QLoRA), LoRA rank 16 / alpha 32
- Data: 1,344 training and 101 validation examples in English, Hindi, Telugu, Tamil, Kannada and Spanish
- Result: validation loss 1.737 (epoch 1) to 1.722 (epoch 2), no overfitting
- Main finding: improved language matching and non-diagnostic behaviour in English and Spanish; Hindi and other Indic-language fluency is limited by the small base model

Details: [docs/training-report.md](docs/training-report.md)

## Repository contents

```
README.md
docs/
  scope-and-ethics.md    scope, safety rules, privacy
  dataset.md             sources, cleaning, counts, limits
  training-report.md     settings, loss, evaluation, limitations
training/
  01_prepare_data_and_translate.ipynb
  03_finetune_qlora_and_eval.ipynb
```
Backend, frontend and model-server folders will be added as they are built.

## Not in this repository

- API keys and tokens (use a `.env` file; never commit it)
- The trained LoRA adapter (stored on Google Drive; to be uploaded to a Hugging Face model repo)
- Raw dataset text and any user chats or journal entries

## Limitations

This is an academic prototype. The model is small, non-English data is machine-translated, and it can make mistakes, including occasionally sounding like it is diagnosing. It must not be used as a substitute for professional care.

## Team

Add team members and guide name here.
