
let serverConnected = true;

// API 错误处理
function handleApiError(error, context) {
    console.error(`API Error (${context}):`, error);
    if (serverConnected) {
        serverConnected = false;
        const indicator = document.getElementById('server-status-indicator');
        if (indicator) {
            indicator.style.display = 'flex';
        }
        
        // 停止所有定时器
        if (logRefreshInterval) {
            clearInterval(logRefreshInterval);
            logRefreshInterval = null;
            // 更新旧版日志刷新按钮和旋转动画状态
            const spinner = document.getElementById('log-refresh-spinner');
            const stopBtn = document.getElementById('stop-log-refresh-btn');
            const startBtn = document.getElementById('start-log-refresh-btn');
            if (spinner) spinner.style.display = 'none';
            if (stopBtn) stopBtn.style.display = 'none';
            if (startBtn) startBtn.style.display = 'inline-block';
        }
        
        if (newLogRefreshInterval) {
            clearInterval(newLogRefreshInterval);
            newLogRefreshInterval = null;
            // 更新新版日志刷新按钮和旋转动画状态
            const spinner = document.getElementById('new-log-refresh-spinner');
            const stopBtn = document.getElementById('stop-new-log-refresh-btn');
            const startBtn = document.getElementById('start-new-log-refresh-btn');
            if (spinner) spinner.style.display = 'none';
            if (stopBtn) stopBtn.style.display = 'none';
            if (startBtn) startBtn.style.display = 'inline-block';
        }
        
        if (statusRefreshInterval) {
            clearInterval(statusRefreshInterval);
            statusRefreshInterval = null;
        }
    }
}

// API 成功处理
function handleApiSuccess() {
    if (!serverConnected) {
        serverConnected = true;
        const indicator = document.getElementById('server-status-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
        // 重新启动状态刷新定时器
        statusRefreshInterval = setInterval(refreshTaskStatus, 5000);
    }
}

// 包装 fetch 请求
async function fetchApi(url, options, context) {
    try {
        const response = await fetch(url, options);
        handleApiSuccess();
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        handleApiError(error, context);
        throw error; // 重新抛出错误，以便调用者可以处理
    }
}


// 全局变量
let currentTask = null;
let logRefreshInterval = null;
let statusRefreshInterval = null;

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化标签页
    initTabs();
    
    // 加载老版本任务列表和配置
    loadTasks();
    loadConfig();
    
    // 设置定时刷新任务状态
    statusRefreshInterval = setInterval(refreshTaskStatus, 5000);
    
    // 绑定配置表单提交事件
    const configForm = document.getElementById('configForm');
    if (configForm) {
        configForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveConfig();
        });
    }

    // 绑定刷新日志按钮事件
    // const refreshLogBtn = document.getElementById('refresh-log-btn');
    // if (refreshLogBtn) {
    //     refreshLogBtn.addEventListener('click', refreshLog);
    // }
    
    // 新版功能初始化
    loadNewTasks();

    // 为新任务表单绑定提交事件
    const createNewTaskForm = document.getElementById('createNewTaskForm');
    if (createNewTaskForm) {
        createNewTaskForm.addEventListener('submit', createNewTask);
    }

    // 编辑任务表单的提交事件在后面单独处理，这里不需要重复绑定

    // 点击模态窗口外部关闭
    window.onclick = function(event) {
        const createTaskModal = document.getElementById('createTaskModal');
        const editTaskModal = document.getElementById('editTaskModal');
        const taskDetailsModal = document.getElementById('taskDetailsModal');

        if (event.target == createTaskModal) {
            closeCreateTaskModal();
        }
        if (event.target == editTaskModal) {
            closeEditModal();
        }
        if (event.target == taskDetailsModal) {
            closeTaskDetailsModal();
        }
    }
});

// 初始化标签页
function initTabs() {
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // 清除所有定时器
            if (logRefreshInterval) clearInterval(logRefreshInterval);
            if (newLogRefreshInterval) clearInterval(newLogRefreshInterval);

            // 移除所有标签页的active类
            tabs.forEach(t => t.classList.remove('active'));
            
            // 移除所有内容区域的active类
            tabContents.forEach(content => content.classList.remove('active'));
            
            // 添加当前标签页的active类
            this.classList.add('active');
            
            // 显示对应的内容区域
            const target = this.getAttribute('data-target');
            document.getElementById(target).classList.add('active');

            // 触发自定义事件，通知标签页已切换
            document.dispatchEvent(new CustomEvent('tabChanged', { detail: { target: target } }));
        });
    });
}

// 加载任务列表
function loadTasks() {
    showLoading('taskList');
    fetchApi('/api/tasks', {}, 'loadTasks')
        .then(data => {
            hideLoading('taskList');
            if (data.success) {
                renderTaskList(data.tasks);
            } else {
                showError('taskList', data.message || '加载任务列表失败');
            }
        })
        .catch(error => {
            hideLoading('taskList');
            showError('taskList', '加载任务列表失败');
        });
}

// 渲染任务列表
function renderTaskList(tasks) {
    const taskListElement = document.getElementById('taskList');
    
    if (!tasks || tasks.length === 0) {
        taskListElement.innerHTML = '<div class="alert alert-info">没有可用的任务</div>';
        return;
    }
    
    let html = '<ul class="task-list">';
    
    tasks.forEach(task => {
        // 确保任务ID不为null
        const taskId = task.id || 'auto_login';
        const isEnabled = task.enabled !== false;
        const statusClass = getStatusClass(task.status, isEnabled);
        const statusText = getStatusText(task.status, isEnabled);
        
        html += `
            <li class="task-item ${!isEnabled ? 'task-disabled' : ''}" data-task-id="${taskId}" onclick="viewTaskLogs('${taskId}')">
                <div class="task-header">
                    <div class="task-id">${taskId}</div>
                    <div class="task-name">${task.name}</div>
                </div>
                <div class="task-description">${task.description || '无描述'}</div>
                <div class="task-command">
                    <strong>命令:</strong> <code>${task.command || 'python auto_login.py'}</code>
                </div>
                <div class="task-schedule">
                    <strong>调度:</strong> ${task.schedule || '未知调度'}
                </div>
                <div class="task-actions">
                    <span class="task-status ${statusClass}">${statusText}</span>
                    <div class="action-buttons">
                        ${isEnabled && task.status === 'running' 
                            ? `<button class="btn btn-danger btn-sm stop-task" onclick="event.stopPropagation(); stopTask('${taskId}')">停止</button>`
                            : isEnabled 
                                ? `<button class="btn btn-success btn-sm start-task" onclick="event.stopPropagation(); startTask('${taskId}')">启动</button>`
                                : '<button class="btn btn-secondary btn-sm" disabled>已禁用</button>'
                        }
                    </div>
                </div>
            </li>
        `;
    });
    
    html += '</ul>';
    taskListElement.innerHTML = html;
    
    // 绑定任务操作事件
    bindTaskEvents();
}

