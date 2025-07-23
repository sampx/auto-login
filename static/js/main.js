/**
 * 主入口文件 - 重构版本
 * 协调各个模块，处理页面初始化和全局事件
 */

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
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

    // 移除点击模态窗口外部关闭的功能
    // 只能通过关闭按钮或取消按钮关闭模态窗口
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

window.stopNewLogRefresh = LogsManager.stopNewLogRefresh;
window.startNewLogRefresh = LogsManager.startNewLogRefresh;

window.clearNewLog = LogsManager.clearNewLog;

window.validateCron = Scheduler.validateCron;
window.stopReconnect = APIManager.stopReconnect;

// 兼容性函数 - 保持HTML中的onclick调用正常工作
window.viewNewLogs = LogsManager.viewNewLogs;

// 确保所有模块都已加载
console.log('Task Manager - 重构版本已加载');