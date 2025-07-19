// 全局变量
let currentTask = null;
let logRefreshInterval = null;
let statusRefreshInterval = null;

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化标签页
    initTabs();
    
    // 加载任务列表
    loadTasks();
    
    // 设置定时刷新任务状态
    statusRefreshInterval = setInterval(refreshTaskStatus, 5000);
    
    // 加载配置
    loadConfig();
    
    // 绑定配置表单提交事件
    const configForm = document.getElementById('configForm');
    if (configForm) {
        configForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveConfig();
        });
    }

    // 绑定刷新日志按钮事件
    const refreshLogBtn = document.getElementById('refresh-log-btn');
    if (refreshLogBtn) {
        refreshLogBtn.addEventListener('click', refreshLog);
    }
});

// 初始化标签页
function initTabs() {
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // 移除所有标签页的active类
            tabs.forEach(t => t.classList.remove('active'));
            
            // 移除所有内容区域的active类
            tabContents.forEach(content => content.classList.remove('active'));
            
            // 添加当前标签页的active类
            this.classList.add('active');
            
            // 显示对应的内容区域
            const target = this.getAttribute('data-target');
            document.getElementById(target).classList.add('active');
        });
    });
}

// 加载任务列表
function loadTasks() {
    showLoading('taskList');
    
    fetch('/api/tasks')
        .then(response => response.json())
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
            showError('taskList', error.message || '加载任务列表失败');
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
                            ? '<button class="btn btn-danger btn-sm stop-task" onclick="event.stopPropagation(); stopTask(\'' + taskId + '\')">停止</button>'
                            : isEnabled 
                                ? '<button class="btn btn-success btn-sm start-task" onclick="event.stopPropagation(); startTask(\'' + taskId + '\')">启动</button>'
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

// 查看任务日志
function viewTaskLogs(taskId) {
    if (!taskId || taskId === 'null') {
        console.warn('无效的任务ID:', taskId);
        return;
    }
    
    if (currentTask === taskId) {
        // 如果点击的是同一个任务，则不重新加载日志
        return;
    }

    currentTask = taskId;
    
    // 更新日志标题
    const logTitle = document.getElementById('logTitle');
    if (logTitle) {
        logTitle.textContent = `任务日志 - ${taskId}`;
    }
    
    // 加载任务日志
    loadTaskLogs(taskId);
    
    // 设置定时刷新日志 - 每2秒自动刷新一次，实现类似tail -f的效果
    if (logRefreshInterval) {
        clearInterval(logRefreshInterval);
    }
    
    logRefreshInterval = setInterval(() => {
        if (currentTask === taskId) {
            loadTaskLogs(taskId, false);
        }
    }, 500);
}

// 刷新日志
function refreshLog() {
    if (currentTask) {
        loadTaskLogs(currentTask, true);
    }
}

// 加载任务日志
function loadTaskLogs(taskId, showLoadingIndicator = true) {
    if (!taskId || taskId === 'null') {
        console.warn('无效的任务ID:', taskId);
        return;
    }
    
    if (showLoadingIndicator) {
        showLoading('logViewer');
    }
    
    fetch(`/api/tasks/${taskId}/logs?limit=100`)
        .then(response => response.json())
        .then(data => {
            if (showLoadingIndicator) {
                hideLoading('logViewer');
            }
            
            if (data.success) {
                console.log("Logs received:", data.logs); // Debug log
                renderLogs(data.logs);
            } else {
                showError('logViewer', data.message || '加载日志失败');
            }
        })
        .catch(error => {
            if (showLoadingIndicator) {
                hideLoading('logViewer');
            }
            showError('logViewer', error.message || '加载日志失败');
        });
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
            html += `${escapeHtml(log.raw)}\n`;
        } else {
            // 格式化时间戳
            const timestamp = formatTimestamp(log.timestamp);
            html += `${timestamp} ${log.level} ${escapeHtml(log.message)}\n`;
        }
    });
    
    html += '</pre>';
    logViewerElement.innerHTML = html;
    
    // 滚动到底部
    logViewerElement.scrollTop = logViewerElement.scrollHeight;
}

// 格式化时间戳
function formatTimestamp(timestamp) {
    try {
        const date = new Date(timestamp);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    } catch (e) {
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
        
        fetch(`/api/tasks/${taskId}/status`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateTaskStatus(taskItem, data.status, data.enabled);
                }
            })
            .catch(error => {
                console.error('刷新任务状态失败:', error);
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
    
    fetch('/api/config')
        .then(response => response.json())
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
            showError('configForm', error.message || '加载配置失败');
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
    
    fetch('/api/config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    })
        .then(response => response.json())
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
            showError('configForm', error.message || '保存配置失败');
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
    fetch(`/api/tasks/${currentTask}/logs/clear`, {
        method: 'POST'
    })
        .then(response => response.json())
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
            showMessage(error.message || '清空日志失败', 'danger');
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
    
    fetch(`/api/tasks/${taskId}/toggle`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ enabled: enabled })
    })
        .then(response => response.json())
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
            showMessage(error.message || `${actionText}任务失败`, 'danger');
            taskOperationInProgress = false;
        });
}

// 页面卸载前清理
window.addEventListener('beforeunload', function() {
    if (logRefreshInterval) {
        clearInterval(logRefreshInterval);
    }
    
    if (statusRefreshInterval) {
        clearInterval(statusRefreshInterval);
    }
});