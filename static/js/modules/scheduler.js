/**
 * 新版任务调度器模块
 * 处理新版本的任务管理功能
 */

const Scheduler = {
    // 加载新版任务列表
    async loadNewTasks(showLoading = true) {
        const taskList = document.getElementById('newTaskList');
        if (!taskList) return;
        
        if (showLoading) {
            taskList.innerHTML = `
                <div class="text-center">
                    <div class="spinner"></div>
                    <p>加载中...</p>
                </div>
            `;
        }

        try {
            const result = await APIManager.fetchApi(`${StateManager.getNewApiBaseUrl()}/api/scheduler/tasks`, {}, 'loadNewTasks');
            if (result.success) {
                this.renderNewTaskList(result.data);
            } else {
                if (showLoading) {
                    taskList.innerHTML = `<div class="text-center text-danger">加载失败: ${result.message}</div>`;
                }
            }
        } catch (error) {
            if (showLoading) {
                taskList.innerHTML = `<div class="text-center text-danger">网络错误，无法加载任务列表。</div>`;
            }
        }
    },

    // 渲染新版任务列表
    renderNewTaskList(tasks) {
        const taskList = document.getElementById('newTaskList');
        if (!taskList) return;
        
        if (tasks.length === 0) {
            taskList.innerHTML = '<div class="text-center text-muted">暂无任务</div>';
            return;
        }

        const html = tasks.map(task => {
            const isEnabled = task.task_enabled;
            const statusClass = isEnabled ? 'task-enabled' : 'task-disabled';

            return `
            <div class="new-task-item ${statusClass}">
                <div class="task-info-container" onclick="LogsManager.viewNewLogs('${task.task_id}', '${task.task_name}')">
                    <div class="task-primary-info">
                        <div class="task-name" title="${task.task_name}">${task.task_name}</div>
                        <div class="task-schedule-cron">${task.task_schedule}</div>
                    </div>
                    <div class="task-description-small" title="${task.task_desc || '无描述'}">${task.task_desc || '无描述'}</div>
                    <div class="task-next-run">
                        <strong>下次执行:</strong> ${task.next_run_time ? new Date(task.next_run_time).toLocaleString() : 'N/A'}
                    </div>
                </div>
                <div class="task-actions-panel" onclick="event.stopPropagation();">
                    <button class="btn btn-sm btn-success" onclick="window.Scheduler.executeNewTask('${task.task_id}')">运行一次</button>
                    ${isEnabled
                        ? `<button class="btn btn-sm btn-warning" onclick="window.Scheduler.toggleNewTask('${task.task_id}', false)">禁用</button>`
                        : `<button class="btn btn-sm btn-success" onclick="window.Scheduler.toggleNewTask('${task.task_id}', true)">启用</button>`
                    }
                    <button class="btn btn-sm btn-secondary" onclick="window.Scheduler.showTaskDetails('${task.task_id}')">详情</button>
                    <button class="btn btn-sm btn-warning" onclick="window.Scheduler.openEditModal('${task.task_id}')">编辑</button>
                    <button class="btn btn-sm btn-danger" onclick="window.Scheduler.deleteNewTask('${task.task_id}')">删除</button>
                </div>
            </div>
        `}).join('');

        taskList.innerHTML = html;
    },

    // 创建新版任务
    async createNewTask(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const task = {
            task_id: formData.get('task_id'),
            task_name: formData.get('task_name'),
            task_desc: formData.get('task_desc') || '',
            task_exec: formData.get('task_exec'),
            task_schedule: formData.get('task_schedule'),
            task_timeout: parseInt(formData.get('task_timeout')) || 300,
            task_retry: parseInt(formData.get('task_retry')) || 0,
            task_retry_interval: 60,
            task_enabled: formData.get('task_enabled') === 'true',
            task_log: formData.get('task_log') || `logs/task_${formData.get('task_id')}.log`,
            task_env: {},
            task_dependencies: [],
            task_notify: {}
        };

        try {
            const result = await APIManager.fetchApi(`${StateManager.getNewApiBaseUrl()}/api/scheduler/tasks`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(task)
            }, 'createNewTask');
            
            if (result.success) {
                UIManager.showNewMessage('任务创建成功', 'success');
                UIManager.ModalManager.closeCreateTaskModal();
                // 静默刷新任务列表，不显示额外通知
                await this.loadNewTasks(false);
            } else {
                // 显示错误消息
                const errorMessageDiv = document.getElementById('createTaskErrorMessage');
                if (errorMessageDiv) {
                    errorMessageDiv.textContent = `创建失败: ${result.message}`;
                } else {
                    UIManager.showNewMessage(`创建失败: ${result.message}`, 'error');
                }
            }
        } catch (error) {
            // 显示错误消息
            const errorMessageDiv = document.getElementById('createTaskErrorMessage');
            if (errorMessageDiv) {
                errorMessageDiv.textContent = `创建失败: 网络错误`;
            } else {
                UIManager.showNewMessage(`创建失败: 网络错误`, 'error');
            }
        }
    },

    // 执行新版任务
    async executeNewTask(taskId) {
        try {
            const result = await APIManager.fetchApi(`${StateManager.getNewApiBaseUrl()}/api/scheduler/tasks/${taskId}/run-once`, {
                method: 'POST'
            }, `executeNewTask for ${taskId}`);
            
            if (result.success) {
                UIManager.showNewMessage(`任务 ${taskId} 开始执行`, 'success');
                // 自动查看该任务的日志
                const taskElement = document.querySelector(`.new-task-item .task-name[title='${taskId}']`);
                const taskName = taskElement ? taskElement.innerText : taskId;
                setTimeout(() => {
                    LogsManager.viewNewLogs(taskId, taskName);
                }, 500); // 延迟500ms等待日志写入
            } else {
                UIManager.showNewMessage(`执行失败: ${result.message}`, 'error');
            }
        } catch (error) {
            UIManager.showNewMessage(`执行失败: 网络错误`, 'error');
        }
    },

    // 删除新版任务
    async deleteNewTask(taskId) {
        if (!confirm(`确定要删除任务 ${taskId} 吗？`)) {
            return;
        }

        try {
            const result = await APIManager.fetchApi(`${StateManager.getNewApiBaseUrl()}/api/scheduler/tasks/${taskId}`, {
                method: 'DELETE'
            }, `deleteNewTask for ${taskId}`);
            
            if (result.success) {
                UIManager.showNewMessage('任务删除成功', 'success');
                this.loadNewTasks();
                if (StateManager.getCurrentNewTaskId() === taskId) {
                    // 清理定时器
                    if (StateManager.getNewLogRefreshInterval()) {
                        clearInterval(StateManager.getNewLogRefreshInterval());
                        StateManager.setNewLogRefreshInterval(null);
                    }
                    const newLogViewer = document.getElementById('newLogViewer');
                    if (newLogViewer) {
                        newLogViewer.innerHTML = '<div class="log-placeholder">请选择一个任务查看日志</div>';
                    }
                    StateManager.setCurrentNewTaskId(null);
                }
            } else {
                UIManager.showNewMessage(`删除失败: ${result.message}`, 'error');
            }
        } catch (error) {
            UIManager.showNewMessage(`删除失败: 网络错误`, 'error');
        }
    },

    // 启用/禁用新版任务
    async toggleNewTask(taskId, enabled) {
        if (!confirm(`确定要${enabled ? '启用' : '禁用'}任务 ${taskId} 吗？`)) {
            return;
        }

        try {
            const result = await APIManager.fetchApi(`${StateManager.getNewApiBaseUrl()}/api/scheduler/tasks/${taskId}/toggle`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ enabled: enabled })
            }, `toggleNewTask for ${taskId}`);
            
            if (result.success) {
                UIManager.showNewMessage(`任务 ${taskId} 已${enabled ? '启用' : '禁用'}`, 'success');
                this.loadNewTasks(); // 重新加载任务列表
            } else {
                UIManager.showNewMessage(`操作失败: ${result.message}`, 'error');
            }
        } catch (error) {
            UIManager.showNewMessage(`操作失败: 网络错误`, 'error');
        }
    },

    // 验证CRON表达式
    async validateCron() {
        const expression = document.getElementById('cronExpression').value.trim();
        const resultDiv = document.getElementById('cronResult');
        
        if (!expression) {
            resultDiv.innerHTML = '<span class="text-danger">请输入CRON表达式</span>';
            return;
        }

        try {
            const result = await APIManager.fetchApi(`${StateManager.getNewApiBaseUrl()}/api/scheduler/validate-cron`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ cron: expression })
            }, 'validateCron');
            
            if (result.data.valid) {
                const nextRun = new Date(result.data.next_run);
                resultDiv.innerHTML = `
                    <span class="text-success">✅ 有效</span><br>
                    <small>下次执行时间: ${nextRun.toLocaleString()}</small>
                `;
            } else {
                resultDiv.innerHTML = `
                    <span class="text-danger">❌ 无效</span><br>
                    <small>${result.data.error}</small>
                `;
            }
        } catch (error) {
            resultDiv.innerHTML = `<span class="text-danger">验证失败: 网络错误</span>`;
        }
    },

    // 显示任务详情
    async showTaskDetails(taskId) {
        try {
            const result = await APIManager.fetchApi(`${StateManager.getNewApiBaseUrl()}/api/scheduler/tasks/${taskId}`, {}, `showTaskDetails for ${taskId}`);
            
            if (result.success) {
                const task = result.data;
                const content = document.getElementById('taskDetailsContent');
                
                if (content) {
                    content.innerHTML = `
                        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
                            <div style="margin-bottom: 15px;">
                                <strong style="color: #333;">任务名称:</strong>
                                <div style="margin-top: 5px; padding: 8px; background: #f8f9fa; border-radius: 3px;">${task.task_name}</div>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <strong style="color: #333;">任务ID:</strong>
                                <div style="margin-top: 5px; padding: 8px; background: #f8f9fa; border-radius: 3px; font-family: monospace;">${task.task_id}</div>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <strong style="color: #333;">任务描述:</strong>
                                <div style="margin-top: 5px; padding: 8px; background: #f8f9fa; border-radius: 3px;">${task.task_desc || '无描述'}</div>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <strong style="color: #333;">执行命令:</strong>
                                <div style="margin-top: 5px; padding: 8px; background: #f8f9fa; border-radius: 3px; font-family: monospace; font-size: 13px;">${task.task_exec}</div>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <strong style="color: #333;">调度表达式:</strong>
                                <div style="margin-top: 5px; padding: 8px; background: #f8f9fa; border-radius: 3px; font-family: monospace;">${task.task_schedule}</div>
                            </div>
                            
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                                <div>
                                    <strong style="color: #333;">超时时间:</strong>
                                    <div style="margin-top: 5px; padding: 8px; background: #f8f9fa; border-radius: 3px;">${task.task_timeout} 秒</div>
                                </div>
                                <div>
                                    <strong style="color: #333;">重试次数:</strong>
                                    <div style="margin-top: 5px; padding: 8px; background: #f8f9fa; border-radius: 3px;">${task.task_retry} 次</div>
                                </div>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <strong style="color: #333;">日志文件:</strong>
                                <div style="margin-top: 5px; padding: 8px; background: #f8f9fa; border-radius: 3px; font-family: monospace;">${task.task_log}</div>
                            </div>
                            
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                                <div>
                                    <strong style="color: #333;">启用状态:</strong>
                                    <div style="margin-top: 5px; padding: 8px; background: #f8f9fa; border-radius: 3px;">
                                        <span style="color: ${task.task_enabled ? '#28a745' : '#dc3545'};">
                                            ${task.task_enabled ? '启用' : '禁用'}
                                        </span>
                                    </div>
                                </div>
                                <div>
                                    <strong style="color: #333;">下次执行:</strong>
                                    <div style="margin-top: 5px; padding: 8px; background: #f8f9fa; border-radius: 3px;">
                                        ${task.next_run_time ? new Date(task.next_run_time).toLocaleString() : '未安排'}
                                    </div>
                                </div>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <strong style="color: #333;">创建时间:</strong>
                                <div style="margin-top: 5px; padding: 8px; background: #f8f9fa; border-radius: 3px;">${new Date(task.created_at).toLocaleString()}</div>
                            </div>
                            
                            ${task.last_run_time ? `
                            <div style="margin-bottom: 15px;">
                                <strong style="color: #333;">上次执行:</strong>
                                <div style="margin-top: 5px; padding: 8px; background: #f8f9fa; border-radius: 3px;">${new Date(task.last_run_time).toLocaleString()}</div>
                            </div>
                            ` : ''}
                        </div>
                    `;
                }
                
                UIManager.ModalManager.showTaskDetailsModal();
            } else {
                UIManager.showNewMessage(`获取任务详情失败: ${result.message}`, 'error');
            }
        } catch (error) {
            UIManager.showNewMessage(`获取任务详情失败: 网络错误`, 'error');
        }
    },

    // 打开编辑模态窗口
    async openEditModal(taskId) {
        const modal = document.getElementById('editTaskModal');
        const form = document.getElementById('editTaskForm');
        const errorMessageDiv = document.getElementById('editTaskErrorMessage');
        
        if (errorMessageDiv) {
            errorMessageDiv.textContent = ''; // 清除之前的错误信息
        }
        
        try {
            const response = await APIManager.fetchApi(`${StateManager.getNewApiBaseUrl()}/api/scheduler/tasks/${taskId}`, {}, `openEditModal for ${taskId}`);
            if (!response.success) {
                UIManager.showNewMessage(`错误: ${response.message}`, 'error');
                return;
            }
            
            const task = response.data;
            
            if (form) {
                // 填充表单的所有字段，确保不遗漏任何配置
                const fields = {
                    'task_id': task.task_id,
                    'task_name': task.task_name,
                    'task_schedule': task.task_schedule,
                    'task_exec': task.task_exec,
                    'task_desc': task.task_desc || '',
                    'task_timeout': task.task_timeout || 300,
                    'task_retry': task.task_retry || 0,
                    'task_retry_interval': task.task_retry_interval || 60,
                    'task_log': task.task_log || `logs/task_${task.task_id}.log`,
                    'task_enabled': task.task_enabled.toString()
                };
                
                for (const [fieldName, value] of Object.entries(fields)) {
                    const field = form[fieldName];
                    if (field) {
                        field.value = value;
                    }
                }
            }
            
            const editModalTitle = document.getElementById('editModalTitle');
            if (editModalTitle) {
                editModalTitle.innerText = `编辑任务: ${task.task_name}`;
            }
            
            UIManager.ModalManager.showEditModal();
        } catch (error) {
            UIManager.showNewMessage(`网络错误: ${error.message}`, 'error');
        }
    },

    // 更新任务
    async updateTask(e) {
        e.preventDefault();
        const form = e.target;
        const taskId = form.task_id.value;
        
        // 获取原始任务数据，以保留未在表单中显示的字段
        try {
            const response = await APIManager.fetchApi(`${StateManager.getNewApiBaseUrl()}/api/scheduler/tasks/${taskId}`, {}, `getOriginalTask for ${taskId}`);
            if (!response.success) {
                const errorMessageDiv = document.getElementById('editTaskErrorMessage');
                if (errorMessageDiv) {
                    errorMessageDiv.textContent = `获取原始任务数据失败: ${response.message}`;
                }
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
            const result = await APIManager.fetchApi(`${StateManager.getNewApiBaseUrl()}/api/scheduler/tasks/${taskId}`, {
                method: 'PUT',
                headers: headers,
                body: JSON.stringify(taskData)
            }, `updateTask for ${taskId}`);
            
            if (result.success) {
                UIManager.showNewMessage('任务更新成功!', 'success');
                UIManager.ModalManager.closeEditModal();
                this.loadNewTasks(false); // 静默刷新任务列表
            } else {
                const errorMessageDiv = document.getElementById('editTaskErrorMessage');
                if (errorMessageDiv) {
                    errorMessageDiv.textContent = `更新失败: ${result.message}`;
                }
            }
        } catch (error) {
            const errorMessageDiv = document.getElementById('editTaskErrorMessage');
            if (errorMessageDiv) {
                errorMessageDiv.textContent = `更新失败: ${error.message}`;
            }
        }
    }
};

// 导出新版调度器
window.Scheduler = Scheduler;