// 获取状态类名
function getStatusClass(status, enabled) {
    if (!enabled) {
        return 'status-disabled';
    }
    switch (status) {
        case 'running':
            return 'status-running';
        case 'stopped':
            return 'status-stopped';
        default:
            return 'status-stopped';
    }
}

// 获取状态文本
function getStatusText(status, enabled) {
    if (!enabled) {
        return '禁用';
    }
    switch (status) {
        case 'running':
            return '运行中';
        case 'stopped':
            return '已停止';
        default:
            return '已停止';
    }
}

// 绑定任务操作事件
function bindTaskEvents() {
    // 启动任务按钮
    document.querySelectorAll('.start-task').forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const taskItem = this.closest('.task-item');
            const taskId = taskItem.getAttribute('data-task-id');
            startTask(taskId);
        });
    });
    
    // 停止任务按钮
    document.querySelectorAll('.stop-task').forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const taskItem = this.closest('.task-item');
            const taskId = taskItem.getAttribute('data-task-id');
            stopTask(taskId);
        });
    });
}

// 用于跟踪任务操作状态的变量
let taskOperationInProgress = false;

// 启动任务
function startTask(taskId) {
    // 防止无效的任务ID
    if (!taskId || taskId === 'null') {
        showMessage('无效的任务ID', 'danger');
        return;
    }
    
    // 防止重复操作
    if (taskOperationInProgress) {
        console.log('操作正在进行中，请稍候...');
        return;
    }
    
    taskOperationInProgress = true;
    
    // 禁用所有按钮，防止重复点击
    const taskItem = document.querySelector(`[data-task-id="${taskId}"]`);
    if (!taskItem) {
        taskOperationInProgress = false;
        return;
    }
    
    const buttons = taskItem.querySelectorAll('button');
    buttons.forEach(btn => btn.disabled = true);
    
    fetch(`/api/tasks/${taskId}/start`, {
        method: 'POST'
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message || '任务已启动', 'success');
                // 延迟刷新任务列表，给任务启动一些时间
                setTimeout(() => {
                    loadTasks();
                    // 自动查看该任务的日志
                    viewTaskLogs(taskId);
                    // 重置操作状态
                    taskOperationInProgress = false;
                }, 1000);
            } else {
                showMessage(data.message || '启动任务失败', 'danger');
                // 重新启用按钮
                buttons.forEach(btn => btn.disabled = false);
                // 重置操作状态
                taskOperationInProgress = false;
            }
        })
        .catch(error => {
            showMessage(error.message || '启动任务失败', 'danger');
            // 重新启用按钮
            buttons.forEach(btn => btn.disabled = false);
            // 重置操作状态
            taskOperationInProgress = false;
        });
}

// 停止任务
function stopTask(taskId) {
    // 防止无效的任务ID
    if (!taskId || taskId === 'null') {
        showMessage('无效的任务ID', 'danger');
        return;
    }
    
    // 防止重复操作
    if (taskOperationInProgress) {
        console.log('操作正在进行中，请稍候...');
        return;
    }
    
    taskOperationInProgress = true;
    
    fetch(`/api/tasks/${taskId}/stop`, {
        method: 'POST'
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message || '任务已停止', 'success');
                loadTasks();
            } else {
                showMessage(data.message || '停止任务失败', 'danger');
            }
            // 重置操作状态
            taskOperationInProgress = false;
        })
        .catch(error => {
            showMessage(error.message || '停止任务失败', 'danger');
            // 重置操作状态
            taskOperationInProgress = false;
        });
}

function toggleLogRefresh(isNew, start) {
    const spinner = document.getElementById(isNew ? 'new-log-refresh-spinner' : 'log-refresh-spinner');
    const stopBtn = document.getElementById(isNew ? 'stop-new-log-refresh-btn' : 'stop-log-refresh-btn');
    const startBtn = document.getElementById(isNew ? 'start-new-log-refresh-btn' : 'start-log-refresh-btn');
    const interval = isNew ? newLogRefreshInterval : logRefreshInterval;
    
    if (start) {
        spinner.style.display = 'inline-block';
        stopBtn.style.display = 'inline-block';
        startBtn.style.display = 'none';
    } else {
        if (interval) {
            clearInterval(interval);
            if (isNew) newLogRefreshInterval = null; else logRefreshInterval = null;
        }
        spinner.style.display = 'none';
        stopBtn.style.display = 'none';
        startBtn.style.display = 'inline-block';
    }
}

function stopLogRefresh() {
    toggleLogRefresh(false, false);
}

function startLogRefresh() {
    if (currentTask) {
        viewTaskLogs(currentTask);
    }
}

function stopNewLogRefresh() {
    toggleLogRefresh(true, false);
}

function startNewLogRefresh() {
    if (currentNewTaskId) {
        viewNewLogs(currentNewTaskId, document.getElementById('newLogTitle').textContent.replace('任务日志: ', ''));
    }
}

function viewTaskLogs(taskId) {
    if (!taskId || taskId === 'null') {
        console.warn('无效的任务ID:', taskId);
        return;
    }
    
    // 如果是同一个任务且定时器已在运行，则不操作
    if (currentTask === taskId && logRefreshInterval) {
        return;
    }

    currentTask = taskId;
    document.getElementById('logTitle').textContent = `任务日志 - ${taskId}`;
    
    // 停止旧的定时器
    if (logRefreshInterval) {
        clearInterval(logRefreshInterval);
        logRefreshInterval = null;
    }

    // 立即加载一次日志
    loadTaskLogs(taskId, true);
    
    // 只有在服务器连接正常时才启动定时器
    if (serverConnected) {
        // 启动新的定时器
        logRefreshInterval = setInterval(() => {
            if (currentTask === taskId) {
                loadTaskLogs(taskId, false);
            }
        }, 2000);
        toggleLogRefresh(false, true);
    } else {
        // 服务器已断开连接，不启动定时器，确保旋转动画不显示
        toggleLogRefresh(false, false);
    }
}

