# Instructions for Claude on VPS

Hi Claude! I need your help making this webapp publicly accessible.

## Quick Context
- **Project:** White Raven Tales - Gothic horror story search engine
- **Location:** `/opt/white-raven-webapp-github`
- **GitHub:** https://github.com/RoboSyntax/white-raven-webapp
- **Current Status:** Docker container running internally on port 5001, but NOT accessible from outside

## The Problem
```bash
# This works (internally):
curl http://localhost:5001/api/stats

# This does NOT work (externally):
# Browser: http://n8n.srv859437.hstgr.cloud:5001
# Page doesn't load - probably firewall or needs reverse proxy
```

## What I Need
Make the webapp accessible from the internet at one of these:
- **Option A:** http://n8n.srv859437.hstgr.cloud:5001 (simple - just open firewall)
- **Option B:** https://raven.n8n.srv859437.hstgr.cloud (better - reverse proxy + SSL)

## Useful Info
- **Qdrant:** localhost:6333 (1101 stories in white_raven_tales collection)
- **Ollama:** localhost:11434 (nomic-embed-text model)
- **Docker Network:** root_n8n-network
- **Other apps work:** Check how white-raven-tales-app (nginx) is configured

## Check This First
```bash
# Container status
sudo docker ps | grep white-raven-webapp

# Firewall
sudo ufw status

# Test internally
curl http://localhost:5001/api/stats
```

## Full Documentation
See `HANDOVER.md` in `/opt/white-raven-webapp-github/` for complete technical details.

## Success
When done, I should be able to:
1. Open the webapp in my browser from outside the VPS
2. Use the search functionality
3. Browse and view horror stories

Thanks! 🐦‍⬛
