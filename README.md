# Real-Time Digital Self Platform

## Production-Ready AI Digital Clone with Redis & RQ

### Overview
A fully functional, production-ready platform that creates AI-powered digital versions of users. Built with SOLID principles, Redis caching, RQ background job processing, and designed to handle 1000+ concurrent users efficiently.

---

## Architecture

### Backend (FastAPI + Redis + RQ)

#### SOLID Principles Implementation

**1. Single Responsibility Principle**
- **Services Layer**: Each service handles one responsibility
  - `AuthService`: Authentication & JWT token management
  - `CacheService`: Redis caching operations
  - `LLMService`: Groq API integration for AI responses
  - `VideoService`: Newport AI video generation with RQ jobs
  - `KnowledgeService`: RAG system with ChromaDB

**2. Open/Closed Principle**
- Services are open for extension but closed for modification
- New services can be added without changing existing code

**3. Liskov Substitution Principle**
- Repository pattern allows substituting different data stores
- All repositories follow the same interface contract

**4. Interface Segregation Principle**
- Each service exposes only the methods needed by clients
- Routes depend only on specific service methods

**5. Dependency Inversion Principle**
- High-level modules (routes) depend on abstractions (services/repositories)
- Low-level modules (MongoDB, Redis) are injected via dependency injection

---

### Production Features

#### Redis Integration
- **Caching**: User profiles, conversation context, frequently accessed data
- **Session Management**: JWT token validation caching
- **Rate Limiting**: Request throttling per user
- **Job Queue**: RQ (Redis Queue) for background processing

#### RQ Background Workers
- **Video Generation Jobs**: Newport AI video synthesis runs asynchronously
- **Avatar Training Jobs**: Long-running avatar model training
- **Knowledge Indexing**: Document embedding generation
- **Scalable**: Multiple workers can process jobs in parallel

#### Performance Optimizations
1. **Database Indexing**: MongoDB indexes on frequently queried fields
2. **Connection Pooling**: Motor AsyncIO for MongoDB
3. **Async/Await**: Non-blocking I/O throughout
4. **Caching Strategy**: Redis TTL-based cache invalidation
5. **Lazy Loading**: On-demand resource loading

---

### Tech Stack

#### Backend
- **Framework**: FastAPI (Python 3.11)
- **Database**: MongoDB (Motor AsyncIO driver)
- **Cache & Queue**: Redis + RQ
- **AI APIs**: 
  - Groq API (Llama 3.1 70B) for LLM
  - Newport AI for video generation
- **Vector DB**: ChromaDB for RAG
- **Embeddings**: Sentence-Transformers

#### Frontend
- **Framework**: React 19
- **Routing**: React Router v7
- **UI Components**: Shadcn/UI (Radix UI)
- **Styling**: TailwindCSS
- **State**: Context API
- **HTTP Client**: Axios
- **Notifications**: Sonner

---

## Project Structure

```
/app/
├── backend/
│   ├── server.py                 # FastAPI app entry point
│   ├── .env                      # Environment variables
│   ├── requirements.txt          # Python dependencies
│   ├── models/                   # Pydantic models
│   │   ├── user.py
│   │   ├── avatar.py
│   │   ├── conversation.py
│   │   └── knowledge.py
│   ├── services/                 # Business logic (SOLID)
│   │   ├── auth_service.py
│   │   ├── cache_service.py
│   │   ├── llm_service.py
│   │   ├── video_service.py
│   │   └── knowledge_service.py
│   ├── repositories/             # Data access layer
│   │   ├── user_repository.py
│   │   ├── avatar_repository.py
│   │   ├── conversation_repository.py
│   │   └── knowledge_repository.py
│   ├── routes/                   # API endpoints
│   │   ├── auth_routes.py
│   │   ├── user_routes.py
│   │   ├── avatar_routes.py
│   │   ├── conversation_routes.py
│   │   ├── knowledge_routes.py
│   │   └── chat_routes.py
│   ├── workers/                  # RQ background jobs
│   │   ├── video_worker.py
│   │   └── start_worker.py
│   └── uploads/                  # File storage
│
├── frontend/
│   ├── src/
│   │   ├── App.js               # Main app component
│   │   ├── App.css              # Global styles
│   │   ├── context/
│   │   │   └── AuthContext.js   # Authentication context
│   │   ├── services/
│   │   │   └── api.js           # API client
│   │   ├── components/
│   │   │   ├── AuthForm.js
│   │   │   ├── ChatInterface.js
│   │   │   ├── OnboardingFlow.js
│   │   │   └── ui/              # Shadcn UI components
│   │   └── pages/
│   │       └── Dashboard.js
│   └── package.json
│
└── scripts/
    └── start_redis.sh           # Redis startup script
```

---

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user

### User Management
- `GET /api/users/profile` - Get user profile
- `PUT /api/users/profile` - Update profile

