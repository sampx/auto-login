/**
 * 日志管理模块
 * 处理老版本和新版本的日志查看功能
 */

// 老版本日志功能
const LegacyLogs = {
    // 查看任务日志
    viewTaskLogs(taskId) {
        if (!Utils.isValidTaskId(taskId)) {
            console.warn('无效的任务ID:', taskId);
            return;
        }
        
        // 如果是同一个任务且定时器已在运行，则不操作
        if (StateManager.getCurrentTask() === taskId && StateManager.getLogRefreshInterval()) {
            return;
        }

        StateManager.setCurrentTask(taskId);
        const logTitle = document.getElementById('logTitle');
        if (logTitle) {
            logTitle.textContent = `任务日志 - ${taskId}`;
        }
        
        // 停止旧的定时器
        if (StateManager.getLogRefreshInterval()) {
            clearInterval(StateManager.getLogRefreshInterval());
            StateManager.setLogRefreshInterval(null);
        }

        // 立即加载一次日志
        this.loadTaskLogs(taskId, true);
        
        // 只有在服务器连接正常时才启动定时器
        if (StateManager.getServerConnected()) {
            // 启动新的定时器
            const interval = setInterval(() => {
                if (StateManager.getCurrentTask() === taskId) {
                    this.loadTaskLogs(taskId, false);
                }
            }, 2000);
            StateManager.setLogRefreshInterval(interval);
            UIManager.toggleLogRefresh(false, true);
        } else {
            // 服务器已断开连接，不启动定时器，确保旋转动画不显示
            UIManager.toggleLogRefresh(false, false);
        }
    },

    // 加载任务日志
    async loadTaskLogs(taskId, showLoadingIndicator = true) {
        if (!Utils.isValidTaskId(taskId)) {
            console.warn('无效的任务ID:', taskId);
            return;
        }
        
        const logViewerElement = document.getElementById('logViewer');
        if (!logViewerElement) return;
        
        if (showLoadingIndicator) {
            logViewerElement.innerHTML = '<div class="text-center"><div class="spinner"></div><p>加载中...</p></div>';
        }
        
        try {
            const data = await APIManager.fetchApi(`/api/tasks/${taskId}/logs?limit=100`, {}, `loadTaskLogs for ${taskId}`);
            if (showLoadingIndicator) {
                UIManager.hideLoading('logViewer');
            }
            this.renderLogs(data.logs);
        } catch (error) {
            if (showLoadingIndicator) {
                UIManager.hideLoading('logViewer');
            }
            logViewerElement.innerHTML = '<div class="log-placeholder"><p>加载日志失败</p></div>';
            UIManager.toggleLogRefresh(false, false); // 停止刷新动画和按钮
        }
    },

    // 渲染日志
    renderLogs(logs) {
        const logViewerElement = document.getElementById('logViewer');
        if (!logViewerElement) return;
        
        if (!logs || logs.length === 0) {
            logViewerElement.innerHTML = '<div class="log-placeholder"><p>没有可用的日志</p></div>';
            return;
        }
        
        let html = '<pre>';
        
        logs.forEach(log => {
            if (log.raw) {
                html += `${Utils.escapeHtml(log.raw)}\n`;
            } else {
                // 格式化时间戳
                const timestamp = Utils.formatTimestamp(log.timestamp);
                html += `${timestamp} ${log.level} ${Utils.escapeHtml(log.message)}\n`;
            }
        });
        
        html += '</pre>';
        logViewerElement.innerHTML = html;
        
        // 滚动到底部
        logViewerElement.scrollTop = logViewerElement.scrollHeight;
    },

    // 清空日志
    async clearLogs() {
        const currentTask = StateManager.getCurrentTask();
        if (!currentTask) return;
        
        // 显示加载中
        const logViewerElement = document.getElementById('logViewer');
        if (logViewerElement) {
            logViewerElement.innerHTML = '<div class="text-center"><div class="spinner"></div><p>正在清空日志...</p></div>';
        }
        
        try {
            const data = await APIManager.fetchApi(`/api/tasks/${currentTask}/logs/clear`, {
                method: 'POST'
            }, `clearLogs for ${currentTask}`);
            
            if (data.success) {
                UIManager.showMessage('日志已清空', 'success');
                if (logViewerElement) {
                    logViewerElement.innerHTML = '<div class="log-placeholder"><p>日志已清空，等待新日志...</p></div>';
                }
                
                // 重新启动日志刷新
                if (StateManager.getLogRefreshInterval()) {
                    clearInterval(StateManager.getLogRefreshInterval());
                }
                
                const interval = setInterval(() => {
                    const current = StateManager.getCurrentTask();
                    if (current) {
                        this.loadTaskLogs(current, false);
                    }
                }, 2000);
                StateManager.setLogRefreshInterval(interval);
            } else {
                UIManager.showMessage(data.message || '清空日志失败', 'danger');
                this.loadTaskLogs(currentTask); // 重新加载日志
            }
        } catch (error) {
            UIManager.showMessage('清空日志失败', 'danger');
            this.loadTaskLogs(currentTask); // 重新加载日志
        }
    },

    // 开始日志刷新
    startLogRefresh() {
        const currentTask = StateManager.getCurrentTask();
        if (currentTask) {
            this.viewTaskLogs(currentTask);
        }
    },

    // 停止日志刷新
    stopLogRefresh() {
        UIManager.toggleLogRefresh(false, false);
    }
};

