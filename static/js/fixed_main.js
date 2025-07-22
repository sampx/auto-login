// 编辑任务表单提交处理
function setupEditTaskFormHandler() {
    const editTaskForm = document.getElementById('editTaskForm');
    if (!editTaskForm) return;
    
    // 移除所有现有的事件监听器
    const newEditTaskForm = editTaskForm.cloneNode(true);
    editTaskForm.parentNode.replaceChild(newEditTaskForm, editTaskForm);
    
    // 添加新的事件监听器
    newEditTaskForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const form = e.target;
        const taskId = form.task_id.value;
        
        // 获取原始任务数据，以保留未在表单中显示的字段
        try {
            const response = await fetchApi(`${NEW_API_BASE_URL}/api/scheduler/tasks/${taskId}`, {}, `getOriginalTask for ${taskId}`);
            if (!response.success) {
                const errorMessageDiv = document.getElementById('editTaskErrorMessage');
                errorMessageDiv.textContent = `获取原始任务数据失败: ${response.message}`;
                return;
            }
            
            const originalTask = response.data;
            
            // 创建更新数据，只更新表单中的字段，保留其他字段的原始值
            const taskData = {
                task_id: taskId,
                task_name: form.task_name.value,
                task_schedule: form.task_schedule.value,
                task_exec: form.task_exec.value,
                task_desc: form.task_desc.value,
                task_enabled: form.task_enabled.value === 'true',
                task_timeout: parseInt(form.task_timeout.value),
                task_retry: parseInt(form.task_retry.value),
                task_retry_interval: parseInt(form.task_retry_interval.value),
                task_log: form.task_log.value,
                // 保留原始值
                task_env: originalTask.task_env || {},
                task_dependencies: originalTask.task_dependencies || [],
                task_notify: originalTask.task_notify || {}
            };
            
            // 添加唯一请求ID，防止重复提交
            const requestId = `edit_${taskId}_${Date.now()}`;
            const headers = {
                'Content-Type': 'application/json',
                'X-Request-ID': requestId
            };
            
            // 发送更新请求
            const result = await fetchApi(`${NEW_API_BASE_URL}/api/scheduler/tasks/${taskId}`, {
                method: 'PUT',
                headers: headers,
                body: JSON.stringify(taskData)
            }, `updateTask for ${taskId}`);
            
            if (result.success) {
                showNewMessage('任务更新成功!', 'success');
                closeEditModal();
                loadNewTasks(false); // 静默刷新任务列表
            } else {
                const errorMessageDiv = document.getElementById('editTaskErrorMessage');
                errorMessageDiv.textContent = `更新失败: ${result.message}`;
            }
        } catch (error) {
            const errorMessageDiv = document.getElementById('editTaskErrorMessage');
            errorMessageDiv.textContent = `更新失败: ${error.message}`;
        }
    });
}

// 在页面加载完成后设置事件处理器
document.addEventListener('DOMContentLoaded', function() {
    setupEditTaskFormHandler();
});

// 打开编辑任务模态窗口
async function openEditModal(taskId) {
    const modal = document.getElementById('editTaskModal');
    const form = document.getElementById('editTaskForm');
    const errorMessageDiv = document.getElementById('editTaskErrorMessage');
    errorMessageDiv.textContent = ''; // 清除之前的错误信息
    
    try {
        const response = await fetchApi(`${NEW_API_BASE_URL}/api/scheduler/tasks/${taskId}`, {}, `openEditModal for ${taskId}`);
        if (!response.success) {
            showNewMessage(`错误: ${response.message}`, 'error');
            return;
        }
        
        const task = response.data;
        
        // 填充表单的所有字段，确保不遗漏任何配置
        form.task_id.value = task.task_id;
        form.task_name.value = task.task_name;
        form.task_schedule.value = task.task_schedule;
        form.task_exec.value = task.task_exec;
        form.task_desc.value = task.task_desc || '';
        
        // 填充高级配置字段
        form.task_timeout.value = task.task_timeout || 300;
        form.task_retry.value = task.task_retry || 0;
        form.task_retry_interval.value = task.task_retry_interval || 60;
        form.task_log.value = task.task_log || `logs/task_${task.task_id}.log`;
        
        // 保存当前的启用状态，但不在表单中显示
        form.task_enabled.value = task.task_enabled.toString();
        
        document.getElementById('editModalTitle').innerText = `编辑任务: ${task.task_name}`;
        modal.style.display = 'block';
    } catch (error) {
        showNewMessage(`网络错误: ${error.message}`, 'error');
    }
}

// 关闭编辑任务模态窗口
function closeEditModal() {
    document.getElementById('editTaskModal').style.display = 'none';
}