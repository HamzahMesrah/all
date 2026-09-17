import os

def create_files():
    # Define the files and their content
    files = {
        'index.html': '''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title> Reader</title>
    <link rel="icon" type="image/svg+xml" href="Icon.svg">
    <!-- استدعاء خط Cairo -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="style.css">
</head>
<body>

    <div id="sidebar">
        <div class="sidebar-content">
            <h2>الملفات</h2>
            <ul id="file-list"></ul>
        </div>
    </div>

    <div id="main-content">
        <div id="toolbar">
            <div class="toolbar-right">
                <button id="toggle-btn">☰ القائمة الجانبية</button>
            </div>
            <div class="toolbar-center">
                <span id="current-filename">الرجاء اختيار ملف</span>
            </div>
            <div class="toolbar-left">
                <button id="theme-btn">🌙 الوضع الداكن</button>
            </div>
        </div>
        <div id="viewer">
            <div class="placeholder">الرجاء اختيار ملف نصي من القائمة الجانبية لعرض محتواه.<br>(استخدم الأسهم ← → للتنقل بين الملفات)</div>
        </div>
    </div>

    <div id="bottom-bar">
        <button id="prev-btn"> → السابق</button>
        <button id="font-down-btn">-</button>
        <span id="font-size-display">1.3</span>
        <button id="font-up-btn">+</button>
        <button id="next-btn">التالي ←</button>
    </div>

    <script src="script.js" defer></script>
</body>
</html>''',

        'script.js': '''const sidebar = document.getElementById('sidebar');
const toggleBtn = document.getElementById('toggle-btn');
const themeBtn = document.getElementById('theme-btn');
const fontUpBtn = document.getElementById('font-up-btn');
const fontDownBtn = document.getElementById('font-down-btn');
const fontSizeDisplay = document.getElementById('font-size-display');
const fileList = document.getElementById('file-list');
const viewer = document.getElementById('viewer');
const currentFilename = document.getElementById('current-filename');

// Array to keep track of all discovered files for navigation
let availableFiles = [];

// Cache settings
const CACHE_PREFIX = 'file_cache_';

function getCache(filename) {
    return localStorage.getItem(CACHE_PREFIX + filename);
}

function setCache(filename, content) {
    try {
        localStorage.setItem(CACHE_PREFIX + filename, content);
    } catch (e) {
        if (e.name === 'QuotaExceededError') {
            console.warn('Cache quota exceeded, some files may not be cached.');
        }
    }
}

function removeCache(filename) {
    localStorage.removeItem(CACHE_PREFIX + filename);
}

function clearInvalidCache(availableFiles) {
    const keys = Object.keys(localStorage);
    keys.forEach(key => {
        if (key.startsWith(CACHE_PREFIX)) {
            const filename = key.substring(CACHE_PREFIX.length);
            if (!availableFiles.includes(filename)) {
                localStorage.removeItem(key);
            }
        }
    });
}

async function preFetchFiles(files) {
    for (const filename of files) {
        if (!getCache(filename)) {
            try {
                const response = await fetch(filename);
                if (response.ok) {
                    const text = await response.text();
                    setCache(filename, text);
                }
            } catch (e) {
                // Ignore pre-fetch errors
            }
        }
    }
}

// إدارة الثيم
const currentTheme = localStorage.getItem('theme') || 'light';
document.documentElement.setAttribute('data-theme', currentTheme);
updateThemeButtonText(currentTheme);

// إدارة حجم الخط
let currentFontSize = parseFloat(localStorage.getItem('fontSize')) || 1.3;
function updateFontSize() {
    viewer.style.fontSize = `${currentFontSize}rem`;
    localStorage.setItem('fontSize', currentFontSize);
    fontSizeDisplay.textContent = currentFontSize.toFixed(1);
}
updateFontSize();

fontUpBtn.addEventListener('click', () => {
    currentFontSize += 0.1;
    updateFontSize();
});

fontDownBtn.addEventListener('click', () => {
    if (currentFontSize > 0.5) {
        currentFontSize -= 0.1;
        updateFontSize();
    }
});

themeBtn.addEventListener('click', () => {
    let theme = document.documentElement.getAttribute('data-theme');
    let newTheme = theme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeButtonText(newTheme);
});

function updateThemeButtonText(theme) {
    themeBtn.textContent = theme === 'dark' ? '☀️ الوضع الفاتح' : '🌙 الوضع الداكن';
}

toggleBtn.addEventListener('click', () => {
    toggleSidebar();
});

function toggleSidebar() {
    sidebar.classList.toggle('hidden');
    localStorage.setItem('sidebarHidden', sidebar.classList.contains('hidden'));
}

// Initialize sidebar state
if (localStorage.getItem('sidebarHidden') === 'true') {
    sidebar.classList.add('hidden');
}

const prevBtn = document.getElementById('next-btn');
const nextBtn = document.getElementById('prev-btn');
prevBtn.addEventListener('click', () => navigateFile('prev'));
nextBtn.addEventListener('click', () => navigateFile('next'));

async function loadFileContent(filename) {
    if (!filename) return;
    try {
        let text;
        const cachedContent = getCache(filename);
        if (cachedContent !== null) {
            text = cachedContent;
        } else {
            const response = await fetch(filename);
            if (!response.ok) throw new Error('الملف غير موجود');
            text = await response.text();
            setCache(filename, text);
        }
        viewer.textContent = text + '\\n\\n\\n\\n\\n';
        viewer.scrollTop = 0;
        currentFilename.textContent = filename.replace('.txt', '');

        localStorage.setItem('lastViewedFile', filename);

        document.querySelectorAll('.file-item').forEach(item => {
            item.classList.toggle('active', item.getAttribute('data-filename') === filename);
        });
    } catch (err) {
        viewer.innerHTML = `<span style="color:red">خطأ في تحميل الملف: ${err.message}</span>`;
    }
}

// Navigation Logic
function navigateFile(direction) {
    const currentFile = localStorage.getItem('lastViewedFile');
    const currentIndex = availableFiles.indexOf(currentFile);

    if (currentIndex === -1) return; // No file currently selected

    if (direction === 'prev' && currentIndex < availableFiles.length - 1) {
        loadFileContent(availableFiles[currentIndex + 1]);
    } else if (direction === 'next' && currentIndex > 0) {
        loadFileContent(availableFiles[currentIndex - 1]);
    }
}

// Keyboard Listeners
window.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
        e.preventDefault();
        toggleSidebar();
    } else if (e.key === '=' || e.key === '+') {
        currentFontSize += 0.1;
        updateFontSize();
    } else if (e.key === '-' || e.key === '_') {
        if (currentFontSize > 0.5) {
            currentFontSize -= 0.1;
            updateFontSize();
        }
    } else if (e.key === 'ArrowRight') {
        // Since it's RTL, Right Arrow usually means "Next" or "Forward"
        navigateFile('next');
    } else if (e.key === 'ArrowLeft') {
        navigateFile('prev');
    }
});

async function initFileScanner() {
    let i = 1;
    const maxAttempts = 10000;
    const savedFile = localStorage.getItem('lastViewedFile');

    while (i <= maxAttempts) {
        const filename = `${i}.txt`;
        try {
            const response = await fetch(filename, { method: 'HEAD' });
            if (response.ok) {
                availableFiles.push(filename); // Add to our tracking array

                const li = document.createElement('li');
                li.className = 'file-item';
                li.setAttribute('data-filename', filename);
                li.textContent = `${i}`;
                li.onclick = () => loadFileContent(filename);
                fileList.appendChild(li);
            } else {
                break;
            }
        } catch (e) {
            // console.log(`Error scanning ${filename}`);
        }
        i++;
    }

    clearInvalidCache(availableFiles);
    preFetchFiles(availableFiles);

    if (savedFile && availableFiles.includes(savedFile)) {
        loadFileContent(savedFile);
    }
}

initFileScanner();''',

        'style.css': ''':root {
    --sidebar-width: 280px;
    --primary-color: #00838f;
    --accent-color: #00bcd4;
    --bg-color: #f4f7f6;
    --text-color: #2c3e50;
    --panel-bg: #ffffff;
    --panel-bg-rgba: rgba(255, 255, 255, 0.8);
    --border-color: #006064;
    --shadow-color: rgba(0,0,0,0.1);
    --header-height: 60px;
}

* {
    box-sizing: border-box;
    -webkit-tap-highlight-color: transparent;
}

[data-theme="dark"] {
    --bg-color: #121212;
    --text-color: #e0e0e0;
    --panel-bg: #1e1e1e;
    --panel-bg-rgba: rgba(30, 30, 30, 0.8);
    --primary-color: #006064;
    --accent-color: #00bcd4;
    --border-color: #00838f;
    --shadow-color: rgba(0,0,0,0.5);
}

body {
    font-family: 'Cairo', sans-serif;
    margin: 0;
    display: flex;
    height: 100vh;
    background-color: var(--bg-color);
    color: var(--text-color);
    overflow: hidden;
    transition: background-color 0.3s, color 0.3s;
}

/* SIDEBAR - Desktop optimized */
#sidebar {
    width: var(--sidebar-width);
    background-color: var(--primary-color);
    color: white;
    height: 100%;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    overflow-y: auto;
    overflow-x: hidden;
    flex-shrink: 0;
    z-index: 100;
    box-shadow: 2px 0 10px var(--shadow-color);
}
#sidebar.hidden {
    width: 0 !important;
    opacity: 0;
    pointer-events: none;
    transform: translateX(100%); /* RTL slide out */
}
.sidebar-content {
    width: var(--sidebar-width);
}
#sidebar h2 {
    padding: 20px;
    font-size: 1.2rem;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    margin: 0;
    display: flex;
    align-items: center;
    gap: 10px;
}
#file-list {
    list-style: none;
    padding: 0;
    margin: 0;
}
.file-item {
    padding: 15px 20px;
    cursor: pointer;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    transition: all 0.2s;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.file-item:hover, .file-item.active {
    background-color: var(--accent-color);
    color: white;
    padding-right: 30px;
}

/* MAIN CONTENT */
#main-content {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    position: relative;
}
#toolbar {
    height: var(--header-height);
    padding: 0 20px;
    background: var(--panel-bg-rgba);
    box-shadow: 0 8px 30px var(--shadow-color);
    display: flex;
    align-items: center;
    justify-content: space-between;
    transition: background-color 0.3s;
    z-index: 50;
    padding: 10px;
    border-bottom: 1px solid var(--border-color);
    backdrop-filter: blur(10px);
}
.toolbar-right, .toolbar-left, .toolbar-center {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px;
}
.toolbar-center {
    justify-content: center;
    flex-grow: 1;
    font-size: 1.1rem;
    padding: 10px;
}

button {
    background: var(--primary-color);
    color: white;
    border: none;
    padding: 8px 16px;
    cursor: pointer;
    border-radius: 5px;
    font-weight: 600;
    transition: all 0.2s;
    font-family: 'Cairo', sans-serif;
    display: flex;
    align-items: center;
    gap: 5px;
}
button:active {
    transform: scale(0.95);
}
button:hover {
    background: var(--accent-color);
}

#current-filename {
    font-weight: 700;
    max-width: 40% ;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

#viewer {
    padding: 30px 30px 100px 30px;
    font-size: 1.3rem;
    line-height: 1.8;
    white-space: pre-wrap;
    overflow-y: auto;
    flex-grow: 1;
    width: 100%;
    scroll-behavior: smooth;
}

/* BOTTOM NAVIGATION BAR */
#bottom-bar {
    position: fixed;
    bottom: 25px;
    left: 50%;
    transform: translateX(-50%);
    background: var(--panel-bg-rgba);
    color: var(--text-color);
    padding: 8px 10px;
    border-radius: 5px;
    box-shadow: 0 8px 30px var(--shadow-color);
    display: flex;
    align-items: center;
    gap: 10px;
    z-index: 1000;
    border: 1px solid var(--border-color);
    backdrop-filter: blur(10px);
}
#font-size-display {
    font-weight: 800;
    min-width: 35px;
    text-align: center;
    font-size: 0.9rem;
}
.nav-btn {
    padding: 8px 20px;
    border-radius: 20px;
}
.font-btn {
    width: 35px;
    height: 35px;
    padding: 0;
    justify-content: center;
    border-radius: 50%;
}

.placeholder {
    color: #888;
    text-align: center;
    margin-top: 100px;
    font-size: 1.1rem;
}

/* RESPONSIVE DESIGN */

/* Tablet (up to 1024px) */
@media (max-width: 1024px) {
    :root {
        --sidebar-width: 240px;
    }
    #viewer {
        padding: 20px;
    }
}

/* Phone (up to 768px) */
@media (max-width: 768px) {
    body {
        flex-direction: column;
    }
    #sidebar {
        position: fixed;
        right: 0;
        top: 0;
        width: 100% !important; /* Full screen sidebar */
        max-width: 100%;
        box-shadow: none;
        transform: translateX(100%); /* Start hidden */
        z-index: 200;
    }
    #sidebar.hidden {
        transform: translateX(100%);
        opacity: 0;
        width: 0;
    }
    #sidebar:not(.hidden) {
        transform: translateX(0);
        width: 100% !important;
        opacity: 1;
    }
    .sidebar-content {
        width: 100%;
    }
    #toolbar {
        padding: 10px 10px;
    }
    #current-filename {
        font-size: 0.9rem;
        max-width: 30%;
    }
    #viewer {
        padding: 20px 15px 120px 15px;
        font-size: 1.2rem;
    }
    #bottom-bar {
        bottom: 15px;
        width: 90%;
        justify-content: space-between;
        padding: 5px 10px;
    }
    .nav-btn {
        padding: 8px 12px;
        font-size: 0.85rem;
    }
    #toggle-btn {
        padding: 5px 10px;
        font-size: 0.8rem;
    }
    /* Hide text labels on phones to make buttons smaller/icon-only */
    #toggle-btn {
        font-size: 0;
    }
    #toggle-btn::before {
        content: '☰';
        font-size: 1.2rem;
    }
    #theme-btn {
        font-size: 0;
    }
    #theme-btn::before {
        content: '🌙';
        font-size: 1.2rem;
    }
    /* Special handling for theme button text updates via JS */
    [data-theme="dark"] #theme-btn::before {
        content: '☀️';
    }

    .toolbar-left button {
        padding: 8px;
    }
}

/* Tiny Phone (up to 480px) */
@media (max-width: 480px) {
    #toolbar .toolbar-center {
        display: none;
    }
    #toolbar .toolbar-right {
        flex-grow: 1;
    }
    #toolbar .toolbar-right button {
        width: auto;
        min-width: 40px;
        justify-content: center;
    }
    #bottom-bar {
        gap: 5px;
    }
    .nav-btn {
        flex: 1;
        text-align: center;
        padding: 8px 5px;
        font-size: 0.75rem;
    }
}'''
    }

    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create each file
    for filename, content in files.items():
        filepath = os.path.join(current_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'✅ Created: {filename}')
        except Exception as e:
            print(f'❌ Error creating {filename}: {e}')

    print(f'\n📁 All files created in: {current_dir}')
    print('📄 Files created: index.html, script.js, style.css')
    print('💡 Open index.html in your browser to view the app.')

if __name__ == '__main__':
    create_files()
