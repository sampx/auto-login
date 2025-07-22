def update_task(self, task: Task) -> bool:
    """更新任务"""
    if task.task_id not in self.tasks:
        return False
    try:
        original_task = self.tasks[task.task_id]
        
        # 检查任务是否有变更
        has_changes = not (task == original_task)
        
        if not has_changes:
            self.logger.info(f"任务 {task.task_id} 无任何变更，跳过更新")
            return True
        
        self.logger.info(f"任务 {task.task_id} 配置发生变更，开始更新...")
        
        # 检查日志文件路径是否变更
        if task.task_log != original_task.task_log and os.path.exists(original_task.task_log):
            try:
                # 如果旧日志文件存在且与新日志文件不同，则删除旧日志文件
                os.remove(original_task.task_log)
                self.logger.info(f"已删除任务 {task.task_id} 的旧日志文件: {original_task.task_log}")
            except Exception as e:
                self.logger.warning(f"删除任务 {task.task_id} 的旧日志文件失败: {e}")
        
        # 停止该任务的调度计划
        if self.scheduler.get_job(task.task_id):
            self.scheduler.remove_job(task.task_id)
            self.logger.info(f"已从调度器中移除任务 {task.task_id} 的调度计划")
        else:
            self.logger.info(f"任务 {task.task_id} 当前没有活动的调度计划")
        
        # 停止该任务的所有正在执行的进程
        stopped_count = self.task_executor.stop_all_tasks_by_id(task.task_id)
        if stopped_count > 0:
            self.logger.info(f"已终止任务 {task.task_id} 的 {stopped_count} 个正在执行的进程")
        else:
            self.logger.info(f"任务 {task.task_id} 当前没有正在执行的进程")
        
        # 更新任务配置
        self.tasks[task.task_id] = task
        
        # 如果任务启用，重新添加到调度器
        if task.task_enabled:
            self._add_task_to_scheduler(task)
            self.logger.info(f"已将任务 {task.task_id} 添加到调度计划")
        else:
            self.logger.info(f"任务 {task.task_id} 已禁用，不会添加到调度计划")
        
        self._mark_api_operation()
        self.task_loader.save_tasks(list(self.tasks.values()))
        self.logger.info(f"成功更新任务: {task.task_id}")
        return True
    except Exception as e:
        self.logger.error(f"更新任务 {task.task_id} 失败: {e}")
        return False