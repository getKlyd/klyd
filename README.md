```ascii
                                                                                  
kkkkkkkk                                                                  lllllll 
k::::::k                                                                  l:::::l 
k::::::k                                                                  l:::::l 
k::::::k                                                                  l:::::l 
 k:::::k    kkkkkkk         eeeeeeeeeeee             eeeeeeeeeeee          l::::l 
 k:::::k   k:::::k        ee::::::::::::ee         ee::::::::::::ee        l::::l 
 k:::::k  k:::::k        e::::::eeeee:::::ee      e::::::eeeee:::::ee      l::::l 
 k:::::k k:::::k        e::::::e     e:::::e     e::::::e     e:::::e      l::::l 
 k::::::k:::::k         e:::::::eeeee::::::e     e:::::::eeeee::::::e      l::::l 
 k:::::::::::k          e:::::::::::::::::e      e:::::::::::::::::e       l::::l 
 k:::::::::::k          e::::::eeeeeeeeeee       e::::::eeeeeeeeeee        l::::l 
 k::::::k:::::k         e:::::::e                e:::::::e                 l::::l 
k::::::k k:::::k        e::::::::e               e::::::::e               l::::::l
k::::::k  k:::::k        e::::::::eeeeeeee        e::::::::eeeeeeee       l::::::l
k::::::k   k:::::k        ee:::::::::::::e         ee:::::::::::::e       l::::::l
kkkkkkkk    kkkkkkk         eeeeeeeeeeeeee           eeeeeeeeeeeeee       llllllll
                                                                                  

```


install → keel init → keel config --api-key sk-... → keel run aider

## Quickstart

```bash
# 1. Install
pip install .

# 2. Initialize in your repo
cd your-project
keel init

# 3. Configure an API Key
# Anthropic (Default)
keel config --api-key sk-ant-...

# OR OpenAI
keel config --openai-key sk-proj-... --model gpt-4o

# OR OpenRouter
keel config --openrouter-key sk-or-... --model openrouter/auto

# OR Gemini
keel config --gemini-key AIza... --model gemini-1.5-pro

# OR Groq
keel config --groq-key gsk_... --model llama3-8b-8192

# 4. Use your agent as normal
keel run aider
```

Decisions will automatically populate after you make commits. Review flagged contradictions using `keel review`. Check current status with `keel status`.
