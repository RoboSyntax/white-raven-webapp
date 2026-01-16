# White Raven Tales - VPS YouTube Automation Factory

**For Claude on VPS:** Complete implementation guide for n8n-based video automation

---

## Executive Summary

**Mission**: Build fully automated n8n workflows on VPS for end-to-end YouTube video production (Story → Voice → Visuals → Edit → Upload)

**Target**: 3-7 videos/week for White Raven Tales channel

**All work happens on VPS** - No Windows PC dependencies, no password prompts needed

---

## VPS Context & Current State

### Infrastructure Already Running

| Service | Status | Location | Access |
|---------|--------|----------|--------|
| **n8n** | ✅ Running | https://n8n.srv859437.hstgr.cloud | Web UI |
| **Qdrant Vector DB** | ✅ Running | localhost:6333 | Internal |
| **Ollama** | ✅ Running | localhost:11434 | Internal |
| **White Raven Webapp** | ✅ Running | http://localhost:5001 | Internal |
| **FFmpeg** | ⚠️ Check if installed | `which ffmpeg` | CLI |
| **Docker** | ✅ Running | All services containerized | CLI |

### Story Database
- **Qdrant Collection**: `white_raven_tales`
- **Story Count**: 1,101 stories
- **Access**: Via white-raven-webapp API at http://localhost:5001

### API Endpoints Available
```bash
# Story Selection
GET http://localhost:5001/api/stories/random?min_quality=7
GET http://localhost:5001/api/stories/recent
GET http://localhost:5001/api/stories/top
POST http://localhost:5001/api/stories/search

# Metadata
GET http://localhost:5001/api/stats
GET http://localhost:5001/api/moods
```

---

## Required API Keys (External Services)

### 1. Claude API (Anthropic)
**Purpose**: Refine stories for YouTube narration (add hook, CTA, optimize length)

**How to get**:
```bash
# Visit: https://console.anthropic.com/
# Create account, get API key
# Cost: ~$0.05/video (~$1.50/week for 30 videos)
```

**Store in n8n Credentials**:
- Name: `Claude API`
- Type: `Header Auth`
- Header Name: `x-api-key`
- Value: `sk-ant-api03-...`

---

### 2. ElevenLabs API
**Purpose**: Text-to-speech voice narration

**How to get**:
```bash
# Visit: https://elevenlabs.io/
# Create account, get API key
# Voice ID needed: z2nzgwINFZrM0t9eOfjM (White Raven female voice)
```

**Store in n8n Credentials**:
- Name: `ElevenLabs API`
- Type: `Header Auth`
- Header Name: `xi-api-key`
- Value: `your_elevenlabs_key`

---

### 3. Pexels Video API
**Purpose**: Download gothic B-roll footage

**How to get**:
```bash
# Visit: https://www.pexels.com/api/
# Create account, get API key (free tier: 200 requests/hour)
```

**Store in n8n Credentials**:
- Name: `Pexels API`
- Type: `Header Auth`
- Header Name: `Authorization`
- Value: `your_pexels_key`

---

### 4. fal.ai API
**Purpose**: Generate gothic thumbnails (Flux model)

**How to get**:
```bash
# Visit: https://fal.ai/
# Create account, get API key
# Free tier: 10 images
```

**Store in n8n Credentials**:
- Name: `fal.ai API`
- Type: `Header Auth`
- Header Name: `Authorization`
- Value: `Key your_fal_key`

---

### 5. YouTube Data API v3
**Purpose**: Upload videos to YouTube

**How to get**:
```bash
# 1. Go to: https://console.cloud.google.com/
# 2. Create new project: "WhiteRavenYouTube"
# 3. Enable: YouTube Data API v3
# 4. Create OAuth 2.0 credentials
# 5. Download JSON credentials file
```

**Store in n8n Credentials**:
- Name: `YouTube OAuth2`
- Type: `OAuth2 API`
- Grant Type: `Authorization Code`
- Client ID: from downloaded JSON
- Client Secret: from downloaded JSON
- Scope: `https://www.googleapis.com/auth/youtube.upload`

---