// 加载任务日志
async function loadTaskLogs(taskId, showLoadingIndicator = true) {
    if (!taskId || taskId === 'null') {
        console.warn('无效的任务ID:', taskId);
        return;
    }
    
    const logViewerElement = document.getElementById('logViewer');
    if (showLoadingIndicator) {
        logViewerElement.innerHTML = '<div class="text-center"><div class="spinner"></div><p>加载中...</p></div>';
    }
    
    try {
        const data = await fetchApi(`/api/tasks/${taskId}/logs?limit=100`, {}, `loadTaskLogs for ${taskId}`);
        if (showLoadingIndicator) {
            hideLoading('logViewer');
        }
        renderLogs(data.logs);
    } catch (error) {
        if (showLoadingIndicator) {
            hideLoading('logViewer');
        }
        logViewerElement.innerHTML = '<div class="log-placeholder"><p>加载日志失败</p></div>';
        toggleLogRefresh(false, false); // 停止刷新动画和按钮
    }
}

// 渲染日志
function renderLogs(logs) {
    const logViewerElement = document.getElementById('logViewer');
    
    if (!logs || logs.length === 0) {
        logViewerElement.innerHTML = '<div class="log-placeholder"><p>没有可用的日志</p></div>';
        return;
    }
    
    let html = '<pre>';
    
    logs.forEach(log => {
        if (log.raw) {
            html += `${escapeHtml(log.raw)}
`;
        } else {
            // 格式化时间戳
            const timestamp = formatTimestamp(log.timestamp);
            html += `${timestamp} ${log.level} ${escapeHtml(log.message)}
`;
        }
    });
    
    html += '</pre>';
    logViewerElement.innerHTML = html;
    
    // 滚动到底部
    logViewerElement.scrollTop = logViewerElement.scrollHeight;
}

// 格式化时间戳
function formatTimestamp(timestamp) {
    // 如果时间戳为空或无效，返回空字符串
    if (!timestamp || timestamp.trim() === '') {
        return '';
    }
    
    try {
        // 处理带毫秒的时间戳格式 (2023-10-27 10:30:00,123)
        let dateStr = timestamp;
        if (timestamp.includes(',')) {
            // 将逗号替换为点，使其符合 JavaScript Date 构造函数的格式
            dateStr = timestamp.replace(',', '.');
        }
        
        const date = new Date(dateStr);
        
        // 检查日期是否有效
        if (isNaN(date.getTime())) {
            // 如果无法解析，尝试手动解析格式 YYYY-MM-DD HH:mm:ss
            const match = timestamp.match(/^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2})/);
            if (match) {
                const [, datePart, timePart] = match;
                const parsedDate = new Date(`${datePart}T${timePart}`);
                if (!isNaN(parsedDate.getTime())) {
                    return parsedDate.toLocaleString('zh-CN', {
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit'
                    });
                }
            }
            // 如果仍然无法解析，返回原始时间戳
            return timestamp;
        }
        
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    } catch (e) {
        // 出错时返回原始时间戳
        return timestamp;
    }
}

// HTML转义函数
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 刷新任务状态
function refreshTaskStatus() {
    if (!serverConnected) return;
    const taskItems = document.querySelectorAll('.task-item');
    
    // 如果正在进行任务操作，暂时不刷新状态
    if (taskOperationInProgress) {
        return;
    }
    
    taskItems.forEach(taskItem => {
        const taskId = taskItem.getAttribute('data-task-id');
        
        // 防止 null 或 undefined 的任务ID
        if (!taskId || taskId === 'null') {
            return;
        }
        
        fetchApi(`/api/tasks/${taskId}/status`, {}, `refreshTaskStatus for ${taskId}`)
            .then(data => {
                if (data.success) {
                    updateTaskStatus(taskItem, data.status, data.enabled);
                }
            })
            .catch(error => {
                // 错误已由 fetchApi 处理
            });
    });
}

// 更新任务状态
function updateTaskStatus(taskItem, status, enabled) {
    const statusElement = taskItem.querySelector('.task-status');
    const startStopButton = taskItem.querySelector('.start-task, .stop-task');
    const toggleButton = taskItem.querySelector('.toggle-task');
    
    const currentStatus = statusElement.textContent.trim();
    const newStatusText = getStatusText(status, enabled);
    const newStatusClass = getStatusClass(status, enabled);
    
    // 更新状态显示
    statusElement.textContent = newStatusText;
    statusElement.className = `task-status ${newStatusClass}`;
    
    // 更新启动/停止按钮
    if (startStopButton) {
        if (enabled) {
            if (status === 'running') {
                startStopButton.textContent = '停止';
                startStopButton.className = 'btn btn-danger btn-sm stop-task';
                startStopButton.disabled = false;
            } else {
                startStopButton.textContent = '启动';
                startStopButton.className = 'btn btn-success btn-sm start-task';
                startStopButton.disabled = false;
            }
        } else {
            startStopButton.textContent = '已禁用';
            startStopButton.className = 'btn btn-secondary btn-sm';
            startStopButton.disabled = true;
        }
    }
    
    // 更新启用/禁用按钮
    if (toggleButton) {
        toggleButton.textContent = enabled ? '禁用' : '启用';
        toggleButton.className = `btn ${enabled ? 'btn-warning' : 'btn-success'} btn-sm toggle-task`;
    }
    
    // 更新任务项样式
    if (enabled) {
        taskItem.classList.remove('task-disabled');
    } else {
        taskItem.classList.add('task-disabled');
    }
    
    // 重新绑定事件
    bindTaskEvents();
    
    // 如果状态从运行中变为已停止，可能是任务自动结束，显示提示
    if (currentStatus === '运行中' && status === 'stopped' && enabled) {
        showMessage('任务已自动结束', 'info');
    }
}

