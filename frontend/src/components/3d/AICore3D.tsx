import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import type { AICoreStatus } from '../../types';
import { AICoreFallback } from './AICoreFallback';

interface AICore3DProps {
  status: AICoreStatus;
  size?: number;
  className?: string;
  onClick?: () => void;
  onResetStatus?: () => void;
}

export const AICore3D: React.FC<AICore3DProps> = ({
  status = 'idle',
  size = 220,
  className = '',
  onClick,
  onResetStatus,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [webGLFailed, setWebGLFailed] = useState(false);
  const mouseRef = useRef({ x: 0, y: 0, targetX: 0, targetY: 0 });
  const statusRef = useRef(status);

  useEffect(() => {
    statusRef.current = status;
    // Auto-recovery timer for error state so the core doesn't get permanently stuck in error
    if (status === 'error') {
      const timer = setTimeout(() => {
        if (onResetStatus) {
          onResetStatus();
        }
      }, 4500);
      return () => clearTimeout(timer);
    }
  }, [status, onResetStatus]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Check WebGL availability
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        powerPreference: 'high-performance',
      });
    } catch {
      setWebGLFailed(true);
      return;
    }

    renderer.setSize(size, size);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    container.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
    camera.position.z = 4.2;

    // Group for mouse tracking rotation
    const mainGroup = new THREE.Group();
    scene.add(mainGroup);

    // 1. Central Icosahedron Core
    const coreGeo = new THREE.IcosahedronGeometry(0.85, 2);
    const coreMat = new THREE.MeshStandardMaterial({
      color: 0x6366f1,
      roughness: 0.2,
      metalness: 0.8,
      wireframe: false,
      emissive: 0x4f46e5,
      emissiveIntensity: 0.6,
    });
    const coreMesh = new THREE.Mesh(coreGeo, coreMat);
    mainGroup.add(coreMesh);

    // Wireframe overlay for futuristic tech feel
    const wireMat = new THREE.MeshBasicMaterial({
      color: 0xa5b4fc,
      wireframe: true,
      transparent: true,
      opacity: 0.35,
    });
    const wireMesh = new THREE.Mesh(coreGeo, wireMat);
    wireMesh.scale.setScalar(1.02);
    mainGroup.add(wireMesh);

    // 2. Translucent Concentric Orbital Rings
    const ringGeo1 = new THREE.TorusGeometry(1.35, 0.02, 16, 100);
    const ringMat1 = new THREE.MeshStandardMaterial({
      color: 0x38bdf8,
      emissive: 0x0284c7,
      emissiveIntensity: 0.8,
      roughness: 0.1,
      metalness: 0.9,
    });
    const ring1 = new THREE.Mesh(ringGeo1, ringMat1);
    ring1.rotation.x = Math.PI / 3;
    mainGroup.add(ring1);

    const ringGeo2 = new THREE.TorusGeometry(1.65, 0.015, 16, 100);
    const ringMat2 = new THREE.MeshStandardMaterial({
      color: 0xc084fc,
      emissive: 0x9333ea,
      emissiveIntensity: 0.7,
      roughness: 0.2,
      metalness: 0.9,
    });
    const ring2 = new THREE.Mesh(ringGeo2, ringMat2);
    ring2.rotation.y = Math.PI / 4;
    mainGroup.add(ring2);

    const ringGeo3 = new THREE.TorusGeometry(1.95, 0.012, 16, 100);
    const ringMat3 = new THREE.MeshStandardMaterial({
      color: 0x818cf8,
      emissive: 0x4338ca,
      emissiveIntensity: 0.6,
      roughness: 0.2,
      metalness: 0.9,
    });
    const ring3 = new THREE.Mesh(ringGeo3, ringMat3);
    ring3.rotation.z = Math.PI / 6;
    mainGroup.add(ring3);

    // 3. Swirling Quantum Particles
    const particleCount = 280;
    const particlePositions = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
      const radius = 1.2 + Math.random() * 1.4;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      particlePositions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      particlePositions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      particlePositions[i * 3 + 2] = radius * Math.cos(phi);
    }
    const particleGeo = new THREE.BufferGeometry();
    particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
    const particleMat = new THREE.PointsMaterial({
      color: 0x38bdf8,
      size: 0.045,
      transparent: true,
      opacity: 0.75,
      blending: THREE.AdditiveBlending,
    });
    const particleCloud = new THREE.Points(particleGeo, particleMat);
    mainGroup.add(particleCloud);

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x818cf8, 2.5, 10);
    pointLight.position.set(2, 3, 4);
    scene.add(pointLight);

    const backLight = new THREE.PointLight(0x38bdf8, 2.0, 10);
    backLight.position.set(-2, -2, -2);
    scene.add(backLight);

    // Mouse Move Listener
    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const y = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      mouseRef.current.targetX = x * 0.45;
      mouseRef.current.targetY = y * 0.45;
    };

    container.addEventListener('mousemove', handleMouseMove);

    // Animation Loop
    let animationFrameId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();
      const currentStatus = statusRef.current;

      // Status parameters
      let speedMult = 1.0;
      let targetCoreColor = new THREE.Color(0x6366f1);
      let targetEmissive = new THREE.Color(0x4f46e5);

      switch (currentStatus) {
        case 'initializing':
          speedMult = 0.8;
          targetCoreColor.setHex(0x38bdf8);
          targetEmissive.setHex(0x0284c7);
          break;
        case 'listening':
          speedMult = 1.6;
          targetCoreColor.setHex(0x2dd4bf);
          targetEmissive.setHex(0x0d9488);
          break;
        case 'thinking':
          speedMult = 2.4;
          targetCoreColor.setHex(0x8b5cf6);
          targetEmissive.setHex(0x7c3aed);
          break;
        case 'planning':
          speedMult = 2.2;
          targetCoreColor.setHex(0xa855f7);
          targetEmissive.setHex(0x9333ea);
          break;
        case 'processing':
          speedMult = 2.0;
          targetCoreColor.setHex(0x06b6d4);
          targetEmissive.setHex(0x0891b2);
          break;
        case 'executing':
          speedMult = 2.8;
          targetCoreColor.setHex(0xf59e0b);
          targetEmissive.setHex(0xd97706);
          break;
        case 'awaiting_approval':
          speedMult = 1.2;
          targetCoreColor.setHex(0xfbbf24);
          targetEmissive.setHex(0xf59e0b);
          break;
        case 'completed':
          speedMult = 1.5;
          targetCoreColor.setHex(0x10b981);
          targetEmissive.setHex(0x059669);
          break;
        case 'error':
          speedMult = 1.4;
          targetCoreColor.setHex(0xf43f5e);
          targetEmissive.setHex(0xe11d48);
          break;
        case 'idle':
        default:
          speedMult = 1.0;
          targetCoreColor.setHex(0x6366f1);
          targetEmissive.setHex(0x4f46e5);
          break;
      }

      // Smooth color transitions
      coreMat.color.lerp(targetCoreColor, 0.05);
      coreMat.emissive.lerp(targetEmissive, 0.05);
      particleMat.color.lerp(targetCoreColor, 0.05);

      // Rotations
      const delta = 0.01 * speedMult;
      coreMesh.rotation.x += delta * 0.7;
      coreMesh.rotation.y += delta;
      wireMesh.rotation.x -= delta * 0.5;
      wireMesh.rotation.y -= delta * 0.8;

      ring1.rotation.x += delta * 1.2;
      ring1.rotation.y += delta * 0.8;
      ring2.rotation.y -= delta * 1.5;
      ring2.rotation.z += delta * 0.9;
      ring3.rotation.z += delta * 1.8;
      ring3.rotation.x -= delta * 0.6;

      particleCloud.rotation.y += delta * 0.5;
      particleCloud.rotation.x += delta * 0.3;

      // Core pulsating scale
      const pulseScale = 1.0 + Math.sin(elapsed * 2.5 * speedMult) * 0.045;
      coreMesh.scale.setScalar(pulseScale);
      wireMesh.scale.setScalar(pulseScale * 1.02);

      // Smooth mouse follow lerp
      mouseRef.current.x += (mouseRef.current.targetX - mouseRef.current.x) * 0.08;
      mouseRef.current.y += (mouseRef.current.targetY - mouseRef.current.y) * 0.08;
      mainGroup.rotation.y = mouseRef.current.x;
      mainGroup.rotation.x = -mouseRef.current.y;

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
      container.removeEventListener('mousemove', handleMouseMove);
      if (renderer.domElement && container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      coreGeo.dispose();
      coreMat.dispose();
      wireMat.dispose();
      ringGeo1.dispose();
      ringMat1.dispose();
      ringGeo2.dispose();
      ringMat2.dispose();
      ringGeo3.dispose();
      ringMat3.dispose();
      particleGeo.dispose();
      particleMat.dispose();
      renderer.dispose();
    };
  }, [size]);

  if (webGLFailed) {
    return <AICoreFallback status={status} size={size} />;
  }

  const getStatusColor = () => {
    switch (status) {
      case 'listening':
        return 'border-teal-500/80 text-teal-300 shadow-teal-500/20';
      case 'thinking':
      case 'planning':
        return 'border-purple-500/80 text-purple-300 shadow-purple-500/20';
      case 'executing':
      case 'processing':
        return 'border-amber-500/80 text-amber-300 shadow-amber-500/20';
      case 'awaiting_approval':
        return 'border-yellow-500/80 text-yellow-300 shadow-yellow-500/20';
      case 'completed':
        return 'border-emerald-500/80 text-emerald-300 shadow-emerald-500/20';
      case 'error':
        return 'border-rose-500/80 text-rose-300 shadow-rose-500/20';
      case 'initializing':
        return 'border-cyan-500/80 text-cyan-300 shadow-cyan-500/20';
      default:
        return 'border-indigo-500/80 text-indigo-300 shadow-indigo-500/20';
    }
  };

  return (
    <div
      ref={containerRef}
      onClick={onClick}
      className={`relative flex items-center justify-center cursor-pointer transition-transform hover:scale-105 ${className}`}
      style={{ width: size, height: size }}
      title={`LifeSync 3D AI Core - Status: ${status} (Click to open AI Assistant)`}
    >
      <div
        className={`absolute -bottom-1 px-3 py-1 rounded-full bg-slate-950/90 border text-[10px] font-mono tracking-wider backdrop-blur-md shadow-lg pointer-events-none transition-colors duration-300 ${getStatusColor()}`}
      >
        {status.replace('_', ' ').toUpperCase()}
      </div>
    </div>
  );
};
