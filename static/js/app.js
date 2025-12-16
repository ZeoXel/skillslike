// SkillsLike Frontend Application

const API_BASE = 'http://localhost:8000';
let sessionId = generateSessionId();
let isLoading = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('sessionId').textContent = sessionId;
    checkHealth();
    loadSkills();
    setupEventListeners();
});

function setupEventListeners() {
    const form = document.getElementById('chatForm');
    const input = document.getElementById('messageInput');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = input.value.trim();
        if (message && !isLoading) {
            await sendMessage(message);
            input.value = '';
        }
    });

    // Auto-focus input
    input.focus();
}

function generateSessionId() {
    return 'session-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
}

async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();

        updateStatus(true, `正常 (${data.skills_loaded} 个技能)`);
    } catch (error) {
        updateStatus(false, '连接失败');
        console.error('Health check failed:', error);
    }
}

function updateStatus(isOnline, text) {
    const indicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');

    if (isOnline) {
        indicator.className = 'w-3 h-3 rounded-full bg-green-500 animate-pulse';
        statusText.textContent = text;
        statusText.className = 'text-sm text-green-600';
    } else {
        indicator.className = 'w-3 h-3 rounded-full bg-red-500';
        statusText.textContent = text;
        statusText.className = 'text-sm text-red-600';
    }
}

