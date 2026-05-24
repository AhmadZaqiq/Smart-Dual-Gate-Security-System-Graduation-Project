window.MantrapVisual = (function () {
    const THREE_URL = "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js";

    let scene = null;
    let camera = null;
    let renderer = null;
    let rootGroup = null;
    let chamberGroup = null;
    let outerDoor = null;
    let innerDoor = null;
    let personGroup = null;
    let alarmLight = null;
    let statusLine = null;
    let animationStarted = false;
    let threeLoading = false;
    let lastStatus = null;
    let innerDoorStableState = "UNKNOWN";
    let innerDoorPendingState = null;
    let innerDoorPendingCount = 0;
    let persistedDetectedPersonCount = 0;

    const view = {
        rotationX: -0.42,
        rotationY: 0.62,
        targetRotationX: -0.42,
        targetRotationY: 0.62,
        zoom: 1,
        targetZoom: 1,
        dragging: false,
        lastX: 0,
        lastY: 0,
    };

    function loadThree(callback) {
        if (window.THREE) {
            callback();
            return;
        }

        if (threeLoading) {
            const wait = setInterval(() => {
                if (window.THREE) {
                    clearInterval(wait);
                    callback();
                }
            }, 100);
            return;
        }

        threeLoading = true;

        const script = document.createElement("script");
        script.src = THREE_URL;
        script.onload = callback;
        script.onerror = () => console.warn("[VISUAL] Failed to load Three.js");
        document.head.appendChild(script);
    }

    function normalizeDoor(value) {
        if (!value) {
            return "UNKNOWN";
        }

        return String(value).toUpperCase();
    }

    function resolveVisualMode(status) {
        if (status.alarm_level === "LOCKDOWN" || status.fsm_state === "SECURITY_LOCKDOWN") {
            return "lockdown";
        }

        if (status.alarm_level === "WARNING" || status.alarm_active) {
            return "warning";
        }

        return "normal";
    }

    function colorByMode(mode) {
        if (mode === "lockdown") {
            return 0xef4444;
        }

        if (mode === "warning") {
            return 0xf59e0b;
        }

        return 0x22d3ee;
    }

    function makeMaterial(color, options = {}) {
        return new THREE.MeshStandardMaterial({
            color,
            roughness: options.roughness ?? 0.45,
            metalness: options.metalness ?? 0.25,
            transparent: options.transparent ?? false,
            opacity: options.opacity ?? 1,
            emissive: options.emissive ?? 0x000000,
            emissiveIntensity: options.emissiveIntensity ?? 0,
        });
    }

    function makeBox(width, height, depth, material) {
        const geometry = new THREE.BoxGeometry(width, height, depth);
        const mesh = new THREE.Mesh(geometry, material);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        return mesh;
    }

    function addEdges(mesh, color = 0x38bdf8, opacity = 0.32) {
        const edges = new THREE.EdgesGeometry(mesh.geometry);
        const line = new THREE.LineSegments(
            edges,
            new THREE.LineBasicMaterial({
                color,
                transparent: true,
                opacity,
            }),
        );

        mesh.add(line);
        return line;
    }

    function createTextSprite(text, color = "#cbd5e1") {
        const canvas = document.createElement("canvas");
        canvas.width = 512;
        canvas.height = 128;

        const ctx = canvas.getContext("2d");

        function draw(value, drawColor) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.font = "700 34px Arial";
            ctx.fillStyle = drawColor;
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(value, canvas.width / 2, canvas.height / 2);
        }

        draw(text, color);

        const texture = new THREE.CanvasTexture(canvas);
        const material = new THREE.SpriteMaterial({
            map: texture,
            transparent: true,
        });

        const sprite = new THREE.Sprite(material);
        sprite.scale.set(2.8, 0.7, 1);
        sprite.userData.drawText = draw;
        sprite.userData.texture = texture;

        return sprite;
    }

    function updateTextSprite(sprite, text, color = "#cbd5e1") {
        if (!sprite || !sprite.userData.drawText || !sprite.userData.texture) {
            return;
        }

        sprite.userData.drawText(text, color);
        sprite.userData.texture.needsUpdate = true;
    }

    function createSingleDoorSystem(xPosition, label, side) {
        const group = new THREE.Group();
        group.position.set(xPosition, 0, 0);

        const frameMat = makeMaterial(0x334155, {
            metalness: 0.35,
            roughness: 0.35,
            emissive: 0x0f172a,
            emissiveIntensity: 0.08,
        });

        const doorMat = makeMaterial(0x1e293b, {
            metalness: 0.25,
            roughness: 0.22,
            transparent: true,
            opacity: 0.94,
            emissive: 0x0f172a,
            emissiveIntensity: 0.15,
        });

        const frameWidth = 1.02;
        const frameHeight = 1.62;
        const frameDepth = 0.12;
        const doorWidth = 0.82;
        const doorHeight = 1.42;
        const hingeOffset = 0.41;

        const frameTop = makeBox(frameWidth, 0.12, frameDepth, frameMat);
        frameTop.position.y = 1.48;

        const frameLeft = makeBox(0.10, frameHeight, frameDepth, frameMat);
        frameLeft.position.set(-0.46, 0.73, 0);

        const frameRight = makeBox(0.10, frameHeight, frameDepth, frameMat);
        frameRight.position.set(0.46, 0.73, 0);

        const pivot = new THREE.Group();

        if (side === "left") {
            pivot.position.set(-hingeOffset, 0.73, 0);
        } else {
            pivot.position.set(hingeOffset, 0.73, 0);
        }

        const leaf = makeBox(doorWidth, doorHeight, 0.06, doorMat);

        if (side === "left") {
            leaf.position.x = doorWidth / 2;
        } else {
            leaf.position.x = -doorWidth / 2;
        }

        addEdges(leaf, 0x94a3b8, 0.45);

        const handleMat = makeMaterial(0x94a3b8, {
            metalness: 0.7,
            roughness: 0.2,
            emissive: 0x334155,
            emissiveIntensity: 0.12,
        });

        const handle = makeBox(0.03, 0.18, 0.03, handleMat);
        handle.position.set(side === "left" ? 0.65 : -0.65, 0, 0.045);
        leaf.add(handle);

        pivot.add(leaf);

        const labelSprite = createTextSprite(label);
        labelSprite.position.set(0, 1.92, 0);

        group.add(frameTop, frameLeft, frameRight, pivot, labelSprite);

        return {
            group,
            pivot,
            leaf,
            side,
            targetState: "UNKNOWN",
        };
    }

    function personColorByCount(total) {
        if (total === 1) {
            return {
                main: 0x22c55e,
                emissive: 0x15803d,
                label: "#86efac",
            };
        }

        if (total >= 2) {
            return {
                main: 0xef4444,
                emissive: 0x991b1b,
                label: "#fca5a5",
            };
        }

        return {
            main: 0x64748b,
            emissive: 0x334155,
            label: "#cbd5e1",
        };
    }

    function createPerson(index, total) {
        const group = new THREE.Group();

        const positions = [
            { x: 0.00, z: 0.00 },
            { x: -0.42, z: 0.22 },
            { x: 0.42, z: 0.22 },
            { x: 0.00, z: -0.42 },
        ];

        const position = positions[index] || { x: 0, z: 0 };
        group.position.set(position.x, 0.08, position.z);

        const personColors = personColorByCount(total);

        const bodyMat = makeMaterial(personColors.main, {
            emissive: personColors.emissive,
            emissiveIntensity: total >= 2 ? 0.82 : 0.48,
            metalness: 0.12,
            roughness: 0.28,
        });

        const darkMat = makeMaterial(0x0f172a, {
            emissive: 0x020617,
            emissiveIntensity: 0.2,
            metalness: 0.18,
            roughness: 0.38,
        });

        const head = new THREE.Mesh(new THREE.SphereGeometry(0.15, 24, 24), bodyMat);
        head.position.y = 0.88;
        head.castShadow = true;

        const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.16, 0.48, 8, 18), bodyMat);
        body.position.y = 0.48;
        body.castShadow = true;

        const leftArm = makeBox(0.055, 0.36, 0.055, darkMat);
        leftArm.position.set(-0.22, 0.52, 0);
        leftArm.rotation.z = -0.18;

        const rightArm = makeBox(0.055, 0.36, 0.055, darkMat);
        rightArm.position.set(0.22, 0.52, 0);
        rightArm.rotation.z = 0.18;

        const leftLeg = makeBox(0.065, 0.34, 0.065, darkMat);
        leftLeg.position.set(-0.07, 0.12, 0);

        const rightLeg = makeBox(0.065, 0.34, 0.065, darkMat);
        rightLeg.position.set(0.07, 0.12, 0);

        const ring = new THREE.Mesh(
            new THREE.TorusGeometry(0.31, 0.018, 8, 40),
            makeMaterial(personColors.main, {
                transparent: true,
                opacity: 0.78,
                emissive: personColors.emissive,
                emissiveIntensity: total >= 2 ? 0.95 : 0.65,
            }),
        );

        ring.rotation.x = Math.PI / 2;
        ring.position.y = 0.03;

        const label = createTextSprite(String(index + 1), personColors.label);
        label.scale.set(0.45, 0.18, 1);
        label.position.set(0, 1.2, 0);

        group.add(head, body, leftArm, rightArm, leftLeg, rightLeg, ring, label);

        return group;
    }

    function buildScene() {
        const canvas = document.getElementById("mantrap-3d-canvas");
        const wrap = document.getElementById("mantrap-3d-canvas-wrap");

        if (!canvas || !wrap || scene) {
            return;
        }

        scene = new THREE.Scene();
        scene.fog = new THREE.Fog(0x020617, 8, 18);

        camera = new THREE.PerspectiveCamera(42, wrap.clientWidth / wrap.clientHeight, 0.1, 100);
        camera.position.set(0, 3.4, 7.4);

        renderer = new THREE.WebGLRenderer({
            canvas,
            antialias: true,
            alpha: true,
            powerPreference: "high-performance",
        });

        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.7));
        renderer.setSize(wrap.clientWidth, wrap.clientHeight);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;

        rootGroup = new THREE.Group();

        // Raise the whole model higher.
        rootGroup.position.set(0, 1.65, 0);

        scene.add(rootGroup);

        const ambient = new THREE.AmbientLight(0x94a3b8, 0.62);
        scene.add(ambient);

        const keyLight = new THREE.DirectionalLight(0xffffff, 1.55);
        keyLight.position.set(3, 6, 5);
        keyLight.castShadow = true;
        scene.add(keyLight);

        alarmLight = new THREE.PointLight(0x22d3ee, 1.7, 7);
        alarmLight.position.set(0, 2.6, 0);
        scene.add(alarmLight);

        const floorMat = makeMaterial(0x0f172a, {
            metalness: 0.18,
            roughness: 0.58,
            emissive: 0x020617,
            emissiveIntensity: 0.08,
        });

        const floor = makeBox(7.2, 0.08, 3.8, floorMat);
        floor.position.y = -0.08;
        rootGroup.add(floor);
        addEdges(floor, 0x22d3ee, 0.2);

        const chamberMat = makeMaterial(0x082f49, {
            transparent: true,
            opacity: 0.18,
            metalness: 0.2,
            roughness: 0.25,
            emissive: 0x0891b2,
            emissiveIntensity: 0.18,
        });

        chamberGroup = new THREE.Group();

        const chamberWidth = 3.6;
        const chamberDepth = 2.6;
        const wallHeight = 1.75;
        const wallThickness = 0.05;
        const doorOpeningWidth = 0.98;

        const chamberFloor = makeBox(chamberWidth, 0.06, chamberDepth, chamberMat);
        chamberFloor.position.y = 0.02;

        const backWall = makeBox(chamberWidth, wallHeight, 0.06, chamberMat);
        backWall.position.set(0, wallHeight / 2, -chamberDepth / 2);

        const frontWall = makeBox(chamberWidth, wallHeight, 0.04, chamberMat);
        frontWall.position.set(0, wallHeight / 2, chamberDepth / 2);

        const sideSegmentLength = (chamberDepth - doorOpeningWidth) / 2;
        const segmentZ = (doorOpeningWidth / 2) + (sideSegmentLength / 2);

        const leftWallFront = makeBox(wallThickness, wallHeight, sideSegmentLength, chamberMat);
        leftWallFront.position.set(-chamberWidth / 2, wallHeight / 2, segmentZ);

        const leftWallBack = makeBox(wallThickness, wallHeight, sideSegmentLength, chamberMat);
        leftWallBack.position.set(-chamberWidth / 2, wallHeight / 2, -segmentZ);

        const rightWallFront = makeBox(wallThickness, wallHeight, sideSegmentLength, chamberMat);
        rightWallFront.position.set(chamberWidth / 2, wallHeight / 2, segmentZ);

        const rightWallBack = makeBox(wallThickness, wallHeight, sideSegmentLength, chamberMat);
        rightWallBack.position.set(chamberWidth / 2, wallHeight / 2, -segmentZ);

        const leftLintel = makeBox(wallThickness, 0.22, doorOpeningWidth, chamberMat);
        leftLintel.position.set(-chamberWidth / 2, wallHeight - 0.11, 0);

        const rightLintel = makeBox(wallThickness, 0.22, doorOpeningWidth, chamberMat);
        rightLintel.position.set(chamberWidth / 2, wallHeight - 0.11, 0);

        [
            chamberFloor,
            backWall,
            frontWall,
            leftWallFront,
            leftWallBack,
            rightWallFront,
            rightWallBack,
            leftLintel,
            rightLintel,
        ].forEach((mesh) => {
            addEdges(mesh, 0x22d3ee, 0.42);
            chamberGroup.add(mesh);
        });

        const chamberLabel = createTextSprite("SECURE CHAMBER", "#bae6fd");
        chamberLabel.position.set(0, 2.05, -0.35);
        chamberGroup.add(chamberLabel);

        personGroup = new THREE.Group();
        personGroup.position.y = 0.05;
        chamberGroup.add(personGroup);

        rootGroup.add(chamberGroup);

        // Doors are now integrated into the chamber wall openings.
        outerDoor = createSingleDoorSystem(-(chamberWidth / 2) - 0.02, "OUTER DOOR", "left");
        innerDoor = createSingleDoorSystem((chamberWidth / 2) + 0.02, "INNER DOOR", "right");

        outerDoor.group.rotation.y = Math.PI / 2;
        innerDoor.group.rotation.y = Math.PI / 2;

        rootGroup.add(outerDoor.group);
        rootGroup.add(innerDoor.group);

        statusLine = new THREE.Mesh(
            new THREE.TorusGeometry(1.95, 0.018, 8, 120),
            makeMaterial(0x22d3ee, {
                transparent: true,
                opacity: 0.64,
                emissive: 0x0891b2,
                emissiveIntensity: 0.38,
            }),
        );

        statusLine.rotation.x = Math.PI / 2;
        statusLine.position.y = 0.05;
        chamberGroup.add(statusLine);

        bindMouseControls(wrap);
        bindResetButton();

        window.addEventListener("resize", resizeRenderer);

        if (!animationStarted) {
            animationStarted = true;
            animate();
        }
    }

    function bindMouseControls(wrap) {
        wrap.addEventListener("pointerdown", (event) => {
            view.dragging = true;
            view.lastX = event.clientX;
            view.lastY = event.clientY;
            wrap.setPointerCapture(event.pointerId);
        });

        wrap.addEventListener("pointermove", (event) => {
            if (!view.dragging) {
                return;
            }

            const dx = event.clientX - view.lastX;
            const dy = event.clientY - view.lastY;

            view.targetRotationY += dx * 0.008;
            view.targetRotationX += dy * 0.006;
            view.targetRotationX = Math.max(-1.05, Math.min(0.1, view.targetRotationX));

            view.lastX = event.clientX;
            view.lastY = event.clientY;
        });

        wrap.addEventListener("pointerup", () => {
            view.dragging = false;
        });

        wrap.addEventListener("pointercancel", () => {
            view.dragging = false;
        });

        wrap.addEventListener("wheel", (event) => {
            event.preventDefault();

            view.targetZoom += event.deltaY * 0.001;
            view.targetZoom = Math.max(0.72, Math.min(1.55, view.targetZoom));
        }, { passive: false });
    }

    function bindResetButton() {
        const button = document.getElementById("mantrap-3d-reset-view");

        if (!button) {
            return;
        }

        button.addEventListener("click", () => {
            view.targetRotationX = -0.42;
            view.targetRotationY = 0.62;
            view.targetZoom = 1;
        });
    }

    function resizeRenderer() {
        const wrap = document.getElementById("mantrap-3d-canvas-wrap");

        if (!wrap || !camera || !renderer) {
            return;
        }

        camera.aspect = wrap.clientWidth / wrap.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(wrap.clientWidth, wrap.clientHeight);
    }

    function resolveStableInnerDoorState(state) {
        const normalized = normalizeDoor(state);
        const systemIsOff = lastStatus && (
            lastStatus.fsm_state === "SYSTEM_OFF" ||
            lastStatus.system_online === false
        );

        if (systemIsOff && normalized !== "OPEN") {
            innerDoorStableState = "CLOSED";
            innerDoorPendingState = null;
            innerDoorPendingCount = 0;
            return innerDoorStableState;
        }

        if (normalized === "UNKNOWN") {
            return innerDoorStableState;
        }

        if (normalized === innerDoorStableState) {
            innerDoorPendingState = null;
            innerDoorPendingCount = 0;
            return innerDoorStableState;
        }

        if (normalized !== innerDoorPendingState) {
            innerDoorPendingState = normalized;
            innerDoorPendingCount = 1;
            return innerDoorStableState;
        }

        innerDoorPendingCount += 1;

        const requiredStableReads = systemIsOff ? 8 : 3;

        if (innerDoorPendingCount >= requiredStableReads) {
            innerDoorStableState = normalized;
            innerDoorPendingState = null;
            innerDoorPendingCount = 0;
        }

        return innerDoorStableState;
    }

    function updateDoorVisual(door, state) {
        if (!door) {
            return;
        }

        const normalized = normalizeDoor(state);
        door.targetState = normalized;

        // Single door leaf opens inward toward the chamber.
        let targetAngle = 0;

        if (normalized === "OPEN") {
            if (door.side === "left") {
                targetAngle = -Math.PI / 2;
            } else {
                targetAngle = Math.PI / 2;
            }
        }

        door.pivot.rotation.y += (targetAngle - door.pivot.rotation.y) * 0.12;

        const color = normalized === "OPEN"
            ? 0x22d3ee
            : normalized === "CLOSED"
                ? 0x10b981
                : 0x64748b;

        door.group.traverse((child) => {
            if (child.isMesh && child.material && child.material.emissive) {
                child.material.emissive.setHex(color);
                child.material.emissiveIntensity = normalized === "UNKNOWN" ? 0.08 : 0.18;
            }
        });
    }

    function resolveDisplayPersonCount(status) {
        const liveCount = Number(status.yolo_person_count) || 0;
        const yoloRunning = Boolean(status.yolo_running);

        if (yoloRunning) {
            persistedDetectedPersonCount = liveCount;
            return liveCount;
        }

        if (liveCount > 0) {
            persistedDetectedPersonCount = liveCount;
            return liveCount;
        }

        return persistedDetectedPersonCount;
    }

    function renderPersons(count) {
        if (!personGroup) {
            return;
        }

        const total = Math.max(0, Math.min(Number(count) || 0, 4));

        if (personGroup.userData.lastCount === total) {
            return;
        }

        personGroup.userData.lastCount = total;
        personGroup.clear();

        for (let index = 0; index < total; index += 1) {
            personGroup.add(createPerson(index, total));
        }
    }

    function applyMode(mode) {
        const color = colorByMode(mode);

        if (alarmLight) {
            alarmLight.color.setHex(color);
            alarmLight.intensity = mode === "lockdown" ? 3.2 : mode === "warning" ? 2.4 : 1.6;
        }

        if (statusLine && statusLine.material) {
            statusLine.material.color.setHex(color);
            statusLine.material.emissive.setHex(color);
            statusLine.material.opacity = mode === "normal" ? 0.5 : 0.82;
        }

        if (chamberGroup) {
            chamberGroup.traverse((child) => {
                if (child.isMesh && child.material && child.material.emissive) {
                    child.material.emissive.setHex(color);
                    child.material.emissiveIntensity = mode === "lockdown" ? 0.34 : mode === "warning" ? 0.26 : 0.16;
                }
            });
        }
    }

    function updateOverlay(status) {
        const stage = document.getElementById("mantrap-stage");
        const modeBadge = document.getElementById("mantrap-visual-mode-badge");
        const workflowLabel = document.getElementById("visual-workflow-label");
        const personCount = document.getElementById("visual-person-count");
        const mode = resolveVisualMode(status);

        if (stage) {
            stage.dataset.mode = mode;
        }

        if (modeBadge) {
            modeBadge.textContent = mode.toUpperCase();
            modeBadge.className = `badge ${mode === "lockdown" ? "bg-danger" : mode === "warning" ? "bg-warning" : "bg-success"}`;
        }

        if (workflowLabel) {
            const label = window.MantrapLabels
                ? window.MantrapLabels.workflowLabel(status.fsm_state, status.workflow)
                : (status.workflow?.workflow_label || status.fsm_state || "--");

            workflowLabel.textContent = `Workflow: ${label}`;
        }

        if (personCount) {
            personCount.textContent = status.yolo_person_count ?? 0;
        }

        applyMode(mode);
    }

    function animate() {
        requestAnimationFrame(animate);

        if (!renderer || !scene || !camera || !rootGroup) {
            return;
        }

        view.rotationX += (view.targetRotationX - view.rotationX) * 0.08;
        view.rotationY += (view.targetRotationY - view.rotationY) * 0.08;
        view.zoom += (view.targetZoom - view.zoom) * 0.08;

        rootGroup.rotation.x = view.rotationX;
        rootGroup.rotation.y = view.rotationY;
        rootGroup.scale.setScalar(view.zoom);

        if (lastStatus) {
            updateDoorVisual(outerDoor, lastStatus.outer_door);
            updateDoorVisual(innerDoor, resolveStableInnerDoorState(lastStatus.inner_door));
        }

        const time = performance.now() * 0.001;

        if (statusLine) {
            statusLine.rotation.z = time * 0.28;
        }

        if (personGroup) {
            personGroup.children.forEach((person, index) => {
                person.position.y = 0.05 + Math.sin(time * 2.2 + index) * 0.035;
                person.rotation.y += 0.01;
            });
        }

        renderer.render(scene, camera);
    }

    function init() {
        loadThree(() => {
            buildScene();

            if (lastStatus) {
                renderPersons(resolveDisplayPersonCount(lastStatus));
                updateOverlay(lastStatus);
            }
        });
    }

    return {
        update(status) {
            lastStatus = status || {};

            if (!scene) {
                init();
            }

            if (scene) {
                renderPersons(resolveDisplayPersonCount(lastStatus));
                updateOverlay(lastStatus);
            }
        },
    };
})();