### Avatar
- `POST /api/avatars/upload` - Upload avatar video
- `GET /api/avatars/status/{avatar_id}` - Get training status
- `GET /api/avatars/my-avatar` - Get user's avatar

### Conversations
- `POST /api/conversations/` - Create conversation
- `GET /api/conversations/` - List conversations
- `GET /api/conversations/{id}` - Get conversation
- `DELETE /api/conversations/{id}` - Delete conversation

### Chat
- `POST /api/chat/send` - Send message & get AI response
- `GET /api/chat/video-status/{job_id}` - Check video generation status

### Knowledge Base
- `POST /api/knowledge/` - Add knowledge entry
- `POST /api/knowledge/upload` - Upload document (PDF/TXT)
- `GET /api/knowledge/` - List knowledge
- `DELETE /api/knowledge/{id}` - Delete knowledge

---

## Environment Variables

```bash
# MongoDB
MONGO_URL="mongodb://localhost:27017"
DB_NAME="digital_self_db"

# Redis
REDIS_HOST="localhost"
REDIS_PORT=6379

# JWT
JWT_SECRET_KEY="your-secret-key-change-in-production"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Keys
GROQ_API_KEY="your-groq-api-key"
NEWPORT_API_KEY="your-newport-api-key"

# Storage
UPLOAD_DIR="/app/backend/uploads"
MAX_UPLOAD_SIZE=104857600

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
```

---

## Installation & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB
- Redis

### Backend Setup

```bash
cd /app/backend

# Install dependencies
pip install -r requirements.txt

# Start Redis
/app/scripts/start_redis.sh

# Start RQ worker (separate terminal)
python workers/start_worker.py

# Start FastAPI server
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend Setup

```bash
cd /app/frontend

# Install dependencies
yarn install

# Start development server
yarn start
```

---

## Features Implemented

### Core Features
- ✅ JWT-based authentication (email/password)
- ✅ User onboarding flow (5 steps)
- ✅ Avatar video upload & training
- ✅ Personality configuration (formality, enthusiasm, verbosity, humor)
- ✅ Real-time chat with AI digital self
- ✅ Knowledge base with RAG (upload PDFs, TXT)
- ✅ Conversation management
- ✅ Background job processing with RQ

### AI Integration
- ✅ Groq API (Llama 3.1 70B) for natural language responses
- ✅ Personality-aware prompt engineering
- ✅ Context-aware conversations (last 10 messages)
- ✅ Knowledge-augmented generation (RAG)
- ✅ Newport AI video generation (queued jobs)

### Performance
- ✅ Redis caching for fast data access
- ✅ Async MongoDB operations
- ✅ Background job processing
- ✅ Optimized for 1000+ concurrent users

---

## Scalability

### Horizontal Scaling
1. **Multiple RQ Workers**: Run multiple worker processes
   ```bash
   # Worker 1
   python workers/start_worker.py
   # Worker 2 (separate process)
   python workers/start_worker.py
   ```

2. **Load Balancer**: Deploy behind Nginx/HAProxy
3. **Redis Cluster**: For distributed caching
4. **MongoDB Replica Set**: For database redundancy

### Monitoring
- RQ Dashboard for job monitoring
- Redis INFO for cache metrics
- FastAPI /health endpoint

---

## Best Practices Implemented

### Code Quality
- ✅ SOLID principles throughout
- ✅ Type hints (Pydantic models)
- ✅ Async/await for I/O operations
- ✅ Proper error handling
- ✅ Input validation

### Security
- ✅ Password hashing (bcrypt)
- ✅ JWT token authentication
- ✅ CORS configuration
- ✅ Input sanitization
- ✅ Environment variable protection

### Performance
- ✅ Database indexing
- ✅ Connection pooling
- ✅ Caching strategy
- ✅ Background jobs for heavy tasks
- ✅ Pagination on list endpoints

---

## Testing

### Manual Testing
1. Visit: `https://codebase-explorer-25.preview.emergentagent.com`
2. Create account
3. Complete onboarding
4. Upload avatar video
5. Start conversation
6. Upload knowledge documents

### API Testing
```bash
# Health check
curl https://codebase-explorer-25.preview.emergentagent.com/api/health

# Register
curl -X POST https://codebase-explorer-25.preview.emergentagent.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com","password":"password123"}'
```

---

## Future Enhancements

- [ ] Voice cloning integration (Coqui TTS / XTTS v2)
- [ ] Real-time WebSocket chat
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Mobile app (React Native)
- [ ] Social sharing of conversations
- [ ] Custom avatar styles
- [ ] Integration with calendar apps

---

## License
MIT License

## Credits
- Built with FastAPI, React, MongoDB, Redis
- AI powered by Groq API and Newport AI
- Vector search by ChromaDB