// 加载配置
function loadConfig() {
    showLoading('configForm');
    fetchApi('/api/config', {}, 'loadConfig')
        .then(data => {
            hideLoading('configForm');
            if (data.success) {
                renderConfig(data.config);
            } else {
                showError('configForm', data.message || '加载配置失败');
            }
        })
        .catch(error => {
            hideLoading('configForm');
            showError('configForm', '加载配置失败');
        });
}

// 渲染配置
function renderConfig(config) {
    for (const key in config) {
        const input = document.getElementById(key);
        if (input) {
            input.value = config[key];
        }
    }
}

// 保存配置
function saveConfig() {
    showLoading('configForm');
    
    const formData = new FormData(document.getElementById('configForm'));
    const config = {};
    
    for (const [key, value] of formData.entries()) {
        config[key] = value;
    }
    
    fetchApi('/api/config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    }, 'saveConfig')
        .then(data => {
            hideLoading('configForm');
            
            if (data.success) {
                showSuccess('configForm', data.message || '配置已保存');
            }
            else {
                showError('configForm', data.message || '保存配置失败');
            }
        })
        .catch(error => {
            hideLoading('configForm');
            showError('configForm', '保存配置失败');
        });
}

// 显示加载中
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    
    if (element) {
        element.innerHTML = '<div class="text-center"><div class="spinner"></div><p>加载中...</p></div>';
    }
}

// 隐藏加载中
function hideLoading(elementId) {
    // 不做任何操作，内容将被新内容替换
}

// 显示消息
function showMessage(message, type = 'info') {
    const messageContainer = document.getElementById('message-container');
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${type}`;
    alertElement.textContent = message;
    
    messageContainer.innerHTML = ''; // 清空旧消息
    messageContainer.appendChild(alertElement);
    
    // 5秒后自动移除
    setTimeout(() => {
        alertElement.remove();
    }, 5000);
}

// 显示错误消息
function showError(elementId, message) {
    const alertElement = document.createElement('div');
    alertElement.className = 'alert alert-danger';
    alertElement.textContent = message;
    
    const element = document.getElementById(elementId);
    
    if (element) {
        element.prepend(alertElement);
        
        // 5秒后自动移除
        setTimeout(() => {
            alertElement.remove();
        }, 5000);
    }
}

// 清空日志
function clearLogs() {
    if (!currentTask) return;
    
    // 显示加载中
    const logViewerElement = document.getElementById('logViewer');
    logViewerElement.innerHTML = '<div class="text-center"><div class="spinner"></div><p>正在清空日志...</p></div>';
    
    // 调用API清空日志文件
    fetchApi(`/api/tasks/${currentTask}/logs/clear`, {
        method: 'POST'
    }, `clearLogs for ${currentTask}`)
        .then(data => {
            if (data.success) {
                showMessage('日志已清空', 'success');
                logViewerElement.innerHTML = '<div class="log-placeholder"><p>日志已清空，等待新日志...</p></div>';
                
                // 重新启动日志刷新
                if (logRefreshInterval) {
                    clearInterval(logRefreshInterval);
                }
                
                logRefreshInterval = setInterval(() => {
                    if (currentTask) {
                        loadTaskLogs(currentTask, false);
                    }
                }, 2000);
            } else {
                showMessage(data.message || '清空日志失败', 'danger');
                loadTaskLogs(currentTask); // 重新加载日志
            }
        })
        .catch(error => {
            showMessage('清空日志失败', 'danger');
            loadTaskLogs(currentTask); // 重新加载日志
        });
}

// 启用/禁用任务
function toggleTask(taskId, enabled) {
    // 防止无效的任务ID
    if (!taskId || taskId === 'null') {
        showMessage('无效的任务ID', 'danger');
        return;
    }
    
    // 防止重复操作
    if (taskOperationInProgress) {
        console.log('操作正在进行中，请稍候...');
        return;
    }
    
    taskOperationInProgress = true;
    
    const actionText = enabled ? '启用' : '禁用';
    
    fetchApi(`/api/tasks/${taskId}/toggle`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ enabled: enabled })
    }, `toggleTask for ${taskId}`)
        .then(data => {
            if (data.success) {
                showMessage(data.message || `任务已${actionText}`, 'success');
                loadTasks(); // 刷新任务列表
            } else {
                showMessage(data.message || `${actionText}任务失败`, 'danger');
            }
            taskOperationInProgress = false;
        })
        .catch(error => {
            showMessage(`${actionText}任务失败`, 'danger');
            taskOperationInProgress = false;
        });
}

// 页面卸载前清理
window.addEventListener('beforeunload', function() {
    if (logRefreshInterval) {
        clearInterval(logRefreshInterval);
    }
    if (newLogRefreshInterval) {
        clearInterval(newLogRefreshInterval);
    }
    if (statusRefreshInterval) {
        clearInterval(statusRefreshInterval);
    }
});

// 新版任务调度器API配置和变量
const NEW_API_BASE_URL = '';
let currentNewTaskId = null;
let newLogRefreshInterval = null;


// 新版任务调度器功能
function showNewMessage(message, type = 'info') {
    const container = document.getElementById('new-message-container');
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${type}`;
    alertElement.textContent = message;
    
    // 清空旧消息，避免显示多条相同的通知
    container.innerHTML = '';
    container.appendChild(alertElement);
    
    // 5秒后自动移除
    setTimeout(() => {
        alertElement.remove();
    }, 5000);
}

// 显示创建任务模态窗口
function showCreateTaskModal() {
    document.getElementById('createTaskModal').style.display = 'block';
}

// 关闭创建任务模态窗口
function closeCreateTaskModal() {
    document.getElementById('createTaskModal').style.display = 'none';
    document.getElementById('createNewTaskForm').reset();
}

