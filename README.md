<center>

```ascii

           ▄█   ▄█▄            ▄█                 ▄██   ▄             ████████▄            
          ███ ▄███▀           ███                 ███   ██▄           ███   ▀███           
          ███▐██▀             ███                 ███▄▄▄███           ███    ███           
         ▄█████▀              ███                 ▀▀▀▀▀▀███           ███    ███           
        ▀▀█████▄              ███                 ▄██   ███           ███    ███           
          ███▐██▄             ███                 ███   ███           ███    ███           
          ███ ▀███▄           ███▌    ▄           ███   ███           ███   ▄███           
          ███   ▀█▀           █████▄▄██            ▀█████▀            ████████▀            
          ▀                   ▀                                                            

```
</center>

install → klyd init → klyd config --api-key sk-... → klyd run aider

## Quickstart

```bash
# 1. Install
pip install .

# 2. Initialize in your repo
cd your-project
klyd init

# 3. Configure an API Key
# Anthropic (Default)
klyd config --api-key sk-ant-...

# OR OpenAI
klyd config --openai-key sk-proj-... --model gpt-4o

# OR OpenRouter
klyd config --openrouter-key sk-or-... --model openrouter/auto

# OR Gemini
klyd config --gemini-key AIza... --model gemini-1.5-pro

# OR Groq
klyd config --groq-key gsk_... --model llama3-8b-8192

# 4. Use your agent as normal
klyd run aider
```

Decisions will automatically populate after you make commits. Review flagged contradictions using `klyd review`. Check current status with `klyd status`.
