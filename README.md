# Uso
Lo que necesitas para que funcione es:
- Un servidor con usuario y base de datos "mealie".
- ``
  flux bootstrap github \
  --owner=github-username \
  --repository=homelab \
  --branch=main \
  --path=./clusters/production \ #Esto debe ser relativo a donde estes en la máquina mientras ejecutes el comando.
  --personal 
``
- kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.13.12/config/manifests/metallb-native.yaml (puedes usar el installer normal pero por alguna razon me daba errores)
- Instalar CNI Flannel
- Al hacer el kubectl init hacerlo con las IPs de Flannel.