// 加载新版任务列表
async function loadNewTasks(showLoading = true) {
    const taskList = document.getElementById('newTaskList');
    
    if (showLoading) {
        taskList.innerHTML = `
            <div class="text-center">
                <div class="spinner"></div>
                <p>加载中...</p>
            </div>
        `;
    }

    try {
        const result = await fetchApi(`${NEW_API_BASE_URL}/api/scheduler/tasks`, {}, 'loadNewTasks');
        if (result.success) {
            renderNewTaskList(result.data);
        } else {
            if (showLoading) {
                taskList.innerHTML = `<div class="text-center text-danger">加载失败: ${result.message}</div>`;
            }
        }
    } catch (error) {
        if (showLoading) {
            taskList.innerHTML = `<div class="text-center text-danger">网络错误，无法加载任务列表。</div>`;
        }
    }
}

// 渲染新版任务列表
function renderNewTaskList(tasks) {
    const taskList = document.getElementById('newTaskList');
    
    if (tasks.length === 0) {
        taskList.innerHTML = '<div class="text-center text-muted">暂无任务</div>';
        return;
    }

    const html = tasks.map(task => {
        const isEnabled = task.task_enabled;
        const statusClass = isEnabled ? 'task-enabled' : 'task-disabled';

        return `
        <div class="new-task-item ${statusClass}">
            <div class="task-info-container" onclick="viewNewLogs('${task.task_id}', '${task.task_name}')">
                <div class="task-primary-info">
                    <div class="task-name" title="${task.task_name}">${task.task_name}</div>
                    <div class="task-schedule-cron">${task.task_schedule}</div>
                </div>
                <div class="task-description-small" title="${task.task_desc || '无描述'}">${task.task_desc || '无描述'}</div>
                <div class="task-next-run">
                    <strong>下次执行:</strong> ${task.next_run_time ? new Date(task.next_run_time).toLocaleString() : 'N/A'}
                </div>
            </div>
            <div class="task-actions-panel" onclick="event.stopPropagation();">
                <button class="btn btn-sm btn-success" onclick="executeNewTask('${task.task_id}')">运行一次</button>
                ${isEnabled
                    ? `<button class="btn btn-sm btn-warning" onclick="toggleNewTask('${task.task_id}', false)">禁用</button>`
                    : `<button class="btn btn-sm btn-success" onclick="toggleNewTask('${task.task_id}', true)">启用</button>`
                }
                <button class="btn btn-sm btn-secondary" onclick="showTaskDetails('${task.task_id}')">详情</button>
                <button class="btn btn-sm btn-warning" onclick="openEditModal('${task.task_id}')">编辑</button>
                <button class="btn btn-sm btn-danger" onclick="deleteNewTask('${task.task_id}')">删除</button>
            </div>
        </div>
    `}).join('');

    taskList.innerHTML = html;
}

async function createNewTask(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const task = {
        task_id: formData.get('task_id'),
        task_name: formData.get('task_name'),
        task_desc: formData.get('task_desc') || '',
        task_exec: formData.get('task_exec'),
        task_schedule: formData.get('task_schedule'),
        task_timeout: parseInt(formData.get('task_timeout')) || 300,
        task_retry: parseInt(formData.get('task_retry')) || 0,
        task_retry_interval: 60,
        task_enabled: formData.get('task_enabled') === 'true',
        task_log: formData.get('task_log') || `logs/task_${formData.get('task_id')}.log`,
        task_env: {},
        task_dependencies: [],
        task_notify: {}
    };

    try {
        const result = await fetchApi(`${NEW_API_BASE_URL}/api/scheduler/tasks`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(task)
        }, 'createNewTask');
        
        if (result.success) {
            showNewMessage('任务创建成功', 'success');
            closeCreateTaskModal();
            // 静默刷新任务列表，不显示额外通知
            await loadNewTasks(false);
        } else {
            // 显示错误消息
            const errorMessageDiv = document.getElementById('createTaskErrorMessage');
            if (errorMessageDiv) {
                errorMessageDiv.textContent = `创建失败: ${result.message}`;
            } else {
                showNewMessage(`创建失败: ${result.message}`, 'error');
            }
        }
    } catch (error) {
        // 显示错误消息
        const errorMessageDiv = document.getElementById('createTaskErrorMessage');
        if (errorMessageDiv) {
            errorMessageDiv.textContent = `创建失败: 网络错误`;
        } else {
            showNewMessage(`创建失败: 网络错误`, 'error');
        }
    }
}

