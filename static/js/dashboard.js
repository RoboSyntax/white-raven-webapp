// ============================================================================
// WHITE RAVEN TALES - SEMANTIC SEARCH DASHBOARD
// ============================================================================

let currentFilters = {
    mood: [],
    min_quality: 6,
    min_length: 30,
    max_length: 120
};

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    loadRecentStories();
    loadMoods();
    loadStats();
    setupEventListeners();
});

// ============================================================================
// SEMANTIC SEARCH
// ============================================================================

async function searchStories() {
    const query = document.getElementById('search-input').value.trim();

    if (!query) {
        showError('Please enter a search query');
        return;
    }

    showLoading();

    try {
        const response = await fetch('/api/stories/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: query,
                filters: currentFilters,
                limit: 12
            })
        });

        const results = await response.json();

        if (response.ok) {
            displayResults(results);
        } else {
            showError(results.error || 'Search failed');
        }
    } catch (err) {
        showError(`Network error: ${err.message}`);
    } finally {
        hideLoading();
    }
}

// ============================================================================
// FILTERS
// ============================================================================

function setupFilters() {
    // Mood checkboxes
    document.querySelectorAll('.mood-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            chip.classList.toggle('selected');
            updateMoodFilters();
        });
    });

    // Quality slider
    const qualitySlider = document.getElementById('quality-slider');
    if (qualitySlider) {
        qualitySlider.addEventListener('input', (e) => {
            currentFilters.min_quality = parseInt(e.target.value);
            document.getElementById('quality-value').textContent = e.target.value;
        });
    }

    // Length range
    const lengthMin = document.getElementById('length-min');
    const lengthMax = document.getElementById('length-max');

    if (lengthMin) {
        lengthMin.addEventListener('input', (e) => {
            currentFilters.min_length = parseInt(e.target.value) || 30;
        });
    }

    if (lengthMax) {
        lengthMax.addEventListener('input', (e) => {
            currentFilters.max_length = parseInt(e.target.value) || 120;
        });
    }

    // Toggle filters panel
    const toggleBtn = document.getElementById('toggle-filters');
    const filterContent = document.getElementById('filter-content');

    if (toggleBtn && filterContent) {
        toggleBtn.addEventListener('click', () => {
            filterContent.classList.toggle('hidden');
        });
    }
}

function updateMoodFilters() {
    currentFilters.mood = Array.from(
        document.querySelectorAll('.mood-chip.selected')
    ).map(chip => chip.dataset.mood);
}

// ============================================================================
// BROWSE FUNCTIONS
// ============================================================================

async function loadRandomStory() {
    showLoading();
    try {
        const response = await fetch('/api/stories/random');
        const story = await response.json();
        if (response.ok && story) {
            showStoryModal(story);
        } else {
            showError('No stories found');
        }
    } catch (err) {
        showError('Failed to load random story');
    } finally {
        hideLoading();
    }
}

async function loadRecentStories() {
    try {
        const response = await fetch('/api/stories/recent');
        const stories = await response.json();
        displayResults(stories);
    } catch (err) {
        console.error('Failed to load recent stories:', err);
        showError('Failed to load stories');
    }
}

async function loadTopStories() {
    showLoading();
    try {
        const response = await fetch('/api/stories/top');
        const stories = await response.json();
        displayResults(stories);
    } catch (err) {
        showError('Failed to load top stories');
    } finally {
        hideLoading();
    }
}

// ============================================================================
// DISPLAY RESULTS
// ============================================================================

function displayResults(stories) {
    const grid = document.getElementById('story-grid');
    grid.innerHTML = '';

    if (!stories || stories.length === 0) {
        grid.innerHTML = '<p class="no-results" style="text-align:center;color:var(--fog-gray);padding:40px;">No stories found. Try different filters or search terms.</p>';
        document.getElementById('results-count').textContent = 'No stories found';
        return;
    }

    document.getElementById('results-count').textContent = `${stories.length} stories found`;

    stories.forEach(story => {
        const card = createStoryCard(story);
        grid.appendChild(card);
    });
}

function createStoryCard(story) {
    const card = document.createElement('div');
    card.className = 'story-card';
    card.dataset.storyId = story.id;

    const moodEmoji = getMoodEmoji(story.mood);
    const qualityStars = '⭐'.repeat(Math.round(story.quality_score || 5));

    card.innerHTML = `
        <h3 class="story-title">${moodEmoji} ${story.title}</h3>
        <p class="story-preview">${story.preview}</p>
        <div class="story-meta">
            <span class="meta-badge similarity-score">
                Score: ${(story.score || 0).toFixed(2)}
            </span>
            <span class="meta-badge mood-badge">
                ${(story.mood || 'unknown').replace('_', ' ')}
            </span>
            <span class="meta-badge">⏱️ ${story.length_seconds || 60}s</span>
            <span class="meta-badge quality-stars">${qualityStars}</span>
        </div>
        <button class="read-btn">Read Full Story</button>
    `;

    card.querySelector('.read-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        loadFullStory(story.id);
    });

    return card;
}

