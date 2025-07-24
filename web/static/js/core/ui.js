/**
 * UI操作和消息显示模块
 * 统一处理所有UI相关操作
 */

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

// 显示新版消息
function showNewMessage(message, type = 'info') {
    const container = document.getElementById('new-message-container');
    if (!container) return;
    
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${type}`;
    alertElement.textContent = message;
    
    // 清空旧消息，避免显示多条相同的通知
    container.innerHTML = '';
    container.appendChild(alertElement);
    
    // 5秒后自动移除
    setTimeout(() => {
        if (alertElement.parentNode) {
            alertElement.remove();
        }
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
            if (alertElement.parentNode) {
                alertElement.remove();
            }
        }, 5000);
    }
}

// 显示成功消息
function showSuccess(elementId, message) {
    const alertElement = document.createElement('div');
    alertElement.className = 'alert alert-success';
    alertElement.textContent = message;
    
    const element = document.getElementById(elementId);
    if (element) {
        element.prepend(alertElement);
        
        // 5秒后自动移除
        setTimeout(() => {
            if (alertElement.parentNode) {
                alertElement.remove();
            }
        }, 5000);
    }
}

// 模态窗口管理
const ModalManager = {
    // 显示创建任务模态窗口
    showCreateTaskModal() {
        const modal = document.getElementById('createTaskModal');
        if (modal) {
            modal.style.display = 'block';
        }
    },

    // 关闭创建任务模态窗口
    closeCreateTaskModal() {
        const modal = document.getElementById('createTaskModal');
        const form = document.getElementById('createNewTaskForm');
        if (modal) {
            modal.style.display = 'none';
        }
        if (form) {
            form.reset();
        }
    },

    // 显示编辑任务模态窗口
    showEditModal() {
        const modal = document.getElementById('editTaskModal');
        if (modal) {
            modal.style.display = 'block';
        }
    },

    // 关闭编辑任务模态窗口
    closeEditModal() {
        const modal = document.getElementById('editTaskModal');
        if (modal) {
            modal.style.display = 'none';
        }
    },

    // 显示任务详情模态窗口
    showTaskDetailsModal() {
        const modal = document.getElementById('taskDetailsModal');
        if (modal) {
            modal.style.display = 'block';
        }
    },

    // 关闭任务详情模态窗口
    closeTaskDetailsModal() {
        const modal = document.getElementById('taskDetailsModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }
};

// 日志刷新控制
function toggleLogRefresh(isNew, start) {
    const spinner = document.getElementById(isNew ? 'new-log-refresh-spinner' : 'log-refresh-spinner');
    const stopBtn = document.getElementById(isNew ? 'stop-new-log-refresh-btn' : 'stop-log-refresh-btn');
    const startBtn = document.getElementById(isNew ? 'start-new-log-refresh-btn' : 'start-log-refresh-btn');
    
    if (start) {
        if (spinner) spinner.style.display = 'inline-block';
        if (stopBtn) stopBtn.style.display = 'inline-block';
        if (startBtn) startBtn.style.display = 'none';
    } else {
        const interval = isNew ? StateManager.getNewLogRefreshInterval() : StateManager.getLogRefreshInterval();
        if (interval) {
            clearInterval(interval);
            if (isNew) {
                StateManager.setNewLogRefreshInterval(null);
            } else {
                StateManager.setLogRefreshInterval(null);
            }
        }
        if (spinner) spinner.style.display = 'none';
        if (stopBtn) stopBtn.style.display = 'none';
        if (startBtn) startBtn.style.display = 'inline-block';
    }
}

// 导出UI管理器
window.UIManager = {
    showLoading,
    hideLoading,
    showNewMessage,
    showError,
    showSuccess,
    toggleLogRefresh,
    ModalManager
};