async function updateTask(taskId, taskData) {
    const errorMessageDiv = document.getElementById('editTaskErrorMessage');
    errorMessageDiv.textContent = ''; // Clear previous errors

    try {
        const result = await fetchApi(`${NEW_API_BASE_URL}/api/scheduler/tasks/${taskId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(taskData)
        }, `updateTask for ${taskId}`);

        if (result.success) {
            // 只显示一条成功消息
            showNewMessage('任务更新成功!', 'success');
            closeEditModal();
            // 静默刷新任务列表，不显示额外通知
            await loadNewTasks(false); 
        } else {
            // 只在模态框内显示错误，不在通知区域重复显示
            errorMessageDiv.textContent = `更新失败: ${result.message}`;
        }
    } catch (error) {
        // 只在模态框内显示错误，不在通知区域重复显示
        errorMessageDiv.textContent = `更新失败: 网络错误`;
    }
}

// 创建新版任务
document.getElementById('createNewTaskForm').addEventListener('submit', createNewTask);

// 编辑任务表单提交处理
document.getElementById('editTaskForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const form = e.target;
    const taskId = form.task_id.value;
    
    // 获取原始任务数据，以保留未在表单中显示的字段
    try {
        const response = await fetchApi(`${NEW_API_BASE_URL}/api/scheduler/tasks/${taskId}`, {}, `getOriginalTask for ${taskId}`);
        if (!response.success) {
            const errorMessageDiv = document.getElementById('editTaskErrorMessage');
            errorMessageDiv.textContent = `获取原始任务数据失败: ${response.message}`;
            return;
        }
        
        const originalTask = response.data;
        
        // 创建更新数据，只更新表单中的字段，保留其他字段的原始值
        const taskData = {
            task_id: taskId,
            task_name: form.task_name.value,
            task_schedule: form.task_schedule.value,
            task_exec: form.task_exec.value,
            task_desc: form.task_desc.value,
            task_enabled: form.task_enabled.value === 'true',
            task_timeout: parseInt(form.task_timeout.value),
            task_retry: parseInt(form.task_retry.value),
            task_retry_interval: parseInt(form.task_retry_interval.value),
            task_log: form.task_log.value,
            // 保留原始值
            task_env: originalTask.task_env || {},
            task_dependencies: originalTask.task_dependencies || [],
            task_notify: originalTask.task_notify || {}
        };
        
        // 添加唯一请求ID，防止重复提交
        const requestId = `edit_${taskId}_${Date.now()}`;
        const headers = {
            'Content-Type': 'application/json',
            'X-Request-ID': requestId
        };
        
        // 发送更新请求
        const result = await fetchApi(`${NEW_API_BASE_URL}/api/scheduler/tasks/${taskId}`, {
            method: 'PUT',
            headers: headers,
            body: JSON.stringify(taskData)
        }, `updateTask for ${taskId}`);
        
        if (result.success) {
            showNewMessage('任务更新成功!', 'success');
            closeEditModal();
            loadNewTasks(false); // 静默刷新任务列表
        } else {
            const errorMessageDiv = document.getElementById('editTaskErrorMessage');
            errorMessageDiv.textContent = `更新失败: ${result.message}`;
        }
    } catch (error) {
        const errorMessageDiv = document.getElementById('editTaskErrorMessage');
        errorMessageDiv.textContent = `更新失败: ${error.message}`;
    }
});

// 执行新版任务
async function executeNewTask(taskId) {
    try {
        const result = await fetchApi(`${NEW_API_BASE_URL}/api/scheduler/tasks/${taskId}/run-once`, {
            method: 'POST'
        }, `executeNewTask for ${taskId}`);
        
        if (result.success) {
            showNewMessage(`任务 ${taskId} 开始执行`, 'success');
            // 自动查看该任务的日志
            const taskElement = document.querySelector(`.new-task-item .task-name[title='${taskId}']`);
            const taskName = taskElement ? taskElement.innerText : taskId;
            setTimeout(() => {
                viewNewLogs(taskId, taskName);
            }, 500); // 延迟500ms等待日志写入
        } else {
            showNewMessage(`执行失败: ${result.message}`, 'error');
        }
    } catch (error) {
        showNewMessage(`执行失败: 网络错误`, 'error');
    }
}

// 查看新版日志
async function viewNewLogs(taskId, taskName) {
    if (!taskId) {
        console.warn('无效的任务ID:', taskId);
        return;
    }
    
    // 如果是同一个任务且定时器已在运行，则不操作
    if (currentNewTaskId === taskId && newLogRefreshInterval) {
        return;
    }

    currentNewTaskId = taskId;
    document.getElementById('newLogTitle').textContent = `任务日志: ${taskName}`;
    
    // 停止旧的定时器
    if (newLogRefreshInterval) {
        clearInterval(newLogRefreshInterval);
        newLogRefreshInterval = null;
    }

    // 重置当前日志文件路径
    currentLogFile = null;

    // 立即加载一次日志
    await loadNewTaskLogs(taskId, true);
    
    // 只有在服务器连接正常时才启动定时器
    if (serverConnected) {
        // 启动新的定时器
        newLogRefreshInterval = setInterval(() => {
            if (currentNewTaskId === taskId) {
                loadNewTaskLogs(taskId, false);
            }
        }, 2000);
        toggleLogRefresh(true, true);
    } else {
        // 服务器已断开连接，不启动定时器，确保旋转动画不显示
        toggleLogRefresh(true, false);
    }
}

// 渲染新版日志
function renderNewLogs(logs) {
    const logViewer = document.getElementById('newLogViewer');
    
    if (!logs || logs.length === 0) {
        logViewer.innerHTML = '<div class="log-placeholder">暂无日志</div>';
        return;
    }

    const html = logs.map(log => `
        <div class="log-line ${log.content.includes('ERROR') ? 'error' : log.content.includes('WARNING') ? 'warning' : ''}">
            <span class="log-line-number">${log.line}</span>
            <span class="log-line-content">${escapeHtml(log.content)}</span>
        </div>
    `).join('');

    logViewer.innerHTML = html;
    logViewer.scrollTop = logViewer.scrollHeight;
}

// 加载新版任务日志
async function loadNewTaskLogs(taskId, showLoadingIndicator = true) {
    if (!taskId) {
        console.warn('无效的任务ID:', taskId);
        return;
    }
    
    const logViewer = document.getElementById('newLogViewer');
    if (showLoadingIndicator) {
        logViewer.innerHTML = '<div class="text-center"><div class="spinner"></div><p>加载中...</p></div>';
    }
    
    try {
        const result = await fetchApi(`${NEW_API_BASE_URL}/api/scheduler/tasks/${taskId}/logs`, {}, `loadNewTaskLogs for ${taskId}`);
        if (showLoadingIndicator) hideLoading('newLogViewer');
        
        // 保存当前日志文件路径，用于后续刷新
        if (result.log_file) {
            currentLogFile = result.log_file;
            console.log(`已更新日志文件路径: ${currentLogFile}`);
        }
        
        renderNewLogs(result.data);
    } catch (error) {
        if (showLoadingIndicator) hideLoading('newLogViewer');
        logViewer.innerHTML = '<div class="log-placeholder"><p>加载日志失败</p></div>';
        // 停止日志刷新和旋转动画
        toggleLogRefresh(true, false);
    }
}

function refreshNewLog() {
    if (currentNewTaskId) {
        loadNewTaskLogs(currentNewTaskId, true);
        showNewMessage('日志已刷新', 'info');
    } else {
        showNewMessage('请先选择一个任务', 'warning');
    }
}

// 清空新版任务日志
async function clearNewLog() {
    if (!currentNewTaskId) {
        showNewMessage('请先选择一个任务', 'warning');
        return;
    }
    
    if (!confirm(`确定要清空任务 ${currentNewTaskId} 的日志吗？`)) {
        return;
    }
    
    // 显示加载中
    document.getElementById('newLogViewer').innerHTML = '<div class="text-center"><div class="spinner"></div><p>正在清空日志...</p></div>';
    
    try {
        // 获取最新的任务信息，确保使用正确的日志文件路径
        const taskInfo = await fetchApi(`${NEW_API_BASE_URL}/api/scheduler/tasks/${currentNewTaskId}`, {}, `getTaskInfo for ${currentNewTaskId}`);
        
        if (!taskInfo.success) {
            showNewMessage('获取任务信息失败', 'error');
            return;
        }
        
        const result = await fetchApi(`${NEW_API_BASE_URL}/api/scheduler/tasks/${currentNewTaskId}/logs/clear`, {
            method: 'POST'
        }, `clearNewLog for ${currentNewTaskId}`);
        
        if (result.success) {
            showNewMessage('日志已清空', 'success');
            document.getElementById('newLogViewer').innerHTML = '<div class="log-placeholder"><p>日志已清空，等待新日志...</p></div>';
            
            // 重新启动日志刷新
            if (newLogRefreshInterval) {
                clearInterval(newLogRefreshInterval);
            }
            
            newLogRefreshInterval = setInterval(() => {
                if (currentNewTaskId) {
                    loadNewTaskLogs(currentNewTaskId, false);
                }
            }, 2000);
        } else {
            showNewMessage(`清空日志失败: ${result.message}`, 'error');
            loadNewTaskLogs(currentNewTaskId); // 重新加载日志
        }
    } catch (error) {
        showNewMessage(`清空日志失败: 网络错误`, 'error');
        loadNewTaskLogs(currentNewTaskId); // 重新加载日志
    }
}

// 删除新版任务
async function deleteNewTask(taskId) {
    if (!confirm(`确定要删除任务 ${taskId} 吗？`)) {
        return;
    }

    try {
        const result = await fetchApi(`${NEW_API_BASE_URL}/api/scheduler/tasks/${taskId}`, {
            method: 'DELETE'
        }, `deleteNewTask for ${taskId}`);
        
        if (result.success) {
            showNewMessage('任务删除成功', 'success');
            loadNewTasks();
            if (currentNewTaskId === taskId) {
                // 清理定时器
                if (newLogRefreshInterval) {
                    clearInterval(newLogRefreshInterval);
                    newLogRefreshInterval = null;
                }
                document.getElementById('newLogViewer').innerHTML = '<div class="log-placeholder">请选择一个任务查看日志</div>';
                currentNewTaskId = null;
            }
        } else {
            showNewMessage(`删除失败: ${result.message}`, 'error');
        }
    } catch (error) {
        showNewMessage(`删除失败: 网络错误`, 'error');
    }
}

// 启用/禁用新版任务
async function toggleNewTask(taskId, enabled) {
    if (!confirm(`确定要${enabled ? '启用' : '禁用'}任务 ${taskId} 吗？`)) {
        return;
    }

    try {
        const result = await fetchApi(`${NEW_API_BASE_URL}/api/scheduler/tasks/${taskId}/toggle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ enabled: enabled })
        }, `toggleNewTask for ${taskId}`);
        
        if (result.success) {
            showNewMessage(`任务 ${taskId} 已${enabled ? '启用' : '禁用'}`, 'success');
            loadNewTasks(); // 重新加载任务列表
        } else {
            showNewMessage(`操作失败: ${result.message}`, 'error');
        }
    } catch (error) {
        showNewMessage(`操作失败: 网络错误`, 'error');
    }
}

