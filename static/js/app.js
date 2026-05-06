/**
 * 凤凰台现金管理系统 - 前端主逻辑
 * 版本: 2.1 (增加编辑功能)
 */

// 配置
const CONFIG = {
    API_BASE: '',
    NOTIFICATION_DURATION: 3000,
    AUTO_REFRESH_INTERVAL: 60000,
};

// 系统状态
const state = {
    transactions: [],
    balance: 0,
    currentPeriod: 'day',
    selectedDate: null,
    categories: ['餐饮', '交通', '购物', '娱乐', '工资', '其他'],
    isLoading: false,
    editingTransaction: null
};

// DOM 元素
const elements = {
    currentDate: null,
    totalIncome: null,
    totalExpense: null,
    netBalance: null,
    transactionList: null,
    addTransactionBtn: null,
    mainChart: null,
    dateSelector: null,
    periodButtons: null,
    notification: null
};

// 全局变量暴露
window.state = state;
window.updateUI = updateUI;
window.addTransaction = addTransaction;

// ==================== 初始化 ====================
function init() {
    // 获取 DOM 元素
    elements.currentDate = document.getElementById('currentDate');
    elements.totalIncome = document.getElementById('totalIncome');
    elements.totalExpense = document.getElementById('totalExpense');
    elements.netBalance = document.getElementById('netBalance');
    elements.transactionList = document.getElementById('transactionList');
    elements.addTransactionBtn = document.getElementById('addTransaction');
    elements.mainChart = document.getElementById('mainChart');
    elements.dateSelector = document.getElementById('dateSelector');
    elements.periodButtons = document.querySelectorAll('.period-selector button');
    elements.notification = document.getElementById('notification');
    
    // 初始化日期
    const today = formatDate(new Date());
    state.selectedDate = today;
    if (elements.dateSelector) {
        elements.dateSelector.value = today;
    }
    
    // 绑定事件
    bindEvents();
    
    // 更新时间显示
    updateDateTime();
    setInterval(updateDateTime, 60000);
    
    // 加载数据
    loadData();

    // 加载账本列表
    loadLedgers();

    // 定期刷新
    setInterval(loadData, CONFIG.AUTO_REFRESH_INTERVAL);
}

// ==================== 事件绑定 ====================
function bindEvents() {
    // 添加交易
    if (elements.addTransactionBtn) {
        elements.addTransactionBtn.addEventListener('click', addTransaction);
    }
    
    // 周期切换
    if (elements.periodButtons) {
        elements.periodButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                elements.periodButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                state.currentPeriod = btn.dataset.period;
                updateUI();
            });
        });
    }
    
    // 日期选择
    if (elements.dateSelector) {
        elements.dateSelector.addEventListener('change', (e) => {
            state.selectedDate = e.target.value;
            updateDateTime();
            updateUI();
        });
    }
    
    // Enter 提交
    const amountInput = document.getElementById('amount');
    if (amountInput) {
        amountInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                addTransaction();
            }
        });
    }
}

// ==================== 数据加载 ====================
async function loadData() {
    if (state.isLoading) return;
    
    try {
        state.isLoading = true;
        
        const response = await fetch(`${CONFIG.API_BASE}/api/transactions`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            state.transactions = data.transactions || [];
            state.balance = data.balance || 0;
            updateUI();
        } else {
            throw new Error(data.message || '加载失败');
        }
        
    } catch (error) {
        console.error('数据加载失败:', error);
        showNotification('数据加载失败: ' + error.message, 'error');
    } finally {
        state.isLoading = false;
    }
}

// ==================== UI 更新 ====================
function updateUI() {
    updateBalance();
    renderTransactionList();
    renderChart();
}

function updateDateTime() {
    if (!elements.currentDate) return;
    
    const now = new Date();
    const weekDays = ['日', '一', '二', '三', '四', '五', '六'];
    const dateStr = `${now.getFullYear()}年${now.getMonth() + 1}月${now.getDate()}日 星期${weekDays[now.getDay()]}`;
    const timeStr = `${now.getHours() < 12 ? '上午' : '下午'}`;
    
    elements.currentDate.textContent = `${dateStr} ${timeStr}`;
}

function updateBalance() {
    const filtered = filterTransactions();
    
    const totalIncome = filtered
        .filter(t => t.type === 'income')
        .reduce((sum, t) => sum + parseFloat(t.amount || 0), 0);
    
    const totalExpense = filtered
        .filter(t => t.type === 'expense')
        .reduce((sum, t) => sum + parseFloat(t.amount || 0), 0);
    
    if (elements.totalIncome) {
        elements.totalIncome.textContent = `¥${totalIncome.toFixed(2)}`;
    }
    if (elements.totalExpense) {
        elements.totalExpense.textContent = `¥${totalExpense.toFixed(2)}`;
    }
    if (elements.netBalance) {
        elements.netBalance.textContent = `¥${(totalIncome - totalExpense).toFixed(2)}`;
    }
}

