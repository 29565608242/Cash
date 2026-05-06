/**
 * 数据工具（导入/导出）前端逻辑
 */

// 状态
let currentUploadId = null;
let currentColumns = [];
let currentTotalRows = 0;
let exportPollTimer = null;
let exportPage = 1;

// DOM 引用
const $ = (id) => document.getElementById(id);

// ==================== Tab 切换 ====================
function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    if (tab === 'import') {
        document.querySelector('.tab-btn').classList.add('active');
        $('tab-import').classList.add('active');
    } else {
        document.querySelectorAll('.tab-btn')[1].classList.add('active');
        $('tab-export').classList.add('active');
        loadExportHistory();
    }
}

// ==================== 通知 ====================
let notiTimer = null;
function showNotification(message, type) {
    const el = $('notification');
    el.textContent = message;
    el.className = 'notification ' + type + ' show';
    clearTimeout(notiTimer);
    notiTimer = setTimeout(() => el.classList.remove('show'), 4000);
}

// ==================== 导入：文件上传 ====================
function handleFileSelect(input) {
    const file = input.files[0];
    if (!file) return;
    uploadFile(file);
}

// 拖拽上传
const uploadZone = $('uploadZone');
uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragover');
});
uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('dragover');
});
uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
});

async function uploadFile(file) {
    // 校验
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['csv', 'xlsx', 'xls'].includes(ext)) {
        showNotification('不支持的文件格式', 'error');
        return;
    }

    // 隐藏旧结果
    $('mapping-panel').style.display = 'none';
    $('preview-panel').style.display = 'none';
    $('result-panel').style.display = 'none';
    $('uploadProgress').style.display = 'block';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const resp = await fetch('/api/import/upload', { method: 'POST', body: formData });
        const data = await resp.json();

        $('uploadProgress').style.display = 'none';

        if (!data.success) {
            showNotification(data.message || '上传失败', 'error');
            return;
        }

        currentUploadId = data.upload_id;
        currentColumns = data.columns;
        currentTotalRows = data.total_rows;

        // 显示映射
        renderColumnMapping(data.columns, data.auto_mapping);
        $('mapping-panel').style.display = 'block';

        // 显示预览
        renderPreview(data.sample_rows, data.columns);
        $('preview-panel').style.display = 'block';
        $('previewCount').textContent = `（共 ${data.total_rows} 行，显示前 ${data.sample_rows.length} 行）`;

        showNotification(`文件解析成功，共 ${data.total_rows} 条记录`, 'success');
    } catch (e) {
        $('uploadProgress').style.display = 'none';
        showNotification('上传失败: ' + e.message, 'error');
    }
}