// 验证CRON表达式
async function validateCron() {
    const expression = document.getElementById('cronExpression').value.trim();
    const resultDiv = document.getElementById('cronResult');
    
    if (!expression) {
        resultDiv.innerHTML = '<span class="text-danger">请输入CRON表达式</span>';
        return;
    }

    try {
        const result = await fetchApi(`${NEW_API_BASE_URL}/api/scheduler/validate-cron`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ cron: expression })
        }, 'validateCron');
        
        if (result.data.valid) {
            const nextRun = new Date(result.data.next_run);
            resultDiv.innerHTML = `
                <span class="text-success">✅ 有效</span><br>
                <small>下次执行时间: ${nextRun.toLocaleString()}</small>
            `;
        } else {
            resultDiv.innerHTML = `
                <span class="text-danger">❌ 无效</span><br>
                <small>${result.data.error}</small>
            `;
        }
    } catch (error) {
        resultDiv.innerHTML = `<span class="text-danger">验证失败: 网络错误</span>`;
    }
}

// 显示任务详情
async function showTaskDetails(taskId) {
    try {
        const result = await fetchApi(`${NEW_API_BASE_URL}/api/scheduler/tasks/${taskId}`, {}, `showTaskDetails for ${taskId}`);
        
        if (result.success) {
            const task = result.data;
            const content = document.getElementById('taskDetailsContent');
            
            content.innerHTML = `
                <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
                    <div style="margin-bottom: 15px;">
                        <strong style="color: #333;">任务名称:</strong>
                        <div style="margin-top: 5px; padding: 8px; background: #f8f9fa; border-radius: 3px;">${task.task_name}</div>
                    </div>
                    
                    <div style="margin-bottom: 15px;">
                        <strong style="color: #333;">任务ID:</strong>
                        <div style="margin-top: 5px; padding: 8px; background: #f8f9fa; border-radius: 3px; font-family: monospace;">${task.task_id}</div>
                    </div>
                    
                    <div style="margin-bottom: 15px;">
                        <strong style="color: #333;">任务描述:</strong>
                        <div style="margin-top: 5px; padding: 8px; background: #f8f9fa; border-radius: 3px;">${task.task_desc || '无描述'}</div>
                    </div>
                    
                    <div style="margin-bottom: 15px;">
                        <strong style="color: #333;">执行命令:</strong>
                        <div style="margin-top: 5px; padding: 8px; background: #f8f9fa; border-radius: 3px; font-family: monospace; font-size: 13px;">${task.task_exec}</div>
                    </div>
                    
                    <div style="margin-bottom: 15px;">
                        <strong style="color: #333;">调度表达式:</strong>
                        <div style="margin-top: 5px; padding: 8px; background: #f8f9fa; border-radius: 3px; font-family: monospace;">${task.task_schedule}</div>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                        <div>
                            <strong style="color: #333;">超时时间:</strong>
                            <div style="margin-top: 5px; padding: 8px; background: #f8f9fa; border-radius: 3px;">${task.task_timeout} 秒</div>
                        </div>
                        <div>
                            <strong style="color: #333;">重试次数:</strong>
                            <div style="margin-top: 5px; padding: 8px; background: #f8f9fa; border-radius: 3px;">${task.task_retry} 次</div>
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 15px;">
                        <strong style="color: #333;">日志文件:</strong>
                        <div style="margin-top: 5px; padding: 8px; background: #f8f9fa; border-radius: 3px; font-family: monospace;">${task.task_log}</div>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                        <div>
                            <strong style="color: #333;">启用状态:</strong>
                            <div style="margin-top: 5px; padding: 8px; background: #f8f9fa; border-radius: 3px;">
                                <span style="color: ${task.task_enabled ? '#28a745' : '#dc3545'};">
                                    ${task.task_enabled ? '启用' : '禁用'}
                                </span>
                            </div>
                        </div>
                        <div>
                            <strong style="color: #333;">下次执行:</strong>
                            <div style="margin-top: 5px; padding: 8px; background: #f8f9fa; border-radius: 3px;">
                                ${task.next_run_time ? new Date(task.next_run_time).toLocaleString() : '未安排'}
                            </div>
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 15px;">
                        <strong style="color: #333;">创建时间:</strong>
                        <div style="margin-top: 5px; padding: 8px; background: #f8f9fa; border-radius: 3px;">${new Date(task.created_at).toLocaleString()}</div>
                    </div>
                    
                    ${task.last_run_time ? `
                    <div style="margin-bottom: 15px;">
                        <strong style="color: #333;">上次执行:</strong>
                        <div style="margin-top: 5px; padding: 8px; background: #f8f9fa; border-radius: 3px;">${new Date(task.last_run_time).toLocaleString()}</div>
                    </div>
                    ` : ''}
                </div>
            `;
            
            document.getElementById('taskDetailsModal').style.display = 'block';
        } else {
            showNewMessage(`获取任务详情失败: ${result.message}`, 'error');
        }
    } catch (error) {
        showNewMessage(`获取任务详情失败: 网络错误`, 'error');
    }
}

