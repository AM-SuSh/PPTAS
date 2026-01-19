<script setup>
import { ref, computed } from 'vue'
import ToolSidebar from './ToolSidebar.vue'
import PPTPreview from './PPTPreview.vue'
import ContentView from './ContentView.vue'

const props = defineProps({
  slides: Array
})

const currentSlideIndex = ref(0)
const activeTool = ref('explain')

const currentSlide = computed(() => props.slides[currentSlideIndex.value])

const selectSlide = (index) => {
  currentSlideIndex.value = index
}

const handleToolChange = (toolName) => {
  activeTool.value = toolName
}
</script>

<template>
  <div class="workspace-layout">
    <div class="workspace-main">
      <div class="left-panel">
        <PPTPreview
          :slides="slides"
          :current-index="currentSlideIndex"
          @select="selectSlide"
        />
      </div>

      <div class="right-panel">
        <ContentView
          :slide="currentSlide"
          :active-tool="activeTool"
        />
      </div>
    </div>

    <ToolSidebar
      :active-tool="activeTool"
      @tool-change="handleToolChange"
    />
  </div>
</template>

<style scoped>
.workspace-layout {
  flex: 1;
  display: flex;
  height: calc(100vh - 64px);
  overflow: hidden;
}

.workspace-main {
  flex: 1;
  display: flex;
  width: 100%;
}

.left-panel {
  width: 40%;
  border-right: 1px solid #e2e8f0;
  background: #f1f5f9;
  display: flex;
  flex-direction: column;
}

.right-panel {
  width: 60%;
  background: #ffffff;
  overflow-y: auto;
  position: relative;
}
</style>
