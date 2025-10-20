# Frontend Features Guide

## Overview

Your DollarClub frontend provides comprehensive script management and monitoring capabilities with a clean, modern UI.

---

## Pages Overview

### 1. **Dashboard** (`/dashboard`)

**Purpose**: Quick overview of script activity

**Features**:
- ✅ Total scripts count
- ✅ Running scripts count
- ✅ Completed scripts count
- ✅ Failed scripts count
- ✅ Recent 5 scripts with status
- ✅ Quick links to view all scripts

**Use Case**: Get a quick snapshot of your trading platform's activity

---

### 2. **Scripts** (`/scripts`)

**Purpose**: Full script management interface

**Features**:

#### **Upload Scripts**:
- ✅ Drag & drop file upload
- ✅ Click to select files
- ✅ File type validation (`.py`, `.js`, `.ts`)
- ✅ Size limit: 10MB
- ✅ Real-time upload feedback

#### **Manage Scripts**:
- ✅ **Start** (▶️ Play button) - Execute a script
  - Click play button to start execution
  - Script status changes to "running"
  - Real-time log capture begins
  
- ✅ **Stop** (⏹️ Square button) - Cancel running script
  - Only available for running scripts
  - Kills the process immediately
  - Marks script as "cancelled"
  
- ✅ **Remove** (🗑️ Trash button) - Delete script
  - Permanently deletes script and file
  - Cannot delete running scripts
  - Confirmation dialog

- ✅ **View Logs** (⬇️ Download button) - See execution output
  - Real-time execution logs
  - Error messages
  - Execution history

#### **Script Information**:
- Original filename
- Unique filename (UUID)
- File size
- Status badge (uploaded, running, completed, failed, cancelled)
- Creation date
- Execution timestamps

---

### 3. **Monitor** (`/monitor`) 🆕

**Purpose**: Real-time performance monitoring and analytics

**Features**:

#### **Key Performance Indicators (KPIs)**:
1. **Total Executions**
   - Count of all script runs
   - All-time metric
   - Activity icon indicator

2. **Success Rate**
   - Percentage of successful executions
   - Completed / Total ratio
   - Trend indicator (up/down)

3. **Average Execution Time**
   - Mean duration per script
   - Formatted as hours/minutes/seconds
   - Performance indicator

4. **Active Scripts**
   - Currently running scripts
   - Live count with pulse animation
   - Real-time updates every 5 seconds

#### **Status Distribution**:
- Visual breakdown by status:
  - 🟢 Completed (green)
  - 🔵 Running (blue)
  - 🔴 Failed (red)
  - 🟡 Uploaded (yellow)
- Percentage calculations
- Color-coded indicators

#### **System Health**:
- Success rate health bar
- Active scripts monitoring
- Failed scripts tracking
- Overall health status:
  - 🟢 **Healthy**: Success rate ≥ 80%
  - 🟡 **Warning**: Success rate 50-79%
  - 🔴 **Critical**: Success rate < 50%

#### **Recent Executions**:
- Last 10 script runs
- Execution timeline
- Duration tracking
- Time ago formatting ("5m ago", "2h ago")

**Refresh Rate**: Auto-refreshes every 5 seconds for real-time monitoring

---

### 4. **Settings** (`/settings`)

**Purpose**: Account and integration management

**Features**:
- ✅ Account information
- ✅ Email and username display
- ✅ Account type (Email/Google)
- ✅ Member since date
- ✅ Verification status
- ✅ IBKR integration
- ✅ Security settings (2FA, password change)
- ✅ Danger zone (account deletion)

---

## Script Actions Workflow

### **1. Upload & Execute Flow**

```
Upload Script → Saved → Click Execute → Celery Task → Running → Completed/Failed
```

**Steps**:
1. Go to **Scripts** page
2. Drag & drop `.py` file or click to select
3. File uploads immediately
4. Click ▶️ Play button to execute
5. Monitor status in real-time
6. Click ⬇️ Download to view logs