function renderTransactionList() {
    if (!elements.transactionList) return;
    
    const filtered = filterTransactions()
        .sort((a, b) => new Date(b.time) - new Date(a.time))
        .slice(0, 50); // 只显示前50条
    
    if (filtered.length === 0) {
        elements.transactionList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <p>暂无交易记录</p>
            </div>
        `;
        return;
    }
    
    elements.transactionList.innerHTML = '';
    
    filtered.forEach(transaction => {
        const item = document.createElement('div');
        item.className = 'transaction-item';
        item.dataset.id = transaction.id;
        
        const time = new Date(transaction.time);
        const timeStr = formatDateTime(time);
        
        item.innerHTML = `
            <div class="transaction-info">
                <div style="font-weight: 500;">${escapeHtml(transaction.remark || transaction.category)}</div>
                <div class="transaction-category">${escapeHtml(transaction.category)} · ${getTimePeriod(time)}</div>
                <div class="transaction-time">${timeStr}${transaction.username ? ' · 👤 ' + escapeHtml(transaction.username) : ''}</div>
            </div>
            <div class="transaction-amount ${transaction.type}">
                ${transaction.type === 'income' ? '+' : '-'}¥${parseFloat(transaction.amount).toFixed(2)}
            </div>
            <div class="transaction-actions">
                <button class="btn-edit" onclick="editTransaction(${transaction.id})" title="编辑">
                    ✏️
                </button>
                <button class="btn-delete" onclick="deleteTransaction(${transaction.id})">
                    🗑️ 删除
                </button>
            </div>
        `;
        
        elements.transactionList.appendChild(item);
    });
}

function renderChart() {
    if (!elements.mainChart || typeof echarts === 'undefined') {
        if (elements.mainChart) {
            elements.mainChart.innerHTML = '<p style="color:#888;text-align:center;padding:40px;">图表功能不可用</p>';
        }
        return;
    }
    
    const chart = echarts.init(elements.mainChart);
    const filtered = filterTransactions();
    
    if (state.currentPeriod === 'day') {
        renderDayChart(chart, filtered);
    } else if (state.currentPeriod === 'week') {
        renderWeekChart(chart, filtered);
    } else {
        renderMonthChart(chart, filtered);
    }
    
    window.addEventListener('resize', () => chart.resize());
}

function renderDayChart(chart, transactions) {
    const categoryData = {};
    
    transactions.forEach(t => {
        if (!t || !t.category) return;
        
        if (!categoryData[t.category]) {
            categoryData[t.category] = { income: 0, expense: 0 };
        }
        
        const amount = parseFloat(t.amount) || 0;
        if (t.type === 'income') {
            categoryData[t.category].income += amount;
        } else {
            categoryData[t.category].expense += amount;
        }
    });
    
    const categories = Object.keys(categoryData);
    const incomeData = categories.map(c => categoryData[c].income);
    const expenseData = categories.map(c => categoryData[c].expense);
    
    const option = {
        title: {
            text: '当日分类趋势',
            left: 'center',
            textStyle: { 
                fontSize: 16, 
                fontWeight: 'bold',
                color: '#333'
            }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: { 
                type: 'cross',
                label: {
                    backgroundColor: '#6a7985'
                }
            },
            formatter: params => {
                let result = `<strong>${params[0].axisValue}</strong><br>`;
                let total = 0;
                params.forEach(p => {
                    if (p.value > 0) {
                        const value = Math.abs(p.value).toFixed(2);
                        result += `${p.marker} ${p.seriesName}: ¥${value}<br>`;
                        total += p.value;
                    }
                });
                if (params.length > 1) {
                    result += `<strong>合计: ¥${total.toFixed(2)}</strong>`;
                }
                return result;
            }
        },
        legend: { 
            data: ['收入', '支出'], 
            bottom: 5,
            icon: 'roundRect'
        },
        grid: { 
            left: '3%', 
            right: '4%', 
            bottom: '15%', 
            top: '18%', 
            containLabel: true 
        },
        xAxis: { 
            type: 'category', 
            data: categories,
            axisLabel: {
                rotate: categories.length > 5 ? 30 : 0,
                interval: 0
            }
        },
        yAxis: { 
            type: 'value',
            name: '金额（¥）',
            axisLabel: {
                formatter: value => {
                    if (value >= 1000) {
                        return (value / 1000).toFixed(1) + 'k';
                    }
                    return value.toFixed(0);
                }
            }
        },
        series: [
            {
                name: '收入',
                type: 'line',
                data: incomeData,
                smooth: true,
                itemStyle: { color: '#43e97b' },
                lineStyle: { width: 3 },
                areaStyle: {
                    color: {
                        type: 'linear',
                        x: 0, y: 0, x2: 0, y2: 1,
                        colorStops: [
                            { offset: 0, color: 'rgba(67, 233, 123, 0.3)' },
                            { offset: 1, color: 'rgba(67, 233, 123, 0.05)' }
                        ]
                    }
                },
                symbolSize: 8
            },
            {
                name: '支出',
                type: 'line',
                data: expenseData,
                smooth: true,
                itemStyle: { color: '#f72585' },
                lineStyle: { width: 3 },
                areaStyle: {
                    color: {
                        type: 'linear',
                        x: 0, y: 0, x2: 0, y2: 1,
                        colorStops: [
                            { offset: 0, color: 'rgba(247, 37, 133, 0.3)' },
                            { offset: 1, color: 'rgba(247, 37, 133, 0.05)' }
                        ]
                    }
                },
                symbolSize: 8
            }
        ]
    };
    
    chart.setOption(option);
}

function renderWeekChart(chart, transactions) {
    // 计算本周每天的收支情况
    const weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
    const selectedDate = new Date(state.selectedDate);
    const dayOfWeek = selectedDate.getDay();
    const monday = new Date(selectedDate);
    monday.setDate(selectedDate.getDate() - (dayOfWeek === 0 ? 6 : dayOfWeek - 1));
    
    const incomeData = [0, 0, 0, 0, 0, 0, 0];
    const expenseData = [0, 0, 0, 0, 0, 0, 0];
    
    transactions.forEach(t => {
        const tDate = new Date(t.date);
        const diff = Math.floor((tDate - monday) / (1000 * 60 * 60 * 24));
        
        if (diff >= 0 && diff < 7) {
            const amount = parseFloat(t.amount) || 0;
            if (t.type === 'income') {
                incomeData[diff] += amount;
            } else if (t.type === 'expense') {
                expenseData[diff] += amount;
            }
        }
    });
    
    const option = {
        title: {
            text: '本周收支趋势',
            left: 'center',
            textStyle: { fontSize: 16, fontWeight: 'bold' }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'cross' }
        },
        legend: {
            data: ['收入', '支出'],
            bottom: 0
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '15%',
            top: '15%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: weekDays,
            boundaryGap: false
        },
        yAxis: {
            type: 'value',
            name: '金额（¥）'
        },
        series: [
            {
                name: '收入',
                type: 'line',
                data: incomeData,
                itemStyle: { color: '#4cc9f0' },
                smooth: true,
                areaStyle: {
                    color: {
                        type: 'linear',
                        x: 0, y: 0, x2: 0, y2: 1,
                        colorStops: [
                            { offset: 0, color: 'rgba(76, 201, 240, 0.3)' },
                            { offset: 1, color: 'rgba(76, 201, 240, 0.05)' }
                        ]
                    }
                }
            },
            {
                name: '支出',
                type: 'line',
                data: expenseData,
                itemStyle: { color: '#f72585' },
                smooth: true,
                areaStyle: {
                    color: {
                        type: 'linear',
                        x: 0, y: 0, x2: 0, y2: 1,
                        colorStops: [
                            { offset: 0, color: 'rgba(247, 37, 133, 0.3)' },
                            { offset: 1, color: 'rgba(247, 37, 133, 0.05)' }
                        ]
                    }
                }
            }
        ]
    };
    
    chart.setOption(option);
}

function renderMonthChart(chart, transactions) {
    // 获取当前月份的天数
    const selectedDate = new Date(state.selectedDate);
    const year = selectedDate.getFullYear();
    const month = selectedDate.getMonth();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    
    // 初始化数据
    const incomeData = Array(daysInMonth).fill(0);
    const expenseData = Array(daysInMonth).fill(0);
    const dateLabels = Array.from({length: daysInMonth}, (_, i) => `${i+1}日`);
    
    // 统计每天的收支
    transactions.forEach(t => {
        if (!t.date) return;
        
        const tDate = new Date(t.date);
        if (tDate.getFullYear() === year && tDate.getMonth() === month) {
            const day = tDate.getDate() - 1;  // 数组索引从0开始
            const amount = parseFloat(t.amount) || 0;
            
            if (t.type === 'income') {
                incomeData[day] += amount;
            } else if (t.type === 'expense') {
                expenseData[day] += amount;
            }
        }
    });
    
    const option = {
        title: {
            text: `${year}年${month + 1}月收支统计`,
            left: 'center',
            textStyle: { fontSize: 16, fontWeight: 'bold' }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'shadow' },
            formatter: params => {
                let result = params[0].axisValue + '<br>';
                let totalIncome = 0;
                let totalExpense = 0;
                
                params.forEach(p => {
                    if (p.value > 0) {
                        result += `${p.marker} ${p.seriesName}: ¥${p.value.toFixed(2)}<br>`;
                        if (p.seriesName === '收入') totalIncome = p.value;
                        else totalExpense = p.value;
                    }
                });
                
                const net = totalIncome - totalExpense;
                result += `<strong>净收入: ¥${net.toFixed(2)}</strong>`;
                return result;
            }
        },
        legend: {
            data: ['收入', '支出'],
            bottom: 0
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '15%',
            top: '15%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: dateLabels,
            axisLabel: {
                interval: Math.floor(daysInMonth / 10), // 避免标签过密
                rotate: 0
            }
        },
        yAxis: {
            type: 'value',
            name: '金额（¥）'
        },
        series: [
            {
                name: '收入',
                type: 'bar',
                data: incomeData,
                itemStyle: { color: '#4cc9f0' },
                barMaxWidth: 30
            },
            {
                name: '支出',
                type: 'bar',
                data: expenseData,
                itemStyle: { color: '#f72585' },
                barMaxWidth: 30
            }
        ]
    };
    
    chart.setOption(option);
}

// ==================== 交易操作 ====================
async function addTransaction() {
    const type = document.getElementById('transactionType')?.value;
    const amount = parseFloat(document.getElementById('amount')?.value);
    const category = document.getElementById('category')?.value;
    const remark = document.getElementById('remark')?.value || '';
    
    if (!amount || isNaN(amount) || amount <= 0) {
        showNotification('请输入有效的金额', 'error');
        return;
    }
    
    const now = new Date();
    const transaction = {
        type,
        amount,
        category,
        remark,
        date: formatDate(now),
        time: now.toISOString()
    };
    
    try {
        const response = await fetch(`${CONFIG.API_BASE}/api/transactions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(transaction)
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            document.getElementById('amount').value = '';
            document.getElementById('remark').value = '';
            showNotification('交易添加成功 ✅', 'success');
            await loadData();
        } else {
            throw new Error(data.message || '添加失败');
        }
        
    } catch (error) {
        console.error('添加交易错误:', error);
        showNotification('添加失败: ' + error.message, 'error');
    }
}

