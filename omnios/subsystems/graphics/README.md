# OmniGraph

Planned user-mode compositor using Vulkan. API translation candidates: DXVK for D3D9/10/11 and vkd3d-proton for D3D12; OpenGL through Mesa/Zink where extensions match. Metal and SurfaceFlinger need distinct adapters. The kernel should mediate GPU memory/queues and isolation, not intercept user-mode DirectX/Metal calls as syscalls.
