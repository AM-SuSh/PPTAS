<script setup>
import {computed, onMounted, ref, watch, nextTick} from 'vue'

const props = defineProps({
  root: {type: Object, required: true}
})

const containerRef = ref(null)
const selected = ref(null)

// 视图状态
const pan = ref({x: 100, y: 100})
const zoom = ref(0.9)
const isPanning = ref(false)
const lastPos = ref({x: 0, y: 0})

// 布局参数
const CONFIG = {
  nodeHeight: 40,
  levelGap: 240,
  siblingGap: 20,
  charWidth: 14,
  padding: 20
}

// --- 布局引擎 ---
// 1. 计算每个节点所需的垂直空间和宽度
function computeMetrics(node) {
  const labelWidth = Math.max(100, (node.label?.length || 0) * CONFIG.charWidth + 30)
  node._width = labelWidth

  if (!node.children || node.children.length === 0) {
    node._areaHeight = CONFIG.nodeHeight
    return
  }

  let childrenHeight = 0
  node.children.forEach(child => {
    computeMetrics(child)
    childrenHeight += child._areaHeight + CONFIG.siblingGap
  })
  // 减去最后一个多余的间隔
  childrenHeight -= CONFIG.siblingGap

  node._areaHeight = Math.max(CONFIG.nodeHeight, childrenHeight)
}

// 2. 分配坐标 (X 轴按层级，Y 轴按子树居中)
function assignCoords(node, x, yStart) {
  const xPos = x
  const yPos = yStart + node._areaHeight / 2

  node._x = xPos
  node._y = yPos

  if (node.children && node.children.length > 0) {
    let currentY = yStart
    node.children.forEach(child => {
      assignCoords(child, x + CONFIG.levelGap, currentY)
      currentY += child._areaHeight + CONFIG.siblingGap
    })
  }
}

const layout = computed(() => {
  if (!props.root) return {nodes: [], edges: []}

  const rootCopy = JSON.parse(JSON.stringify(props.root))

  // 执行布局计算
  computeMetrics(rootCopy)
  assignCoords(rootCopy, 50, 50)

  const nodes = []
  const edges = []

  function flatten(node, parent = null) {
    nodes.push(node)
    if (parent) {
      edges.push({
        id: `${parent.id}-${node.id}`,
        x1: parent._x + parent._width,
        y1: parent._y,
        x2: node._x,
        y2: node._y
      })
    }
    (node.children || []).forEach(c => flatten(c, node))
  }

  flatten(rootCopy)
  return {nodes, edges}
})

// --- 交互逻辑 ---
const onWheel = (e) => {
  e.preventDefault()
  const delta = e.deltaY > 0 ? -0.05 : 0.05
  const newZoom = zoom.value + delta
  zoom.value = Math.min(2, Math.max(0.2, newZoom))
}

const startPan = (e) => {
  if (e.button !== 0) return // 仅限左键
  isPanning.value = true
  lastPos.value = {x: e.clientX, y: e.clientY}
}

const doPan = (e) => {
  if (!isPanning.value) return
  const dx = e.clientX - lastPos.value.x
  const dy = e.clientY - lastPos.value.y
  pan.value.x += dx
  pan.value.y += dy
  lastPos.value = {x: e.clientX, y: e.clientY}
}

const endPan = () => isPanning.value = false

// 初始化视图位置
watch(() => props.root, () => {
  selected.value = null
  pan.value = {x: 80, y: window.innerHeight / 3}
  zoom.value = 0.8
}, {immediate: true})

onMounted(() => {
  containerRef.value?.addEventListener('wheel', onWheel, {passive: false})
})
</script>

