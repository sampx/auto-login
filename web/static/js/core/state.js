/**
 * 全局状态管理模块
 * 统一管理所有全局变量和状态
 */

// 连接状态
let serverConnected = true;
let reconnectActive = true;

// 定时器管理
let logRefreshInterval = null;
let newLogRefreshInterval = null;
let statusRefreshInterval = null;
let healthCheckInterval = null;

// 任务状态
let currentTask = null;
let currentNewTaskId = null;
let taskOperationInProgress = false;
let currentLogFile = null;

// API配置
const NEW_API_BASE_URL = '';

// 状态管理器
const StateManager = {
    // 连接状态
    getServerConnected: () => serverConnected,
    setServerConnected: (value) => { serverConnected = value; },
    
    getReconnectActive: () => reconnectActive,
    setReconnectActive: (value) => { reconnectActive = value; },
    
    // 定时器管理
    getLogRefreshInterval: () => logRefreshInterval,
    setLogRefreshInterval: (value) => { logRefreshInterval = value; },
    
    getNewLogRefreshInterval: () => newLogRefreshInterval,
    setNewLogRefreshInterval: (value) => { newLogRefreshInterval = value; },
    
    getStatusRefreshInterval: () => statusRefreshInterval,
    setStatusRefreshInterval: (value) => { statusRefreshInterval = value; },
    
    getHealthCheckInterval: () => healthCheckInterval,
    setHealthCheckInterval: (value) => { healthCheckInterval = value; },
    
    // 任务状态
    getCurrentTask: () => currentTask,
    setCurrentTask: (value) => { currentTask = value; },
    
    getCurrentNewTaskId: () => currentNewTaskId,
    setCurrentNewTaskId: (value) => { currentNewTaskId = value; },
    
    getTaskOperationInProgress: () => taskOperationInProgress,
    setTaskOperationInProgress: (value) => { taskOperationInProgress = value; },
    
    getCurrentLogFile: () => currentLogFile,
    setCurrentLogFile: (value) => { currentLogFile = value; },
    
    // API配置
    getNewApiBaseUrl: () => NEW_API_BASE_URL,
    
    // 清理所有定时器
    clearAllIntervals: () => {
        if (logRefreshInterval) {
            clearInterval(logRefreshInterval);
            logRefreshInterval = null;
        }
        if (newLogRefreshInterval) {
            clearInterval(newLogRefreshInterval);
            newLogRefreshInterval = null;
        }
        if (statusRefreshInterval) {
            clearInterval(statusRefreshInterval);
            statusRefreshInterval = null;
        }
        if (healthCheckInterval) {
            clearInterval(healthCheckInterval);
            healthCheckInterval = null;
        }
    }
};

// 导出状态管理器
window.StateManager = StateManager;