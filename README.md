环境配置
```python
conda create -n PPTAS python=3.9 
```

前端配置与运行：
```
cd PPTAS/frontend
npm install 
npm run dev
```

前端架构
```
frontend/
├──src/
│   ├── api/
│   │    ├── index.js
│   │    └── 123
│   ├── components/
│   │    ├── ContentView.vue    // 内容展示，目前是预设
│   │    ├── LoadingState.vue     
│   │    ├── MindmapGraph.vue   // 思维导图图像显示逻辑
│   │    ├── MindmapTree.vue    // 思维导图树结构
│   │    ├── Navbar.vue         // 顶部导航与状态
│   │    ├── PPTPreview.vue     // 左侧PPT
│   │    ├── SlideCard.vue      // 单页 PPT 内容对比卡片
│   │    ├── ToolSidebar.vue    // 功能工具栏
│   │    ├── UploadZone.vue     // 上传区域
│   │    └── Wordspace.vue      // 核心工作区，PPT预览和扩展内容
│   ├── utils/
│   │    ├── pptParser.js
│   │    ├── 123
│   │    ├── 123
│   │    └── searchEngine.js
│   ├── style.css              // 全局基础样式
│   ├── App.vue                // 主页面逻辑组合
│   └── main.js                // 入口文件
├── index.html
├── package.json
├── package-lock.json
└── vite.config.js
```

后端配置与运行：
```
cd PPTAS/backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

docker 部署：

前置条件：
- 已安装 Docker 运行时环境（Windows/Mac 使用 Docker Desktop，Linux 使用 Docker Engine）
- Docker daemon 进程已启动并运行

```
# 启动容器
docker-compose up --build -d

# 访问应用
# 前端：http://localhost
# 后端 API：http://localhost:8000/docs

# 查看日志
docker-compose logs -f backend

# 停止容器
docker-compose down
```

为支持 PPTX 文件的预览功能，需要安装 LibreOffice：
- Windows: 从 https://www.libreoffice.org/ 下载并安装（请不要变更下载位置，保持默认安全路径）
- Linux: `sudo apt-get install libreoffice` 或 `sudo yum install libreoffice`
- Mac: `brew install --cask libreoffice`

安装后，系统会自动检测 LibreOffice 并将 PPTX 文件转换为 PDF 以便在前端显示预览。