## VPS Directory Structure

Create these directories on VPS:

```bash
# Create working directories
sudo mkdir -p /opt/white-raven-automation/{tmp,output,projects,logs}
sudo mkdir -p /opt/white-raven-automation/tmp/{audio,videos,thumbnails,srt}
sudo mkdir -p /opt/white-raven-automation/output/{final,archive}
sudo chown -R ubuntu:ubuntu /opt/white-raven-automation
chmod -R 755 /opt/white-raven-automation

# Verify structure
tree -L 2 /opt/white-raven-automation
```

**Expected output**:
```
/opt/white-raven-automation/
├── tmp/
│   ├── audio/
│   ├── videos/
│   ├── thumbnails/
│   └── srt/
├── output/
│   ├── final/
│   └── archive/
├── projects/
└── logs/
```

---

## Implementation Workflow

### Phase 1: Setup & Verification (30 min)

#### 1.1 Check FFmpeg Installation
```bash
# Test if FFmpeg is installed
ffmpeg -version

# If not installed:
sudo apt update
sudo apt install -y ffmpeg

# Verify installation
ffmpeg -version
ffprobe -version
```

#### 1.2 Test Story API
```bash
# Test random story fetch
curl -s http://localhost:5001/api/stories/random | jq .

# Test with quality filter
curl -s "http://localhost:5001/api/stories/random?min_quality=7" | jq .

# Check stats
curl -s http://localhost:5001/api/stats | jq .
```

#### 1.3 Test Qdrant Connection
```bash
# Check Qdrant health
curl -s http://localhost:6333/collections/white_raven_tales | jq .

# Should show:
# - "points_count": 1101
# - "status": "green"
```

---

### Phase 2: Build n8n Sub-Workflows (4-6 hours)

#### 2.1 Create n8n Tags
In n8n web UI:
1. Settings → Tags
2. Create tags:
   - `white_raven` (color: purple)
   - `video_automation` (color: blue)
   - `youtube` (color: red)

---

#### 2.2 Sub-Workflow 1: Story Selection

**Name**: `SW - WhiteRaven - Story Selection - Qdrant - v1.0`

**Nodes**:

1. **Manual Trigger** (for testing) or **Schedule Trigger** (Mon 9am, Wed 2pm, Fri 11am)

2. **HTTP Request Node**: Fetch Story
   - Method: GET
   - URL: `http://localhost:5001/api/stories/random?min_quality=7`
   - Authentication: None (internal)
   - Response: JSON
   - Store response in `{{ $json }}`

3. **Set Variables Node**: Extract Story Data
   ```javascript
   // Code Node
   const story = $input.item.json;

   return {
     story_id: story.id,
     story_title: story.title,
     story_content: story.content,
     story_mood: story.mood,
     story_themes: story.themes,
     story_quality: story.quality_score
   };
   ```

4. **Error Handler** (If Node): Fallback to hardcoded story
   - Condition: `{{ $json.story_id }} is empty`
   - If true → use backup story from local file

**Output**: `{ story_id, story_title, story_content, story_mood }`

**Test**: Click "Execute Workflow" and verify story data appears in output

---

#### 2.3 Sub-Workflow 2: Claude Script Refinement

**Name**: `SW - WhiteRaven - Script Refinement - Claude - v1.0`

**Nodes**:

1. **HTTP Request Node**: Claude API
   - Method: POST
   - URL: `https://api.anthropic.com/v1/messages`
   - Authentication: Use credential "Claude API"
   - Headers:
     - `anthropic-version: 2023-06-01`
     - `content-type: application/json`
   - Body (JSON):
   ```json
   {
     "model": "claude-3-5-sonnet-20241022",
     "max_tokens": 1024,
     "messages": [
       {
         "role": "user",
         "content": "Adapt this gothic horror story for YouTube Shorts narration.\n\nOriginal story:\n{{ $json.story_content }}\n\nRequirements:\n- Target length: 90 seconds (220-250 words)\n- Add compelling hook in first 5 seconds\n- White Raven Tales brand voice: mysterious, poetic, atmospheric\n- End with call-to-action: 'Follow for more tales from the shadows'\n- Remove any content that doesn't work for narration\n- Output ONLY the refined script, no explanations\n\nRefined script:"
       }
     ]
   }
   ```

