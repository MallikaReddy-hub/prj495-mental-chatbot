# Scope and Ethics Note (PRJ_495)

## 1. What the chatbot is
A non-clinical emotional-support companion. It listens, reflects, offers general coping ideas (breathing, grounding, study or sleep routines) and shares helpline information. It does not diagnose conditions, recommend medicines or doses, or act as a therapist.

## 2. What it must not do
- Diagnose ("you have depression/anxiety/ADHD") or imply a diagnosis
- Recommend, name or dose medicines, or advise stopping medication
- Present itself as a replacement for a doctor, psychologist or counselor
- Continue a normal chat when a user may be in crisis

## 3. Crisis handling
- A rule-based safety layer runs **before** the language model. It checks text (and speech after transcription) for self-harm and suicide phrases in each supported language.
- If triggered, the model is **not** called. The system shows a fixed, empathetic message, strongly encourages contacting someone immediately, and lists helplines for the user's country and language.
- The phrase lists for Telugu, Tamil and Kannada need review by native speakers.
- Helpline numbers must be verified before every release.
- The model was deliberately not trained on crisis conversations, because a small model should not improvise in those situations.

## 4. Voice and camera
- **Voice:** users can speak their message and listen to replies. Speech is converted to text and then goes through the same crisis check as typed messages. Voice input uses the browser's own speech service (in Chrome and Edge this sends audio to the browser vendor), so the interface says so. Audio is never stored by this application.
- **Camera:** facial expression analysis was considered and deliberately excluded. Research on inferring emotion from faces is contested, accuracy varies with lighting, culture and skin tone, and a user study of face-aware chatbots found no clear gain in perceived empathy. A camera also raises privacy and consent concerns that are heavier in a mental health setting.

## 5. Data and privacy
| Data | Stored? | Notes |
|---|---|---|
| Account (email, name, password hash) | Yes | Passwords stored only as bcrypt hashes |
| Conversations | Yes, so users can revisit them | User can delete any conversation |
| Mood journal entries | Yes | User can delete entries |
| Audio | No | Transcribed, then discarded |

- Sharing a conversation is opt-in per conversation, read-only, expiring and revocable. Nothing is public by default.
- Users can delete their account and all associated data.
- User chats are not used to train the model.
- Secrets (API keys, tokens) are kept out of the repository.

## 6. Known limitations to disclose to users
- The assistant is an AI, can be wrong, and is not a substitute for professional help.
- Replies in Hindi, Telugu, Tamil and Kannada are less reliable than in English and Spanish.
- Mood cues from a camera are approximate and can be inaccurate.
