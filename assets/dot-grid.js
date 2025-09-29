// Dot Grid Background Animation with GSAP
// Based on reactbits.dev implementation

(function () {
  // Wait for GSAP to load
  function waitForGSAP(callback) {
    if (typeof gsap !== "undefined" && gsap.registerPlugin) {
      callback();
    } else {
      setTimeout(() => waitForGSAP(callback), 100);
    }
  }

  // Throttle function for performance
  function throttle(func, limit) {
    let lastCall = 0;
    return function (...args) {
      const now = performance.now();
      if (now - lastCall >= limit) {
        lastCall = now;
        func.apply(this, args);
      }
    };
  }

  // Convert hex to RGB
  function hexToRgb(hex) {
    const m = hex.match(/^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i);
    if (!m) return { r: 0, g: 0, b: 0 };
    return {
      r: parseInt(m[1], 16),
      g: parseInt(m[2], 16),
      b: parseInt(m[3], 16),
    };
  }

  function initDotGrid() {
    const canvas = document.getElementById("dotCanvas");
    if (!canvas) {
      setTimeout(initDotGrid, 100);
      return;
    }

    const wrapper = canvas.parentElement;
    if (!wrapper) return;

    const ctx = canvas.getContext("2d");

    // Configuration (matching reactbits.dev defaults)
    const config = {
      dotSize: 3,
      gap: 32,
      baseColor: "#666666",
      activeColor: "#ffffff",
      proximity: 150,
      speedTrigger: 100,
      shockRadius: 250,
      shockStrength: 5,
      maxSpeed: 5000,
      resistance: 750,
      returnDuration: 1.5,
    };

    const baseRgb = hexToRgb(config.baseColor);
    const activeRgb = hexToRgb(config.activeColor);

    let dots = [];
    let animationId = null;

    const pointer = {
      x: 0,
      y: 0,
      vx: 0,
      vy: 0,
      speed: 0,
      lastTime: 0,
      lastX: 0,
      lastY: 0,
    };

    // Create circle path for better performance
    let circlePath = null;
    if (typeof Path2D !== "undefined") {
      circlePath = new Path2D();
      circlePath.arc(0, 0, config.dotSize / 2, 0, Math.PI * 2);
    }

    function buildGrid() {
      const rect = wrapper.getBoundingClientRect();
      const width = rect.width;
      const height = rect.height;
      const dpr = window.devicePixelRatio || 1;

      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.scale(dpr, dpr);

      const cols = Math.floor(
        (width + config.gap) / (config.dotSize + config.gap)
      );
      const rows = Math.floor(
        (height + config.gap) / (config.dotSize + config.gap)
      );
      const cell = config.dotSize + config.gap;

      const gridW = cell * cols - config.gap;
      const gridH = cell * rows - config.gap;

      const extraX = width - gridW;
      const extraY = height - gridH;

      const startX = extraX / 2 + config.dotSize / 2;
      const startY = extraY / 2 + config.dotSize / 2;

      dots = [];
      for (let y = 0; y < rows; y++) {
        for (let x = 0; x < cols; x++) {
          const cx = startX + x * cell;
          const cy = startY + y * cell;
          dots.push({
            cx,
            cy,
            xOffset: 0,
            yOffset: 0,
            _inertiaApplied: false,
          });
        }
      }
    }

    function draw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const proxSq = config.proximity * config.proximity;

      for (const dot of dots) {
        const ox = dot.cx + dot.xOffset;
        const oy = dot.cy + dot.yOffset;
        const dx = dot.cx - pointer.x;
        const dy = dot.cy - pointer.y;
        const dsq = dx * dx + dy * dy;

        let style = config.baseColor;
        if (dsq <= proxSq) {
          const dist = Math.sqrt(dsq);
          const t = 1 - dist / config.proximity;
          const r = Math.round(baseRgb.r + (activeRgb.r - baseRgb.r) * t);
          const g = Math.round(baseRgb.g + (activeRgb.g - baseRgb.g) * t);
          const b = Math.round(baseRgb.b + (activeRgb.b - baseRgb.b) * t);
          style = `rgb(${r},${g},${b})`;
        }

        ctx.save();
        ctx.translate(ox, oy);
        ctx.fillStyle = style;

        if (circlePath) {
          ctx.fill(circlePath);
        } else {
          ctx.beginPath();
          ctx.arc(0, 0, config.dotSize / 2, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.restore();
      }

      animationId = requestAnimationFrame(draw);
    }

    function handleMouseMove(e) {
      const now = performance.now();
      const dt = pointer.lastTime ? now - pointer.lastTime : 16;
      const dx = e.clientX - pointer.lastX;
      const dy = e.clientY - pointer.lastY;

      let vx = (dx / dt) * 1000;
      let vy = (dy / dt) * 1000;
      let speed = Math.hypot(vx, vy);

      if (speed > config.maxSpeed) {
        const scale = config.maxSpeed / speed;
        vx *= scale;
        vy *= scale;
        speed = config.maxSpeed;
      }

      pointer.lastTime = now;
      pointer.lastX = e.clientX;
      pointer.lastY = e.clientY;
      pointer.vx = vx;
      pointer.vy = vy;
      pointer.speed = speed;

      const rect = canvas.getBoundingClientRect();
      pointer.x = e.clientX - rect.left;
      pointer.y = e.clientY - rect.top;

      // Fast movement shock wave effect
      for (const dot of dots) {
        const dist = Math.hypot(dot.cx - pointer.x, dot.cy - pointer.y);
        if (
          speed > config.speedTrigger &&
          dist < config.proximity &&
          !dot._inertiaApplied
        ) {
          dot._inertiaApplied = true;
          gsap.killTweensOf(dot);

          const pushX = dot.cx - pointer.x + vx * 0.005;
          const pushY = dot.cy - pointer.y + vy * 0.005;

          gsap.to(dot, {
            inertia: {
              xOffset: pushX,
              yOffset: pushY,
              resistance: config.resistance,
            },
            onComplete: () => {
              gsap.to(dot, {
                xOffset: 0,
                yOffset: 0,
                duration: config.returnDuration,
                ease: "elastic.out(1,0.75)",
              });
              dot._inertiaApplied = false;
            },
          });
        }
      }
    }

    function handleClick(e) {
      const rect = canvas.getBoundingClientRect();
      const cx = e.clientX - rect.left;
      const cy = e.clientY - rect.top;

      // Click shock wave effect
      for (const dot of dots) {
        const dist = Math.hypot(dot.cx - cx, dot.cy - cy);
        if (dist < config.shockRadius && !dot._inertiaApplied) {
          dot._inertiaApplied = true;
          gsap.killTweensOf(dot);

          const falloff = Math.max(0, 1 - dist / config.shockRadius);
          const pushX = (dot.cx - cx) * config.shockStrength * falloff;
          const pushY = (dot.cy - cy) * config.shockStrength * falloff;

          gsap.to(dot, {
            inertia: {
              xOffset: pushX,
              yOffset: pushY,
              resistance: config.resistance,
            },
            onComplete: () => {
              gsap.to(dot, {
                xOffset: 0,
                yOffset: 0,
                duration: config.returnDuration,
                ease: "elastic.out(1,0.75)",
              });
              dot._inertiaApplied = false;
            },
          });
        }
      }
    }

    buildGrid();
    draw();

    // Event listeners with throttling
    const throttledMove = throttle(handleMouseMove, 50);
    window.addEventListener("mousemove", throttledMove, { passive: true });
    window.addEventListener("click", handleClick);

    // Resize handling
    let resizeTimeout;
    function handleResize() {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {
        buildGrid();
      }, 100);
    }
    window.addEventListener("resize", handleResize);

    // Cleanup
    window.cleanupDotGrid = function () {
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
      window.removeEventListener("mousemove", throttledMove);
      window.removeEventListener("click", handleClick);
      window.removeEventListener("resize", handleResize);
    };
  }

  // Wait for GSAP to be available, then initialize
  waitForGSAP(() => {
    // Register InertiaPlugin
    if (gsap.registerPlugin && typeof InertiaPlugin !== "undefined") {
      gsap.registerPlugin(InertiaPlugin);
    }

    // Initialize when DOM is ready
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", initDotGrid);
    } else {
      initDotGrid();
    }
  });
})();
