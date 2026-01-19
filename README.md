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
│   │    ├── ContentView.vue         // 顶部导航与状态
│   │    ├── LoadingState.vue     // 文件上传与拖拽
│   │    ├── Navbar.vue         // 顶部导航与状态
│   │    ├── PPTPreview.vue     // 左侧PPT
│   │    ├── SlideCard.vue      // 核心：单页 PPT 内容对比卡片
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