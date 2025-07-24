# 任务调度引擎优化建议

本文档基于对现有 `scheduler_engine.py` 和 `scheduler_api.py` 的代码分析,提出了一系列可行的功能增强和优化建议,旨在提升调度引擎的健壮性、可观测性和用户体验。

## 2. 任务执行历史记录

- **当前问题**:
  - 系统只记录了任务的输出日志,但没有一个结构化的执行历史。
  - 用户无法方便地查看一个任务过去的执行情况,例如:
    - 历史运行时间点。
    - 每次执行的成功/失败状态。
    - 每次执行的具体耗时。

- **优化建议**:
  - **后端**:
    - 将每次的 `TaskExecution` 执行记录持久化。可以选择:
      - **SQLite 数据库**: 创建一个简单的 `task_history` 表来存储记录,这是最可靠的方案。
      - **JSON 日志文件**: 为每个任务创建一个 `.history.json` 文件来追加记录。
    - 增加一个新的 API 端点,例如 `GET /api/scheduler/tasks/<task_id>/history`,用于分页查询指定任务的执行历史。
  - **前端**:
    - 在每个任务卡片上增加一个“历史记录”按钮。
    - 点击按钮后,弹出一个模态框,以列表形式清晰地展示该任务最近的执行记录(执行时间、状态、耗时等)。

## 3. 任务依赖功能 (DAG)

- **当前问题**:
  - `Task` 数据类中虽然已经定义了 `task_dependencies` 字段,但后端的调度逻辑并未实现此功能。
  - 无法配置任务之间的依赖关系,例如“任务 B 必须在任务 A 成功后才能执行”。

- **优化建议**:
  - **后端**:
    - 在 `SchedulerEngine` 中实现任务依赖处理逻辑。
    - 当一个任务成功执行后,检查是否有其他任务依赖于它。
    - 如果有,立即触发被依赖任务的执行(可以放入一个执行队列中)。
    - 需要处理循环依赖问题,确保不会造成死循环。
  - **前端**:
    - 在任务创建/编辑界面上,允许用户通过一个下拉列表或多选框来选择其依赖的前置任务。

## 5. 配置安全性与健壮性

- **当前问题**:
  - `tasks/config.json` 文件如果被手动修改错误(例如,JSON 格式损坏、字段类型错误),可能导致整个调度引擎启动失败或运行时异常。

- **优化建议**:
  - **后端**:
    - 引入 `JSON Schema` 或使用 `Pydantic` 等库对任务配置进行严格的校验。
    - 在加载 `tasks/config.json` 文件时,以及通过 API 创建/更新任务时,都使用 Schema 进行验证。
    - 如果验证失败,应拒绝加载或保存,并返回清晰的错误信息,而不是让程序崩溃。

## 9. 高度可配置的通知系统

- **核心思想**: 将通知功能解耦成一个通用的、基于规则的事件处理系统。引擎负责在正确的时间点,根据正确的条件触发“通知事件”,而具体的通知方式(邮件、Webhook 等)只是事件的消费者。

- **配置规范 (`task_notify` 字段)**: `task_notify` 应为一个**规则列表(数组)**,每个规则对象包含:
  - `name` (string): 规则名称,用于界面展示 (e.g., "技术失败时立即告警给管理员")。
  - `enabled` (boolean): 是否启用此规则。
  - `triggers` (array of strings): 触发通知的事件类型,与退出码规范联动。
    - `success`: 任务执行成功 (`exit 0`)。
    - `business_failure`: 任务业务失败 (`exit 1`)。
    - `technical_failure`: 任务技术失败 (`exit 2` 或其他)。
    - `timeout`: 任务执行超时。
  - `threshold` (integer, default: 1): 触发通知所需的**连续**事件发生次数。例如,设置为 `3` 和 `triggers: ["technical_failure"]` 意为“当任务**连续**第 3 次发生技术失败时”才发送通知。
  - `channels` (array of objects): 定义通知发送的渠道,允许一条规则通过多种方式发送。

- **渠道对象 (`channels`) 设计 (以 Email 为例)**:
  ```json
  {
    "type": "email",
    "recipients": ["admin@example.com", "dev-on-call@example.com"],
    "subject_template": "任务告警: {{task_name}} 执行失败!",
    "body_template": "任务 [{{task_id}}] 在 {{execution_end_time}} 执行失败。\n状态: {{execution_status}}\n连续失败次数: {{threshold_count}}\n\n最后日志输出:\n---\n{{execution_log_tail}}\n---"
  }
  ```

- **内容模板变量**: 引擎在发送通知时,应提供以下变量供模板使用:
  - `{{task_id}}`, `{{task_name}}`, `{{execution_status}}`, `{{execution_start_time}}`, `{{execution_end_time}}`, `{{execution_duration}}`, `{{threshold_count}}`, `{{execution_log_tail}}` (最后 N 行日志)。