2. **Code Node**: Extract Refined Script
   ```javascript
   const response = $input.item.json;
   const refined_script = response.content[0].text;

   return {
     refined_script: refined_script,
     word_count: refined_script.split(' ').length
   };
   ```

**Output**: `{ refined_script, word_count }`

**Test**: Input sample story, verify output is 220-250 words with hook and CTA

---

#### 2.4 Sub-Workflow 3: ElevenLabs Voice Generation

**Name**: `SW - WhiteRaven - Narration - ElevenLabs - v1.0`

**Nodes**:

1. **HTTP Request Node**: ElevenLabs TTS
   - Method: POST
   - URL: `https://api.elevenlabs.io/v1/text-to-speech/z2nzgwINFZrM0t9eOfjM`
   - Authentication: Use credential "ElevenLabs API"
   - Body (JSON):
   ```json
   {
     "text": "{{ $json.refined_script }}",
     "model_id": "eleven_multilingual_v2",
     "voice_settings": {
       "stability": 0.35,
       "similarity_boost": 0.75,
       "style": 0.45,
       "use_speaker_boost": true
     }
   }
   ```
   - Response Format: Binary (audio/mpeg)

2. **Write Binary File Node**: Save Audio
   - File Path: `/opt/white-raven-automation/tmp/audio/{{ $json.story_id }}.mp3`
   - Data: `{{ $binary.data }}`

3. **Code Node**: Calculate Duration
   ```javascript
   // Use ffprobe to get audio duration
   const { execSync } = require('child_process');
   const audioPath = `/opt/white-raven-automation/tmp/audio/${$json.story_id}.mp3`;

   const duration = execSync(`ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${audioPath}"`).toString().trim();

   return {
     audio_url: audioPath,
     duration_seconds: parseFloat(duration)
   };
   ```

**Output**: `{ audio_url, duration_seconds }`

**Test**: Input refined script, verify MP3 file created and duration is ~90 seconds

---

#### 2.5 Sub-Workflow 4: Pexels B-Roll Download

**Name**: `SW - WhiteRaven - Asset Download - Pexels - v1.0`

**Nodes**:

1. **Code Node**: Extract Visual Keywords
   ```javascript
   const script = $json.refined_script;
   const mood = $json.story_mood;

   // Gothic keyword mappings
   const moodKeywords = {
     'psychological': ['dark mirror', 'shadows moving', 'unsettling silence'],
     'gothic_decay': ['abandoned mansion', 'crumbling building', 'fog cemetery'],
     'isolation': ['dark forest alone', 'empty corridor', 'single candle'],
     'ancient_dread': ['old book pages', 'ancient symbols', 'mysterious artifact'],
     'madness': ['distorted reflection', 'spinning room', 'fractured reality']
   };

   // Get keywords for story mood
   let keywords = moodKeywords[mood] || ['dark atmospheric', 'gothic horror', 'mysterious shadow'];

   // Add generic gothic terms
   keywords.push('gothic candles', 'moonlight window', 'dark silhouette');

   return {
     search_keywords: keywords.slice(0, 5) // Max 5 keywords
   };
   ```

2. **Loop Node**: For Each Keyword
   - Items: `{{ $json.search_keywords }}`

3. **HTTP Request Node**: Pexels Video Search (inside loop)
   - Method: GET
   - URL: `https://api.pexels.com/videos/search?query={{ $json.keyword }}&orientation=portrait&per_page=2`
   - Authentication: Use credential "Pexels API"

4. **Code Node**: Download Top Video (inside loop)
   ```javascript
   const videos = $input.item.json.videos;

   if (videos && videos.length > 0) {
     const video = videos[0];
     const videoUrl = video.video_files.find(f => f.quality === 'hd').link;

     // Download video
     const { execSync } = require('child_process');
     const filename = `${$json.story_id}_${$json.keyword.replace(/\s+/g, '_')}.mp4`;
     const outputPath = `/opt/white-raven-automation/tmp/videos/${filename}`;

     execSync(`wget -q -O "${outputPath}" "${videoUrl}"`);

     return {
       video_path: outputPath,
       keyword: $json.keyword
     };
   }

   return { error: 'No video found' };
   ```

