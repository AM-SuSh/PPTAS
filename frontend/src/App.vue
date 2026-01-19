<script setup>
import {ref, onMounted, onUnmounted} from 'vue';
import Navbar from './components/Navbar.vue';
import UploadZone from './components/UploadZone.vue';
import Workspace from './components/Workspace.vue';
import {pptApi} from './api/index.js';

// 应用状态
const appState = ref('upload'); // 'upload' | 'workspace'
const isLoading = ref(false);
const fileName = ref('');
const slidesData = ref([]);

// 上传处理
const handleFileUpload = async (file) => {
  fileName.value = file ? file.name : "深度学习架构分析.pptx";
  isLoading.value = true;
  appState.value = 'upload'; // 保持在上传界面显示加载

  try {
    // 模拟 API 调用，实际应替换为 uploadAndParsePPT
    await new Promise(resolve => setTimeout(resolve, 1500));

    // 模拟返回数据
    slidesData.value = [
      {
        page_num: 1,
        title: "Transformer 结构总览",
        image: "https://via.placeholder.com/960x720?text=Slide+1",
        raw_points: ["Encoder-Decoder 架构", "自注意力机制", "进入工作台"],
        expanded_html: "<p><strong>核心概念：</strong>Transformer 是一种完全基于注意力机制的架构，摒弃了传统的循环和卷积网络。</p>",
        references: [{title: "Attention Is All You Need", url: "#", source: "Arxiv"}]
      },
      {
        page_num: 2,
        title: "Self-Attention 机制详解",
        image: "https://via.placeholder.com/960x720?text=Slide+2",
        raw_points: ["Q, K, V 向量计算", "缩放点积", "Softmax 归一化"],
        expanded_html: "<p><strong>计算公式：</strong>Attention(Q, K, V) = softmax(QK^T / √d_k)V。</p>",
        references: [{title: "Self-Attention Networks", url: "#", source: "Arxiv"}]
      }
    ];

    appState.value = 'workspace';
  } catch (error) {
    console.error("上传失败", error);
    alert("解析失败，请重试");
  } finally {
    isLoading.value = false;
  }
};

const resetApp = () => {
  appState.value = 'upload';
  slidesData.value = [];
  fileName.value = '';
};
</script>

<template>
  <div class="app-container">
    <!-- 顶部导航 -->
    <Navbar>
      <div v-if="appState === 'workspace'" class="workspace-controls">
        <span class="file-name-display">{{ fileName }}</span>
        <button @click="resetApp" class="btn-close">✕ 关闭</button>
      </div>
    </Navbar>

    <!-- 上传页 -->
    <main v-if="appState === 'upload'" class="upload-main">
      <UploadZone
          v-if="!isLoading"
          @file-selected="handleFileUpload"
          @mock-click="handleFileUpload"
      />

      <!-- 加载状态 -->
      <div v-if="isLoading" class="loading-overlay">
        <div class="spinner"></div>
        <h3>正在解析 PPT 结构...</h3>
        <p>提取语义层级并构建知识图谱</p>
      </div>
    </main>

    <!-- 工作台页 (核心布局) -->
    <Workspace
        v-if="appState === 'workspace'"
        :slides="slidesData"
    />
  </div>
</template>

<style scoped>
.app-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.upload-main {
  flex: 1;
  overflow-y: auto;
  background: #f8fafc;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2rem;
}

.workspace-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.file-name-display {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.9rem;
  background: rgba(255, 255, 255, 0.1);
  padding: 4px 12px;
  border-radius: 4px;
}

.btn-close {
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.4);
  color: #fca5a5;
  padding: 4px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: 0.3s;
}

.btn-close:hover {
  background: rgba(239, 68, 68, 0.4);
  color: white;
}

.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #64748b;
}

.spinner {
  width: 60px;
  height: 60px;
  border: 5px solid #e2e8f0;
  border-top: 5px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>