function getMoodEmoji(mood) {
    const emojiMap = {
        psychological: '🧠',
        gothic_decay: '🏚️',
        isolation: '🌑',
        conspiracy: '👁️',
        madness: '🌀',
        ancient_dread: '🦑',
        urban_legend: '🏙️',
        whispers: '👻'
    };
    return emojiMap[mood] || '📖';
}

// ============================================================================
// STORY MODAL (FULL VIEW)
// ============================================================================

async function loadFullStory(storyId) {
    try {
        const response = await fetch(`/api/stories/${storyId}`);
        const story = await response.json();

        if (response.ok) {
            showStoryModal(story);
        } else {
            showError('Failed to load story');
        }
    } catch (err) {
        showError('Failed to load story');
    }
}

function showStoryModal(story) {
    const modal = document.getElementById('story-modal');
    const moodEmoji = getMoodEmoji(story.mood);

    modal.querySelector('.modal-story-title').textContent = `${moodEmoji} ${story.title}`;

    // Format themes
    const themes = story.themes && story.themes.length > 0
        ? story.themes.join(', ')
        : 'None';

    // Format date
    const createdDate = story.created_at
        ? new Date(story.created_at).toLocaleDateString()
        : 'Unknown';

    modal.querySelector('.modal-story-meta').innerHTML = `
        <div class="meta-row">
            <span>Mood: <strong>${(story.mood || 'unknown').replace('_', ' ')}</strong></span>
            <span>Quality: ${'⭐'.repeat(story.quality_score || 5)}</span>
            <span>Length: ${story.length_seconds || 60}s</span>
        </div>
        <div class="meta-row">
            <span>Themes: ${themes}</span>
        </div>
        <div class="meta-row">
            <span>Source: ${story.source || 'unknown'}</span>
            <span>Created: ${createdDate}</span>
        </div>
    `;

    modal.querySelector('.story-full-text').textContent = story.content || 'No content available';
    modal.style.display = 'block';

    // Copy button
    const copyBtn = modal.querySelector('.copy-btn');
    copyBtn.onclick = () => {
        navigator.clipboard.writeText(story.content || '').then(() => {
            showToast('Story copied to clipboard!');
        }).catch(() => {
            showError('Failed to copy to clipboard');
        });
    };
}

function closeStoryModal() {
    document.getElementById('story-modal').style.display = 'none';
}

// ============================================================================
// STATS & METADATA
// ============================================================================

async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();

        document.getElementById('total-stories').textContent = stats.total_stories || 0;
        document.getElementById('moods-count').textContent = stats.moods_count || 0;
        document.getElementById('avg-quality').textContent = (stats.avg_quality || 0).toFixed(1);
    } catch (err) {
        console.error('Failed to load stats:', err);
    }
}

async function loadMoods() {
    try {
        const response = await fetch('/api/moods');
        const moods = await response.json();

        const container = document.getElementById('mood-chips-container');
        container.innerHTML = '';

        moods.forEach(mood => {
            const chip = document.createElement('div');
            chip.className = 'mood-chip';
            chip.dataset.mood = mood;
            chip.textContent = mood.replace('_', ' ');
            container.appendChild(chip);
        });

        setupFilters();
    } catch (err) {
        console.error('Failed to load moods:', err);
    }
}

// ============================================================================
// UI HELPERS
// ============================================================================

function showLoading() {
    document.getElementById('loading-spinner').style.display = 'block';
}

function hideLoading() {
    document.getElementById('loading-spinner').style.display = 'none';
}

function showError(message) {
    const toast = document.getElementById('error-toast');
    toast.textContent = message;
    toast.style.display = 'block';
    setTimeout(() => toast.style.display = 'none', 3000);
}

function showToast(message) {
    const toast = document.getElementById('success-toast');
    toast.textContent = message;
    toast.style.display = 'block';
    setTimeout(() => toast.style.display = 'none', 2000);
}

// ============================================================================
// EVENT LISTENERS
// ============================================================================

function setupEventListeners() {
    // Search
    const searchBtn = document.getElementById('search-btn');
    const searchInput = document.getElementById('search-input');

    if (searchBtn) {
        searchBtn.addEventListener('click', searchStories);
    }

    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') searchStories();
        });
    }

    // Browse shortcuts
    const randomBtn = document.getElementById('random-btn');
    const recentBtn = document.getElementById('recent-btn');
    const topBtn = document.getElementById('top-btn');

    if (randomBtn) randomBtn.addEventListener('click', loadRandomStory);
    if (recentBtn) recentBtn.addEventListener('click', loadRecentStories);
    if (topBtn) topBtn.addEventListener('click', loadTopStories);

    // Modal
    const closeModal = document.getElementById('close-modal');
    if (closeModal) {
        closeModal.addEventListener('click', closeStoryModal);
    }

    window.addEventListener('click', (e) => {
        const modal = document.getElementById('story-modal');
        if (e.target === modal) closeStoryModal();
    });
}