<template>
  <div class="mindmap-container" ref="containerRef"
       @mousedown="startPan" @mousemove="doPan" @mouseup="endPan" @mouseleave="endPan">

    <!-- 画布主体 -->
    <svg class="mindmap-svg">
      <defs>
        <filter id="nodeShadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.1"/>
        </filter>
      </defs>

      <g :transform="`translate(${pan.x}, ${pan.y}) scale(${zoom})`">
        <!-- 连线 (贝塞尔曲线) -->
        <path v-for="edge in layout.edges" :key="edge.id" class="edge-line"
              :d="`M ${edge.x1} ${edge.y1} C ${(edge.x1 + edge.x2)/2} ${edge.y1}, ${(edge.x1 + edge.x2)/2} ${edge.y2}, ${edge.x2} ${edge.y2}`"/>

        <!-- 节点 -->
        <g v-for="node in layout.nodes" :key="node.id"
           class="node-group" :class="{ 'is-selected': selected?.id === node.id }"
           :transform="`translate(${node._x}, ${node._y - 20})`"
           @click.stop="selected = node">

          <rect class="node-card" :width="node._width" height="40" rx="8"/>
          <text class="node-label" :x="15" :y="25">{{ node.label }}</text>

          <!-- 类型小标记 -->
          <circle v-if="node.meta?.kind === 'slide'" cx="5" cy="20" r="3" fill="#3b82f6"/>
        </g>
      </g>
    </svg>

    <!-- 底部操作提示 -->
    <div class="controls-hint">
      滚轮缩放 · 左键按住拖拽 · 点击查看详情
    </div>

    <!-- 悬浮详情面板 (不再挤占空间) -->
    <Transition name="slide">
      <div v-if="selected" class="detail-panel">
        <div class="detail-header">
          <h3>节点详情</h3>
          <button @click="selected = null" class="close-btn">✕</button>
        </div>
        <div class="detail-content">
          <div class="info-row">
            <label>标题</label>
            <p>{{ selected.label }}</p>
          </div>
          <div v-if="selected.meta?.kind" class="info-row">
            <label>类型</label>
            <span class="badge">{{ selected.meta.kind }}</span>
          </div>
          <div v-if="selected.meta?.page_num" class="info-row">
            <label>对应页码</label>
            <p>第 {{ selected.meta.page_num }} 页</p>
          </div>

          <div v-if="selected.meta?.images?.length" class="detail-section">
            <label>视觉素材</label>
            <div class="image-placeholder" v-for="img in selected.meta.images" :key="img">
              <span class="icon">🖼️</span> {{ img.split('/').pop() }}
            </div>
          </div>

          <div v-if="selected.meta?.references?.length" class="detail-section">
            <label>参考引用</label>
            <a v-for="ref in selected.meta.references" :key="ref.url" :href="ref.url" target="_blank" class="ref-link">
              {{ ref.title }} <small>{{ ref.source }}</small>
            </a>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.mindmap-container {
  position: relative;
  width: 100%;
  height: 100%;
  background-color: #fcfcfd;
  background-image: radial-gradient(#e5e7eb 1px, transparent 1px);
  background-size: 30px 30px;
  overflow: hidden;
  cursor: grab;
}

.mindmap-container:active {
  cursor: grabbing;
}

.mindmap-svg {
  width: 100%;
  height: 100%;
  display: block;
}

/* 连线样式 */
.edge-line {
  fill: none;
  stroke: #cbd5e1;
  stroke-width: 1.5;
  transition: all 0.3s;
}

/* 节点样式 */
.node-group {
  cursor: pointer;
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.node-card {
  fill: #ffffff;
  stroke: #e2e8f0;
  stroke-width: 1;
  filter: url(#nodeShadow);
}

.node-group:hover .node-card {
  stroke: #94a3b8;
  fill: #f8fafc;
}

.node-group.is-selected .node-card {
  stroke: #3b82f6;
  stroke-width: 2;
  fill: #eff6ff;
}

.node-label {
  font-size: 13px;
  font-weight: 500;
  fill: #1e293b;
  pointer-events: none;
  user-select: none;
}

/* 详情面板 (浮动) */
.detail-panel {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 320px;
  max-height: calc(100% - 40px);
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(226, 232, 240, 0.8);
  display: flex;
  flex-direction: column;
  z-index: 100;
}

.detail-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-header h3 {
  margin: 0;
  font-size: 1.1rem;
  color: #0f172a;
}

.close-btn {
  background: #f1f5f9;
  border: none;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
  color: #64748b;
}

.detail-content {
  padding: 20px;
  overflow-y: auto;
}

.info-row {
  margin-bottom: 16px;
}

.info-row label {
  display: block;
  font-size: 11px;
  text-transform: uppercase;
  color: #94a3b8;
  margin-bottom: 4px;
  letter-spacing: 0.05em;
}

.info-row p {
  margin: 0;
  color: #1e293b;
  line-height: 1.5;
  font-size: 14px;
}

.badge {
  display: inline-block;
  padding: 2px 8px;
  background: #dbeafe;
  color: #1e40af;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.detail-section {
  margin-top: 20px;
}

.detail-section label {
  display: block;
  font-weight: 600;
  font-size: 13px;
  margin-bottom: 8px;
}

.image-placeholder {
  background: #f8fafc;
  border: 1px dashed #e2e8f0;
  padding: 8px;
  border-radius: 6px;
  font-size: 12px;
  color: #64748b;
  margin-bottom: 6px;
}

.ref-link {
  display: block;
  padding: 10px;
  background: #f8fafc;
  border-radius: 8px;
  text-decoration: none;
  color: #3b82f6;
  font-size: 13px;
  margin-bottom: 8px;
}

.controls-hint {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(15, 23, 42, 0.7);
  color: white;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 12px;
  backdrop-filter: blur(4px);
  pointer-events: none;
}

/* 动画 */
.slide-enter-active, .slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from, .slide-leave-to {
  transform: translateX(50px);
  opacity: 0;
}
</style>