5. **Aggregate Node**: Collect All Downloaded Videos
   ```javascript
   const videos = $input.all().map(item => item.json.video_path).filter(Boolean);

   return {
     video_paths: videos,
     video_count: videos.length
   };
   ```

**Output**: `{ video_paths[], video_count }`

**Test**: Input story mood, verify 4-5 videos downloaded to /tmp/videos/

---

#### 2.6 Sub-Workflow 5: FFmpeg Video Assembly

**Name**: `SW - WhiteRaven - Video Assembly - FFmpeg - v1.0`

**Nodes**:

1. **Code Node**: Generate FFmpeg Command
   ```javascript
   const storyId = $json.story_id;
   const audioPa th = $json.audio_url;
   const videoPaths = $json.video_paths;
   const duration = $json.duration_seconds;

   // Create concat file for FFmpeg
   const concatContent = videoPaths.map(path => `file '${path}'`).join('\n');
   const concatFile = `/opt/white-raven-automation/tmp/concat_${storyId}.txt`;

   require('fs').writeFileSync(concatFile, concatContent);

   // Build FFmpeg command
   const outputPath = `/opt/white-raven-automation/output/final/${storyId}_final.mp4`;

   const command = `ffmpeg -f concat -safe 0 -i "${concatFile}" \
     -i "${audioPath}" \
     -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30[v]" \
     -map "[v]" -map 1:a \
     -c:v libx264 -preset fast -crf 22 \
     -c:a aac -b:a 192k \
     -t ${duration} \
     -y "${outputPath}"`;

   return {
     ffmpeg_command: command,
     output_path: outputPath
   };
   ```

2. **Execute Command Node**: Run FFmpeg
   - Command: `{{ $json.ffmpeg_command }}`
   - Timeout: 300000 (5 minutes)

3. **Code Node**: Verify Output
   ```javascript
   const fs = require('fs');
   const outputPath = $json.output_path;

   if (fs.existsSync(outputPath)) {
     const stats = fs.statSync(outputPath);
     return {
       video_url: outputPath,
       file_size_mb: (stats.size / 1024 / 1024).toFixed(2),
       success: true
     };
   }

   return { success: false, error: 'Video file not created' };
   ```

**Output**: `{ video_url, file_size_mb, success }`

**Test**: Input audio + videos, verify final MP4 created at 1080x1920 resolution

---

#### 2.7 Sub-Workflow 6: fal.ai Thumbnail Generation

**Name**: `SW - WhiteRaven - Thumbnail - fal.ai - v1.0`

**Nodes**:

1. **Code Node**: Build Thumbnail Prompt
   ```javascript
   const title = $json.story_title;
   const mood = $json.story_mood;

   const prompt = `Gothic horror YouTube thumbnail.

   Title: "${title}"

   Style: Dark purple and midnight blue gradient background, mysterious fog, silhouette of a raven, antique gold accents, cinematic dramatic lighting.

   Text overlay: Large gothic serif font with "${title}" in center, glowing antique gold color with dark shadow for contrast.

   Composition: Centered text, atmospheric fog at edges, raven silhouette in corner, high contrast for YouTube visibility.

   Mood: ${mood}, mysterious, haunting, professional.

   Aspect ratio: 16:9 (1280x720)
   Quality: High detail, sharp text, YouTube thumbnail optimized.`;

   return {
     thumbnail_prompt: prompt
   };
   ```

2. **HTTP Request Node**: fal.ai API
   - Method: POST
   - URL: `https://fal.run/fal-ai/flux/schnell`
   - Authentication: Use credential "fal.ai API"
   - Body (JSON):
   ```json
   {
     "prompt": "{{ $json.thumbnail_prompt }}",
     "image_size": "landscape_16_9",
     "num_inference_steps": 4,
     "num_images": 1
   }
   ```

