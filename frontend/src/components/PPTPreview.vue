<script setup>
import { computed } from 'vue'

const props = defineProps({
  slides: Array,
  currentIndex: Number
})

const emit = defineEmits(['select'])

const hasSlides = computed(() => props.slides && props.slides.length > 0)

const selectPrev = () => {
  if (!hasSlides.value) return
  const next = (props.currentIndex - 1 + props.slides.length) % props.slides.length
  emit('select', next)
}

const selectNext = () => {
  if (!hasSlides.value) return
  const next = (props.currentIndex + 1) % props.slides.length
  emit('select', next)
}
</script>

<template>
  <div class="ppt-preview-container" v-if="hasSlides">
    <div class="main-stage">
      <button class="nav-btn prev" @click="selectPrev">‹</button>
      <div class="slide-number-badge">Slide {{ (currentIndex || 0) + 1 }} / {{ slides.length }}</div>
      <div class="slide-image-wrapper">
        <img :src="slides[currentIndex]?.image" alt="Slide Preview" class="slide-image" />
      </div>
      <div class="slide-caption">
        {{ slides[currentIndex]?.title }}
      </div>
      <button class="nav-btn next" @click="selectNext">›</button>
    </div>

    <div class="thumbnail-list">
      <div
        v-for="(slide, index) in slides"
        :key="slide.page_num"
        :class="['thumb-item', { active: index === currentIndex }]"
        @click="$emit('select', index)"
      >
        <img :src="slide.image" class="thumb-img" />
        <span class="thumb-num">{{ slide.page_num }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ppt-preview-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #e2e8f0;
}

.main-stage {
  flex: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 20px;
  border-bottom: 1px solid #cbd5e1;
  position: relative;
  background: #cbd5e1;
}

.slide-number-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  background: rgba(0,0,0,0.6);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
}

.slide-image-wrapper {
  width: 100%;
  max-width: 600px;
  aspect-ratio: 16/9;
  background: white;
  box-shadow: 0 10px 25px rgba(0,0,0,0.3);
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.slide-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.slide-caption {
  margin-top: 1rem;
  font-weight: 600;
  color: #334155;
  text-align: center;
  padding: 0 1rem;
  font-size: 0.9rem;
}

.nav-btn {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: none;
  background: rgba(0,0,0,0.35);
  color: white;
  font-size: 1.4rem;
  cursor: pointer;
  transition: background 0.2s, transform 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
}

.nav-btn:hover {
  background: rgba(0,0,0,0.55);
  transform: translateY(-50%) scale(1.03);
}

.nav-btn.prev {
  left: 12px;
}

.nav-btn.next {
  right: 12px;
}

.thumbnail-list {
  flex: 1;
  overflow-x: auto;
  overflow-y: hidden;
  padding: 10px 16px;
  display: flex;
  gap: 12px;
  background: #f1f5f9;
  scroll-snap-type: x mandatory;
}

.thumb-item {
  position: relative;
  cursor: pointer;
  border-radius: 6px;
  overflow: hidden;
  border: 2px solid transparent;
  transition: all 0.2s;
  aspect-ratio: 16/9;
  width: 140px;
  flex: 0 0 auto;
  scroll-snap-align: start;
}

.thumb-item:hover {
  border-color: #94a3b8;
  transform: translateY(-2px);
}

.thumb-item.active {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
}

.thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumb-num {
  position: absolute;
  bottom: 2px;
  right: 2px;
  background: rgba(0,0,0,0.7);
  color: white;
  font-size: 0.6rem;
  padding: 2px 4px;
  border-radius: 2px;
}
</style>
