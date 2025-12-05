# GitHub 設定指南

## 系統已經準備好推送到 GitHub！

本地 Git repository 已經初始化並完成第一個 commit。

### 📋 已完成的步驟

✅ Git repository 初始化
✅ 所有檔案已加入
✅ 第一個 commit 已創建
✅ .gitignore 已配置

### 🚀 接下來的步驟

#### 方法 1：在 GitHub 網站上創建 repository（推薦）

1. **前往 GitHub**
   - 登入 https://github.com
   - 點擊右上角的 `+` → `New repository`

2. **創建 Repository**
   - Repository name: `semiconductor-training-system` 或你喜歡的名稱
   - Description: `AI-powered semiconductor equipment fault handling training system with natural language simulation`
   - 選擇 Public 或 Private
   - **不要**勾選 "Initialize this repository with a README"（因為我們已經有了）
   - 點擊 `Create repository`

3. **連接本地與遠端**

   GitHub 會顯示指令，你可以使用這些指令（在項目目錄執行）：

   ```bash
   cd "c:\Users\user\Desktop\在職碩\OneDrive - 長庚大學\長庚碩班\論文\semiconductor_training_system"

   # 添加遠端 repository（替換 YOUR_USERNAME 為你的 GitHub 用戶名）
   git remote add origin https://github.com/YOUR_USERNAME/semiconductor-training-system.git

   # 推送代碼
   git branch -M main
   git push -u origin main
   ```

#### 方法 2：使用 GitHub Desktop（如果已安裝）

1. 打開 GitHub Desktop
2. File → Add Local Repository
3. 選擇項目資料夾
4. Publish repository 到 GitHub

### 📊 Repository 資訊

**Local Repository 狀態：**
- Branch: master
- Commits: 1
- Files: 30
- Lines of Code: 8892+

**已包含的檔案：**
- ✅ 核心模組（NLU, Scenario Engine, AI Advisor）
- ✅ 介面檔案（Simulation, Visual, Interactive）
- ✅ 完整文檔（README, Guides）
- ✅ 配置檔案（requirements.txt, .gitignore）

### 🔐 如果需要身份驗證

如果推送時要求身份驗證，你有幾個選擇：

#### 選項 1：Personal Access Token（推薦）

1. 前往 GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token (classic)
3. 選擇 scopes：`repo` (所有)
4. 生成並複製 token
5. 推送時使用 token 作為密碼

#### 選項 2：SSH Key

```bash
# 生成 SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# 複製公鑰
cat ~/.ssh/id_ed25519.pub

# 在 GitHub Settings → SSH and GPG keys 中添加
```

然後將遠端 URL 改為 SSH：
```bash
git remote set-url origin git@github.com:YOUR_USERNAME/semiconductor-training-system.git
```

### 📝 建議的 Repository 描述

**Title:**
Semiconductor Equipment Fault Handling Training System

**Description:**
An AI-powered interactive training system for semiconductor equipment fault diagnosis and handling. Features natural language understanding, dynamic fault progression, Socratic AI advisor, and real-time visualization.

**Topics (tags):**
- `semiconductor`
- `training-system`
- `ai-advisor`
- `natural-language-processing`
- `digital-twin`
- `fault-diagnosis`
- `gradio`
- `education`
- `simulation`

### 🌟 README 預覽

你的 repository 已經包含完整的 README.md，包括：
- 系統架構圖
- 功能特色
- 安裝指南
- 使用說明
- API 文檔
- 研究貢獻

### 📦 下一步：創建 Release

推送到 GitHub 後，可以創建第一個 release：

1. 前往 repository → Releases → Create a new release
2. Tag version: `v1.0.0`
3. Release title: `Initial Release - Natural Language Simulation Training`
4. Description: 描述主要功能

### 🔄 未來更新流程

當你做了更改後：

```bash
# 查看改動
git status

# 添加改動
git add .

# 提交改動
git commit -m "描述改動內容"

# 推送到 GitHub
git push
```

### ❓ 常見問題

**Q: 推送時卡住了？**
A: 可能是網路問題或認證問題，檢查 GitHub 登入狀態

**Q: 想要重新命名 repository？**
A: 在 GitHub repository Settings 中可以重新命名

**Q: 不小心推送了敏感資料？**
A: 立即刪除 commit 並使用 `git push --force`，或聯絡 GitHub support

### 📞 需要協助？

如果遇到問題：
1. 檢查 Git 配置：`git config --list`
2. 檢查遠端連接：`git remote -v`
3. 查看詳細錯誤訊息

---

**所有檔案已經準備好！只需要在 GitHub 上創建 repository 並推送即可。** 🎉