// 编辑交易
window.editTransaction = async function(id) {
    const transaction = state.transactions.find(t => t.id === id);
    if (!transaction) {
        showNotification('未找到该交易记录', 'error');
        return;
    }
    
    // 填充表单
    document.getElementById('transactionType').value = transaction.type;
    document.getElementById('amount').value = transaction.amount;
    document.getElementById('category').value = transaction.category;
    document.getElementById('remark').value = transaction.remark || '';
    
    // 修改按钮
    const btn = document.getElementById('addTransaction');
    const btnText = document.getElementById('btnText');
    if (btnText) {
        btnText.textContent = '💾 保存修改';
    } else {
        btn.textContent = '💾 保存修改';
    }
    btn.style.background = 'linear-gradient(135deg, #f72585 0%, #ff6a00 100%)';
    
    // 保存编辑状态
    state.editingTransaction = id;
    
    // 修改按钮事件
    btn.onclick = () => saveEditTransaction(id);
    
    // 滚动到表单
    document.querySelector('.form-section').scrollIntoView({ behavior: 'smooth' });
    
    showNotification('编辑模式：修改后点击"保存修改"', 'info');
};

// 保存编辑
async function saveEditTransaction(id) {
    const type = document.getElementById('transactionType')?.value;
    const amount = parseFloat(document.getElementById('amount')?.value);
    const category = document.getElementById('category')?.value;
    const remark = document.getElementById('remark')?.value || '';
    
    if (!amount || isNaN(amount) || amount <= 0) {
        showNotification('请输入有效的金额', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${CONFIG.API_BASE}/api/transactions/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type, amount, category, remark })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showNotification('修改成功 ✅', 'success');
            cancelEdit();
            await loadData();
        } else {
            throw new Error(data.message || '修改失败');
        }
        
    } catch (error) {
        console.error('修改交易错误:', error);
        showNotification('修改失败: ' + error.message, 'error');
    }
}

