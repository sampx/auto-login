/**
 * 主入口文件 - 重构版本
 * 协调各个模块，处理页面初始化和全局事件
 */

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化标签页
    UIManager.TabManager.initTabs();
    
    // 加载老版本任务列表和配置
    LegacyTasks.loadTasks();
    LegacyTasks.loadConfig();
    
    // 设置定时刷新任务状态
    const statusInterval = setInterval(() => {
        LegacyTasks.refreshTaskStatus();
    }, 5000);
    StateManager.setStatusRefreshInterval(statusInterval);
    
    // 绑定配置表单提交事件
    const configForm = document.getElementById('configForm');
    if (configForm) {
        configForm.addEventListener('submit', function(e) {
            e.preventDefault();
            LegacyTasks.saveConfig();
        });
    }
    
    // 新版功能初始化
    Scheduler.loadNewTasks();

    // 为新任务表单绑定提交事件
    const createNewTaskForm = document.getElementById('createNewTaskForm');
    if (createNewTaskForm) {
        createNewTaskForm.addEventListener('submit', Scheduler.createNewTask.bind(Scheduler));
    }

    // 编辑任务表单提交事件
    const editTaskForm = document.getElementById('editTaskForm');
    if (editTaskForm) {
        editTaskForm.addEventListener('submit', Scheduler.updateTask.bind(Scheduler));
    }

    // 点击模态窗口外部关闭
    window.onclick = function(event) {
        const createTaskModal = document.getElementById('createTaskModal');
        const editTaskModal = document.getElementById('editTaskModal');
        const taskDetailsModal = document.getElementById('taskDetailsModal');

        if (event.target == createTaskModal) {
            UIManager.ModalManager.closeCreateTaskModal();
        }
        if (event.target == editTaskModal) {
            UIManager.ModalManager.closeEditModal();
        }
        if (event.target == taskDetailsModal) {
            UIManager.ModalManager.closeTaskDetailsModal();
        }
    }
});

// 标签页切换时初始化对应内容
document.addEventListener('tabChanged', function(e) {
    if (e.detail.target === 'new-scheduler') {
        Scheduler.loadNewTasks();
    }
});

// 页面卸载前清理
window.addEventListener('beforeunload', function(event) {
    // 清理所有定时器
    StateManager.clearAllIntervals();
});

// 全局函数导出（保持向后兼容）
window.showCreateTaskModal = UIManager.ModalManager.showCreateTaskModal;
window.closeCreateTaskModal = UIManager.ModalManager.closeCreateTaskModal;
window.closeEditModal = UIManager.ModalManager.closeEditModal;
window.closeTaskDetailsModal = UIManager.ModalManager.closeTaskDetailsModal;

window.stopLogRefresh = LogsManager.stopLogRefresh;
window.startLogRefresh = LogsManager.startLogRefresh;
window.stopNewLogRefresh = LogsManager.stopNewLogRefresh;
window.startNewLogRefresh = LogsManager.startNewLogRefresh;

window.clearLogs = LogsManager.clearLogs;
window.clearNewLog = LogsManager.clearNewLog;

window.validateCron = Scheduler.validateCron;
window.stopReconnect = APIManager.stopReconnect;

// 兼容性函数 - 保持HTML中的onclick调用正常工作
window.viewTaskLogs = LogsManager.viewTaskLogs;
window.viewNewLogs = LogsManager.viewNewLogs;

// 确保所有模块都已加载
console.log('Task Manager - 重构版本已加载');