### **2. Cancel Running Script**

```
Running Script → Click Stop → Process Killed → Status: Cancelled
```

**Steps**:
1. Find running script (blue "running" badge)
2. Click ⏹️ Square button
3. Process terminates immediately
4. Logs show "[Script cancelled by user]"

### **3. Delete Script**

```
Non-Running Script → Click Delete → Confirm → File & Record Removed
```

**Steps**:
1. Find script (not running)
2. Click 🗑️ Trash button
3. Confirm deletion in dialog
4. Script and file permanently deleted

---

## Real-time Features

### **Auto-Refresh**:
- **Dashboard**: 30 seconds
- **Scripts**: 30 seconds
- **Monitor**: 5 seconds (fastest for real-time monitoring)

### **Live Status Updates**:
- Script status changes reflected automatically
- Log updates during execution
- Progress indicators for running scripts

---

## UI Components

### **Status Badges**:
- 🔵 **Running** - Script is executing (with spinner animation)
- 🟢 **Completed** - Successful execution
- 🔴 **Failed** - Execution error
- ⚪ **Cancelled** - User-terminated
- 🟡 **Uploaded** - Ready to execute

### **Action Buttons**:
- **Primary** (green) - Start execution
- **Danger** (red) - Stop or delete
- **Info** (blue) - View logs
- **Disabled** - Greyed out when action not available

---

## Performance Metrics Explained

### **Success Rate**:
```
Success Rate = (Completed Scripts / Total Scripts) × 100
```
- **Good**: ≥ 80%
- **Acceptable**: 50-79%
- **Poor**: < 50%

### **Average Execution Time**:
```
Avg Time = Σ(completion_time - start_time) / Total Completed Scripts
```
- Calculated from completed scripts only
- Excludes failed or cancelled executions

### **System Health Score**:
```
Health = f(Success Rate, Active Scripts, Failed Scripts)
```
- Considers multiple metrics
- Weighted towards success rate
- Real-time health indicator

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + U` | Upload script (when on Scripts page) |
| `Ctrl/Cmd + M` | Go to Monitor |
| `Ctrl/Cmd + S` | Go to Scripts |
| `Ctrl/Cmd + D` | Go to Dashboard |

*(Note: Shortcuts need to be implemented if desired)*

---

## Tips & Best Practices

### **📊 Monitoring**:
1. Check **Monitor** page regularly for system health
2. Watch for declining success rates
3. Monitor average execution times for performance degradation
4. Keep failed scripts under control

### **📝 Script Management**:
1. Name scripts descriptively
2. Test scripts before production use
3. Monitor logs during first execution
4. Delete old/unused scripts regularly

### **⚡ Performance**:
1. Limit concurrent executions (max 5 by default)
2. Cancel stuck scripts promptly
3. Review failed scripts to identify issues
4. Use Monitor page for bottleneck identification

---

## Troubleshooting

### **Script Stays "Running" Forever**
**Solution**: 
1. Click Stop button
2. If still stuck, check Celery worker is running
3. Backend may need restart

### **Upload Fails**
**Causes**:
- File too large (>10MB)
- Wrong file type (must be .py, .js, .ts)
- Network error

**Solution**: Check file size and type, retry upload

### **Can't Delete Script**
**Cause**: Script is running

**Solution**: Stop the script first, then delete

### **Logs Not Updating**
**Cause**: Auto-refresh paused or network issue

**Solution**: 
1. Refresh browser
2. Check network connection
3. Verify backend is running

---

## Mobile Responsive

✅ All pages are mobile-responsive:
- Sidebar collapses to hamburger menu
- Tables scroll horizontally
- Cards stack vertically
- Touch-friendly buttons

---

## Next Steps

- [ ] Try uploading a test script
- [ ] Execute the script and monitor logs
- [ ] Check the Monitor page for real-time metrics
- [ ] Practice starting and stopping scripts
- [ ] Delete test scripts when done

**Your frontend is ready to manage trading scripts! 🚀**