// 取消编辑
function cancelEdit() {
    state.editingTransaction = null;
    
    const btn = document.getElementById('addTransaction');
    const btnText = document.getElementById('btnText');
    if (btnText) {
        btnText.textContent = '✅ 添加交易';
    } else {
        btn.textContent = '✅ 添加交易';
    }
    btn.style.background = '';
    btn.onclick = addTransaction;
    
    document.getElementById('amount').value = '';
    document.getElementById('remark').value = '';
}

// 删除交易
window.deleteTransaction = async function(id) {
    const transaction = state.transactions.find(t => t.id === id);
    if (!transaction) {
        showNotification('未找到该交易记录', 'error');
        return;
    }
    
    const confirmMsg = `确定删除这条记录吗？\n\n分类: ${transaction.category}\n金额: ¥${transaction.amount}\n备注: ${transaction.remark || '无'}`;
    
    if (!confirm(confirmMsg)) {
        return;
    }
    
    try {
        const response = await fetch(`${CONFIG.API_BASE}/api/transactions/${id}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showNotification('删除成功 ✅', 'success');
            await loadData();
        } else {
            throw new Error(data.message || '删除失败');
        }
        
    } catch (error) {
        console.error('删除交易错误:', error);
        showNotification('删除失败: ' + error.message, 'error');
    }
};

// ==================== 辅助函数 ====================
function filterTransactions() {
    if (!state.selectedDate) return state.transactions;
    
    return state.transactions.filter(t => {
        if (!t || !t.date) return false;
        
        switch (state.currentPeriod) {
            case 'day':
                return t.date === state.selectedDate;
            case 'week':
                // 获取选中日期所在周的起始和结束日期
                const selectedDate = new Date(state.selectedDate);
                const dayOfWeek = selectedDate.getDay();
                const monday = new Date(selectedDate);
                monday.setDate(selectedDate.getDate() - (dayOfWeek === 0 ? 6 : dayOfWeek - 1));
                const sunday = new Date(monday);
                sunday.setDate(monday.getDate() + 6);
                
                const transactionDate = new Date(t.date);
                return transactionDate >= monday && transactionDate <= sunday;
            case 'month':
                const month = state.selectedDate.substring(0, 7);
                return t.date.startsWith(month);
            default:
                return true;
        }
    });
}

function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function formatDateTime(date) {
    const dateStr = formatDate(date);
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${dateStr} ${hours}:${minutes}`;
}

function getTimePeriod(date) {
    const hours = date.getHours();
    if (hours >= 6 && hours < 12) return '上午';
    if (hours >= 12 && hours < 14) return '中午';
    if (hours >= 14 && hours < 18) return '下午';
    return '晚上';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showNotification(message, type = 'info') {
    if (!elements.notification) return;
    
    const colors = {
        success: 'rgba(76, 201, 240, 0.95)',
        error: 'rgba(247, 37, 133, 0.95)',
        info: 'rgba(67, 97, 238, 0.95)'
    };
    
    elements.notification.textContent = message;
    elements.notification.style.backgroundColor = colors[type] || colors.info;
    elements.notification.classList.add('show');
    
    setTimeout(() => {
        elements.notification.classList.remove('show');
    }, CONFIG.NOTIFICATION_DURATION);
}

// ==================== 账本管理功能 ====================

// 当前管理的账本 ID（用于成员、邀请码弹窗）
let currentManageLedgerId = null;

// 加载账本列表
async function loadLedgers() {
    try {
        const res = await fetch('/api/ledgers');
        const data = await res.json();
        if (!data.success) return;

        const select = document.getElementById('ledgerSelect');
        if (!select) return;

        select.innerHTML = '<option value="">-- 选择账本 --</option>';
        data.ledgers.forEach(l => {
            const opt = document.createElement('option');
            opt.value = l.id;
            opt.textContent = l.name + (l.role === 'manager' ? ' (管理)' : '');
            select.appendChild(opt);
        });

        // 如果已有 active_ledger_id，选中它
        if (window.activeLedgerId && select.querySelector(`option[value="${window.activeLedgerId}"]`)) {
            select.value = window.activeLedgerId;
        } else if (data.ledgers.length > 0) {
            select.value = data.ledgers[0].id;
            await switchLedger(data.ledgers[0].id, true);
        }
    } catch (e) {
        console.error('加载账本失败:', e);
    }
}

// 切换账本
async function switchLedger(ledgerId, silent = false) {
    try {
        const res = await fetch(`/api/ledgers/${ledgerId}/switch`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            window.activeLedgerId = ledgerId;
            if (!silent) {
                showNotification('已切换账本', 'success');
            }
            // 触发所有数据的全面刷新（交易、账户、预算等）
            await loadData();
            if (typeof loadBudget === 'function') loadBudget();
            if (typeof loadAccounts === 'function') loadAccounts();
        }
    } catch (e) {
        console.error('切换账本失败:', e);
    }
}

// 账本下拉切换事件
async function onLedgerChange() {
    const select = document.getElementById('ledgerSelect');
    if (!select.value) return;
    await switchLedger(parseInt(select.value));
}

// 关闭弹窗
function closeModal(id) {
    document.getElementById(id).classList.remove('active');
}

// 打开管理账本弹窗
async function openManageLedgersModal() {
    const modal = document.getElementById('manageLedgersModal');
    modal.classList.add('active');
    await refreshLedgerList();
}

// 打开加入账本弹窗
function openJoinLedgerModal() {
    const modal = document.getElementById('joinLedgerModal');
    modal.classList.add('active');
    document.getElementById('joinCodeInput').value = '';
    document.getElementById('joinResult').textContent = '';
}

// 刷新账本列表
async function refreshLedgerList() {
    try {
        const res = await fetch('/api/ledgers');
        const data = await res.json();
        const container = document.getElementById('ledgerList');
        if (!data.success || !data.ledgers || data.ledgers.length === 0) {
            container.innerHTML = '<div style="color:#999;padding:10px;">暂无账本</div>';
            return;
        }

        container.innerHTML = data.ledgers.map(l => `
            <div class="ledger-list-item">
                <div class="ledger-info">
                    <div class="name">📒 ${escapeHtml(l.name)}</div>
                    <div class="meta">${l.owner_name ? '创建者: ' + escapeHtml(l.owner_name) : ''} | 成员: ${l.member_count || 1} | 角色: ${l.role}</div>
                </div>
                <div class="actions">
                    ${l.role === 'manager' || l.role === 'owner' ? `
                        <button onclick="openMemberModal(${l.id})">👥 成员</button>
                        <button onclick="openInviteCodeModal(${l.id})">🔗 邀请</button>
                    ` : ''}
                    ${l.role === 'manager' ? `
                        <button class="btn-danger" onclick="deleteLedger(${l.id})">🗑 删除</button>
                    ` : ''}
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.error('刷新账本列表失败:', e);
    }
}

// 创建账本
async function createLedger() {
    const nameInput = document.getElementById('newLedgerName');
    const name = nameInput.value.trim();
    if (!name) {
        showNotification('请输入账本名称', 'error');
        return;
    }
    try {
        const res = await fetch('/api/ledgers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        const data = await res.json();
        if (data.success) {
            showNotification('账本创建成功', 'success');
            nameInput.value = '';
            await refreshLedgerList();
            await loadLedgers();
        } else {
            showNotification(data.message || '创建失败', 'error');
        }
    } catch (e) {
        showNotification('创建失败: ' + e.message, 'error');
    }
}

// 删除账本
async function deleteLedger(id) {
    if (!confirm('确定删除该账本吗？此操作不可撤销。')) return;
    try {
        const res = await fetch(`/api/ledgers/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            showNotification('账本已删除', 'success');
            await refreshLedgerList();
            await loadLedgers();
            await loadData();
        } else {
            showNotification(data.message || '删除失败', 'error');
        }
    } catch (e) {
        showNotification('删除失败: ' + e.message, 'error');
    }
}

// 打开成员管理弹窗
async function openMemberModal(ledgerId) {
    currentManageLedgerId = ledgerId;
    const modal = document.getElementById('memberModal');
    modal.classList.add('active');
    document.getElementById('addMemberUsername').value = '';

    try {
        const res = await fetch(`/api/ledgers/${ledgerId}/members`);
        const data = await res.json();
        const container = document.getElementById('memberList');
        if (!data.success) {
            container.innerHTML = '<div style="color:#999;">获取成员失败</div>';
            return;
        }

        const roleLabel = { 'owner': '所有者', 'manager': '管理员', 'editor': '编辑者', 'viewer': '查看者' };
        let html = `<div class="member-row">
            <div class="member-info">
                <div class="member-avatar">${escapeHtml(data.owner.username.charAt(0).toUpperCase())}</div>
                <div>
                    <div class="username">${escapeHtml(data.owner.username)} <span class="role-badge owner">所有者</span></div>
                </div>
            </div>
        </div>`;
        data.members.forEach(m => {
            const isSelf = m.user_id === window.activeUserId;
            html += `
            <div class="member-row">
                <div class="member-info">
                    <div class="member-avatar">${escapeHtml(m.username.charAt(0).toUpperCase())}</div>
                    <div>
                        <div class="username">${escapeHtml(m.username)}${isSelf ? ' <span style="font-size:0.75rem;color:#999;">(你)</span>' : ''}</div>
                    </div>
                </div>
                <span class="role-badge ${m.role}">${roleLabel[m.role] || m.role}</span>
                ${!isSelf ? `
                <div style="display:flex;gap:4px;flex-shrink:0;">
                    <select onchange="changeMemberRole(${ledgerId},${m.user_id},this.value)" style="padding:4px 6px;border:1.5px solid #e5e7eb;border-radius:6px;font-size:0.78rem;font-family:inherit;background:#fafafa;cursor:pointer;outline:none;">
                        <option value="viewer" ${m.role === 'viewer' ? 'selected' : ''}>查看者</option>
                        <option value="editor" ${m.role === 'editor' ? 'selected' : ''}>编辑者</option>
                        <option value="manager" ${m.role === 'manager' ? 'selected' : ''}>管理员</option>
                    </select>
                    <button onclick="removeMember(${ledgerId},${m.user_id})" style="padding:4px 10px;border:1.5px solid #fecaca;border-radius:6px;background:#fef2f2;color:#dc2626;cursor:pointer;font-size:0.78rem;font-weight:500;font-family:inherit;transition:all 0.2s;">移除</button>
                </div>
                ` : ''}
            </div>`;
        });
        container.innerHTML = html;
    } catch (e) {
        console.error('获取成员失败:', e);
    }
}

// 添加成员
async function addMember() {
    const username = document.getElementById('addMemberUsername').value.trim();
    const role = document.getElementById('addMemberRole').value;
    if (!username) {
        showNotification('请输入用户名', 'error');
        return;
    }
    try {
        const res = await fetch(`/api/ledgers/${currentManageLedgerId}/members`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, role })
        });
        const data = await res.json();
        if (data.success) {
            showNotification('成员添加成功', 'success');
            document.getElementById('addMemberUsername').value = '';
            await openMemberModal(currentManageLedgerId);
        } else {
            showNotification(data.message || '添加失败', 'error');
        }
    } catch (e) {
        showNotification('添加失败: ' + e.message, 'error');
    }
}

