#!/bin/bash
# ProktorAI — Kubernetes жылдам орналастыру скрипті
# Қолданылуы: ./k8s/deploy.sh [apply|delete|status]

set -e
ACTION=${1:-apply}
K8S_DIR="$(dirname "$0")"

case "$ACTION" in
  apply)
    echo "ProktorAI Kubernetes-ке орналастырылуда..."
    kubectl $ACTION -f "$K8S_DIR/namespace.yml"
    kubectl $ACTION -f "$K8S_DIR/secrets.yml"
    kubectl $ACTION -f "$K8S_DIR/postgres.yml"
    kubectl $ACTION -f "$K8S_DIR/redis.yml"
    kubectl $ACTION -f "$K8S_DIR/kafka.yml"
    echo "Инфрақұрылым дайын болғанша күтілуде (30с)..."
    sleep 30
    kubectl $ACTION -f "$K8S_DIR/backend.yml"
    kubectl $ACTION -f "$K8S_DIR/ai-service.yml"
    kubectl $ACTION -f "$K8S_DIR/frontend.yml"
    echo "Барлық сервистер орналастырылды!"
    kubectl get pods -n proktorai
    ;;
  delete)
    echo "ProktorAI жойылуда..."
    kubectl delete namespace proktorai --ignore-not-found
    echo "Жойылды."
    ;;
  status)
    kubectl get pods,services,ingress -n proktorai
    ;;
  *)
    echo "Қолданылуы: $0 [apply|delete|status]"
    exit 1
    ;;
esac