async function loadSkills() {
    const skillsList = document.getElementById('skillsList');
    skillsList.innerHTML = '<div class="text-center py-4 text-slate-400">加载中...</div>';

    try {
        const response = await fetch(`${API_BASE}/api/skills`);
        const skills = await response.json();

        if (skills.length === 0) {
            skillsList.innerHTML = `
                <div class="text-center py-8 text-slate-400">
                    <svg class="w-12 h-12 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"/>
                    </svg>
                    <p>暂无技能</p>
                </div>
            `;
            return;
        }

        skillsList.innerHTML = skills.map(skill => `
            <div class="skill-badge p-4 border border-slate-200 rounded-lg hover:border-blue-300 cursor-pointer">
                <div class="flex items-start gap-3">
                    <div class="w-10 h-10 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-lg flex items-center justify-center flex-shrink-0">
                        <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                        </svg>
                    </div>
                    <div class="flex-1 min-w-0">
                        <h4 class="font-semibold text-slate-800 text-sm mb-1">${escapeHtml(skill.name)}</h4>
                        <p class="text-xs text-slate-600 line-clamp-2 mb-2">${escapeHtml(skill.description)}</p>
                        <div class="flex items-center gap-2">
                            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700">
                                ${escapeHtml(skill.runtime)}
                            </span>
                            ${skill.tags ? `<span class="text-xs text-slate-400">${escapeHtml(skill.tags)}</span>` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Failed to load skills:', error);
        skillsList.innerHTML = `
            <div class="text-center py-8 text-red-400">
                <svg class="w-12 h-12 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                </svg>
                <p>加载失败</p>
                <button onclick="loadSkills()" class="mt-2 text-sm text-blue-600 hover:text-blue-700">重试</button>
            </div>
        `;
    }
}

async function sendMessage(message) {
    if (isLoading) return;

    isLoading = true;
    const sendButton = document.getElementById('sendButton');
    const originalText = sendButton.textContent;
    sendButton.textContent = '发送中...';
    sendButton.disabled = true;

    // Add user message
    addMessage('user', message);

    // Add typing indicator
    const typingId = addTypingIndicator();

    try {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                thread_id: sessionId
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        // Remove typing indicator
        removeTypingIndicator(typingId);

        // Add assistant message
        addMessage('assistant', data.text, data.files);

    } catch (error) {
        console.error('Chat error:', error);
        removeTypingIndicator(typingId);
        addMessage('error', `发送失败: ${error.message}`);
    } finally {
        isLoading = false;
        sendButton.textContent = originalText;
        sendButton.disabled = false;
        document.getElementById('messageInput').focus();
    }
}

function addMessage(role, content, files = []) {
    const messagesContainer = document.getElementById('chatMessages');

    // Remove welcome message if exists
    const welcome = messagesContainer.querySelector('.text-center');
    if (welcome) welcome.remove();

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message-enter';

    if (role === 'user') {
        messageDiv.innerHTML = `
            <div class="flex justify-end">
                <div class="max-w-2xl">
                    <div class="bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-sm">
                        <p class="text-sm whitespace-pre-wrap">${escapeHtml(content)}</p>
                    </div>
                    <p class="text-xs text-slate-400 mt-1 text-right">${new Date().toLocaleTimeString('zh-CN')}</p>
                </div>
            </div>
        `;
    } else if (role === 'assistant') {
        // Check if this is an image generation result
        const isImageGen = content.includes('file_id:') && (content.includes('图片生成成功') || content.includes('Image generated'));

        const filesHtml = files && files.length > 0 ? `
            <div class="mt-3 pt-3 border-t border-slate-200">
                ${isImageGen ? '<p class="text-xs text-slate-500 mb-2">生成的图片:</p>' : '<p class="text-xs text-slate-500 mb-2">附件:</p>'}
                ${files.map(fileId => {
                    if (isImageGen) {
                        return `
                            <div class="mt-2">
                                <img src="${API_BASE}/api/file/${fileId}"
                                     alt="Generated image"
                                     class="max-w-full rounded-lg shadow-md cursor-pointer hover:shadow-lg transition-shadow"
                                     onclick="window.open('${API_BASE}/api/file/${fileId}', '_blank')"
                                     loading="lazy">
                                <a href="${API_BASE}/api/file/${fileId}"
                                   download
                                   class="inline-flex items-center gap-2 px-3 py-1.5 mt-2 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg text-sm transition-colors">
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                                    </svg>
                                    下载原图
                                </a>
                            </div>
                        `;
                    } else {
                        return `
                            <a href="${API_BASE}/api/file/${fileId}"
                               target="_blank"
                               class="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg text-sm transition-colors mr-2">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                                </svg>
                                下载文件
                            </a>
                        `;
                    }
                }).join('')}
            </div>
        ` : '';

        messageDiv.innerHTML = `
            <div class="flex justify-start">
                <div class="max-w-2xl">
                    <div class="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
                        <p class="text-sm text-slate-800 whitespace-pre-wrap">${escapeHtml(content)}</p>
                        ${filesHtml}
                    </div>
                    <p class="text-xs text-slate-400 mt-1">${new Date().toLocaleTimeString('zh-CN')}</p>
                </div>
            </div>
        `;
    } else if (role === 'error') {
        messageDiv.innerHTML = `
            <div class="flex justify-center">
                <div class="max-w-md bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
                    <div class="flex items-center gap-2">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                        <span>${escapeHtml(content)}</span>
                    </div>
                </div>
            </div>
        `;
    }

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function addTypingIndicator() {
    const messagesContainer = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    const id = 'typing-' + Date.now();
    typingDiv.id = id;
    typingDiv.className = 'message-enter';
    typingDiv.innerHTML = `
        <div class="flex justify-start">
            <div class="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
                <div class="flex items-center gap-1">
                    <span class="typing-indicator"></span>
                    <span class="typing-indicator"></span>
                    <span class="typing-indicator"></span>
                </div>
            </div>
        </div>
    `;
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return id;
}

function removeTypingIndicator(id) {
    const element = document.getElementById(id);
    if (element) element.remove();
}

function clearChat() {
    if (confirm('确定要清空对话历史吗？')) {
        const messagesContainer = document.getElementById('chatMessages');
        messagesContainer.innerHTML = `
            <div class="text-center py-12 text-slate-400">
                <svg class="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                </svg>
                <p class="text-lg">开始对话吧！</p>
                <p class="text-sm mt-1">尝试问我一些问题，我会使用合适的技能来回答</p>
            </div>
        `;

        // Generate new session
        sessionId = generateSessionId();
        document.getElementById('sessionId').textContent = sessionId;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