// 修改成员角色
async function changeMemberRole(ledgerId, userId, role) {
    try {
        const res = await fetch(`/api/ledgers/${ledgerId}/members/${userId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ role })
        });
        const data = await res.json();
        if (data.success) {
            showNotification('角色已更新', 'success');
        } else {
            showNotification(data.message || '更新失败', 'error');
        }
    } catch (e) {
        showNotification('更新失败: ' + e.message, 'error');
    }
}

// 移除成员
async function removeMember(ledgerId, userId) {
    if (!confirm('确定移除该成员吗？')) return;
    try {
        const res = await fetch(`/api/ledgers/${ledgerId}/members/${userId}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            showNotification('成员已移除', 'success');
            await openMemberModal(ledgerId);
        } else {
            showNotification(data.message || '移除失败', 'error');
        }
    } catch (e) {
        showNotification('移除失败: ' + e.message, 'error');
    }
}

// 打开邀请码弹窗
async function openInviteCodeModal(ledgerId) {
    currentManageLedgerId = ledgerId;
    const modal = document.getElementById('inviteCodeModal');
    modal.classList.add('active');

    try {
        const res = await fetch(`/api/ledgers/${ledgerId}/invite-codes`);
        const data = await res.json();
        const container = document.getElementById('inviteCodeList');
        if (!data.success || !data.invite_codes || data.invite_codes.length === 0) {
            container.innerHTML = '<div style="color:#999;padding:10px;">暂无邀请码</div>';
            return;
        }
        container.innerHTML = data.invite_codes.map(c => `
            <div class="invite-code-box">
                <div class="code-info">
                    <span class="code">${escapeHtml(c.code)}</span>
                    <span class="meta">使用: ${c.used_count}/${c.max_uses || '∞'} | ${c.expires_at ? '过期: ' + new Date(c.expires_at).toLocaleString() : '永不过期'} | 创建者: ${escapeHtml(c.creator_name || '未知')}</span>
                </div>
                <div class="actions">
                    <span style="font-size:0.75rem;font-weight:500;color:${c.is_active ? '#10b981' : '#999'};background:${c.is_active ? '#ecfdf5' : '#f3f4f6'};padding:3px 8px;border-radius:6px;">${c.is_active ? '有效' : '已撤销'}</span>
                    <button class="copy-btn" onclick="copyInviteCode('${c.code}')">复制</button>
                    ${c.is_active ? `<button class="revoke-btn" onclick="revokeInviteCode(${ledgerId},${c.id})">撤销</button>` : ''}
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.error('获取邀请码失败:', e);
    }
}

// 生成邀请码
async function createInviteCode() {
    const expiresInHours = parseInt(document.getElementById('inviteExpireHours').value) || 0;
    const maxUses = parseInt(document.getElementById('inviteMaxUses').value) || 0;
    try {
        const res = await fetch(`/api/ledgers/${currentManageLedgerId}/invite-codes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ expires_in_hours: expiresInHours, max_uses: maxUses })
        });
        const data = await res.json();
        if (data.success) {
            showNotification('邀请码已生成', 'success');
            await openInviteCodeModal(currentManageLedgerId);
        } else {
            showNotification(data.message || '生成失败', 'error');
        }
    } catch (e) {
        showNotification('生成失败: ' + e.message, 'error');
    }
}

