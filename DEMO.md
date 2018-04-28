# Demo

## k8s: set namespace
```shell
kubectl config set-context $(kubectl config current-context) --namespace=production
```

## api: GET while disrupting database
```shell
while true; do date && curl -s http://api.production.k8s.lookup8.com:8000/users/ | jq '.[] | .username'; sleep 1; done
```

## database: query number of users
```shell
kubectl exec $(kubectl get pods -l app=mysql-client -o name | awk -F'/' '{ print $2 }') -i -t -- bash -ic "while sleep 1; do date && mysql -h production-cluster-pxc.production -u production -pproduction -e 'SELECT count(*) as total_users FROM production.auth_user'; done"
```

## k8s: watch our CI master and slaves
```shell
watch -p -n 1 kubectl -n ci get pods
```

## k8s: watch our pods during application rollout
```shell
watch -p -n 1 kubectl get pods -l release=mcd-meetup-api-production
```

## database: watch cluster pods
```shell
watch -p -n 1 kubectl get pods -l app=production-cluster-pxc
```

## k8s: get cluster size
```shell
kubectl exec $(kubectl get pods -l app=mysql-client -o name | awk -F'/' '{ print $2 }') -i -t -- bash -ic "while sleep 1; do date && mysql -h production-cluster-pxc.production -u production -pproduction -e 'show status like \"wsrep_cluster_size\"'; done"
```