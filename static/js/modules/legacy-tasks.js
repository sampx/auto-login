/**
 * 老版本任务管理模块
 * 处理老版本的任务列表、启动、停止等功能
 */

const LegacyTasks = {
    // 加载任务列表
    loadTasks() {
        UIManager.showLoading('taskList');
        APIManager.fetchApi('/api/tasks', {}, 'loadTasks')
            .then(data => {
                UIManager.hideLoading('taskList');
                if (data.success) {
                    this.renderTaskList(data.tasks);
                } else {
                    UIManager.showError('taskList', data.message || '加载任务列表失败');
                }
            })
            .catch(error => {
                UIManager.hideLoading('taskList');
                UIManager.showError('taskList', '加载任务列表失败');
            });
    },

    // 渲染任务列表
    renderTaskList(tasks) {
        const taskListElement = document.getElementById('taskList');
        if (!taskListElement) return;
        
        if (!tasks || tasks.length === 0) {
            taskListElement.innerHTML = '<div class="alert alert-info">没有可用的任务</div>';
            return;
        }
        
        let html = '<ul class="task-list">';
        
        tasks.forEach(task => {
            // 确保任务ID不为null
            const taskId = task.id || 'auto_login';
            const isEnabled = task.enabled !== false;
            const statusClass = Utils.getStatusClass(task.status, isEnabled);
            const statusText = Utils.getStatusText(task.status, isEnabled);
            
            html += `
                <li class="task-item ${!isEnabled ? 'task-disabled' : ''}" data-task-id="${taskId}" onclick="LogsManager.viewTaskLogs('${taskId}')">
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
                                ? `<button class="btn btn-danger btn-sm stop-task" onclick="event.stopPropagation(); window.LegacyTasks.stopTask('${taskId}')">停止</button>`
                                : isEnabled 
                                    ? `<button class="btn btn-success btn-sm start-task" onclick="event.stopPropagation(); window.LegacyTasks.startTask('${taskId}')">启动</button>`
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
        this.bindTaskEvents();
    },

    // 绑定任务操作事件
    bindTaskEvents() {
        // 启动任务按钮
        document.querySelectorAll('.start-task').forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                const taskItem = button.closest('.task-item');
                const taskId = taskItem.getAttribute('data-task-id');
                this.startTask(taskId);
            });
        });
        
        // 停止任务按钮
        document.querySelectorAll('.stop-task').forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                const taskItem = button.closest('.task-item');
                const taskId = taskItem.getAttribute('data-task-id');
                this.stopTask(taskId);
            });
        });
    },

    // 启动任务
    startTask(taskId) {
        // 防止无效的任务ID
        if (!Utils.isValidTaskId(taskId)) {
            UIManager.showMessage('无效的任务ID', 'danger');
            return;
        }
        
        // 防止重复操作
        if (StateManager.getTaskOperationInProgress()) {
            console.log('操作正在进行中，请稍候...');
            return;
        }
        
        StateManager.setTaskOperationInProgress(true);
        
        // 禁用所有按钮，防止重复点击
        const taskItem = document.querySelector(`[data-task-id="${taskId}"]`);
        if (!taskItem) {
            StateManager.setTaskOperationInProgress(false);
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
                    UIManager.showMessage(data.message || '任务已启动', 'success');
                    // 延迟刷新任务列表，给任务启动一些时间
                    setTimeout(() => {
                        this.loadTasks();
                        // 自动查看该任务的日志
                        LogsManager.viewTaskLogs(taskId);
                        // 重置操作状态
                        StateManager.setTaskOperationInProgress(false);
                    }, 1000);
                } else {
                    UIManager.showMessage(data.message || '启动任务失败', 'danger');
                    // 重新启用按钮
                    buttons.forEach(btn => btn.disabled = false);
                    // 重置操作状态
                    StateManager.setTaskOperationInProgress(false);
                }
            })
            .catch(error => {
                UIManager.showMessage(error.message || '启动任务失败', 'danger');
                // 重新启用按钮
                buttons.forEach(btn => btn.disabled = false);
                // 重置操作状态
                StateManager.setTaskOperationInProgress(false);
            });
    },

    // 停止任务
    stopTask(taskId) {
        // 防止无效的任务ID
        if (!Utils.isValidTaskId(taskId)) {
            UIManager.showMessage('无效的任务ID', 'danger');
            return;
        }
        
        // 防止重复操作
        if (StateManager.getTaskOperationInProgress()) {
            console.log('操作正在进行中，请稍候...');
            return;
        }
        
        StateManager.setTaskOperationInProgress(true);
        
        fetch(`/api/tasks/${taskId}/stop`, {
            method: 'POST'
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    UIManager.showMessage(data.message || '任务已停止', 'success');
                    this.loadTasks();
                } else {
                    UIManager.showMessage(data.message || '停止任务失败', 'danger');
                }
                // 重置操作状态
                StateManager.setTaskOperationInProgress(false);
            })
            .catch(error => {
                UIManager.showMessage(error.message || '停止任务失败', 'danger');
                // 重置操作状态
                StateManager.setTaskOperationInProgress(false);
            });
    },

    // 启用/禁用任务
    toggleTask(taskId, enabled) {
        // 防止无效的任务ID
        if (!Utils.isValidTaskId(taskId)) {
            UIManager.showMessage('无效的任务ID', 'danger');
            return;
        }
        
        // 防止重复操作
        if (StateManager.getTaskOperationInProgress()) {
            console.log('操作正在进行中，请稍候...');
            return;
        }
        
        StateManager.setTaskOperationInProgress(true);
        
        const actionText = enabled ? '启用' : '禁用';
        
        APIManager.fetchApi(`/api/tasks/${taskId}/toggle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ enabled: enabled })
        }, `toggleTask for ${taskId}`)
            .then(data => {
                if (data.success) {
                    UIManager.showMessage(data.message || `任务已${actionText}`, 'success');
                    this.loadTasks(); // 刷新任务列表
                } else {
                    UIManager.showMessage(data.message || `${actionText}任务失败`, 'danger');
                }
                StateManager.setTaskOperationInProgress(false);
            })
            .catch(error => {
                UIManager.showMessage(`${actionText}任务失败`, 'danger');
                StateManager.setTaskOperationInProgress(false);
            });
    },

    // 刷新任务状态
    refreshTaskStatus() {
        if (!StateManager.getServerConnected()) return;
        const taskItems = document.querySelectorAll('.task-item');
        
        // 如果正在进行任务操作，暂时不刷新状态
        if (StateManager.getTaskOperationInProgress()) {
            return;
        }
        
        taskItems.forEach(taskItem => {
            const taskId = taskItem.getAttribute('data-task-id');
            
            // 防止 null 或 undefined 的任务ID
            if (!Utils.isValidTaskId(taskId)) {
                return;
            }
            
            APIManager.fetchApi(`/api/tasks/${taskId}/status`, {}, `refreshTaskStatus for ${taskId}`)
                .then(data => {
                    if (data.success) {
                        this.updateTaskStatus(taskItem, data.status, data.enabled);
                    }
                })
                .catch(error => {
                    // 错误已由 APIManager.fetchApi 处理
                });
        });
    },

    // 更新任务状态
    updateTaskStatus(taskItem, status, enabled) {
        const statusElement = taskItem.querySelector('.task-status');
        const startStopButton = taskItem.querySelector('.start-task, .stop-task');
        const toggleButton = taskItem.querySelector('.toggle-task');
        
        const currentStatus = statusElement.textContent.trim();
        const newStatusText = Utils.getStatusText(status, enabled);
        const newStatusClass = Utils.getStatusClass(status, enabled);
        
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
        this.bindTaskEvents();
        
        // 如果状态从运行中变为已停止，可能是任务自动结束，显示提示
        if (currentStatus === '运行中' && status === 'stopped' && enabled) {
            UIManager.showMessage('任务已自动结束', 'info');
        }
    },

    // 加载配置
    loadConfig() {
        UIManager.showLoading('configForm');
        APIManager.fetchApi('/api/config', {}, 'loadConfig')
            .then(data => {
                UIManager.hideLoading('configForm');
                if (data.success) {
                    this.renderConfig(data.config);
                } else {
                    UIManager.showError('configForm', data.message || '加载配置失败');
                }
            })
            .catch(error => {
                UIManager.hideLoading('configForm');
                UIManager.showError('configForm', '加载配置失败');
            });
    },

    // 渲染配置
    renderConfig(config) {
        for (const key in config) {
            const input = document.getElementById(key);
            if (input) {
                input.value = config[key];
            }
        }
    },

    // 保存配置
    saveConfig() {
        UIManager.showLoading('configForm');
        
        const configForm = document.getElementById('configForm');
        if (!configForm) {
            UIManager.hideLoading('configForm');
            return;
        }
        
        const formData = new FormData(configForm);
        const config = {};
        
        for (const [key, value] of formData.entries()) {
            config[key] = value;
        }
        
        APIManager.fetchApi('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        }, 'saveConfig')
            .then(data => {
                UIManager.hideLoading('configForm');
                
                if (data.success) {
                    UIManager.showSuccess('configForm', data.message || '配置已保存');
                }
                else {
                    UIManager.showError('configForm', data.message || '保存配置失败');
                }
            })
            .catch(error => {
                UIManager.hideLoading('configForm');
                UIManager.showError('configForm', '保存配置失败');
            });
    }
};

// 导出老版本任务管理器
window.LegacyTasks = LegacyTasks;