/**
 * API请求和连接管理模块
 * 统一处理所有API请求、错误处理和连接状态管理
 */

// API 错误处理
function handleApiError(error, context) {
    console.error(`API Error (${context}):`, error);
    if (StateManager.getServerConnected()) {
        StateManager.setServerConnected(false);
        StateManager.setReconnectActive(true);
        
        const indicator = document.getElementById('server-status-indicator');
        if (indicator) {
            indicator.style.display = 'flex';
        }
        
        // 停止所有定时器
        if (StateManager.getLogRefreshInterval()) {
            clearInterval(StateManager.getLogRefreshInterval());
            StateManager.setLogRefreshInterval(null);
            // 更新旧版日志刷新按钮和旋转动画状态
            const spinner = document.getElementById('log-refresh-spinner');
            const stopBtn = document.getElementById('stop-log-refresh-btn');
            const startBtn = document.getElementById('start-log-refresh-btn');
            if (spinner) spinner.style.display = 'none';
            if (stopBtn) stopBtn.style.display = 'none';
            if (startBtn) startBtn.style.display = 'inline-block';
        }
        
        if (StateManager.getNewLogRefreshInterval()) {
            clearInterval(StateManager.getNewLogRefreshInterval());
            StateManager.setNewLogRefreshInterval(null);
            // 更新新版日志刷新按钮和旋转动画状态
            const spinner = document.getElementById('new-log-refresh-spinner');
            const stopBtn = document.getElementById('stop-new-log-refresh-btn');
            const startBtn = document.getElementById('start-new-log-refresh-btn');
            if (spinner) spinner.style.display = 'none';
            if (stopBtn) stopBtn.style.display = 'none';
            if (startBtn) startBtn.style.display = 'inline-block';
        }
        
        if (StateManager.getStatusRefreshInterval()) {
            clearInterval(StateManager.getStatusRefreshInterval());
            StateManager.setStatusRefreshInterval(null);
        }
        
        // 重置停止按钮状态
        const stopBtn = document.getElementById('stop-reconnect-btn');
        if (stopBtn) {
            stopBtn.disabled = false;
            stopBtn.textContent = '停止检测';
        }
        
        // 重置旋转动画
        const spinner = document.querySelector('.reconnect-spinner');
        if (spinner) {
            spinner.style.animation = 'spin 1s linear infinite';
            spinner.style.borderTop = '3px solid #ffffff';
        }
        
        // 启动健康检查定时器
        if (!StateManager.getHealthCheckInterval()) {
            StateManager.setHealthCheckInterval(setInterval(checkServerHealth, 5000));
        }
    }
}

// API 成功处理
function handleApiSuccess() {
    if (!StateManager.getServerConnected()) {
        StateManager.setServerConnected(true);
        
        // 停止健康检查定时器
        if (StateManager.getHealthCheckInterval()) {
            clearInterval(StateManager.getHealthCheckInterval());
            StateManager.setHealthCheckInterval(null);
        }
        
        // 隐藏断开连接提示
        const indicator = document.getElementById('server-status-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
        
        // 重新启动状态刷新定时器
        if (!StateManager.getStatusRefreshInterval()) {
            StateManager.setStatusRefreshInterval(setInterval(() => {
                if (window.LegacyTasks && window.LegacyTasks.refreshTaskStatus) {
                    window.LegacyTasks.refreshTaskStatus();
                }
            }, 5000));
        }
        
        // 自动刷新任务列表
        if (window.LegacyTasks && window.LegacyTasks.loadTasks) {
            window.LegacyTasks.loadTasks();
        }
        if (window.Scheduler && window.Scheduler.loadNewTasks) {
            window.Scheduler.loadNewTasks();
        }
        
        // 如果当前有选中的任务，重新启动日志刷新
        if (StateManager.getCurrentTask() && window.LogsManager && window.LogsManager.viewTaskLogs) {
            window.LogsManager.viewTaskLogs(StateManager.getCurrentTask());
        }
        if (StateManager.getCurrentNewTaskId() && window.LogsManager && window.LogsManager.viewNewLogs) {
            const taskName = document.getElementById('newLogTitle').textContent.replace('任务日志: ', '');
            window.LogsManager.viewNewLogs(StateManager.getCurrentNewTaskId(), taskName);
        }
        
        // 显示恢复连接的提示消息
        if (window.UIManager && window.UIManager.showMessage) {
            window.UIManager.showMessage('已恢复与服务器的连接', 'success');
        }
    }
}

// 健康检查函数
async function checkServerHealth() {
    // 如果用户已停止重连检测，则不再尝试
    if (!StateManager.getReconnectActive()) {
        if (StateManager.getHealthCheckInterval()) {
            clearInterval(StateManager.getHealthCheckInterval());
            StateManager.setHealthCheckInterval(null);
        }
        return;
    }
    
    try {
        // 使用一个轻量级的API端点来检查服务器状态
        const response = await fetch('/api/scheduler/tasks', {
            method: 'GET',
            headers: {
                'X-Health-Check': 'true' // 可选：添加一个标记，让后端知道这是健康检查
            }
        });
        
        if (response.ok) {
            // 服务器已恢复，停止健康检查定时器
            if (StateManager.getHealthCheckInterval()) {
                clearInterval(StateManager.getHealthCheckInterval());
                StateManager.setHealthCheckInterval(null);
            }
            
            // 调用成功处理函数
            handleApiSuccess();
        }
    } catch (error) {
        // 服务器仍然不可用，继续等待
        console.log("健康检查：服务器仍然不可用");
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

// 停止重连检测
function stopReconnect() {
    StateManager.setReconnectActive(false);
    if (StateManager.getHealthCheckInterval()) {
        clearInterval(StateManager.getHealthCheckInterval());
        StateManager.setHealthCheckInterval(null);
    }
    
    // 更新UI，移除旋转动画
    const spinner = document.querySelector('.reconnect-spinner');
    if (spinner) {
        spinner.style.animation = 'none';
        spinner.style.borderTop = '3px solid rgba(255, 255, 255, 0.3)';
    }
    
    // 更新按钮状态
    const stopBtn = document.getElementById('stop-reconnect-btn');
    if (stopBtn) {
        stopBtn.disabled = true;
        stopBtn.textContent = '已停止检测';
    }
    
    // 更新提示文本
    const statusText = document.querySelector('#server-status-indicator span');
    if (statusText) {
        statusText.textContent = '与服务器连接已断开，已停止自动检测，请联系管理人员。';
    }
}

// 导出API管理器
window.APIManager = {
    fetchApi,
    handleApiError,
    handleApiSuccess,
    checkServerHealth,
    stopReconnect
};