# White Raven Tales Webapp - Handover Documentation

## Project Overview
**Gothic horror story search engine** with Flask backend + Qdrant Vector Database + Ollama embeddings.

## Current Status
- ✅ Code pushed to GitHub: https://github.com/RoboSyntax/white-raven-webapp
- ✅ Cloned on VPS: `/opt/white-raven-webapp-github`
- ✅ Docker container running on port 5001 (internal)
- ❌ **NOT accessible from outside** - needs Nginx/Traefik configuration

## VPS Infrastructure
- **Host:** n8n.srv859437.hstgr.cloud (31.97.45.50)
- **User:** ubuntu
- **Qdrant:** localhost:6333 (collection: white_raven_tales, 1101 stories)
- **Ollama:** localhost:11434 (model: nomic-embed-text for embeddings)
- **Existing apps:** baserow, n8n, other containers on root_n8n-network

## Project Structure
```
/opt/white-raven-webapp-github/
├── app.py                 # Flask backend (448 lines)
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container config (with curl for health checks)
├── docker-compose.yml    # Docker setup (port 5001, root_n8n-network)
├── templates/
│   └── index.html        # Gothic dashboard UI
└── static/
    ├── css/gothic.css    # Dark purple/gold styling
    └── js/dashboard.js   # AJAX semantic search
```

## Docker Container Details
- **Name:** white-raven-webapp
- **Image:** white-raven-webapp-white-raven-webapp
- **Port:** 0.0.0.0:5001->5000/tcp
- **Network:** root_n8n-network
- **Health Check:** curl http://localhost:5000/api/stats
- **Status:** Running and healthy

## API Endpoints (currently working internally)
- `GET /` - Gothic dashboard UI
- `POST /api/stories/search` - Semantic search with filters
- `GET /api/stories/random` - Random stories
- `GET /api/stories/recent` - Recent stories
- `GET /api/stories/top` - Top quality stories
- `GET /api/stories/<id>` - Single story details
- `GET /api/moods` - Available mood filters
- `GET /api/stats` - Database statistics

## What Works
✅ Container is running (45+ minutes uptime)
✅ API responds internally: `curl http://localhost:5001/api/stats` returns JSON
✅ Health checks pass
✅ Qdrant connection works (1101 stories, avg quality 5.0)
✅ GitHub repository is public and synced

## PROBLEM TO SOLVE
❌ **Webapp is NOT accessible from the internet**

When accessing http://n8n.srv859437.hstgr.cloud:5001 from external browser:
- Page does not load
- Probably firewall blocking port 5001
- OR needs reverse proxy (Nginx/Traefik)

## Your Mission
**Make the White Raven webapp publicly accessible at:**
- Option A: `http://n8n.srv859437.hstgr.cloud:5001` (open firewall)
- Option B: `https://raven.n8n.srv859437.hstgr.cloud` (reverse proxy + SSL)

## Environment Variables Needed
The container needs these connections (currently working):
```env
QDRANT_URL=http://host.docker.internal:6333
OLLAMA_URL=http://host.docker.internal:11434
```

## Existing Infrastructure to Consider
Check other running containers for reference:
```bash
sudo docker ps
# You'll see: baserow, n8n, white-raven-tales-app (nginx), etc.
```

Look at how `white-raven-tales-app` (nginx:alpine) is configured - it's publicly accessible.

## Suggested Approach
1. Check UFW firewall: `sudo ufw status`
2. Either:
   - Open port 5001: `sudo ufw allow 5001/tcp`
   - OR configure Nginx reverse proxy
   - OR configure Traefik (if running)
3. Test external access
4. Add SSL certificate if using subdomain

## Testing Commands
```bash
# Check container
sudo docker ps | grep white-raven
sudo docker logs white-raven-webapp --tail 20

# Test internally
curl http://localhost:5001/api/stats
curl -I http://localhost:5001/

# Check network
sudo docker network inspect root_n8n-network

# Check firewall
sudo ufw status
sudo iptables -L -n

# After fix, test externally
curl http://n8n.srv859437.hstgr.cloud:5001/api/stats
```

## GitHub Workflow
If you need to update code:
```bash
cd /opt/white-raven-webapp-github
git pull
sudo docker compose build
sudo docker compose up -d
```

## Technical Details
- **Python:** 3.11-slim
- **Web Server:** Gunicorn (2 workers, 120s timeout)
- **Framework:** Flask 3.1.2 + Flask-CORS
- **Vector DB:** Qdrant Client 1.16.2
- **Embeddings:** 768-dim vectors via Ollama nomic-embed-text
- **Health Check Interval:** 30s

## Gothic Theme Design
- Dark purple/midnight blue color scheme
- Antique gold accents
- Raven and mist imagery
- Responsive design
- AJAX-based search (no page reloads)
- Modal for full story view

## Contact
- GitHub: https://github.com/RoboSyntax/white-raven-webapp
- User: Norman Gehling (robo101@posteo.de)

## Success Criteria
✅ Webapp loads in external browser
✅ Search functionality works
✅ Can browse stories (random, recent, top)
✅ Story modal displays correctly
✅ API endpoints respond from external requests

---

**TLDR:** Container runs, API works internally, but needs firewall/reverse proxy config to be accessible from outside. Please make it publicly accessible!
