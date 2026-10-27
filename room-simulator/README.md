# Headspace: mouse-controlled room vision

A self-contained browser prototype for a virtual head in a furnished living room. Three.js renders the camera's view. No external 3D models, textures, APIs, or credentials are needed.

## Run

Requires Node.js 18+ (Node 20+ recommended) and a browser with WebGL.

```sh
cd /workspace/single-view-image-rectification/room-simulator
npm ci
npm run dev
```

Open the server using your environment's port forwarding, or open the address printed by Vite when running locally. `npm run build` creates a static site in `dist`; `npm run preview` serves that build.

## Controls and measurements

- Drag inside the scene to turn left/right and look up/down. Touch dragging also works.
- Focus the scene and use arrow keys for keyboard rotation; R or Reset view restores defaults.
- Adjust eye height (0.8–2.1 m) and vertical field of view (40–100°).
- The crosshair identifies the first visible surface along the camera's viewing direction. Distance is the straight-line camera-to-surface distance in meters, not distance to the object's center.
- Width × height × depth are declared scene dimensions along the object's local axes. Decorative organic shapes use nominal dimensions.
- The overhead map shows the head position and horizontal field of view. Positive yaw turns right from the initial forward direction (world −Z); positive pitch looks up. Y is vertical.

The room measures 6 × 7 × 3 m. The camera starts at (0, 1.65, 2.4) m and stays at the same floor position while rotating. Furniture measurements are known scene inputs, not estimates inferred from a photograph. This prototype does not yet perform single-image reconstruction, real head tracking, stereo rendering, or walking.

The Python rectification experiments in `../src` are independent and remain unchanged.
