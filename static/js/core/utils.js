/**
 * 通用工具函数模块
 * 包含格式化、转义、状态处理等工具函数
 */

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

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 节流函数
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 验证任务ID
function isValidTaskId(taskId) {
    return taskId && taskId !== 'null' && taskId.trim() !== '';
}

// 导出工具函数
window.Utils = {
    formatTimestamp,
    escapeHtml,
    getStatusClass,
    getStatusText,
    debounce,
    throttle,
    isValidTaskId
};