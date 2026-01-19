<script>
export default {
  name: 'Navbar',
  props: {
    theme: {
      type: String,
      default: 'default',
      validator: value => ['default', 'light', 'dark'].includes(value)
    },
    position: {
      type: String,
      default: 'sticky',
      validator: value => ['static', 'sticky', 'fixed'].includes(value)
    }
  },
  data() {
    return {
      isScrolled: false,
      isMenuOpen: false,
      isMobile: false,
      resizeTimer: null
    }
  },
  computed: {
    navbarClasses() {
      return [
        `navbar-${this.theme}`,
        `navbar-${this.position}`,
        { 'navbar-scrolled': this.isScrolled }
      ]
    }
  },
  mounted() {
    this.checkMobile()
    window.addEventListener('resize', this.handleResize)
    window.addEventListener('scroll', this.handleScroll)
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize)
    window.removeEventListener('scroll', this.handleScroll)
  },
  methods: {
    handleScroll() {
      this.isScrolled = window.scrollY > 50
    },
    handleResize() {
      clearTimeout(this.resizeTimer)
      this.resizeTimer = setTimeout(() => {
        this.checkMobile()
        if (!this.isMobile && this.isMenuOpen) {
          this.isMenuOpen = false
        }
      }, 200)
    },
    checkMobile() {
      this.isMobile = window.innerWidth <= 768
    },
    toggleMenu() {
      this.isMenuOpen = !this.isMenuOpen
    }
  }
}
</script>

<template>
  <header
    class="navbar"
    :class="navbarClasses"
    role="banner"
  >
    <div class="logo" aria-label="PPTAS Logo">
      <span class="icon" aria-hidden="true">🧬</span>
      <span class="text">PPTAS 内容扩展智能体</span>
    </div>

    <button
      class="mobile-menu-btn"
      @click="toggleMenu"
      aria-label="切换菜单"
      v-if="isMobile"
    >
      <span :class="{ 'open': isMenuOpen }"></span>
      <span :class="{ 'open': isMenuOpen }"></span>
      <span :class="{ 'open': isMenuOpen }"></span>
    </button>

    <div class="nav-actions" :class="{ 'active': isMenuOpen }">
      <slot></slot>
    </div>
  </header>
</template>

<style scoped>
.navbar {
  padding: 1rem 5%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  transition: all 0.3s ease;
  width: 100%;
  box-sizing: border-box;
  z-index: 1000;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 700;
  font-size: 1.3rem;
  letter-spacing: -0.5px;
  cursor: pointer;
  transition: transform 0.2s;
}

.logo:hover {
  transform: scale(1.02);
}

.icon {
  font-size: 1.8rem;
  display: inline-block;
  will-change: transform;
  animation: pulse 2s infinite;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 15px;
  transition: all 0.3s ease;
}

.navbar-default {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
}

.navbar-light {
  background: #ffffff;
  color: #1a202c;
  border-bottom: 1px solid #e2e8f0;
}

.navbar-dark {
  background: #1a202c;
  color: #ffffff;
}

.navbar-sticky {
  position: sticky;
  top: 0;
}

.navbar-fixed {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
}

.navbar-scrolled {
  padding: 0.8rem 5%;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  background: rgba(255, 255, 255, 0.95);
  color: #1a202c !important;
  backdrop-filter: blur(10px);
}

.navbar-dark.navbar-scrolled {
  background: rgba(26, 32, 44, 0.95);
  color: #ffffff;
}

.mobile-menu-btn {
  display: none;
  flex-direction: column;
  justify-content: space-around;
  width: 30px;
  height: 25px;
  background: transparent;
  border: none;
  cursor: pointer;
  z-index: 1001;
  padding: 0;
}

.mobile-menu-btn span {
  width: 30px;
  height: 3px;
  background: currentColor;
  border-radius: 10px;
  transition: all 0.3s ease;
  transform-origin: 1px;
}

.mobile-menu-btn span.open:first-child {
  transform: rotate(45deg);
}
.mobile-menu-btn span.open:nth-child(2) {
  opacity: 0;
  transform: translateX(20px);
}
.mobile-menu-btn span.open:nth-child(3) {
  transform: rotate(-45deg);
}

@media (max-width: 768px) {
  .navbar {
    padding: 0.8rem 5%;
  }

  .logo {
    font-size: 1.2rem;
  }

  .mobile-menu-btn {
    display: flex;
  }

  .nav-actions {
    position: fixed;
    top: 0;
    right: 0;
    height: 100vh;
    width: 70%;
    max-width: 300px;
    background: #ffffff;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    box-shadow: -5px 0 15px rgba(0,0,0,0.1);
    transform: translateX(100%);
    padding: 2rem;
    z-index: 1000;
    color: #1a202c;
  }

  .nav-actions.active {
    transform: translateX(0);
  }

  .navbar-dark .nav-actions {
    background: #1a202c;
    color: #ffffff;
  }
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}
</style>