3. **HTTP Request Node**: Download Thumbnail Image
   - Method: GET
   - URL: `{{ $json.images[0].url }}`
   - Response Format: Binary

4. **Write Binary File Node**: Save Thumbnail
   - File Path: `/opt/white-raven-automation/tmp/thumbnails/{{ $json.story_id }}.png`
   - Data: `{{ $binary.data }}`

**Output**: `{ thumbnail_url }`

**Test**: Input story title, verify PNG thumbnail created with text overlay

---

#### 2.8 Sub-Workflow 7: YouTube Upload

**Name**: `SW - WhiteRaven - YouTube Upload - v1.0`

**Nodes**:

1. **Code Node**: Generate YouTube Metadata
   ```javascript
   const title = $json.story_title;
   const mood = $json.story_mood;
   const content = $json.story_content;

   // Title (max 100 chars)
   const youtubeTitle = `${title} | Gothic Horror Short`;

   // Description
   const description = `${content.substring(0, 200)}...

   🐦‍⬛ White Raven Tales - Where stories breathe in shadows

   🔔 Subscribe for more gothic horror tales
   📱 Follow us: @TheQuietFoundry

   #GothicHorror #DarkStories #HorrorShorts #WhiteRavenTales`;

   // Tags
   const tags = [
     'gothic horror',
     'dark stories',
     'horror shorts',
     'creepy tales',
     mood.replace('_', ' '),
     'white raven tales'
   ];

   return {
     youtube_title: youtubeTitle,
     youtube_description: description,
     youtube_tags: tags
   };
   ```

2. **HTTP Request Node**: YouTube Video Upload
   - Method: POST
   - URL: `https://www.googleapis.com/upload/youtube/v3/videos?uploadType=multipart&part=snippet,status`
   - Authentication: Use credential "YouTube OAuth2"
   - Body (Multipart):
     - Part 1 (JSON):
     ```json
     {
       "snippet": {
         "title": "{{ $json.youtube_title }}",
         "description": "{{ $json.youtube_description }}",
         "tags": {{ $json.youtube_tags }},
         "categoryId": "24"
       },
       "status": {
         "privacyStatus": "public",
         "madeForKids": false,
         "selfDeclaredMadeForKids": false
       }
     }
     ```
     - Part 2 (Binary): Video file from `{{ $json.video_url }}`

3. **HTTP Request Node**: Set Thumbnail
   - Method: POST
   - URL: `https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={{ $json.video_id }}`
   - Authentication: Use credential "YouTube OAuth2"
   - Body (Binary): Thumbnail file from `{{ $json.thumbnail_url }}`

**Output**: `{ video_id, video_url }`

**Test**: Upload to YouTube as "unlisted" first, verify video appears correctly

---

### Phase 3: Master Workflow Orchestration (2-3 hours)

#### 3.1 Create Master Workflow

**Name**: `SW - WhiteRaven - Full Factory - Master - v1.0`

**Nodes**:

1. **Schedule Trigger**
   - Cron: `0 9 * * 1` (Monday 9am)
   - Cron: `0 14 * * 3` (Wednesday 2pm)
   - Cron: `0 11 * * 5` (Friday 11am)

2. **Execute Workflow**: Story Selection
   - Workflow: `SW - WhiteRaven - Story Selection - Qdrant - v1.0`
   - Wait for completion: Yes

3. **Execute Workflow**: Claude Script Refinement
   - Workflow: `SW - WhiteRaven - Script Refinement - Claude - v1.0`
   - Input: `{{ $json }}`
   - Wait for completion: Yes

4. **Execute Workflow**: ElevenLabs Narration
   - Workflow: `SW - WhiteRaven - Narration - ElevenLabs - v1.0`
   - Input: `{{ $json }}`
   - Wait for completion: Yes

5. **Execute Workflow**: Pexels Asset Download
   - Workflow: `SW - WhiteRaven - Asset Download - Pexels - v1.0`
   - Input: `{{ $json }}`
   - Wait for completion: Yes

6. **Merge Node**: Combine Audio + Video Data
   - Mode: Merge By Position

