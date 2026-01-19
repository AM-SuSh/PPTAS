<template>
  <div class="app-container">
    <!-- 顶部导航栏 -->
    <header class="navbar">
      <div class="logo">
        <span class="icon">📚</span>
        <span class="text">PPTAS 内容扩展智能体</span>
      </div>
      <div class="nav-actions">
        <button v-if="results.length" @click="reset" class="btn-outline">重新上传</button>
      </div>
    </header>

    <main class="main-content">
      <!-- 第一步：上传区域 (没有结果且不在处理中时显示) -->
      <section v-if="!results.length && !isProcessing" class="welcome-area">
        <div class="hero-text">
          <h1>将枯燥的 PPT 转化为深度复习笔记</h1>
          <p>自动识别逻辑层级，补充原理、公式推导及学术引用</p>
        </div>

        <div class="upload-box" @click="$refs.fileInput.click()" @dragover.prevent @drop.prevent="handleDrop">
          <input type="file" ref="fileInput" hidden @change="handleFileChange" accept=".pptx,.pdf" />
          <div class="upload-icon">📄</div>
          <p>点击或拖拽 PPT 文件到此处</p>
          <div class="file-support">支持 .pptx, .pdf (Max 20MB)</div>
        </div>

        <!-- 临时模拟按钮：让你没后端也能看效果 -->
        <button @click="showMockData" class="btn-mock">✨ 点击预览模拟效果 (无后端模式)</button>
      </section>

      <!-- 第二步：加载动画 -->
      <section v-if="isProcessing" class="loading-area">
        <div class="brain-animation">🧠</div>
        <div class="spinner"></div>
        <h3>AI 正在检索 Wikipedia 与 Arxiv...</h3>
        <p>正在为每页幻灯片生成原理说明与公式推导</p>
      </section>

      <!-- 第三步：结果展示区域 -->
      <section v-if="results.length" class="results-area">
        <div class="results-header">
          <h2>复习笔记：{{ fileName }}</h2>
          <button @click="window.print()" class="btn-primary">保存为 PDF 笔记</button>
        </div>

        <div v-for="(slide, index) in results" :key="index" class="slide-card">
          <div class="slide-info">
            <span class="page-number">SLIDE {{ slide.page_num }}</span>
            <h3 class="slide-title">{{ slide.title }}</h3>
          </div>

          <div class="content-split">
            <!-- 左侧：PPT 原始干货 -->
            <div class="original-content">
              <div class="label">PPT 原始要点</div>
              <ul>
                <li v-for="point in slide.raw_points" :key="point">{{ point }}</li>
              </ul>
            </div>

            <!-- 右侧：AI 扩展深度解释 -->
            <div class="expanded-content">
              <div class="label-ai">💡 AI 深度扩展</div>

              <!-- 模拟 Markdown 渲染的内容 -->
              <div class="markdown-body" v-html="slide.expanded_html"></div>

              <!-- 延伸阅读 -->
              <div v-if="slide.references.length" class="reference-section">
                <p>🔍 延伸阅读:</p>
                <ul>
                  <li v-for="ref in slide.references" :key="ref.url">
                    <a :href="ref.url" target="_blank">{{ ref.title }} <span>({{ ref.source }})</span></a>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const isProcessing = ref(false);
const results = ref([]);
const fileName = ref('未命名文档');

