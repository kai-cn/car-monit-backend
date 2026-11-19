docker exec k3d-v3-server-0 kubectl create deployment v3-ci-probe \
  --image=rancher/mirrored-pause:3.6 --replicas=3 \
  --dry-run=client -o yaml | docker exec -i k3d-v3-server-0 kubectl apply -f -
docker exec k3d-v3-server-0 kubectl rollout status deployment/v3-ci-probe --timeout=240s
docker exec k3d-v3-server-0 kubectl get pods -l app=v3-ci-probe -o wide

