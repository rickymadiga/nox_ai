# 🔥 NOX AI - Advanced Agent System

An intelligent multi-agent orchestration system with capabilities for research, app building, code debugging, and content generation.

## 🎯 Features

### 🔬 **Research Agent**
- Web search via Tavily API
- Multi-step research pipeline
- Source analysis and synthesis
- Evidence validation
- Comprehensive reporting

### 🏗️ **Build Agent**
- Dynamic app generation
- Estimated pricing
- Build quoting system
- Project scaffolding

### 🛠️ **Debug Agent**
- Code analysis
- Error detection
- Intelligent fixes
- Code review

### 🎨 **Content Generator**
- Image generation
- Video creation
- Text generation
- Content optimization

### 🧠 **Lily Orchestrator**
- Intent classification
- Multi-agent routing
- Conversation memory
- System state management

## 📁 Project Structure

```
nox_ai/
├── main.py                          # FastAPI entry point
├── .env                             # Environment variables
├── nox/
│   ├── core/
│   │   ├── engine.py               # Core orchestration engine
│   │   ├── capability_index.py      # Capability management
│   │   ├── memory.py               # In-memory storage
│   │   ├── event_bus.py            # Event system
│   │   └── registry.py             # Agent registry
│   └── runtime/
│       ├── engine_runtime.py       # Runtime wrapper
│       ├── async_runtime.py        # Async execution
│       └── plugin_loader.py        # Plugin loading system
├── orchestrator/
│   ├── lily.py                     # Main orchestrator/brain
│   ├── memory.py                   # Shared memory
│   └── tools.py                    # Tool definitions
├── plugins/
│   ├── research_agent/
│   │   ├── plugin.py
│   │   └── sub_agent/
│   │       ├── research_agent.py
│   │       ├── decomposer.py
│   │       ├── web_searcher.py
│   │       ├── analyzer.py
│   │       ├── validator.py
│   │       ├── synthesizer.py
│   │       └── report_generator.py
│   ├── chat_agent/
│   └── [other_plugins]/
└── nox_backend/
    ├── models/
    ├── routes/
    │   ├── chat.py
    ├── core/
    │   └── database.py
    └── [other_modules]/
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip/poetry

### Installation

1. **Clone repository**
```bash
git clone https://github.com/noxrenovine-coder/nox_ai.git
cd nox_ai
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys:
# - GROQ_API_KEY (Groq LLM)
# - TAVILY_API_KEY (Web search)
# - OPENAI_API_KEY (Optional: OpenAI)
# - DATABASE_URL (PostgreSQL/SQLite)
```

5. **Run the server**
```bash
python main.py
```

Server runs at: `http://localhost:8000`
API Docs: `http://localhost:8000/docs`

## 📊 API Endpoints

### Chat
```
POST /api/chat/message
{
  "prompt": "your message here"
}
```

### Research
```
POST /api/research/research
{
  "prompt": "search topic",
  "research_type": "general"
}
```

### Build
```
POST /api/chat/message
{
  "prompt": "build a todo app"
}
```

### Debug
```
POST /api/chat/message
{
  "prompt": "fix this code: ..."
}
```

## 🧠 How It Works

### Intent Classification Flow
1. **Lily** receives user input
2. Classifies intent (research, build, debug, chat, etc.)
3. Routes to appropriate agent
4. Agent executes task
5. Returns result to frontend

### Research Pipeline
```
User Query
    ↓
Decomposer (break into sub-questions)
    ↓
WebSearcher (gather sources via Tavily)
    ↓
Analyzer (extract key findings)
    ↓
Validator (check evidence quality)
    ↓
Synthesizer (synthesize conclusions)
    ↓
ReportGenerator (format findings)
```

## 🔑 Key Components

### Lily (orchestrator/lily.py)
- Intent classification with priority ordering
- Quote generation for builds
- Conversation memory management
- System state tracking

### Engine (nox/runtime/engine_runtime.py)
- Agent execution orchestration
- Event bus management
- Logging system
- ZIP file handling

### Research Agent (plugins/research_agent/)
- Multi-step research workflow
- Source credibility assessment
- Evidence synthesis
- Comprehensive reporting

## 🛠️ Configuration

### Environment Variables
```env
# APIs
GROQ_API_KEY=your_groq_key
TAVILY_API_KEY=your_tavily_key
OPENAI_API_KEY=your_openai_key

# Database
DATABASE_URL=sqlite:///nox.db

# Server
BASE_URL=http://localhost:8000
DEBUG=False

# Research
RESEARCH_MAX_SOURCES=10
RESEARCH_TIMEOUT=60
RESEARCH_DEPTH=advanced
```

## 📝 Intent Examples

```
Research:  "search AI trends 2024", "what is machine learning", "research quantum computing"
Build:     "build a todo app", "create a dashboard", "make a chat system"
Debug:     "fix this code", "help with this error", "debug this bug"
Content:   "generate image of...", "create video about...", "write article on..."
Chat:      "hello", "how are you", "tell me a joke"
```

## 🎯 Current Features

✅ Research Agent with web search
✅ Intent classification and routing
✅ Conversation memory
✅ Plugin system
✅ Event bus
✅ Async execution
✅ Multi-user support
✅ Chat API
✅ Research API

## 🚧 In Development

⏳ Build Agent (app generation)
⏳ Content Generator (images/videos)
⏳ Payment integration
⏳ User credits system
⏳ Database persistence

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License - see LICENSE file

## 📧 Contact

For questions or support: [your contact info]

---

**Built with 🔥 by NOX AI Team**