// 模拟数据函数：让你看清结果页面的样子
const showMockData = () => {
  isProcessing.value = true;
  fileName.value = "深度学习基础.pptx";

  // 模拟网络延迟
  setTimeout(() => {
    isProcessing.value = false;
    results.value = [
      {
        page_num: 1,
        title: "卷积神经网络 (CNN) 概念",
        raw_points: ["局部感受野", "权值共享", "池化层的作用"],
        expanded_html: `
          <p><strong>原理详解：</strong> 局部感受野模拟了生物视觉系统，只对局部区域的像素进行加权计算。</p>
          <div class="formula">数学表达：$y_{i,j} = \sigma(\sum_{m,n} w_{m,n} x_{i+m, j+n} + b)$</div>
          <p><strong>代码示例：</strong></p>
          <pre><code>nn.Conv2d(in_channels=3, out_channels=64, kernel_size=3)</code></pre>
        `,
        references: [
          { title: "LeCun 原始论文: Gradient-based learning", url: "#", source: "Arxiv" },
          { title: "CNN 维基百科页面", url: "#", source: "Wikipedia" }
        ]
      },
      {
        page_num: 2,
        title: "反向传播算法 (Backpropagation)",
        raw_points: ["链式法则", "损失函数", "权重更新"],
        expanded_html: `
          <p><strong>深度补充：</strong> 反向传播的本质是全微分的链式法则应用。通过计算损失函数对每个权重的偏导数来优化模型。</p>
          <p><strong>推导要点：</strong> $\frac{\partial L}{\partial w} = \frac{\partial L}{\partial y} \cdot \frac{\partial y}{\partial z} \cdot \frac{\partial z}{\partial w}$</p>
        `,
        references: [
          { title: "Deep Learning Book - Chapter 6", url: "#", source: "MIT Press" }
        ]
      }
    ];
  }, 1500);
};

const reset = () => {
  results.value = [];
};

const handleFileChange = (e) => {
  const file = e.target.files[0];
  if (file) {
    fileName.value = file.name;
    // 这里未来调用后端
    showMockData();
  }
};
</script>

<style scoped>
/* 样式部分：让界面看起来高级 */
.app-container { min-height: 100vh; background: #f4f7f9; }
.navbar { background: #fff; padding: 1rem 10%; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
.logo { display: flex; align-items: center; gap: 10px; font-weight: bold; font-size: 1.2rem; color: #2c3e50; }

.main-content { max-width: 1000px; margin: 40px auto; padding: 0 20px; }

/* 上传卡片 */
.welcome-area { text-align: center; margin-top: 100px; }
.hero-text h1 { color: #1a202c; margin-bottom: 10px; }
.hero-text p { color: #718096; margin-bottom: 40px; }
.upload-box { background: white; border: 2px dashed #cbd5e0; padding: 60px; border-radius: 20px; cursor: pointer; transition: 0.3s; }
.upload-box:hover { border-color: #4299e1; background: #ebf8ff; }
.upload-icon { font-size: 3rem; margin-bottom: 20px; }
.btn-mock { margin-top: 20px; background: none; border: 1px solid #4299e1; color: #4299e1; padding: 8px 16px; border-radius: 20px; cursor: pointer; }

/* 结果卡片 */
.results-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
.slide-card { background: white; border-radius: 16px; margin-bottom: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); overflow: hidden; }
.slide-info { background: #2d3748; color: white; padding: 15px 25px; display: flex; align-items: center; gap: 20px; }
.page-number { font-size: 0.8rem; background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 4px; }

.content-split { display: grid; grid-template-columns: 1fr 1.6fr; }
.original-content { padding: 25px; background: #f8fafc; border-right: 1px solid #edf2f7; }
.expanded-content { padding: 25px; }

.label { font-size: 0.75rem; color: #a0aec0; font-weight: bold; margin-bottom: 15px; text-transform: uppercase; }
.label-ai { font-size: 0.75rem; color: #4299e1; font-weight: bold; margin-bottom: 15px; text-transform: uppercase; }

.formula { background: #f7fafc; padding: 15px; border-radius: 8px; font-family: "Courier New", Courier, monospace; margin: 15px 0; border-left: 4px solid #4299e1; }
pre { background: #2d3748; color: #fff; padding: 15px; border-radius: 8px; font-size: 0.9rem; overflow-x: auto; }

.reference-section { margin-top: 20px; padding-top: 20px; border-top: 1px dashed #e2e8f0; }
.reference-section a { color: #3182ce; text-decoration: none; font-size: 0.9rem; display: block; margin-bottom: 5px; }
.reference-section span { color: #a0aec0; font-size: 0.8rem; }

/* 动画 */
.loading-area { text-align: center; padding: 100px 0; }
.spinner { width: 50px; height: 50px; border: 5px solid #e2e8f0; border-top-color: #4299e1; border-radius: 50%; animation: spin 1s linear infinite; margin: 20px auto; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>