// 关闭任务详情模态窗口
function closeTaskDetailsModal() {
    document.getElementById('taskDetailsModal').style.display = 'none';
}

// --- Edit Task Functions ---
async function openEditModal(taskId) {
    const modal = document.getElementById('editTaskModal');
    const form = document.getElementById('editTaskForm');
    const errorMessageDiv = document.getElementById('editTaskErrorMessage');
    errorMessageDiv.textContent = ''; // 清除之前的错误信息
    
    try {
        const response = await fetchApi(`${NEW_API_BASE_URL}/api/scheduler/tasks/${taskId}`, {}, `openEditModal for ${taskId}`);
        if (!response.success) {
            showNewMessage(`错误: ${response.message}`, 'error');
            return;
        }
        
        const task = response.data;
        
        // 填充表单的所有字段，确保不遗漏任何配置
        form.task_id.value = task.task_id;
        form.task_name.value = task.task_name;
        form.task_schedule.value = task.task_schedule;
        form.task_exec.value = task.task_exec;
        form.task_desc.value = task.task_desc || '';
        
        // 填充高级配置字段
        form.task_timeout.value = task.task_timeout || 300;
        form.task_retry.value = task.task_retry || 0;
        form.task_retry_interval.value = task.task_retry_interval || 60;
        form.task_log.value = task.task_log || `logs/task_${task.task_id}.log`;
        
        // 保存当前的启用状态，但不在表单中显示
        form.task_enabled.value = task.task_enabled.toString();
        
        document.getElementById('editModalTitle').innerText = `编辑任务: ${task.task_name}`;
        modal.style.display = 'block';
    } catch (error) {
        showNewMessage(`网络错误: ${error.message}`, 'error');
    }
}

function closeEditModal() {
    document.getElementById('editTaskModal').style.display = 'none';
}

// 编辑任务表单提交处理
document.getElementById('editTaskForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const form = e.target;
    const taskId = form.task_id.value;
    
    // 获取原始任务数据，以保留未在表单中显示的字段
    try {
        const response = await fetchApi(`${NEW_API_BASE_URL}/api/scheduler/tasks/${taskId}`, {}, `getOriginalTask for ${taskId}`);
        if (!response.success) {
            const errorMessageDiv = document.getElementById('editTaskErrorMessage');
            errorMessageDiv.textContent = `获取原始任务数据失败: ${response.message}`;
            return;
        }
        
        const originalTask = response.data;
        
        // 创建更新数据，只更新表单中的字段，保留其他字段的原始值
        const taskData = {
            task_id: taskId,
            task_name: form.task_name.value,
            task_schedule: form.task_schedule.value,
            task_exec: form.task_exec.value,
            task_desc: form.task_desc.value,
            task_enabled: form.task_enabled.value === 'true',
            task_timeout: parseInt(form.task_timeout.value),
            task_retry: parseInt(form.task_retry.value),
            task_retry_interval: parseInt(form.task_retry_interval.value),
            task_log: form.task_log.value,
            // 保留原始值
            task_env: originalTask.task_env || {},
            task_dependencies: originalTask.task_dependencies || [],
            task_notify: originalTask.task_notify || {}
        };
        
        // 添加唯一请求ID，防止重复提交
        const requestId = `edit_${taskId}_${Date.now()}`;
        const headers = {
            'Content-Type': 'application/json',
            'X-Request-ID': requestId
        };
        
        // 发送更新请求
        const result = await fetchApi(`${NEW_API_BASE_URL}/api/scheduler/tasks/${taskId}`, {
            method: 'PUT',
            headers: headers,
            body: JSON.stringify(taskData)
        }, `updateTask for ${taskId}`);
        
        if (result.success) {
            showNewMessage('任务更新成功!', 'success');
            closeEditModal();
            loadNewTasks(false); // 静默刷新任务列表
        } else {
            const errorMessageDiv = document.getElementById('editTaskErrorMessage');
            errorMessageDiv.textContent = `更新失败: ${result.message}`;
        }
    } catch (error) {
        const errorMessageDiv = document.getElementById('editTaskErrorMessage');
        errorMessageDiv.textContent = `更新失败: ${error.message}`;
    }
});

// 标签页切换时初始化对应内容
document.addEventListener('tabChanged', function(e) {
    if (e.detail.target === 'new-scheduler') {
        loadNewTasks();
    }
});
