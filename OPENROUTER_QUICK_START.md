# 🚀 Quick Start Guide - OpenRouter Integration

## Getting Started with OpenRouter

### 1. Install Dependencies
```bash
pip install requests cryptography
```

### 2. Get OpenRouter API Key
1. Visit [OpenRouter.ai](https://openrouter.ai)
2. Sign up for an account
3. Generate an API key from your dashboard
4. Copy the key (starts with `sk-or-...`)

### 3. Launch Application
```bash
python FIelOrganizer.py
```

### 4. Configure OpenRouter
1. **Select Provider**: Choose "OpenRouter" from the dropdown
2. **Enter API Key**: Paste your API key in the password field
3. **Save Key** (Optional): Click "Save" to encrypt and store locally
4. **Select Model**: Choose from available models (Claude 3.5 Sonnet recommended)

### 5. Start Classifying Files
1. Add files or folders to classify
2. Set your destination project folder
3. Choose folder structure (KENT or Sphere)
4. Click "Classify Files"
5. Review and move/copy results

## 🔐 Secure Key Management

### Saving Your API Key
- Click "Save" after entering your key
- Choose a master password
- Key is encrypted and stored locally
- Safe to use on your machine

### Loading Your Saved Key
- Click "Load" button
- Enter your master password
- Key is decrypted and filled in automatically

### Security Notes
- Keys are encrypted with AES-256
- Master password is never stored
- Files are saved in your user home directory
- Only you can decrypt with your password

## 🎯 Model Recommendations

### Best for Quality
- **Claude 3.5 Sonnet** - Excellent reasoning and accuracy
- **GPT-4 Turbo** - Strong performance, good speed

### Best for Speed
- **Claude 3 Haiku** - Fast and efficient
- **GPT-4 Mini** - Quick responses, lower cost

### Best for Complex Tasks
- **Claude 3 Opus** - Maximum capability
- **Llama 3.1 405B** - Open source powerhouse

## 💰 Cost Considerations

OpenRouter charges per API call. Costs vary by model:
- **Budget**: Llama 3.1 8B, Claude Haiku
- **Balanced**: Claude 3.5 Sonnet, GPT-4 Mini  
- **Premium**: Claude Opus, GPT-4 Turbo

Check current pricing at [OpenRouter.ai/pricing](https://openrouter.ai/pricing)

## 🆚 Ollama vs OpenRouter

### Use Ollama When:
- ✅ You want free local processing
- ✅ You have good local hardware (8GB+ RAM)
- ✅ Privacy is paramount
- ✅ You're okay with slower speeds

### Use OpenRouter When:
- ✅ You want the latest/best models
- ✅ You need faster processing
- ✅ Limited local hardware
- ✅ Willing to pay for convenience

## 🔧 Troubleshooting

### "No models found"
- Check your API key is correct
- Ensure internet connection
- Try clicking "Fetch Models" again

### "API Error" messages
- Verify API key is valid
- Check you have OpenRouter credits
- Try a different model

### "Configuration Error"
- Select a provider first
- Enter API key for OpenRouter
- Select a model from dropdown

### Secure storage issues
- Install cryptography: `pip install cryptography`
- Check master password is correct
- Try deleting and re-saving key

## 🎉 Happy Organizing!

You're now ready to use AI-powered file organization with OpenRouter. The system will intelligently classify your files into proper folder structures, saving you hours of manual work!

For more help, check the main README.md file.