7. **Execute Workflow**: FFmpeg Video Assembly
   - Workflow: `SW - WhiteRaven - Video Assembly - FFmpeg - v1.0`
   - Input: `{{ $json }}`
   - Wait for completion: Yes

8. **Execute Workflow**: fal.ai Thumbnail
   - Workflow: `SW - WhiteRaven - Thumbnail - fal.ai - v1.0`
   - Input: `{{ $json }}`
   - Wait for completion: Yes (can run in parallel with video assembly)

9. **Merge Node**: Combine Video + Thumbnail

10. **Human Approval Gate** (Optional - Telegram)
    - Send message with preview to Telegram
    - Buttons: Approve / Reject
    - If rejected → stop workflow

11. **Execute Workflow**: YouTube Upload
    - Workflow: `SW - WhiteRaven - YouTube Upload - v1.0`
    - Input: `{{ $json }}`
    - Wait for completion: Yes

12. **HTTP Request**: X/Twitter Post
    - Use existing @TheQuietFoundry automation
    - Post: "New tale: {{ $json.story_title }} 🐦‍⬛\n{{ $json.video_url }}"

13. **Code Node**: Save Project Manifest
    ```javascript
    const manifest = {
      project_id: $json.story_id,
      story_title: $json.story_title,
      status: 'published',
      youtube_video_id: $json.video_id,
      published_date: new Date().toISOString(),
      assets: {
        audio_url: $json.audio_url,
        video_url: $json.video_url,
        thumbnail_url: $json.thumbnail_url
      }
    };

    const fs = require('fs');
    const manifestPath = `/opt/white-raven-automation/projects/${$json.story_id}_manifest.json`;
    fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));

    return manifest;
    ```

14. **Telegram Notification**: Success
    - Message: `✅ Video published!\nTitle: {{ $json.story_title }}\nURL: {{ $json.video_url }}`

15. **Error Handler** (Try/Catch around entire workflow)
    - On error → Telegram notification with error details
    - Save failed manifest for debugging

---

### Phase 4: Testing & Validation (2-3 hours)

#### 4.1 Component Testing

Test each sub-workflow independently:

```bash
# 1. Test story selection
curl http://localhost:5001/api/stories/random | jq .

# 2. Test Claude API (from n8n or curl)
# 3. Test ElevenLabs API
# 4. Test Pexels download
# 5. Test FFmpeg video assembly
# 6. Test fal.ai thumbnail
# 7. Test YouTube upload (unlisted video first)
```

#### 4.2 End-to-End Test

1. **Disable Schedule Trigger** in master workflow
2. **Add Manual Trigger** for testing
3. **Click "Execute Workflow"**
4. **Monitor execution** (15-20 minutes expected)
5. **Check outputs**:
   - Audio file in /tmp/audio/
   - Videos in /tmp/videos/
   - Final video in /output/final/
   - Thumbnail in /tmp/thumbnails/
   - YouTube video uploaded
   - Manifest saved in /projects/

#### 4.3 Validation Checklist

- [ ] Story fetched from Qdrant (quality 7+)
- [ ] Claude refined script (220-250 words, hook, CTA)
- [ ] ElevenLabs audio generated (~90 seconds)
- [ ] Pexels videos downloaded (5 clips)
- [ ] FFmpeg assembled video (1080x1920, audio synced)
- [ ] fal.ai thumbnail created (1280x720, text readable)
- [ ] YouTube video uploaded (public, metadata correct)
- [ ] X post published
- [ ] Manifest saved
- [ ] No errors in n8n execution log

---

## Production Deployment

### Enable Scheduled Automation

1. **Activate master workflow** with schedule triggers
2. **Set to 3 videos/week**: Mon 9am, Wed 2pm, Fri 11am
3. **Monitor first week**: Check Telegram notifications
4. **Adjust schedule** if needed (can increase to 7/week later)

### Monitoring & Maintenance

**Daily**:
- Check Telegram for success/error notifications
- Verify YouTube channel has new videos

