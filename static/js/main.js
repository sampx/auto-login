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
        html += `
            <li class="task-item" data-task-id="${task.id}" onclick="viewTaskLogs('${task.id}')">
                <div class="task-info">
                    <div class="task-name">${task.name}</div>
                    <div class="task-description">${task.description}</div>
                    <div class="task-schedule">调度: ${task.schedule}</div>
                </div>
                <div class="task-actions">
                    <span class="task-status ${task.status === 'running' ? 'status-running' : 'status-stopped'}">
                        ${task.status === 'running' ? '运行中' : '已停止'}
                    </span>
                    ${task.status === 'running' 
                        ? '<button class="btn btn-danger btn-sm stop-task">停止</button>'
                        : '<button class="btn btn-success btn-sm start-task">启动</button>'}
                </div>
            </li>
        `;
    });
    
    html += '</ul>';
    taskListElement.innerHTML = html;
    
    // 绑定任务操作事件
    bindTaskEvents();
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
    // 防止重复操作
    if (taskOperationInProgress) {
        console.log('操作正在进行中，请稍候...');
        return;
    }
    
    taskOperationInProgress = true;
    
    // 禁用所有按钮，防止重复点击
    const taskItem = document.querySelector(`[data-task-id="${taskId}"]`);
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
    }, 2000);
}

// 刷新日志
function refreshLog() {
    if (currentTask) {
        loadTaskLogs(currentTask, true);
    }
}

// 加载任务日志
function loadTaskLogs(taskId, showLoadingIndicator = true) {
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
        
        fetch(`/api/tasks/${taskId}/status`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateTaskStatus(taskItem, data.status);
                }
            })
            .catch(error => {
                console.error('刷新任务状态失败:', error);
            });
    });
}

// 更新任务状态
function updateTaskStatus(taskItem, status) {
    const statusElement = taskItem.querySelector('.task-status');
    const actionButton = taskItem.querySelector('.btn-success, .btn-danger');
    
    // 获取当前状态，用于检测是否有变化
    const currentStatus = statusElement.textContent.trim() === '运行中' ? 'running' : 'stopped';
    
    // 只有当状态发生变化时才更新UI
    if (currentStatus !== status) {
        if (status === 'running') {
            statusElement.textContent = '运行中';
            statusElement.className = 'task-status status-running';
            
            if (actionButton) {
                actionButton.textContent = '停止';
                actionButton.className = 'btn btn-danger btn-sm stop-task';
            }
        } else {
            statusElement.textContent = '已停止';
            statusElement.className = 'task-status status-stopped';
            
            if (actionButton) {
                actionButton.textContent = '启动';
                actionButton.className = 'btn btn-success btn-sm start-task';
            }
        }
        
        // 重新绑定事件
        bindTaskEvents();
        
        // 如果状态从运行中变为已停止，可能是任务自动结束，显示提示
        if (currentStatus === 'running' && status === 'stopped') {
            showMessage('任务已自动结束', 'info');
        }
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

// 页面卸载前清理
window.addEventListener('beforeunload', function() {
    if (logRefreshInterval) {
        clearInterval(logRefreshInterval);
    }
    
    if (statusRefreshInterval) {
        clearInterval(statusRefreshInterval);
    }
});