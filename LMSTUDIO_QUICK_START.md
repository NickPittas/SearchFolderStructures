# LM Studio Integration - Quick Start Guide

## 🚀 What is LM Studio?

**LM Studio** is a desktop application that allows you to run Large Language Models (LLMs) locally on your computer. It provides an OpenAI-compatible API server, making it easy to integrate with applications like this AI File Organizer.

### Key Benefits:
- ✅ **100% Free** - No API costs, no subscriptions
- ✅ **Complete Privacy** - All processing happens locally on your machine
- ✅ **Offline Capable** - Works without internet connection
- ✅ **Fast** - No network latency (depends on your hardware)
- ✅ **Wide Model Support** - Access to thousands of open-source models

---

## 📥 Installation

### Step 1: Download LM Studio
1. Visit [lmstudio.ai](https://lmstudio.ai)
2. Download the version for your operating system (Windows, Mac, or Linux)
3. Install and launch LM Studio

### Step 2: Download a Model
1. In LM Studio, click the **Search** icon (🔍) in the left sidebar
2. Browse or search for models. Recommended models:
   - **Llama 3.1 8B** - Good balance of speed and quality
   - **Mistral 7B** - Fast and efficient
   - **Qwen 2.5 7B** - Excellent for coding tasks
   - **DeepSeek Coder** - Specialized for code understanding
3. Click **Download** on your chosen model
4. Wait for the download to complete

### Step 3: Start the Local Server
1. Click the **Local Server** tab (↔️) in LM Studio
2. Select your downloaded model from the dropdown
3. Click **Start Server**
4. The server will start on `http://localhost:1234` by default
5. Keep LM Studio running while using the AI File Organizer

---

## 🔧 Using LM Studio with AI File Organizer

### Configuration Steps:

1. **Launch the AI File Organizer** application
2. In the **AI Setup** panel:
   - Select **"LM Studio"** from the Provider dropdown
   - The default URL `http://localhost:1234/v1` should appear
   - (Only change this if you configured LM Studio to use a different port)
3. Click **"Fetch Models"** button
   - This will retrieve the list of loaded models from LM Studio
   - Select your preferred model from the dropdown
4. You're ready to go! Start organizing files with AI

---

## 💡 Tips & Best Practices

### Model Selection
- **For Speed**: Use smaller models (7B parameters or less)
- **For Quality**: Use larger models (13B+ parameters) if your hardware supports it
- **For File Organization**: Most 7B models work excellently for this task

### Hardware Requirements
- **Minimum**: 8GB RAM, modern CPU
- **Recommended**: 16GB+ RAM, dedicated GPU (NVIDIA/AMD)
- **Optimal**: 32GB+ RAM, high-end GPU with 8GB+ VRAM

### Performance Optimization
1. In LM Studio, enable **GPU acceleration** if available
2. Adjust **context length** based on your needs (lower = faster)
3. Use **quantized models** (Q4, Q5) for better performance on limited hardware

---

## 🆚 LM Studio vs Other Providers

| Feature | LM Studio | Ollama | OpenRouter | Mistral |
|---------|-----------|--------|------------|---------|
| **Cost** | Free | Free | Pay-per-use | Pay-per-use |
| **Privacy** | 100% Local | 100% Local | Cloud-based | Cloud-based |
| **Setup** | GUI App | CLI Tool | API Key | API Key |
| **Speed** | Fast (local) | Fast (local) | Network dependent | Network dependent |
| **Model Selection** | Thousands | Hundreds | Premium models | Mistral models only |
| **Offline** | ✅ Yes | ✅ Yes | ❌ No | ❌ No |

---

## 🔍 Troubleshooting

### "Error fetching models"
- **Solution**: Make sure LM Studio's local server is running
- Check that the URL is correct: `http://localhost:1234/v1`
- Verify a model is loaded in LM Studio

### "No models found"
- **Solution**: Load a model in LM Studio's Local Server tab
- Click the model dropdown and select a downloaded model
- Restart the server if needed

### Slow Performance
- **Solution**: 
  - Use a smaller/quantized model
  - Enable GPU acceleration in LM Studio settings
  - Close other resource-intensive applications
  - Reduce batch size in the AI File Organizer

### Connection Refused
- **Solution**:
  - Ensure LM Studio server is started
  - Check firewall settings aren't blocking localhost connections
  - Verify the port number (default: 1234)

---

## 📚 Recommended Models for File Organization

1. **Qwen 2.5 7B Instruct** - Excellent reasoning, fast
2. **Llama 3.1 8B Instruct** - Well-balanced, reliable
3. **Mistral 7B Instruct** - Fast and efficient
4. **DeepSeek Coder 6.7B** - Great for technical file names
5. **Phi-3 Medium** - Compact but powerful

---

## 🎯 Next Steps

Once you have LM Studio configured:
1. Add files to organize using the file browser or drag-and-drop
2. Select your folder structure template (KENT or Sphere)
3. Click "Classify Files" to let AI suggest organization
4. Review and refine the suggestions
5. Execute the file moves

**Enjoy AI-powered file organization with complete privacy and zero cost!** 🎉

