# docker-
docker项目部署实战0-1

用户 → ALB → K8s Ingress → Flask Pod (HPA自动扩缩)
                              ↓
                    ┌─────────┴─────────┐
                    ↓                   ↓
              Redis Cluster         MySQL RDS
              (热销榜缓存)           (订单持久化)
                    ↓                   ↓
              Prometheus ←── 监控 ──→ Grafana