// 新版本日志功能
const NewLogs = {
    // 查看新版日志
    async viewNewLogs(taskId, taskName) {
        if (!Utils.isValidTaskId(taskId)) {
            console.warn('无效的任务ID:', taskId);
            return;
        }
        
        // 如果是同一个任务且定时器已在运行，则不操作
        if (StateManager.getCurrentNewTaskId() === taskId && StateManager.getNewLogRefreshInterval()) {
            return;
        }

        StateManager.setCurrentNewTaskId(taskId);
        const newLogTitle = document.getElementById('newLogTitle');
        if (newLogTitle) {
            newLogTitle.textContent = `任务日志: ${taskName}`;
        }
        
        // 停止旧的定时器
        if (StateManager.getNewLogRefreshInterval()) {
            clearInterval(StateManager.getNewLogRefreshInterval());
            StateManager.setNewLogRefreshInterval(null);
        }

        // 重置当前日志文件路径
        StateManager.setCurrentLogFile(null);

        // 立即加载一次日志
        await this.loadNewTaskLogs(taskId, true);
        
        // 只有在服务器连接正常时才启动定时器
        if (StateManager.getServerConnected()) {
            // 启动新的定时器
            const interval = setInterval(() => {
                if (StateManager.getCurrentNewTaskId() === taskId) {
                    this.loadNewTaskLogs(taskId, false);
                }
            }, 2000);
            StateManager.setNewLogRefreshInterval(interval);
            UIManager.toggleLogRefresh(true, true);
        } else {
            // 服务器已断开连接，不启动定时器，确保旋转动画不显示
            UIManager.toggleLogRefresh(true, false);
        }
    },

    // 加载新版任务日志
    async loadNewTaskLogs(taskId, showLoadingIndicator = true) {
        if (!Utils.isValidTaskId(taskId)) {
            console.warn('无效的任务ID:', taskId);
            return;
        }
        
        const logViewer = document.getElementById('newLogViewer');
        if (!logViewer) return;
        
        if (showLoadingIndicator) {
            logViewer.innerHTML = '<div class="text-center"><div class="spinner"></div><p>加载中...</p></div>';
        }
        
        try {
            const result = await APIManager.fetchApi(`${StateManager.getNewApiBaseUrl()}/api/scheduler/tasks/${taskId}/logs`, {}, `loadNewTaskLogs for ${taskId}`);
            if (showLoadingIndicator) {
                UIManager.hideLoading('newLogViewer');
            }
            
            // 保存当前日志文件路径，用于后续刷新
            if (result.log_file) {
                StateManager.setCurrentLogFile(result.log_file);
                console.log(`已更新日志文件路径: ${result.log_file}`);
            }
            
            this.renderNewLogs(result.data);
        } catch (error) {
            if (showLoadingIndicator) {
                UIManager.hideLoading('newLogViewer');
            }
            logViewer.innerHTML = '<div class="log-placeholder"><p>加载日志失败</p></div>';
            // 停止日志刷新和旋转动画
            UIManager.toggleLogRefresh(true, false);
        }
    },

    // 渲染新版日志
    renderNewLogs(logs) {
        const logViewer = document.getElementById('newLogViewer');
        if (!logViewer) return;
        
        if (!logs || logs.length === 0) {
            logViewer.innerHTML = '<div class="log-placeholder">暂无日志</div>';
            return;
        }

        const html = logs.map(log => `
            <div class="log-line ${log.content.includes('ERROR') ? 'error' : log.content.includes('WARNING') ? 'warning' : ''}">
                <span class="log-line-number">${log.line}</span>
                <span class="log-line-content">${Utils.escapeHtml(log.content)}</span>
            </div>
        `).join('');

        logViewer.innerHTML = html;
        logViewer.scrollTop = logViewer.scrollHeight;
    },

    // 刷新新版日志
    refreshNewLog() {
        const currentNewTaskId = StateManager.getCurrentNewTaskId();
        if (currentNewTaskId) {
            this.loadNewTaskLogs(currentNewTaskId, true);
            UIManager.showNewMessage('日志已刷新', 'info');
        } else {
            UIManager.showNewMessage('请先选择一个任务', 'warning');
        }
    },

    // 清空新版任务日志
    async clearNewLog() {
        const currentNewTaskId = StateManager.getCurrentNewTaskId();
        if (!currentNewTaskId) {
            UIManager.showNewMessage('请先选择一个任务', 'warning');
            return;
        }
        
        if (!confirm(`确定要清空任务 ${currentNewTaskId} 的日志吗？`)) {
            return;
        }
        
        // 显示加载中
        const newLogViewer = document.getElementById('newLogViewer');
        if (newLogViewer) {
            newLogViewer.innerHTML = '<div class="text-center"><div class="spinner"></div><p>正在清空日志...</p></div>';
        }
        
        try {
            // 获取最新的任务信息，确保使用正确的日志文件路径
            const taskInfo = await APIManager.fetchApi(`${StateManager.getNewApiBaseUrl()}/api/scheduler/tasks/${currentNewTaskId}`, {}, `getTaskInfo for ${currentNewTaskId}`);
            
            if (!taskInfo.success) {
                UIManager.showNewMessage('获取任务信息失败', 'error');
                return;
            }
            
            const result = await APIManager.fetchApi(`${StateManager.getNewApiBaseUrl()}/api/scheduler/tasks/${currentNewTaskId}/logs/clear`, {
                method: 'POST'
            }, `clearNewLog for ${currentNewTaskId}`);
            
            if (result.success) {
                UIManager.showNewMessage('日志已清空', 'success');
                if (newLogViewer) {
                    newLogViewer.innerHTML = '<div class="log-placeholder"><p>日志已清空，等待新日志...</p></div>';
                }
                
                // 重新启动日志刷新
                if (StateManager.getNewLogRefreshInterval()) {
                    clearInterval(StateManager.getNewLogRefreshInterval());
                }
                
                const interval = setInterval(() => {
                    const current = StateManager.getCurrentNewTaskId();
                    if (current) {
                        this.loadNewTaskLogs(current, false);
                    }
                }, 2000);
                StateManager.setNewLogRefreshInterval(interval);
            } else {
                UIManager.showNewMessage(`清空日志失败: ${result.message}`, 'error');
                this.loadNewTaskLogs(currentNewTaskId); // 重新加载日志
            }
        } catch (error) {
            UIManager.showNewMessage(`清空日志失败: 网络错误`, 'error');
            this.loadNewTaskLogs(currentNewTaskId); // 重新加载日志
        }
    },

    // 开始新版日志刷新
    startNewLogRefresh() {
        const currentNewTaskId = StateManager.getCurrentNewTaskId();
        if (currentNewTaskId) {
            const taskName = document.getElementById('newLogTitle').textContent.replace('任务日志: ', '');
            this.viewNewLogs(currentNewTaskId, taskName);
        }
    },

    // 停止新版日志刷新
    stopNewLogRefresh() {
        UIManager.toggleLogRefresh(true, false);
    }
};

// 导出日志管理器
window.LogsManager = {
    // 老版本日志功能
    viewTaskLogs: LegacyLogs.viewTaskLogs.bind(LegacyLogs),
    loadTaskLogs: LegacyLogs.loadTaskLogs.bind(LegacyLogs),
    renderLogs: LegacyLogs.renderLogs.bind(LegacyLogs),
    clearLogs: LegacyLogs.clearLogs.bind(LegacyLogs),
    startLogRefresh: LegacyLogs.startLogRefresh.bind(LegacyLogs),
    stopLogRefresh: LegacyLogs.stopLogRefresh.bind(LegacyLogs),
    
    // 新版本日志功能
    viewNewLogs: NewLogs.viewNewLogs.bind(NewLogs),
    loadNewTaskLogs: NewLogs.loadNewTaskLogs.bind(NewLogs),
    renderNewLogs: NewLogs.renderNewLogs.bind(NewLogs),
    refreshNewLog: NewLogs.refreshNewLog.bind(NewLogs),
    clearNewLog: NewLogs.clearNewLog.bind(NewLogs),
    startNewLogRefresh: NewLogs.startNewLogRefresh.bind(NewLogs),
    stopNewLogRefresh: NewLogs.stopNewLogRefresh.bind(NewLogs)
};