**Weekly**:
- Review video performance (views, engagement)
- Check disk usage: `du -sh /opt/white-raven-automation/`
- Clean up old temp files (>7 days old)

**Monthly**:
- Review API usage/costs
- Update Claude prompts if needed
- Add new Pexels keywords for variety

### Cleanup Script

Create `/opt/white-raven-automation/cleanup.sh`:

```bash
#!/bin/bash
# Clean up old temporary files

# Remove temp files older than 7 days
find /opt/white-raven-automation/tmp/ -type f -mtime +7 -delete

# Archive old projects
find /opt/white-raven-automation/output/final/ -type f -mtime +30 -exec mv {} /opt/white-raven-automation/output/archive/ \;

echo "Cleanup complete: $(date)" >> /opt/white-raven-automation/logs/cleanup.log
```

Add to crontab:
```bash
crontab -e
# Add line:
0 2 * * 0 /opt/white-raven-automation/cleanup.sh
```

---

## Troubleshooting

### Common Issues

**1. FFmpeg fails with "No space left on device"**
```bash
# Check disk usage
df -h
# Clean up /tmp/ if needed
sudo rm -rf /opt/white-raven-automation/tmp/*
```

**2. ElevenLabs API rate limit**
```bash
# Error: 429 Too Many Requests
# Solution: Add delay between requests (5 seconds)
# Or: Upgrade ElevenLabs plan
```

**3. Pexels returns no videos**
```bash
# Issue: Query too specific
# Solution: Use broader keywords
# Fallback: Use local stock footage
```

**4. YouTube upload fails**
```bash
# Check quota: https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas
# Daily limit: 10,000 units (1 video upload = ~1600 units)
# Max: 6 videos/day
```

**5. Claude API errors**
```bash
# Error: "rate_limit_error"
# Solution: Add retry logic with exponential backoff
# Or: Upgrade to higher tier
```

---

## Success Criteria

**MVP Complete When**:
1. ✅ Master workflow runs end-to-end without errors
2. ✅ Videos upload to YouTube automatically (3/week)
3. ✅ Quality is consistent (audio synced, no black frames)
4. ✅ Thumbnails look professional (text readable)
5. ✅ X posts publish correctly
6. ✅ No manual intervention needed

**Production-Ready When**:
- Running for 2+ weeks without failures
- 6-9 videos published successfully
- Disk usage stable (<50GB)
- API costs predictable (~$5/week)
- Error recovery works (automatic retries)

---

## Cost Estimates

| Service | Cost/Video | Cost/Week (30 videos) | Notes |
|---------|------------|----------------------|-------|
| Claude API | $0.05 | $1.50 | Script refinement |
| ElevenLabs | $0.10 | $3.00 | Voice narration |
| Pexels | Free | Free | 200 requests/hour |
| fal.ai | $0.05 | $1.50 | Thumbnails |
| YouTube API | Free | Free | 10k units/day |
| FFmpeg | Free | Free | VPS CPU usage |
| **Total** | **$0.20** | **$6.00** | Very affordable! |

---

## Next Steps

1. **Install FFmpeg** (if not already): `sudo apt install ffmpeg`
2. **Create directory structure**: `/opt/white-raven-automation/`
3. **Get API keys**: Claude, ElevenLabs, Pexels, fal.ai, YouTube
4. **Store credentials in n8n**: Use n8n Credentials UI
5. **Build sub-workflows**: One at a time, test each
6. **Build master workflow**: Connect all sub-workflows
7. **End-to-end test**: Run manually first
8. **Enable schedule**: Mon/Wed/Fri automation
9. **Monitor & optimize**: Adjust based on performance

---

## Resources

- **n8n Docs**: https://docs.n8n.io/
- **FFmpeg Docs**: https://ffmpeg.org/documentation.html
- **Claude API**: https://docs.anthropic.com/
- **ElevenLabs API**: https://elevenlabs.io/docs/
- **YouTube API**: https://developers.google.com/youtube/v3

---

🐦‍⬛ **Ready to automate gothic horror video production!** 🐦‍⬛

*This plan is VPS-native - no Windows PC needed, all work happens on server*
