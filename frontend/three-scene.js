/**
 * DESIGNS / LAW — Interactive Three.js Scene
 * Precision geometric design sculpture inspired by industrial patent blueprints,
 * technical drafting wireframes, and registered design engineering.
 */

(function () {
  'use strict';

  // Check WebGL availability
  function isWebGLAvailable() {
    try {
      const canvas = document.createElement('canvas');
      return !!(
        window.WebGLRenderingContext &&
        (canvas.getContext('webgl') || canvas.getContext('experimental-webgl'))
      );
    } catch (e) {
      return false;
    }
  }

  const container = document.getElementById('webgl-container');
  if (!container || !isWebGLAvailable() || typeof THREE === 'undefined') {
    console.warn('[Three.js] WebGL unavailable or container missing. Operating in fallback background mode.');
    return;
  }

  // Check prefers-reduced-motion
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Scene, Camera, Renderer
  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x060911, 0.035);

  const camera = new THREE.PerspectiveCamera(
    55,
    window.innerWidth / window.innerHeight,
    0.1,
    100
  );
  camera.position.set(0, 0, 14);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setClearColor(0x060911, 1);
  container.appendChild(renderer.domElement);

  // Group for floating objects
  const rootGroup = new THREE.Group();
  scene.add(rootGroup);

  // -------------------------------------------------------------------------
  // 1. Central Precision Technical Wireframe Sculpture
  // -------------------------------------------------------------------------
  // Outer wireframe icosahedron
  const outerGeom = new THREE.IcosahedronGeometry(3.2, 1);
  const outerWireMat = new THREE.MeshBasicMaterial({
    color: 0x22d3ee,
    wireframe: true,
    transparent: true,
    opacity: 0.35,
  });
  const outerMesh = new THREE.Mesh(outerGeom, outerWireMat);
  rootGroup.add(outerMesh);

  // Inner translucent core with electric blue accents
  const innerGeom = new THREE.OctahedronGeometry(2.0, 0);
  const innerMat = new THREE.MeshPhongMaterial({
    color: 0x1e3a8a,
    emissive: 0x0f172a,
    specular: 0x38bdf8,
    shininess: 60,
    wireframe: false,
    transparent: true,
    opacity: 0.65,
    flatShading: true,
  });
  const innerMesh = new THREE.Mesh(innerGeom, innerMat);
  rootGroup.add(innerMesh);

  // Inner gold/cyan wireframe accent
  const innerWireMat = new THREE.MeshBasicMaterial({
    color: 0x38bdf8,
    wireframe: true,
    transparent: true,
    opacity: 0.8,
  });
  const innerWireMesh = new THREE.Mesh(innerGeom, innerWireMat);
  rootGroup.add(innerWireMesh);

  // -------------------------------------------------------------------------
  // 2. Floating Technical Blueprint Sheets (Industrial Drawing Plates)
  // -------------------------------------------------------------------------
  const sheetsGroup = new THREE.Group();
  rootGroup.add(sheetsGroup);

  const sheetGeometry = new THREE.PlaneGeometry(2.4, 3.4);
  const sheetWireMat = new THREE.MeshBasicMaterial({
    color: 0x3b82f6,
    wireframe: true,
    transparent: true,
    opacity: 0.22,
    side: THREE.DoubleSide,
  });

  const sheetPositions = [
    { x: -5.5, y: 2.2, z: -2.5, rx: 0.3, ry: 0.5, rz: -0.2 },
    { x: 5.8, y: -2.0, z: -3.0, rx: -0.4, ry: -0.6, rz: 0.3 },
    { x: -4.5, y: -3.2, z: -1.8, rx: 0.5, ry: -0.4, rz: 0.1 },
    { x: 4.8, y: 3.5, z: -2.2, rx: -0.2, ry: 0.7, rz: -0.3 },
  ];

  sheetPositions.forEach((pos) => {
    const sheet = new THREE.Mesh(sheetGeometry, sheetWireMat);
    sheet.position.set(pos.x, pos.y, pos.z);
    sheet.rotation.set(pos.rx, pos.ry, pos.rz);
    sheetsGroup.add(sheet);
  });

  // -------------------------------------------------------------------------
  // 3. Precision Orbiting Nodes and Connecting Rings
  // -------------------------------------------------------------------------
  const ringGeom1 = new THREE.TorusGeometry(4.2, 0.02, 16, 100);
  const ringMat1 = new THREE.MeshBasicMaterial({
    color: 0x0ea5e9,
    transparent: true,
    opacity: 0.25,
  });
  const ringMesh1 = new THREE.Mesh(ringGeom1, ringMat1);
  ringMesh1.rotation.x = Math.PI / 3;
  rootGroup.add(ringMesh1);

  const ringGeom2 = new THREE.TorusGeometry(4.8, 0.015, 16, 100);
  const ringMat2 = new THREE.MeshBasicMaterial({
    color: 0x8b5cf6,
    transparent: true,
    opacity: 0.2,
  });
  const ringMesh2 = new THREE.Mesh(ringGeom2, ringMat2);
  ringMesh2.rotation.y = Math.PI / 4;
  rootGroup.add(ringMesh2);

  // Orbiting nodes (spheres)
  const nodesGroup = new THREE.Group();
  rootGroup.add(nodesGroup);

  const nodeGeom = new THREE.SphereGeometry(0.1, 12, 12);
  const nodeMat = new THREE.MeshBasicMaterial({ color: 0x22d3ee });

  const nodeCount = 8;
  const nodes = [];
  for (let i = 0; i < nodeCount; i++) {
    const node = new THREE.Mesh(nodeGeom, nodeMat);
    const angle = (i / nodeCount) * Math.PI * 2;
    const radius = 4.2;
    node.position.set(Math.cos(angle) * radius, 0, Math.sin(angle) * radius);
    nodesGroup.add(node);
    nodes.push({ mesh: node, angle: angle, speed: 0.008 + (i % 3) * 0.003 });
  }

  // -------------------------------------------------------------------------
  // 4. Controlled Coordinate Particle Field
  // -------------------------------------------------------------------------
  const particleCount = 280;
  const particleGeom = new THREE.BufferGeometry();
  const particlePositions = new Float32Array(particleCount * 3);

  for (let i = 0; i < particleCount * 3; i += 3) {
    particlePositions[i] = (Math.random() - 0.5) * 36;
    particlePositions[i + 1] = (Math.random() - 0.5) * 24;
    particlePositions[i + 2] = (Math.random() - 0.5) * 20 - 4;
  }

  particleGeom.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));

  const particleMat = new THREE.PointsMaterial({
    color: 0x38bdf8,
    size: 0.07,
    transparent: true,
    opacity: 0.45,
  });

  const particleSystem = new THREE.Points(particleGeom, particleMat);
  scene.add(particleSystem);

  // -------------------------------------------------------------------------
  // 5. Ambient & Directional Lighting
  // -------------------------------------------------------------------------
  const ambientLight = new THREE.AmbientLight(0x0f172a, 2.0);
  scene.add(ambientLight);

  const dirLight1 = new THREE.DirectionalLight(0x22d3ee, 1.8);
  dirLight1.position.set(5, 8, 10);
  scene.add(dirLight1);

  const dirLight2 = new THREE.DirectionalLight(0x8b5cf6, 1.2);
  dirLight2.position.set(-6, -6, -4);
  scene.add(dirLight2);

  // -------------------------------------------------------------------------
  // 6. Pointer Parallax Interaction
  // -------------------------------------------------------------------------
  let targetMouseX = 0;
  let targetMouseY = 0;
  let currentMouseX = 0;
  let currentMouseY = 0;

  function onMouseMove(event) {
    targetMouseX = (event.clientX / window.innerWidth - 0.5) * 2;
    targetMouseY = (event.clientY / window.innerHeight - 0.5) * 2;
  }

  window.addEventListener('mousemove', onMouseMove, { passive: true });

  // -------------------------------------------------------------------------
  // 7. Window Resize Handling
  // -------------------------------------------------------------------------
  function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  }

  window.addEventListener('resize', onWindowResize);

  // -------------------------------------------------------------------------
  // 8. Animation Loop
  // -------------------------------------------------------------------------
  let animationFrameId;

  function animate() {
    animationFrameId = requestAnimationFrame(animate);

    // Smooth pointer damping
    currentMouseX += (targetMouseX - currentMouseX) * 0.05;
    currentMouseY += (targetMouseY - currentMouseY) * 0.05;

    camera.position.x = currentMouseX * 1.2;
    camera.position.y = -currentMouseY * 0.8;
    camera.lookAt(scene.position);

    if (!prefersReducedMotion) {
      // Rotate sculpture
      outerMesh.rotation.x += 0.0025;
      outerMesh.rotation.y += 0.004;

      innerMesh.rotation.x -= 0.0035;
      innerMesh.rotation.y -= 0.005;
      innerWireMesh.rotation.x = innerMesh.rotation.x;
      innerWireMesh.rotation.y = innerMesh.rotation.y;

      // Rotate rings & sheets
      ringMesh1.rotation.z += 0.002;
      ringMesh2.rotation.z -= 0.0025;
      sheetsGroup.rotation.y += 0.0015;

      // Update orbiting nodes
      nodes.forEach((item) => {
        item.angle += item.speed;
        item.mesh.position.x = Math.cos(item.angle) * 4.2;
        item.mesh.position.z = Math.sin(item.angle) * 4.2;
        item.mesh.position.y = Math.sin(item.angle * 2) * 0.4;
      });

      // Subtle particle drift
      particleSystem.rotation.y += 0.0004;
    }

    renderer.render(scene, camera);
  }

  animate();

  // Cleanup on unload
  window.addEventListener('beforeunload', () => {
    cancelAnimationFrame(animationFrameId);
    window.removeEventListener('mousemove', onMouseMove);
    window.removeEventListener('resize', onWindowResize);
    renderer.dispose();
  });
})();
