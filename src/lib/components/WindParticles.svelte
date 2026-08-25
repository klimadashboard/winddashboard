<script lang="ts">
	import { onMount } from 'svelte';

	let canvas: HTMLCanvasElement;
	let ctx: CanvasRenderingContext2D;
	let animFrame: number;

	const PARTICLE_COUNT = 160;
	const WIND_ANGLE_DEG = 250; // west-southwesterly, prevailing over Austria
	const WIND_SPEED = 0.35; // pixels per frame base
	const WIND_ANGLE_RAD = (WIND_ANGLE_DEG * Math.PI) / 180;
	const VX = Math.cos(WIND_ANGLE_RAD) * WIND_SPEED;
	const VY = Math.sin(WIND_ANGLE_RAD) * WIND_SPEED;

	interface Particle {
		x: number;
		y: number;
		opacity: number;
		life: number;
		maxLife: number;
		speed: number;
		size: number;
	}

	let particles: Particle[] = [];
	let width = 0;
	let height = 0;

	function createParticle(randomPosition = true): Particle {
		const maxLife = 120 + Math.random() * 180;
		return {
			x: randomPosition ? Math.random() * width : -10,
			y: randomPosition ? Math.random() * height : Math.random() * height,
			opacity: 0,
			life: randomPosition ? Math.random() * maxLife : 0,
			maxLife,
			speed: 0.7 + Math.random() * 0.6,
			size: 1 + Math.random() * 1.2,
		};
	}

	function resize() {
		if (!canvas) return;
		width = canvas.offsetWidth;
		height = canvas.offsetHeight;
		canvas.width = width * window.devicePixelRatio;
		canvas.height = height * window.devicePixelRatio;
		ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
	}

	function tick() {
		if (!ctx || !width) {
			animFrame = requestAnimationFrame(tick);
			return;
		}

		ctx.clearRect(0, 0, width, height);

		for (const p of particles) {
			p.life += 1;
			p.x += VX * p.speed;
			p.y += VY * p.speed;

			// Fade in first 20% of life, fade out last 20%
			const progress = p.life / p.maxLife;
			if (progress < 0.2) {
				p.opacity = progress / 0.2 * 0.38;
			} else if (progress > 0.8) {
				p.opacity = (1 - (progress - 0.8) / 0.2) * 0.38;
			} else {
				p.opacity = 0.38;
			}

			// Reset when out of bounds or life exhausted
			if (p.life >= p.maxLife || p.x < -20 || p.x > width + 20 || p.y < -20 || p.y > height + 20) {
				const reset = createParticle(false);
				p.x = reset.x;
				p.y = reset.y;
				p.life = 0;
				p.maxLife = reset.maxLife;
				p.speed = reset.speed;
			}

			// Draw particle as a small elongated streak
			ctx.save();
			ctx.globalAlpha = p.opacity;
			ctx.strokeStyle = '#93c5fd';
			ctx.lineWidth = p.size;
			ctx.lineCap = 'round';
			ctx.beginPath();
			ctx.moveTo(p.x, p.y);
			ctx.lineTo(p.x - VX * p.speed * 6, p.y - VY * p.speed * 6);
			ctx.stroke();
			ctx.restore();
		}

		animFrame = requestAnimationFrame(tick);
	}

	onMount(() => {
		ctx = canvas.getContext('2d')!;

		const ro = new ResizeObserver(() => {
			resize();
			if (particles.length === 0) {
				particles = Array.from({ length: PARTICLE_COUNT }, () => createParticle(true));
			}
		});
		ro.observe(canvas);
		resize();

		particles = Array.from({ length: PARTICLE_COUNT }, () => createParticle(true));
		animFrame = requestAnimationFrame(tick);

		// Return cleanup — runs only in browser, so cancelAnimationFrame is safe
		return () => {
			ro.disconnect();
			cancelAnimationFrame(animFrame);
		};
	});
</script>

<canvas
	bind:this={canvas}
	class="absolute inset-0 w-full h-full pointer-events-none"
	style="z-index: 1;"
></canvas>