// ==================== 导入：列映射 ====================
function renderColumnMapping(columns, autoMapping) {
    const container = $('mappingContainer');
    container.innerHTML = '';

    const fields = [
        { key: 'type', label: '类型 *', required: true },
        { key: 'amount', label: '金额 *', required: true },
        { key: 'category', label: '分类 *', required: true },
        { key: 'date', label: '日期 *', required: true },
        { key: 'time', label: '时间', required: false },
        { key: 'remark', label: '备注', required: false },
        { key: 'currency', label: '币种', required: false },
        { key: 'original_amount', label: '原币金额', required: false },
    ];

    const optionsHtml = '<option value="">-- 不导入 --</option>' +
        columns.map(c => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join('');

    fields.forEach(field => {
        const autoMatched = autoMapping[field.key];
        const row = document.createElement('div');
        row.className = 'mapping-row';

        const labelSpan = document.createElement('span');
        labelSpan.className = 'mapping-field';
        labelSpan.innerHTML = field.label + (field.required ? '<span class="required">*</span>' : '') +
            (autoMatched ? '<span class="auto-tag">✓ 自动</span>' : '');

        const select = document.createElement('select');
        select.className = 'mapping-select';
        select.id = `map-${field.key}`;
        select.innerHTML = optionsHtml;
        if (autoMatched) select.value = autoMatched;

        row.appendChild(labelSpan);
        row.appendChild(select);
        container.appendChild(row);
    });
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ==================== 导入：预览表格 ====================
function renderPreview(rows, columns) {
    const container = $('previewContainer');
    if (!rows || rows.length === 0) {
        container.innerHTML = '<p class="text-muted">无数据</p>';
        return;
    }

    let html = '<table class="preview-table"><thead><tr>';
    columns.forEach(c => { html += `<th>${escapeHtml(c)}</th>`; });
    html += '</tr></thead><tbody>';

    rows.forEach(row => {
        html += '<tr>';
        columns.forEach((_, idx) => {
            html += `<td>${escapeHtml(String(row[idx] || ''))}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    container.innerHTML = html;
}

// ==================== 导入：确认导入 ====================
async function submitImport() {
    if (!currentUploadId) {
        showNotification('请先上传文件', 'error');
        return;
    }

    const mapping = {};
    const fields = ['type', 'amount', 'category', 'date', 'time', 'remark', 'currency', 'original_amount'];
    fields.forEach(f => {
        const sel = $(`map-${f}`);
        if (sel && sel.value) mapping[f] = sel.value;
    });

    // 检查必填字段
    const required = ['type', 'amount', 'category', 'date'];
    const missing = required.filter(f => !mapping[f]);
    if (missing.length > 0) {
        const names = { type: '类型', amount: '金额', category: '分类', date: '日期' };
        showNotification('请映射必填字段: ' + missing.map(f => names[f]).join(', '), 'error');
        return;
    }

    const btn = $('importBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> 导入中...';

    try {
        const resp = await fetch('/api/import/confirm', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                upload_id: currentUploadId,
                mapping: mapping,
                skip_errors: $('skipErrors').checked,
            })
        });
        const data = await resp.json();

        if (data.success) {
            showNotification(`导入成功: ${data.imported} 条`, 'success');
            renderImportResult(data);
            $('result-panel').style.display = 'block';
            // 重置上传状态
            currentUploadId = null;
            $('fileInput').value = '';
        } else {
            showNotification(data.message || '导入失败', 'error');
            if (data.imported > 0) {
                renderImportResult(data);
                $('result-panel').style.display = 'block';
            }
        }
    } catch (e) {
        showNotification('导入失败: ' + e.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '📥 确认导入';
    }
}

// ==================== 导入：结果 ====================
function renderImportResult(data) {
    const container = $('resultContainer');

    let html = '<div class="result-summary">';
    html += `<div class="result-item"><div class="num success">${data.imported}</div><div class="label">成功导入</div></div>`;
    html += `<div class="result-item"><div class="num ${data.skipped > 0 ? 'warning' : 'success'}">${data.skipped}</div><div class="label">跳过</div></div>`;
    html += `<div class="result-item"><div class="num ${data.errors && data.errors.length > 0 ? 'danger' : 'success'}">${data.errors ? data.errors.length : 0}</div><div class="label">错误</div></div>`;
    html += '</div>';

    if (data.errors && data.errors.length > 0) {
        html += '<div class="error-list">';
        data.errors.forEach(e => {
            html += `<div class="error-item">行 ${e.row}: ${escapeHtml(e.message)}</div>`;
        });
        if (data.errors.length > 50) {
            html += `<div class="error-item">... 还有 ${data.errors.length - 50} 个错误</div>`;
        }
        html += '</div>';
    }

    container.innerHTML = html;
}

// ==================== 导出：创建导出 ====================
async function submitExport() {
    const startDate = $('exportStartDate').value;
    const endDate = $('exportEndDate').value;
    const accountId = $('exportAccountId').value;
    const format = $('exportFormat').value;
    const email = $('exportEmail').value.trim();

    const btn = $('exportBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> 处理中...';

    try {
        const resp = await fetch('/api/export/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                start_date: startDate,
                end_date: endDate,
                account_id: accountId ? parseInt(accountId) : null,
                format: format,
                email_to: email || null,
            })
        });
        const data = await resp.json();

        if (!data.success) {
            showNotification(data.message || '导出失败', 'error');
            btn.disabled = false;
            btn.innerHTML = '📤 开始导出';
            return;
        }

        if (data.sync) {
            // 同步导出：直接下载
            showNotification(`导出完成，共 ${data.total_records} 条`, 'success');
            if (data.download_url) {
                window.location.href = data.download_url;
            }
            btn.disabled = false;
            btn.innerHTML = '📤 开始导出';
            loadExportHistory();
        } else {
            // 异步导出：轮询进度
            showNotification(`后台导出中（${data.total_records} 条），请稍候...`, 'info');
            startExportPolling(data.task_id);
            $('exportProgressPanel').style.display = 'block';
            $('exportProgressInfo').innerHTML = `<p>导出 ${data.total_records} 条记录，后台处理中...</p>`;
            btn.disabled = false;
            btn.innerHTML = '📤 开始导出';
        }
    } catch (e) {
        showNotification('导出失败: ' + e.message, 'error');
        btn.disabled = false;
        btn.innerHTML = '📤 开始导出';
    }
}

// ==================== 导出：轮询进度 ====================
function startExportPolling(taskId) {
    clearInterval(exportPollTimer);
    $('exportProgressFill').style.width = '0%';

    exportPollTimer = setInterval(async () => {
        try {
            const resp = await fetch(`/api/export/status/${taskId}`);
            const data = await resp.json();

            if (!data.success) {
                clearInterval(exportPollTimer);
                return;
            }

            // 更新进度
            const progress = data.progress || 0;
            if (data.status === 'processing') {
                $('exportProgressFill').style.width = '50%';
                $('exportProgressInfo').innerHTML = `<p>正在生成文件...（${data.total_records || '?'} 条记录）</p>`;
            }

            if (data.status === 'completed') {
                clearInterval(exportPollTimer);
                $('exportProgressFill').style.width = '100%';
                $('exportProgressInfo').innerHTML = `<p>✅ 导出完成（${data.total_records} 条）</p>`;

                let actionsHtml = '';
                if (data.download_url) {
                    actionsHtml += `<a href="${data.download_url}" class="btn btn-success btn-sm">⬇️ 下载文件</a> `;
                }
                // 添加重新导出按钮
                actionsHtml += `<button class="btn btn-outline btn-sm" onclick="$('exportProgressPanel').style.display='none'">关闭</button>`;
                $('exportActions').innerHTML = actionsHtml;

                showNotification('导出完成', 'success');
                loadExportHistory();
            }

            if (data.status === 'failed') {
                clearInterval(exportPollTimer);
                $('exportProgressFill').style.width = '0%';
                $('exportProgressFill').style.background = '#f5576c';
                $('exportProgressInfo').innerHTML = `<p>❌ 导出失败: ${escapeHtml(data.error_message || '未知错误')}</p>`;
                showNotification('导出失败', 'error');
            }
        } catch (e) {
            // 网络错误，继续轮询
        }
    }, 2000);
}

// ==================== 导出：历史任务 ====================
async function loadExportHistory(page) {
    if (page != null) exportPage = page;
    const container = $('exportTaskList');
    try {
        const resp = await fetch(`/api/export/list?page=${exportPage}&per_page=8`);
        const data = await resp.json();

        if (!data.success || !data.tasks || data.tasks.length === 0) {
            container.innerHTML = '<p class="text-muted">暂无导出记录</p>';
            return;
        }

        let html = '<div class="task-list">';
        data.tasks.forEach(t => {
            const statusClass = t.status === 'completed' ? 'completed' :
                t.status === 'failed' ? 'failed' :
                t.status === 'processing' ? 'processing' : 'pending';
            const statusText = t.status === 'completed' ? '已完成' :
                t.status === 'failed' ? '失败' :
                t.status === 'processing' ? '处理中' : '等待中';

            const created = t.created_at ? new Date(t.created_at).toLocaleString() : '';
            const fileSize = t.file_size ? formatFileSize(t.file_size) : '';
            const records = t.total_records ? `${t.total_records} 条` : '';
            const format = t.file_format ? t.file_format.toUpperCase() : '';

            html += `<div class="task-item">
                <div class="task-info">
                    <div><strong>${format}</strong> ${records} ${fileSize}</div>
                    <div class="task-meta">${created}</div>
                </div>
                <div style="display:flex;align-items:center;gap:10px;">
                    <span class="task-status ${statusClass}">${statusText}</span>`;

            if (t.download_url) {
                html += `<a href="${t.download_url}" class="btn btn-success btn-sm">⬇️</a>`;
            }

            html += `<button class="btn btn-danger btn-sm" onclick="deleteExport(${t.id})" style="font-size:0.8rem;padding:6px 10px;">🗑️</button>`;

            html += `</div></div>`;
        });
        html += '</div>';

        // 分页控件
        if (data.pages > 1) {
            html += '<div style="display:flex;justify-content:center;align-items:center;gap:12px;margin-top:12px;">';
            html += `<button class="btn btn-outline btn-sm" onclick="loadExportHistory(${exportPage - 1})" ${exportPage <= 1 ? 'disabled style="opacity:0.4"' : ''}>← 上一页</button>`;
            html += `<span style="font-size:0.9rem;color:#666;">第 ${data.page}/${data.pages} 页</span>`;
            html += `<button class="btn btn-outline btn-sm" onclick="loadExportHistory(${exportPage + 1})" ${exportPage >= data.pages ? 'disabled style="opacity:0.4"' : ''}>下一页 →</button>`;
            html += '</div>';
        }

        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = '<p class="text-muted">加载失败</p>';
    }
}

async function deleteExport(taskId) {
    if (!confirm('确定删除此导出记录？')) return;
    try {
        const resp = await fetch(`/api/export/delete/${taskId}`, { method: 'POST' });
        const data = await resp.json();
        if (data.success) {
            showNotification('已删除', 'success');
            loadExportHistory();
        } else {
            showNotification(data.message || '删除失败', 'error');
        }
    } catch (e) {
        showNotification('删除失败: ' + e.message, 'error');
    }
}

function formatFileSize(bytes) {
    if (!bytes) return '';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
}

// ==================== 初始化 ====================
// 自动加载导出历史（如果导出 tab 默认可见）
document.addEventListener('DOMContentLoaded', () => {
    // 设置默认日期范围
    const now = new Date();
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
    $('exportStartDate').value = formatDate(firstDay);
    $('exportEndDate').value = formatDate(now);
});

function formatDate(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
}
