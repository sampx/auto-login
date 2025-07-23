// 健康检查定时器
let healthCheckInterval = null;
let reconnectActive = true;

// 停止重连检测
function stopReconnect() {
    reconnectActive = false;
    if (healthCheckInterval) {
        clearInterval(healthCheckInterval);
        healthCheckInterval = null;
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

// 修改handleApiError函数，添加健康检查定时器
function handleApiError(error, context) {
    console.error(`API Error (${context}):`, error);
    if (serverConnected) {
        serverConnected = false;
        reconnectActive = true;
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
        
        // 添加：启动健康检查定时器
        if (!healthCheckInterval) {
            healthCheckInterval = setInterval(checkServerHealth, 5000); // 每5秒检查一次
        }
    }
}

// 添加健康检查函数
async function checkServerHealth() {
    // 如果用户已停止重连检测，则不再尝试
    if (!reconnectActive) {
        if (healthCheckInterval) {
            clearInterval(healthCheckInterval);
            healthCheckInterval = null;
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
            if (healthCheckInterval) {
                clearInterval(healthCheckInterval);
                healthCheckInterval = null;
            }
            
            // 调用成功处理函数
            handleApiSuccess();
        }
    } catch (error) {
        // 服务器仍然不可用，继续等待
        console.log("健康检查：服务器仍然不可用");
    }
}

// 改进的API成功处理函数
function handleApiSuccess() {
    if (!serverConnected) {
        serverConnected = true;
        
        // 停止健康检查定时器
        if (healthCheckInterval) {
            clearInterval(healthCheckInterval);
            healthCheckInterval = null;
        }
        
        // 隐藏断开连接提示
        const indicator = document.getElementById('server-status-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
        
        // 重新启动状态刷新定时器
        if (!statusRefreshInterval) {
            statusRefreshInterval = setInterval(refreshTaskStatus, 5000);
        }
        
        // 自动刷新任务列表
        loadTasks();  // 刷新老版本任务列表
        loadNewTasks();  // 刷新新版任务列表
        
        // 如果当前有选中的任务，重新启动日志刷新
        if (currentTask) {
            viewTaskLogs(currentTask);
        }
        if (currentNewTaskId) {
            viewNewLogs(currentNewTaskId, document.getElementById('newLogTitle').textContent.replace('任务日志: ', ''));
        }
        
        // 显示恢复连接的提示消息
        showMessage('已恢复与服务器的连接', 'success');
    }
}

// 扩展页面卸载前清理
const originalBeforeUnload = window.onbeforeunload;
window.addEventListener('beforeunload', function(event) {
    // 调用原始的beforeunload处理程序（如果存在）
    if (typeof originalBeforeUnload === 'function') {
        originalBeforeUnload(event);
    }
    
    // 清理健康检查定时器
    if (healthCheckInterval) {
        clearInterval(healthCheckInterval);
    }
});