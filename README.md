# 🚀 Homelab GitOps

This repository contains the automated configuration of my Homelab, managed under the **GitOps** methodology to ensure a reproducible, scalable, and secure environment.

## 🛠 Technologies Used

*   **Orchestration:** [Kubernetes](https://kubernetes.io/) (K8s) on a bare-metal environment.
*   **GitOps:** [FluxCD](https://fluxcd.io/) for continuous synchronization between this repository and the cluster.
*   **Networking:**
    *   **Cilium LB:** Local network IP management for Kubernetes services.
    *   **WireGuard:** Secure tunnel for interconnection between the local cluster and external nodes (VPS).
    *   **Kubernetes Gateway API with Cilium backend:** HTTP traffic management and internal routing.
*   **Security and Access:**
    *   **Cloudflare:** DNS, WAF, and perimeter protection layer.
    *   **VPS:** External entry node acting as a reverse proxy to the homelab via an encrypted tunnel.
    *   **Variable Substitution:** Secrets and sensitive variables management integrated into FluxCD to prevent leaks in Git.
    *   **Cluster-wide Encryption:** This cluster is ciphered with IPSec between nodes and mTLS between Pods, forcing security and auditability.
## 🏗 Architecture

The architecture is based on an **Outbound Tunnel** model. The local cluster establishes an encrypted connection to an external VPS using WireGuard. External traffic reaches the VPS, is filtered, and is securely redirected through the tunnel to the Kubernetes Ingress Controller on the local network.

---


