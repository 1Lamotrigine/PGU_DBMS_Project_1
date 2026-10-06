"use client";

import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import * as THREE from "three";

export type Lane = {
  id: number;
  ru: string;
  en: string;
  image?: string | null;
};

export type LaneSceneHandle = {
  addCard: (lane: Lane) => void;
  destroyCard: (id: number, success: boolean) => void;
  reset: () => void;
};

type Props = {
  accent: string;
  bg: string;
  textColor: string;
  wallColor: string;
  onBreach: (lane: Lane) => void;
};

type CardObj = {
  lane: Lane;
  group: THREE.Group;
  speed: number;
  wobble: number;
  row: number;
  halfW: number;
  dead: boolean;
  dying: boolean;
};

const ROWS = 3;

export const LaneScene = forwardRef<LaneSceneHandle, Props>(function LaneScene(
  { accent, bg, textColor, wallColor, onBreach },
  ref,
) {
  const mountRef = useRef<HTMLDivElement | null>(null);
  const breachRef = useRef(onBreach);
  breachRef.current = onBreach;

  const apiRef = useRef<{
    addCard?: (lane: Lane) => void;
    destroyCard?: (id: number, success: boolean) => void;
    reset?: () => void;
  }>({});

  useImperativeHandle(
    ref,
    () => ({
      addCard: (lane) => apiRef.current.addCard?.(lane),
      destroyCard: (id, success) => apiRef.current.destroyCard?.(id, success),
      reset: () => apiRef.current.reset?.(),
    }),
    [],
  );

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const width = mount.clientWidth || 720;
    const height = mount.clientHeight || 460;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(bg);

    const camera = new THREE.OrthographicCamera(-width / 2, width / 2, height / 2, -height / 2, -100, 100);
    camera.position.z = 10;

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(width, height, false);
    renderer.domElement.style.width = "100%";
    renderer.domElement.style.height = "100%";
    renderer.domElement.style.display = "block";
    mount.appendChild(renderer.domElement);

    const world = new THREE.Group();
    scene.add(world);

    // Base wall (left)
    const wallW = 20;
    const wall = new THREE.Mesh(
      new THREE.PlaneGeometry(wallW, height),
      new THREE.MeshBasicMaterial({ color: new THREE.Color(wallColor) }),
    );
    wall.position.set(-width / 2 + wallW / 2, 0, 0);
    world.add(wall);
    const stripe = new THREE.Mesh(
      new THREE.PlaneGeometry(4, height),
      new THREE.MeshBasicMaterial({ color: new THREE.Color(accent) }),
    );
    stripe.position.set(-width / 2 + wallW + 2, 0, 0.5);
    world.add(stripe);

    const cards: CardObj[] = [];
    const particles: { mesh: THREE.Mesh; vx: number; vy: number; life: number }[] = [];
    let elapsed = 0;

    function laneY(row: number) {
      const gap = height / (ROWS + 1);
      return height / 2 - gap * (row + 1);
    }

    function makeCard(lane: Lane, row: number): CardObj {
      const group = new THREE.Group();
      const cardW = 104;
      const cardH = 104;

      // card background
      const bodyMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(bg === "#0B0B0D" ? "#17181b" : "#FFFFFF") });
      const body = new THREE.Mesh(new THREE.PlaneGeometry(cardW, cardH), bodyMat);
      group.add(body);

      // border
      const border = new THREE.LineSegments(
        new THREE.EdgesGeometry(new THREE.PlaneGeometry(cardW, cardH)),
        new THREE.LineBasicMaterial({ color: new THREE.Color(accent) }),
      );
      group.add(border);

      if (lane.image) {
        // picture instead of the word
        const tex = new THREE.TextureLoader().load(lane.image);
        tex.colorSpace = THREE.SRGBColorSpace;
        const imgMat = new THREE.MeshBasicMaterial({ map: tex, transparent: true });
        const img = new THREE.Mesh(new THREE.PlaneGeometry(cardW - 18, cardH - 18), imgMat);
        img.position.z = 0.1;
        group.add(img);
      } else {
        const label = makeTextMesh(lane.ru, textColor || "#FFFFFF");
        label.position.z = 0.1;
        group.add(label);
      }

      group.position.set(width / 2 + 130, laneY(row), 0);
      world.add(group);

      // Base speed with gentle acceleration over time
      const speed = 42 + Math.min(elapsed * 0.9, 55);
      return { lane, group, speed, wobble: Math.random() * 6, row, halfW: cardW / 2, dead: false, dying: false };
    }

    function spawnParticles(x: number, y: number, color: number) {
      for (let i = 0; i < 14; i++) {
        const p = new THREE.Mesh(
          new THREE.CircleGeometry(3 + Math.random() * 3, 8),
          new THREE.MeshBasicMaterial({ color, transparent: true }),
        );
        p.position.set(x, y, 1);
        world.add(p);
        const ang = Math.random() * Math.PI * 2;
        const sp = 70 + Math.random() * 140;
        particles.push({ mesh: p, vx: Math.cos(ang) * sp, vy: Math.sin(ang) * sp, life: 0.6 });
      }
    }

    let last = performance.now();
    let raf = 0;
    function frame(now: number) {
      const dt = Math.min((now - last) / 1000, 0.05);
      last = now;
      elapsed += dt;

      for (const c of cards) {
        if (c.dead) continue;
        if (!c.dying) {
          c.group.position.x -= c.speed * dt;
          c.wobble += dt * 2.4;
          c.group.position.y += Math.sin(c.wobble) * 0.1;
          // Breach when the card's LEFT EDGE touches the wall's right edge.
          const wallRight = -width / 2 + wallW + 6;
          const leftEdge = c.group.position.x - c.halfW;
          if (leftEdge <= wallRight) {
            c.dead = true;
            c.dying = true;
            spawnParticles(wallRight, c.group.position.y, 0x9aa0a6);
            breachRef.current(c.lane);
          }
        }
      }

      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.life -= dt;
        p.mesh.position.x += p.vx * dt;
        p.mesh.position.y += p.vy * dt;
        p.vy -= 150 * dt;
        (p.mesh.material as THREE.MeshBasicMaterial).opacity = Math.max(0, p.life / 0.6);
        if (p.life <= 0) {
          world.remove(p.mesh);
          (p.mesh.geometry as THREE.BufferGeometry).dispose();
          (p.mesh.material as THREE.Material).dispose();
          particles.splice(i, 1);
        }
      }

      for (let i = cards.length - 1; i >= 0; i--) {
        const c = cards[i];
        if (c.dying) {
          c.group.scale.multiplyScalar(1 - dt * 2.4);
          let maxOpacity = 0;
          c.group.traverse((o) => {
            const mesh = o as THREE.Mesh;
            if (mesh.material) {
              const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
              mats.forEach((m) => {
                m.transparent = true;
                m.opacity = Math.max(0, (m.opacity ?? 1) - dt * 4.5);
                maxOpacity = Math.max(maxOpacity, m.opacity);
              });
            }
          });
          if (maxOpacity <= 0.01) {
            world.remove(c.group);
            c.group.traverse((o) => {
              const mesh = o as THREE.Mesh;
              if (mesh.geometry) mesh.geometry.dispose();
            });
            cards.splice(i, 1);
          }
        }
      }

      renderer.render(scene, camera);
      raf = requestAnimationFrame(frame);
    }
    raf = requestAnimationFrame(frame);

    apiRef.current.addCard = (lane: Lane) => {
      // Pick the row whose newest (right-most) card is farthest from the spawn edge,
      // so a new card never overlaps one that just appeared.
      const rightEdge = width / 2 + 130;
      const rowFront: number[] = new Array(ROWS).fill(-Infinity); // largest x per row
      for (const c of cards) {
        if (c.dead) continue;
        rowFront[c.row] = Math.max(rowFront[c.row], c.group.position.x);
      }
      let bestRow = 0;
      let bestX = Infinity;
      for (let r = 0; r < ROWS; r++) {
        if (rowFront[r] < bestX) {
          bestX = rowFront[r];
          bestRow = r;
        }
      }
      // If even the freest row has a card too close to spawn, skip this spawn.
      if (bestX > rightEdge - 210) return;
      cards.push(makeCard(lane, bestRow));
    };
    apiRef.current.destroyCard = (id: number, success: boolean) => {
      const c = cards.find((x) => x.lane.id === id);
      if (c && !c.dying) {
        c.dead = true;
        c.dying = true;
        spawnParticles(c.group.position.x, c.group.position.y, success ? 0x4a8fd6 : 0x9aa0a6);
      }
    };
    apiRef.current.reset = () => {
      for (const c of cards) {
        world.remove(c.group);
      }
      cards.length = 0;
      elapsed = 0;
    };

    function onResize() {
      if (!mount) return;
      const w = mount.clientWidth;
      const h = mount.clientHeight;
      renderer.setSize(w, h, false);
      camera.left = -w / 2;
      camera.right = w / 2;
      camera.top = h / 2;
      camera.bottom = -h / 2;
      camera.updateProjectionMatrix();
    }
    window.addEventListener("resize", onResize);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", onResize);
      renderer.dispose();
      if (renderer.domElement.parentNode) renderer.domElement.parentNode.removeChild(renderer.domElement);
      apiRef.current = {};
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  void textColor;

  return <div ref={mountRef} style={{ width: "100%", height: "100%" }} />;
});

function makeTextMesh(text: string, color: string): THREE.Mesh {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 160;
  const ctx = canvas.getContext("2d")!;
  ctx.fillStyle = color;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  // auto-fit the font so long words don't overflow the card
  let size = 72;
  ctx.font = `500 ${size}px Inter, Arial, sans-serif`;
  const maxWidth = canvas.width - 40;
  while (ctx.measureText(text).width > maxWidth && size > 28) {
    size -= 4;
    ctx.font = `500 ${size}px Inter, Arial, sans-serif`;
  }
  ctx.fillText(text, canvas.width / 2, canvas.height / 2);
  const texture = new THREE.CanvasTexture(canvas);
  texture.anisotropy = 4;
  const mat = new THREE.MeshBasicMaterial({ map: texture, transparent: true });
  return new THREE.Mesh(new THREE.PlaneGeometry(160, 50), mat);
}