// 撤销邀请码
async function revokeInviteCode(ledgerId, codeId) {
    if (!confirm('确定撤销该邀请码？')) return;
    try {
        const res = await fetch(`/api/ledgers/${ledgerId}/invite-codes/${codeId}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            showNotification('邀请码已撤销', 'success');
            await openInviteCodeModal(ledgerId);
        } else {
            showNotification(data.message || '撤销失败', 'error');
        }
    } catch (e) {
        showNotification('撤销失败: ' + e.message, 'error');
    }
}

// 复制邀请码
function copyInviteCode(code) {
    navigator.clipboard.writeText(code).then(() => {
        showNotification('已复制邀请码', 'success');
    }).catch(() => {
        // fallback
        const ta = document.createElement('textarea');
        ta.value = code;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        showNotification('已复制邀请码', 'success');
    });
}

// 校验并加入账本
async function validateAndJoin() {
    const code = document.getElementById('joinCodeInput').value.trim();
    const resultDiv = document.getElementById('joinResult');
    if (!code) {
        resultDiv.innerHTML = '<span style="color:#dc2626;">请输入邀请码</span>';
        return;
    }

    // 先校验
    try {
        const validateRes = await fetch('/api/ledgers/validate-code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code })
        });
        const validateData = await validateRes.json();
        if (!validateData.valid) {
            resultDiv.innerHTML = `<span style="color:#dc2626;">${validateData.message}</span>`;
            return;
        }

        if (!confirm(`将加入账本「${validateData.ledger_name}」，确认吗？`)) return;

        // 确认加入
        const joinRes = await fetch('/api/ledgers/join', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code })
        });
        const joinData = await joinRes.json();
        if (joinData.success) {
            resultDiv.innerHTML = `<span style="color:#10b981;">✅ ${joinData.message}</span>`;
            showNotification(`已加入账本「${joinData.ledger.name}」`, 'success');
            closeModal('joinLedgerModal');
            await loadLedgers();
            await loadData();
        } else {
            resultDiv.innerHTML = `<span style="color:#dc2626;">${joinData.message}</span>`;
        }
    } catch (e) {
        resultDiv.innerHTML = `<span style="color:#dc2626;">操作失败: ${e.message}</span>`;
    }
}

// ==================== 周期账单功能 ====================

let recurringCategoriesLoaded = false;

// 打开周期账单弹窗
function openRecurringModal() {
    closeModal('recurringFormModal');
    const modal = document.getElementById('recurringModal');
    modal.classList.add('active');
    loadRecurringRules();
    checkRecurringPending();
}

// 加载规则列表
async function loadRecurringRules() {
    const container = document.getElementById('recurringRuleList');
    if (!container) return;
    try {
        const res = await fetch('/api/recurring-rules');
        const data = await res.json();
        const countEl = document.getElementById('recurringCount');
        if (!data.success) {
            container.innerHTML = '<div style="text-align:center;padding:40px;color:#999;">加载失败</div>';
            return;
        }
        if (countEl) countEl.textContent = `共 ${data.total} 条规则`;
        if (data.total === 0) {
            container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">🔄</div><p>暂无周期账单规则</p><p style="font-size:0.85rem;color:#bbb;margin-top:8px;">点击上方「新建规则」设置自动账单</p></div>';
            return;
        }
        container.innerHTML = data.rules.map(r => renderRuleCard(r)).join('');
    } catch (e) {
        console.error('加载周期账单失败:', e);
        container.innerHTML = '<div style="text-align:center;padding:40px;color:#999;">加载失败</div>';
    }
}

function renderRuleCard(r) {
    const periodLabels = { daily: '每天', weekly: '每周', monthly: '每月', yearly: '每年' };
    const typeLabel = r.type === 'income' ? '收入' : '支出';
    const amountClass = r.type === 'income' ? 'income' : 'expense';
    const periodClass = r.period;
    const cardClass = r.is_active ? '' : 'inactive';
    const intervalText = r.interval_value > 1 ? `${r.interval_value}${periodLabels[r.period]}` : periodLabels[r.period];
    const dateRange = r.end_date ? `${r.start_date} ~ ${r.end_date}` : `${r.start_date} 起`;

    let nextDateHtml = '';
    if (r.is_active) {
        nextDateHtml = `<span class="recurring-next-date">⏰ 下次: ${r.next_date}</span>`;
    } else {
        nextDateHtml = '<span style="color:#999;font-size:0.78rem;">已停用</span>';
    }

    return `
    <div class="recurring-rule-card ${cardClass}">
        <div class="recurring-rule-info">
            <div class="recurring-rule-name">
                <span>${escapeHtml(r.name)}</span>
                <span class="recurring-period-badge ${periodClass}">${intervalText}</span>
                ${!r.is_active ? '<span style="font-size:0.7rem;padding:2px 8px;border-radius:10px;background:#f3f4f6;color:#9ca3af;">已停用</span>' : ''}
            </div>
            <div class="recurring-rule-meta">
                <span>📂 ${escapeHtml(r.category)}</span>
                <span>📊 ${typeLabel}</span>
                <span>📅 ${dateRange}</span>
                <span class="recurring-date-range">${nextDateHtml}</span>
                ${r.account_name ? `<span>🏦 ${escapeHtml(r.account_name)}</span>` : ''}
                ${r.remark ? `<span>📝 ${escapeHtml(r.remark)}</span>` : ''}
            </div>
        </div>
        <div class="recurring-rule-amount ${amountClass}">
            ${r.type === 'income' ? '+' : '-'}¥${parseFloat(r.amount).toFixed(2)}
        </div>
        <div class="recurring-rule-actions">
            <button class="toggle-btn ${r.is_active ? 'active-rule' : 'inactive-rule'}" onclick="toggleRecurringRule(${r.id})">
                ${r.is_active ? '⏸ 停用' : '▶ 启用'}
            </button>
            <button onclick="editRecurringRule(${r.id})">✏️ 编辑</button>
            <button class="delete-btn" onclick="deleteRecurringRule(${r.id})">🗑 删除</button>
        </div>
    </div>`;
}

// 检查待生成账单
async function checkRecurringPending() {
    try {
        const res = await fetch('/api/recurring-rules/generate-check');
        const data = await res.json();
        const badge = document.getElementById('recurringPendingBadge');
        if (badge) {
            if (data.success && data.pending_count > 0) {
                badge.textContent = `${data.pending_count} 笔待生成`;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        }
    } catch (e) {
        console.error('检查待生成失败:', e);
    }
}

// 立即生成账单
async function generateRecurringBills() {
    const btn = event && event.target;
    if (btn) {
        btn.disabled = true;
        btn.textContent = '⏳ 生成中...';
    }
    try {
        const res = await fetch('/api/recurring-rules/generate', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showNotification(data.message, 'success');
            checkRecurringPending();
            loadRecurringRules();
            if (typeof loadData === 'function') loadData();
        } else {
            showNotification(data.message || '生成失败', 'error');
        }
    } catch (e) {
        showNotification('生成失败: ' + e.message, 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = '⏳ 立即生成';
        }
    }
}

// 打开新建规则表单
function openAddRecurringRule() {
    document.getElementById('editRecurringRuleId').value = '';
    document.getElementById('recurringFormTitle').textContent = '🔄 新建周期账单规则';
    document.getElementById('recurringSubmitBtn').textContent = '✅ 确认创建';
    document.getElementById('recurringForm').reset();
    document.getElementById('recurringStartDate').value = new Date().toISOString().split('T')[0];
    document.getElementById('recurringInterval').value = 1;

    loadRecurringCategories().then(() => {
        loadRecurringAccounts();
        const modal = document.getElementById('recurringFormModal');
        modal.classList.add('active');
    });
}

// 编辑规则
async function editRecurringRule(id) {
    try {
        const res = await fetch('/api/recurring-rules');
        const data = await res.json();
        if (!data.success) return;
        const rule = data.rules.find(r => r.id === id);
        if (!rule) return;

        document.getElementById('editRecurringRuleId').value = rule.id;
        document.getElementById('recurringFormTitle').textContent = '✏️ 编辑周期账单规则';
        document.getElementById('recurringSubmitBtn').textContent = '💾 保存修改';
        document.getElementById('recurringName').value = rule.name;
        document.getElementById('recurringType').value = rule.type;
        document.getElementById('recurringAmount').value = rule.amount;
        document.getElementById('recurringPeriod').value = rule.period;
        document.getElementById('recurringInterval').value = rule.interval_value || 1;
        document.getElementById('recurringStartDate').value = rule.start_date;
        document.getElementById('recurringEndDate').value = rule.end_date || '';
        document.getElementById('recurringRemark').value = rule.remark || '';

        onRecurringTypeChange();
        await loadRecurringCategories(rule.type);
        document.getElementById('recurringCategory').value = rule.category;

        await loadRecurringAccounts();
        if (rule.account_id) {
            document.getElementById('recurringAccount').value = rule.account_id;
        }

        const modal = document.getElementById('recurringFormModal');
        modal.classList.add('active');
    } catch (e) {
        showNotification('加载规则信息失败', 'error');
    }
}

// 周期类型变化
function onRecurringTypeChange() {
    const type = document.getElementById('recurringType').value;
    loadRecurringCategories(type);
}

// 加载分类
async function loadRecurringCategories(type) {
    const select = document.getElementById('recurringCategory');
    if (!select) return;
    try {
        const res = await fetch(`/api/categories?type=${type || 'expense'}`);
        const data = await res.json();
        if (!data.success) return;
        const currentVal = select.value;
        select.innerHTML = '<option value="">请选择分类</option>';
        data.categories
            .filter(c => c.type === (type || 'expense'))
            .forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.name;
                opt.textContent = c.name;
                select.appendChild(opt);
            });
        if (currentVal) select.value = currentVal;
    } catch (e) {
        console.error('加载分类失败:', e);
    }
}

// 加载账户
async function loadRecurringAccounts() {
    const select = document.getElementById('recurringAccount');
    if (!select) return;
    try {
        const res = await fetch('/api/accounts');
        const data = await res.json();
        if (!data.success) return;
        select.innerHTML = '<option value="">默认账户</option>';
        (data.accounts || []).forEach(a => {
            const opt = document.createElement('option');
            opt.value = a.id;
            opt.textContent = a.name;
            select.appendChild(opt);
        });
    } catch (e) {
        console.error('加载账户失败:', e);
    }
}

// 保存规则
async function saveRecurringRule(event) {
    event.preventDefault();
    const editId = document.getElementById('editRecurringRuleId').value;
    const isEdit = !!editId;

    const data = {
        name: document.getElementById('recurringName').value.trim(),
        type: document.getElementById('recurringType').value,
        amount: parseFloat(document.getElementById('recurringAmount').value),
        category: document.getElementById('recurringCategory').value,
        period: document.getElementById('recurringPeriod').value,
        interval_value: parseInt(document.getElementById('recurringInterval').value) || 1,
        start_date: document.getElementById('recurringStartDate').value,
        end_date: document.getElementById('recurringEndDate').value || '',
        remark: document.getElementById('recurringRemark').value.trim(),
        account_id: document.getElementById('recurringAccount').value || null,
    };

    if (!data.name) { showNotification('请输入账单名称', 'error'); return; }
    if (!data.amount || data.amount <= 0) { showNotification('请输入有效金额', 'error'); return; }
    if (!data.category) { showNotification('请选择分类', 'error'); return; }
    if (!data.start_date) { showNotification('请选择开始日期', 'error'); return; }

    try {
        const url = isEdit ? `/api/recurring-rules/${editId}` : '/api/recurring-rules';
        const method = isEdit ? 'PUT' : 'POST';
        const res = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        const result = await res.json();
        if (result.success) {
            showNotification(result.message, 'success');
            closeModal('recurringFormModal');
            loadRecurringRules();
        } else {
            showNotification(result.message || '保存失败', 'error');
        }
    } catch (e) {
        showNotification('保存失败: ' + e.message, 'error');
    }
}

// 启用/停用规则
async function toggleRecurringRule(id) {
    try {
        const res = await fetch(`/api/recurring-rules/${id}/toggle`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showNotification(data.message, 'success');
            loadRecurringRules();
        } else {
            showNotification(data.message || '操作失败', 'error');
        }
    } catch (e) {
        showNotification('操作失败: ' + e.message, 'error');
    }
}

// 删除规则
async function deleteRecurringRule(id) {
    if (!confirm('确定删除该周期账单规则吗？')) return;
    try {
        const res = await fetch(`/api/recurring-rules/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            showNotification('规则已删除', 'success');
            loadRecurringRules();
        } else {
            showNotification(data.message || '删除失败', 'error');
        }
    } catch (e) {
        showNotification('删除失败: ' + e.message, 'error');
    }
}

// 周期选择变更时更新间隔标签
document.addEventListener('DOMContentLoaded', function() {
    const periodSelect = document.getElementById('recurringPeriod');
    const intervalLabel = document.getElementById('recurringIntervalLabel');
    if (periodSelect && intervalLabel) {
        periodSelect.addEventListener('change', function() {
            const labels = { daily: '天', weekly: '周', monthly: '月', yearly: '年' };
            intervalLabel.textContent = labels[this.value] || '周';
        });
    }
});

// ==================== 启动应用 ====================
document.addEventListener('DOMContentLoaded', init);
